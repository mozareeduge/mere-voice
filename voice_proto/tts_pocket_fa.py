from __future__ import annotations

import hashlib
import importlib.util
import math
import re
import threading
import wave
from pathlib import Path
from typing import Iterable

import numpy as np

from .domain import canonical_json, sha256_bytes, sha256_text
from .storage import DRY_DIR, ROOT, atomic_write_json, load_lines, now_iso, read_json
from .wavio import duration_ms

PROVIDER_REVISION = "MERE-POCKET-FA-V2-3"
CONFIG_PATH = ROOT / "data" / "config" / "tts_provider.json"
OVERRIDES_PATH = ROOT / "data" / "config" / "pocket_phoneme_overrides.json"
CACHE_PATH = ROOT / "data" / "cache" / "pocket_fa_g2p.json"

_TO_PHONEMES = str.maketrans({"/": "a", "a": "A", "@": "?", "$": "S", "c": "C"})
_EZAFE = "1"
_SENTENCE_SPLIT = re.compile(r"(?<=[.!؟])\s+")
_CLAUSE_SPLIT = re.compile(r"(?<=[،؛:])\s+")
_LOCK = threading.Lock()
_RUNTIME = None
_NORMALIZER = None


def _cfg() -> dict:
    doc = read_json(CONFIG_PATH, {})
    cfg = dict(doc.get("pocket_fa_v2") or {})
    if not cfg:
        raise RuntimeError("Pocket provider config missing: data/config/tts_provider.json")
    if not cfg.get("model_revision") or not cfg.get("g2p_revision"):
        raise RuntimeError("Pocket model revisions are unresolved. Rerun INSTALL_AND_VERIFY.bat.")
    return cfg


def _normalizer():
    global _NORMALIZER
    if _NORMALIZER is not None:
        return _NORMALIZER
    cfg = _cfg()
    path = ROOT / cfg["normalizer_path"]
    if not path.is_file():
        raise RuntimeError(f"Pinned Pocket Persian normalizer missing: {path}. Rerun INSTALL_AND_VERIFY.bat.")
    spec = importlib.util.spec_from_file_location("_mere_voice_pocket_normalize_fa", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load Pocket Persian normalizer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, "normalize_for_model", None)
    if not callable(fn):
        raise RuntimeError("Pinned normalize_fa.py has no normalize_for_model function")
    _NORMALIZER = fn
    return _NORMALIZER


def _normalize_persian(text: str) -> str:
    return str(_normalizer()(text)).strip()


def _source_sentences(text: str) -> list[str]:
    text = text.strip()
    return [x.strip() for x in _SENTENCE_SPLIT.split(text) if x.strip()]


def _source_clauses(text: str) -> list[str]:
    return [x.strip() for x in _CLAUSE_SPLIT.split(text) if x.strip()]


def _cache() -> dict:
    return read_json(CACHE_PATH, {"schema_version": 1, "items": {}})


def _save_cache(doc: dict) -> None:
    atomic_write_json(CACHE_PATH, doc)


def _overrides() -> dict:
    return (read_json(OVERRIDES_PATH, {"lines": {}}).get("lines") or {})


class _Runtime:
    def __init__(self, cfg: dict):
        import torch
        import transformers
        from pocket_tts import TTSModel
        from transformers import AutoTokenizer, T5ForConditionalGeneration

        self.torch = torch
        self.transformers_version = transformers.__version__
        expected_transformers = str(cfg.get("transformers_version") or "")
        if expected_transformers and self.transformers_version != expected_transformers:
            raise RuntimeError(
                f"Pocket Farsi runtime requires transformers=={expected_transformers}; "
                f"found {self.transformers_version}. Rerun INSTALL_AND_VERIFY.bat."
            )
        model_config = ROOT / cfg["pinned_model_config"]
        if not model_config.is_file():
            raise RuntimeError(f"Pinned Pocket model config missing: {model_config}. Rerun INSTALL_AND_VERIFY.bat.")
        self.model = TTSModel.load_model(
            config=str(model_config),
            temp=float(cfg.get("temperature", 0.3)),
            eos_threshold=float(cfg.get("eos_threshold", -2.0)),
        )
        self.g2p_tok = AutoTokenizer.from_pretrained(cfg["g2p_id"], revision=cfg["g2p_revision"])
        self.g2p = T5ForConditionalGeneration.from_pretrained(cfg["g2p_id"], revision=cfg["g2p_revision"]).eval()
        self.sp = self.model.flow_lm.conditioner.tokenizer.sp
        sample_rate = getattr(self.model, "sample_rate", None)
        if sample_rate is None:
            sample_rate = self.model.mimi.sample_rate
        self.sample_rate = int(sample_rate)
        ref = ROOT / cfg["reference_audio"]
        if not ref.is_file():
            raise RuntimeError(f"Pocket reference WAV missing: {ref}")
        with wave.open(str(ref), "rb") as w:
            seconds = w.getnframes() / float(w.getframerate())
        if seconds > float(cfg.get("max_prompt_seconds", 5.0)) + 1e-6:
            raise RuntimeError(f"Pocket reference prompt is {seconds:.3f}s; must be <= {cfg.get('max_prompt_seconds', 5.0)}s")
        self.voice_state = self.model.get_state_for_audio_prompt(str(ref))

    def token_count(self, phonemes: str) -> int:
        return len(self.sp.encode(phonemes.replace(_EZAFE, "")))


def _runtime() -> _Runtime:
    global _RUNTIME
    if _RUNTIME is None:
        with _LOCK:
            if _RUNTIME is None:
                _RUNTIME = _Runtime(_cfg())
    return _RUNTIME


def _phonemise_segment(text: str) -> str:
    cfg = _cfg()
    norm = _normalize_persian(text).replace("؟", "").replace("?", "")
    if not norm:
        return ""
    key = sha256_text(canonical_json({"text": norm, "g2p": cfg["g2p_id"], "revision": cfg["g2p_revision"]}))
    cache = _cache()
    hit = (cache.get("items") or {}).get(key)
    if hit and hit.get("phonemes"):
        return hit["phonemes"]
    rt = _runtime()
    enc = rt.g2p_tok([norm], add_special_tokens=False, return_tensors="pt")
    with rt.torch.no_grad():
        out = rt.g2p.generate(**enc, num_beams=5, max_length=512, early_stopping=True)
    raw = rt.g2p_tok.batch_decode(out, skip_special_tokens=True)[0].strip()
    phon = raw.translate(_TO_PHONEMES)
    cache.setdefault("items", {})[key] = {"text": norm, "phonemes": phon, "created_at": now_iso()}
    _save_cache(cache)
    return phon


def _line_override(line_id: str) -> str | None:
    row = _overrides().get(line_id)
    if isinstance(row, dict) and row.get("status") == "approved" and row.get("phonemes"):
        return str(row["phonemes"]).strip()
    return None


def _plan_sentence(sent: str, max_tokens: int, min_tokens: int) -> list[dict]:
    """Mirror the pinned Farsi-v2 demo: sentence boundaries are hard; clause ends are preferred."""
    rt = _runtime()
    words: list[tuple[str, bool]] = []
    for clause in _source_clauses(sent):
        ws = _phonemise_segment(clause).split()
        words.extend((w, i == len(ws) - 1) for i, w in enumerate(ws))
    if not words:
        return []

    joined = " ".join(w for w, _ in words)
    total = rt.token_count(joined)
    n_chunks = max(1, math.ceil(total / max_tokens))
    out: list[dict] = []
    for _ in range(4):
        target = math.ceil(total / n_chunks)
        out = []
        cur = ""
        for i, (word, ends_clause) in enumerate(words):
            trial = f"{cur} {word}".strip()
            bound = bool(cur) and cur.split()[-1].endswith(_EZAFE)
            if cur and not bound and rt.token_count(trial) > max_tokens:
                out.append({"phonemes": cur, "boundary": "budget"})
                cur = word
                continue
            cur = trial
            if not ends_clause or i == len(words) - 1:
                continue
            rest = rt.token_count(" ".join(w for w, _ in words[i + 1:]))
            if rt.token_count(cur) >= min_tokens and rest >= min_tokens:
                out.append({"phonemes": cur, "boundary": "clause"})
                cur = ""
        if cur:
            out.append({"phonemes": cur, "boundary": "sentence"})
        if len(out) <= n_chunks:
            break
        n_chunks = len(out)
    return out


def _plan(line_id: str, text: str) -> list[dict]:
    cfg = _cfg()
    max_tokens = int(cfg.get("max_tokens", 18))
    min_tokens = int(cfg.get("min_tokens", 5))
    override = _line_override(line_id)
    if override:
        return [{"phonemes": override, "boundary": "end"}]

    sentences = _source_sentences(text)
    if not sentences:
        sentences = [text]
    plan: list[dict] = []
    for sidx, sent in enumerate(sentences):
        chunks = _plan_sentence(sent, max_tokens, min_tokens)
        if not chunks:
            continue
        # Preserve author sentence boundary even if the final sentence chunk is short.
        chunks[-1]["boundary"] = "sentence" if sidx < len(sentences) - 1 else "end"
        plan.extend(chunks)
    if not plan:
        raise RuntimeError(f"G2P produced no phonemes for {line_id}")
    return plan


def _trim_silence(a: np.ndarray, sr: int, keep_ms: float = 120.0) -> np.ndarray:
    a = np.asarray(a, dtype=np.float32).reshape(-1)
    if not a.size:
        return a
    rms = float(np.sqrt(np.mean(a.astype(np.float64) ** 2)))
    if rms <= 0:
        return a
    win = max(1, int(0.02 * sr))
    threshold = 0.04 * rms
    loud = []
    for i in range(0, len(a), win):
        seg = a[i:i + win]
        if len(seg) and float(np.sqrt(np.mean(seg.astype(np.float64) ** 2))) > threshold:
            loud.append(i)
    if not loud:
        return a
    margin = int(keep_ms / 1000.0 * sr)
    return a[max(0, loud[0] - margin):min(len(a), loud[-1] + win + margin)]


def _cap_seconds(rt: _Runtime, spoken: str) -> float:
    try:
        tokens = int(rt.model.flow_lm.conditioner.prepare(spoken).shape[1])
    except Exception:
        tokens = rt.token_count(spoken)
    tps = float(getattr(rt.model, "_TOKENS_PER_SECOND_ESTIMATE", 3.0))
    pad = float(getattr(rt.model, "_GEN_SECONDS_PADDING", 2.0))
    try:
        frame_rate = float(rt.model.config.mimi.frame_rate)
        return math.ceil((tokens / tps + pad) * frame_rate) / frame_rate
    except Exception:
        return tokens / tps + pad


def _safe_recovery_split(phonemes: str) -> tuple[str, str] | None:
    rt = _runtime()
    words = phonemes.split()
    if len(words) < 4:
        return None
    candidates = [i for i in range(1, len(words)) if not words[i - 1].endswith(_EZAFE)]
    if not candidates:
        return None
    total = rt.token_count(phonemes)
    best = min(candidates, key=lambda i: abs(rt.token_count(" ".join(words[:i])) - total / 2.0))
    return " ".join(words[:best]), " ".join(words[best:])


def _generate_chunk(phonemes: str, *, line_seed: int, depth: int = 0) -> tuple[np.ndarray, dict]:
    rt = _runtime()
    cfg = _cfg()
    spoken = phonemes.replace(_EZAFE, "")
    cap = _cap_seconds(rt, spoken)
    retries = int(cfg.get("retries", 2))
    cap_ratio = float(cfg.get("cap_ratio", 0.97))
    shortest = None
    attempts: list[float] = []
    for attempt in range(retries + 1):
        rt.torch.manual_seed(line_seed + attempt)
        with _LOCK:
            audio = rt.model.generate_audio(rt.voice_state, spoken, frames_after_eos=int(cfg.get("frames_after_eos", 0)))
        if rt.torch.is_tensor(audio):
            audio = audio.detach().float().cpu().numpy()
        a = np.asarray(audio, dtype=np.float32).reshape(-1)
        seconds = len(a) / float(rt.sample_rate)
        attempts.append(seconds)
        if shortest is None or len(a) < len(shortest):
            shortest = a
        if seconds <= cap_ratio * cap:
            return _trim_silence(a, rt.sample_rate), {"attempts_s": attempts, "recovered": False, "terminal_runaway": False}

    split = _safe_recovery_split(phonemes)
    max_depth = int(cfg.get("max_split_depth", 2))
    if split and depth < max_depth:
        left, right = split
        a1, e1 = _generate_chunk(left, line_seed=line_seed + 101, depth=depth + 1)
        a2, e2 = _generate_chunk(right, line_seed=line_seed + 211, depth=depth + 1)
        seam = np.zeros(int(rt.sample_rate * int(cfg.get("recovery_gap_ms", 50)) / 1000.0), dtype=np.float32)
        return np.concatenate([a1, seam, a2]), {
            "attempts_s": attempts,
            "recovered": True,
            "terminal_runaway": bool(e1.get("terminal_runaway") or e2.get("terminal_runaway")),
            "children": [e1, e2],
        }

    # Never force the harness to invent a fix: preserve the shortest attempt and flag it in provenance.
    a = _trim_silence(shortest if shortest is not None else np.zeros(1, dtype=np.float32), rt.sample_rate)
    return a, {"attempts_s": attempts, "recovered": False, "terminal_runaway": True}


def _write_wav(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(audio, -1, 1) * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm.tobytes())


def synthesize_text(text: str, output_path: Path, *, line_id: str = "SMOKE") -> dict:
    cfg = _cfg()
    rt = _runtime()
    if len(text) > int(cfg.get("max_chars", 2500)):
        raise RuntimeError(f"Pocket input exceeds max_chars={cfg.get('max_chars', 2500)}")
    plan = _plan(line_id, text)
    gaps = {
        "budget": int(cfg.get("budget_gap_ms", 150)),
        "clause": int(cfg.get("clause_gap_ms", 225)),
        "sentence": int(cfg.get("sentence_gap_ms", 300)),
        "end": 0,
    }
    base_seed = int(cfg.get("seed", 230922)) + int(hashlib.sha256((line_id + text).encode("utf-8")).hexdigest()[:8], 16)
    pieces = []
    generation_evidence = []
    for i, chunk in enumerate(plan):
        audio, evidence = _generate_chunk(chunk["phonemes"], line_seed=base_seed + i * 17)
        pieces.append(audio)
        generation_evidence.append({"chunk": i + 1, "tokens": rt.token_count(chunk["phonemes"]), **evidence})
        gap = gaps.get(chunk.get("boundary"), 0) if i < len(plan) - 1 else 0
        if gap:
            pieces.append(np.zeros(int(rt.sample_rate * gap / 1000.0), dtype=np.float32))
    audio = np.concatenate(pieces) if pieces else np.zeros(1, dtype=np.float32)
    _write_wav(output_path, audio, rt.sample_rate)
    return {
        "duration_ms": duration_ms(output_path),
        "plan": plan,
        "generation_evidence": generation_evidence,
        "sample_rate": rt.sample_rate,
    }


def render_with_pocket(line_ids: Iterable[str] | None = None) -> list[dict]:
    cfg = _cfg()
    lines = {x["line_id"]: x for x in load_lines()}
    selected = list(line_ids or lines.keys())
    ref = ROOT / cfg["reference_audio"]
    prompt_sha = sha256_bytes(ref.read_bytes())
    generation_keys = (
        "temperature", "eos_threshold", "max_tokens", "min_tokens", "budget_gap_ms",
        "clause_gap_ms", "sentence_gap_ms", "retries", "seed", "cap_ratio",
        "max_split_depth", "recovery_gap_ms", "frames_after_eos",
    )
    identity = {
        "provider_revision": PROVIDER_REVISION,
        "model_id": cfg["model_id"],
        "model_revision": cfg["model_revision"],
        "g2p_id": cfg["g2p_id"],
        "g2p_revision": cfg["g2p_revision"],
        "pocket_tts_fork_commit": cfg.get("pocket_tts_fork_commit"),
        "pinned_model_config_sha256": sha256_bytes((ROOT / cfg["pinned_model_config"]).read_bytes()),
        "normalizer_sha256": sha256_bytes((ROOT / cfg["normalizer_path"]).read_bytes()),
        "reference_sha256": prompt_sha,
        "generation": {k: cfg.get(k) for k in generation_keys},
    }
    results = []
    for line_id in selected:
        if line_id not in lines:
            raise KeyError(f"unknown line id: {line_id}")
        line = lines[line_id]
        key = sha256_text(canonical_json({
            "text_sha256": sha256_text(line["text_fa"]),
            "identity": identity,
            "override": _line_override(line_id),
        }))
        asset_id = f"ASSET-{line_id}-POCKET-{key[:12]}"
        wav_path = DRY_DIR / f"{asset_id}.wav"
        synth = synthesize_text(line["text_fa"], wav_path, line_id=line_id)
        meta = {
            "asset_id": asset_id,
            "line_id": line_id,
            "status": "READY",
            "source_text_sha256": sha256_text(line["text_fa"]),
            "spoken_text": line["text_fa"],
            "spoken_text_is_canonical": True,
            "engine": "pocket-tts-farsi-v2",
            "provider_revision": PROVIDER_REVISION,
            "fixture": False,
            "model_id": cfg["model_id"],
            "model_revision": cfg["model_revision"],
            "g2p_id": cfg["g2p_id"],
            "g2p_revision": cfg["g2p_revision"],
            "reference_audio": cfg["reference_audio"],
            "reference_sha256": prompt_sha,
            "phoneme_plan": synth["plan"],
            "generation_evidence": synth["generation_evidence"],
            "wav_path": str(wav_path.relative_to(ROOT)).replace("\\", "/"),
            "wav_sha256": sha256_bytes(wav_path.read_bytes()),
            "duration_ms": synth["duration_ms"],
            "sample_rate": synth["sample_rate"],
            "rendered_at": now_iso(),
        }
        atomic_write_json(DRY_DIR / f"{line_id}.json", meta)
        results.append(meta)
    return results
