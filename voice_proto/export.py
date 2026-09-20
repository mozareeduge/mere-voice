from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path

import numpy as np

from .domain import sha256_bytes
from .processing import prepare_variant
from .storage import EXPORTS, MODEL_PROFILE, ROOT, inspect_dry_asset, load_score, now_iso, read_json, saved_revision_info, source_document
from .wavio import read_wav, write_wav
from .version import CANDIDATE_ID


def _audio_for_event(event: dict, mode: str):
    dry = inspect_dry_asset(event["line_id"])
    if not dry or dry.get("status") != "READY":
        raise RuntimeError(f"Dry asset not ready for {event['line_id']}: {dry.get('status')} {dry.get('reason','')}")
    if mode == "dry":
        path = ROOT / dry["wav_path"]
        meta = dry
    else:
        meta = prepare_variant(event["line_id"], event["processing"])
        path = ROOT / meta["wav_path"]
    audio, sr = read_wav(path)
    if audio.shape[0] == 1:
        audio = np.repeat(audio, 2, axis=0)
    return audio[:2], sr, meta


def export_run(mode: str = "processed") -> dict:
    if mode not in {"processed", "dry"}:
        raise ValueError("mode must be processed or dry")
    score = load_score()
    enabled = [e for e in score["events"] if e["enabled"]]
    if not enabled:
        raise RuntimeError("No enabled events to export")
    rendered = []
    sample_rate = None
    end_frames = 0
    for event in enabled:
        audio, sr, meta = _audio_for_event(event, mode)
        if sample_rate is None:
            sample_rate = sr
        if sr != sample_rate:
            raise RuntimeError(f"Mixed sample rates are not supported: {sample_rate} vs {sr}")
        start = round(event["start_ms"] * sr / 1000)
        end_frames = max(end_frames, start + audio.shape[1])
        rendered.append((event, audio, start, meta))
    mix = np.zeros((2, end_frames), dtype=np.float32)
    for event, audio, start, _ in rendered:
        mix[:, start:start + audio.shape[1]] += audio
    peak = float(np.max(np.abs(mix))) if mix.size else 0.0
    normalization = 1.0
    if peak > 0.98:
        normalization = 0.98 / peak
        mix *= normalization

    EXPORTS.mkdir(parents=True, exist_ok=True)
    stamp = now_iso().replace(":", "-").replace("+", "_")
    stem = f"voice-run-{mode}-{stamp}"
    wav_path = EXPORTS / f"{stem}.wav"
    json_path = EXPORTS / f"{stem}.json"
    write_wav(wav_path, mix, int(sample_rate))
    sidecar = {
        "exported_at": now_iso(),
        "candidate": CANDIDATE_ID,
        "mode": mode,
        "source": {k: v for k, v in source_document().items() if k != "lines"},
        "model_profile": read_json(MODEL_PROFILE, {}),
        "export_runtime": {
            "numpy": importlib.metadata.version("numpy"),
            "pedalboard": importlib.metadata.version("pedalboard"),
        },
        "score": score,
        "saved_revision": saved_revision_info(),
        "sample_rate": sample_rate,
        "normalization_factor": normalization,
        "wav_path": str(wav_path.relative_to(ROOT)).replace("\\", "/"),
        "wav_sha256": sha256_bytes(wav_path.read_bytes()),
        "event_audio": [
            {"event_id": e["event_id"], "start_ms": e["start_ms"], "audio": m}
            for e, _, _, m in rendered
        ],
    }
    json_path.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"wav": str(wav_path.relative_to(ROOT)).replace("\\", "/"), "sidecar": str(json_path.relative_to(ROOT)).replace("\\", "/"), "wav_sha256": sidecar["wav_sha256"], "normalization_factor": normalization}
