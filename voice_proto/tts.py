from __future__ import annotations

import hashlib
import importlib.metadata
import shutil
import subprocess
import wave
from pathlib import Path
from typing import Iterable

from .domain import canonical_json, sha256_bytes, sha256_text
from .storage import DRY_DIR, MODEL_PROFILE, ROOT, atomic_write_json, load_lines, now_iso, read_json
from .wavio import duration_ms


def _line_map():
    return {row["line_id"]: row for row in load_lines()}


def _profile():
    return read_json(MODEL_PROFILE, {})


def _file_sha(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _asset_key(line: dict, profile_identity: dict) -> str:
    material = {
        "text_sha256": sha256_text(line["text_fa"]),
        "profile": profile_identity,
    }
    return sha256_text(canonical_json(material))


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
    cfg = SynthesisConfig(**params)
    engine_version = importlib.metadata.version("piper-tts")
    profile_identity = {
        "engine": "piper-tts",
        "engine_version": engine_version,
        "model_sha256": actual_sha,
        "config_sha256": _file_sha(config_path),
        "render_parameters": params,
    }
    results = []
    for line_id in selected:
        line = lines[line_id]
        key = _asset_key(line, profile_identity)
        asset_id = f"ASSET-{line_id}-{key[:12]}"
        wav_path = DRY_DIR / f"{asset_id}.wav"
        if not wav_path.exists():
            tmp = wav_path.with_suffix(".tmp.wav")
            DRY_DIR.mkdir(parents=True, exist_ok=True)
            try:
                with wave.open(str(tmp), "wb") as wav_file:
                    voice.synthesize_wav(line["text_fa"], wav_file, syn_config=cfg)
                tmp.replace(wav_path)
            finally:
                tmp.unlink(missing_ok=True)
        meta = {
            "asset_id": asset_id,
            "line_id": line_id,
            "status": "READY",
            "source_text_sha256": sha256_text(line["text_fa"]),
            "source_status": line.get("source_status"),
            "engine": "piper-tts",
            "engine_version": engine_version,
            "profile_id": profile.get("profile_id"),
            "model_sha256": actual_sha,
            "config_sha256": profile_identity["config_sha256"],
            "wav_path": str(wav_path.relative_to(ROOT)).replace("\\", "/"),
            "wav_sha256": _file_sha(wav_path),
            "duration_ms": duration_ms(wav_path),
            "rendered_at": now_iso(),
            "fixture": False,
        }
        atomic_write_json(DRY_DIR / f"{line_id}.json", meta)
        results.append(meta)
    return results


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
