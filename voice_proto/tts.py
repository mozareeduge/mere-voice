from __future__ import annotations

import hashlib
import importlib.metadata
import re
import shutil
import subprocess
import wave
from pathlib import Path
from typing import Iterable

import numpy as np

from .domain import canonical_json, sha256_bytes, sha256_text
from .storage import DRY_DIR, MODEL_PROFILE, ROOT, atomic_write_json, load_lines, now_iso, read_json
from .wavio import duration_ms

# v2 synthetic control (handoff v2.0, Decision C): canonical text_fa is the only input authority.
# Commas/colons/semicolons stay INSIDE a synthesis span so Piper/eSpeak realises ordinary clause prosody.
# With sentence_gap_ms == 0 (default) the whole line is one native Piper call; with a positive gap the line is
# split ONLY at sentence terminals and that explicit, versioned silence is inserted between completed sentences.
SYNTHESIS_PIPELINE_REVISION = "PIPER-CANONICAL-SPANS-V2"
DEFAULT_SENTENCE_GAP_MS = 0
PRONUNCIATION_OVERRIDES = ROOT / "data" / "config" / "pronunciation_overrides.json"
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?؟…])\s+")


def _line_map():
    return {row["line_id"]: row for row in load_lines()}


def _profile():
    return read_json(MODEL_PROFILE, {})


def _file_sha(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _spoken_text(line: dict) -> str:
    """Text fed to synthesis: always the canonical source text.

    `text_fa_vocalized` is historical evidence only (it violates lexical invariance on 11/17 lines) and must
    never drive release synthesis. Pronunciation repair is done by exact-span overrides (see load_overrides).
    """
    return line["text_fa"]


def load_overrides(path: Path | None = None) -> dict[str, list[dict]]:
    """Approved exact-span raw-phoneme overrides, keyed by line_id. Draft entries are ignored."""
    doc = read_json(path or PRONUNCIATION_OVERRIDES, {"lines": {}})
    out: dict[str, list[dict]] = {}
    for line_id, entries in (doc.get("lines") or {}).items():
        approved = [e for e in entries if e.get("status") == "approved"]
        if approved:
            out[line_id] = approved
    return out


def apply_overrides(text: str, overrides: list[dict]) -> str:
    """Replace each exact source span (nth occurrence) with a Piper raw eSpeak phoneme block `[[ ... ]]`."""
    spans = []
    for entry in overrides:
        span, nth = entry["source"], int(entry.get("occurrence", 1))
        start = -1
        for _ in range(nth):
            start = text.find(span, start + 1)
            if start < 0:
                raise RuntimeError(f"Pronunciation override {entry.get('id')}: span {span!r} occurrence {nth} not found in source text")
        spans.append((start, start + len(span), entry["raw_espeak_ipa"].strip()))
    spans.sort()
    for (_, prev_end, _), (start, _, _) in zip(spans, spans[1:]):
        if start < prev_end:
            raise RuntimeError("Pronunciation overrides overlap")
    for start, end, ipa in reversed(spans):
        text = text[:start] + f"[[ {ipa} ]]" + text[end:]
    return text


def _override_identity(overrides: list[dict]) -> list[dict]:
    return [{k: e.get(k) for k in ("id", "source", "occurrence", "raw_espeak_ipa")} for e in overrides]


def _asset_key(line: dict, profile_identity: dict, overrides: list[dict] | None = None) -> str:
    material = {
        "text_sha256": sha256_text(_spoken_text(line)),
        "overrides": _override_identity(overrides or []),
        "profile": profile_identity,
    }
    return sha256_text(canonical_json(material))


def _synthesis_spans(text: str, sentence_gap_ms: int) -> list[dict]:
    """Split only at sentence terminals, and only when an explicit sentence gap is requested."""
    text = text.strip()
    if sentence_gap_ms <= 0:
        return [{"text": text, "pause_after_ms": 0}] if text else []
    parts = [p.strip() for p in _SENTENCE_SPLIT.split(text) if p and p.strip()]
    return [{"text": p, "pause_after_ms": sentence_gap_ms if i < len(parts) - 1 else 0} for i, p in enumerate(parts)]


def _synthesis_identity(params: dict, sentence_gap_ms: int) -> dict:
    return {
        "pipeline_revision": SYNTHESIS_PIPELINE_REVISION,
        "input_authority": "text_fa",
        "sentence_gap_ms": sentence_gap_ms,
        "render_parameters": params,
    }


def render_with_piper(line_ids: Iterable[str] | None = None) -> list[dict]:
    try:
        from piper import PiperVoice, SynthesisConfig
    except Exception as exc:
        raise RuntimeError("piper-tts is not installed. Run scripts/setup.ps1 (Windows) or pip install -r requirements.txt.") from exc

    profile = _profile()
    model_path = ROOT / profile["model_path"]
    config_path = ROOT / profile["config_path"]
    if not model_path.exists() or not config_path.exists():
        raise RuntimeError("Mana Piper model/config are missing. Run scripts/fetch_model.py first.")
    actual_sha = _file_sha(model_path)
    config_doc = read_json(config_path, {})
    expected_cfg = profile.get("expected_config_invariants", {})
    actual_cfg = {
        "sample_rate": (config_doc.get("audio") or {}).get("sample_rate"),
        "language_code": (config_doc.get("language") or {}).get("code"),
        "espeak_voice": (config_doc.get("espeak") or {}).get("voice"),
        "phoneme_type": config_doc.get("phoneme_type"),
        "num_speakers": config_doc.get("num_speakers"),
    }
    mismatch = {k: (expected_cfg[k], actual_cfg.get(k)) for k in expected_cfg if actual_cfg.get(k) != expected_cfg[k]}
    if mismatch:
        raise RuntimeError(f"Mana config invariant mismatch: {mismatch}")
    expected = profile.get("expected_model_sha256")
    if expected and actual_sha != expected:
        raise RuntimeError(f"Mana model hash mismatch: expected {expected}, got {actual_sha}")

    lines = _line_map()
    selected = list(line_ids or lines.keys())
    voice = PiperVoice.load(str(model_path))
    params = profile.get("render_parameters", {})
    sentence_gap_ms = int((profile.get("prosody") or {}).get("sentence_gap_ms", DEFAULT_SENTENCE_GAP_MS))
    overrides_by_line = load_overrides()
    cfg = SynthesisConfig(**params)
    engine_version = importlib.metadata.version("piper-tts")
    profile_identity = {
        "engine": "piper-tts",
        "engine_version": engine_version,
        "model_sha256": actual_sha,
        "config_sha256": _file_sha(config_path),
        "synthesis": _synthesis_identity(params, sentence_gap_ms),
    }
    sample_rate = int((config_doc.get("audio") or {}).get("sample_rate") or 22050)
    results = []
    for line_id in selected:
        line = lines[line_id]
        line_overrides = overrides_by_line.get(line_id, [])
        chunks = _synthesis_spans(apply_overrides(_spoken_text(line), line_overrides), sentence_gap_ms)
        key = _asset_key(line, profile_identity, line_overrides)
        asset_id = f"ASSET-{line_id}-{key[:12]}"
        wav_path = DRY_DIR / f"{asset_id}.wav"
        if not wav_path.exists():
            DRY_DIR.mkdir(parents=True, exist_ok=True)
            pieces: list[np.ndarray] = []
            tmp = wav_path.with_suffix(".tmp.wav")
            try:
                for index, chunk in enumerate(chunks):
                    chunk_tmp = tmp.with_name(f"{tmp.stem}.{index}.tmp.wav")
                    try:
                        with wave.open(str(chunk_tmp), "wb") as wav_file:
                            voice.synthesize_wav(chunk["text"], wav_file, syn_config=cfg)
                        audio, sr = _read_wav_mono(chunk_tmp)
                        if sr != sample_rate:
                            raise RuntimeError(f"Piper sample rate drifted: {sr} != {sample_rate}")
                        pieces.append(audio)
                        if chunk["pause_after_ms"] > 0:
                            pieces.append(np.zeros((1, int(sample_rate * chunk["pause_after_ms"] / 1000)), dtype=np.float32))
                    finally:
                        chunk_tmp.unlink(missing_ok=True)
                if not pieces:
                    raise RuntimeError(f"No audio produced for {line_id}")
                _write_wav(tmp, np.concatenate(pieces, axis=1), sample_rate)
                tmp.replace(wav_path)
            finally:
                tmp.unlink(missing_ok=True)
        meta = {
            "asset_id": asset_id,
            "line_id": line_id,
            "status": "READY",
            "source_text_sha256": sha256_text(line["text_fa"]),
            "spoken_text": _spoken_text(line),
            "spoken_text_sha256": sha256_text(_spoken_text(line)),
            "spoken_text_is_canonical": _spoken_text(line) == line["text_fa"],
            "pronunciation_overrides": _override_identity(line_overrides),
            "source_status": line.get("source_status"),
            "engine": "piper-tts",
            "engine_version": engine_version,
            "profile_id": profile.get("profile_id"),
            "model_sha256": actual_sha,
            "config_sha256": profile_identity["config_sha256"],
            "synthesis_pipeline": _synthesis_identity(params, sentence_gap_ms),
            "synthesis_spans": [{"text_sha256": sha256_text(c["text"]), "pause_after_ms": c["pause_after_ms"]} for c in chunks],
            "wav_path": str(wav_path.relative_to(ROOT)).replace("\\", "/"),
            "wav_sha256": _file_sha(wav_path),
            "duration_ms": duration_ms(wav_path),
            "rendered_at": now_iso(),
            "fixture": False,
        }
        atomic_write_json(DRY_DIR / f"{line_id}.json", meta)
        results.append(meta)
    return results


def _read_wav_mono(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        channels = w.getnchannels()
        sample_rate = w.getframerate()
        raw = w.readframes(w.getnframes())
    audio = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    return audio.reshape(1, -1), sample_rate


def _write_wav(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    audio = np.clip(audio, -1.0, 1.0)
    pcm = (audio.T.reshape(-1) * 32767.0).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(audio.shape[0])
        w.setsampwidth(2)
        w.setframerate(int(sample_rate))
        w.writeframes(pcm)


def render_fixture_espeak(line_ids: Iterable[str] | None = None) -> list[dict]:
    """Generate clearly-labelled local fixtures. This is never canonical Voice acceptance."""
    exe = shutil.which("espeak") or shutil.which("espeak-ng")
    if not exe:
        raise RuntimeError("espeak/espeak-ng is not installed; supplied fixture WAVs should normally make this unnecessary.")
    lines = _line_map()
    selected = list(line_ids or lines.keys())
    engine_version = subprocess.run([exe, "--version"], capture_output=True, text=True).stdout.strip()
    profile_identity = {"engine": "espeak-fixture", "voice": "fa", "version": engine_version}
    results = []
    for line_id in selected:
        line = lines[line_id]
        key = _asset_key(line, profile_identity)
        asset_id = f"FIXTURE-{line_id}-{key[:12]}"
        wav_path = DRY_DIR / f"{asset_id}.wav"
        DRY_DIR.mkdir(parents=True, exist_ok=True)
        if not wav_path.exists():
            subprocess.run([exe, "-v", "fa", "-s", "145", "-w", str(wav_path), line["text_fa"]], check=True)
        meta = {
            "asset_id": asset_id,
            "line_id": line_id,
            "status": "READY",
            "source_text_sha256": sha256_text(line["text_fa"]),
            "source_status": line.get("source_status"),
            "engine": "espeak-fixture",
            "profile_id": "PRIMARY-WITNESS-ESPEAK-FIXTURE-FA",
            "wav_path": str(wav_path.relative_to(ROOT)).replace("\\", "/"),
            "wav_sha256": _file_sha(wav_path),
            "duration_ms": duration_ms(wav_path),
            "rendered_at": now_iso(),
            "fixture": True,
            "warning": "Temporal/UI fixture only over primary-witness text. Not Piper and not artistic Voice acceptance.",
        }
        atomic_write_json(DRY_DIR / f"{line_id}.json", meta)
        results.append(meta)
    return results
