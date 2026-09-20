from __future__ import annotations

import math
import importlib.metadata
from pathlib import Path

import numpy as np

from .domain import PROCESSING_DEFAULTS, processing_hash, sha256_bytes, validate_processing, variant_key
from .storage import PROCESSED_DIR, ROOT, atomic_write_json, inspect_dry_asset, inspect_variant, now_iso, variant_meta_path, variant_wav_path
from .wavio import duration_ms

PROCESSING_PIPELINE_REVISION = "PEDALBOARD-OFFLINE-V1"


def is_neutral(spec: dict) -> bool:
    return validate_processing(spec) == PROCESSING_DEFAULTS


def prepare_variant(line_id: str, spec: dict) -> dict:
    spec = validate_processing(spec)
    dry = inspect_dry_asset(line_id)
    if not dry or dry.get("status") != "READY":
        raise RuntimeError(f"Dry asset not ready for {line_id}: {dry.get('status')} {dry.get('reason','')}")
    dry_path = ROOT / dry["wav_path"]
    if not dry_path.exists():
        raise RuntimeError(f"Dry WAV missing for {line_id}: {dry_path}")
    key = variant_key(dry, spec)
    wav_path = variant_wav_path(key)
    meta_path = variant_meta_path(key)
    if wav_path.exists() and meta_path.exists():
        cached = inspect_variant(key, dry, spec)
        if cached.get("status") == "READY":
            return cached
        # A corrupt/stale cache is evidence, not reusable output. Rebuild the variant.
        wav_path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if is_neutral(spec):
        # Preserve exact bytes for a semantic DRY identity variant.
        wav_path.write_bytes(dry_path.read_bytes())
    else:
        try:
            from pedalboard import Pedalboard, PitchShift, Delay, Reverb
            from pedalboard.io import AudioFile
        except Exception as exc:
            raise RuntimeError("pedalboard is required to prepare modified event audio. Run pip install -r requirements.txt.") from exc

        with AudioFile(str(dry_path), "r") as f:
            audio = f.read(f.frames)
            sr = f.samplerate

        # Add room for delay/reverb/release tails before processing.
        tail_s = (spec["delay_ms"] / 1000.0) * (1.0 + 4.0 * spec["delay_feedback"]) + (spec["release_ms"] / 1000.0)
        if spec["reverb_mix"] > 0:
            tail_s += 2.0 + 2.0 * spec["reverb_mix"]
        if tail_s > 0:
            pad = np.zeros((audio.shape[0], int(sr * tail_s)), dtype=np.float32)
            audio = np.concatenate([audio, pad], axis=1)

        plugins = []
        if abs(spec["pitch_semitones"]) > 1e-9:
            plugins.append(PitchShift(semitones=spec["pitch_semitones"]))
        if spec["delay_ms"] > 0:
            plugins.append(Delay(delay_seconds=spec["delay_ms"] / 1000.0, feedback=spec["delay_feedback"], mix=0.28))
        if spec["reverb_mix"] > 0:
            plugins.append(Reverb(room_size=0.62, damping=0.45, wet_level=spec["reverb_mix"], dry_level=max(0.0, 1.0 - 0.45 * spec["reverb_mix"])))
        if plugins:
            audio = Pedalboard(plugins)(audio, sr)

        # Envelope after effects so release shapes tails too.
        frames = audio.shape[1]
        attack = min(frames, int(sr * spec["attack_ms"] / 1000.0))
        release = min(frames, int(sr * spec["release_ms"] / 1000.0))
        env = np.ones(frames, dtype=np.float32)
        if attack > 0:
            env[:attack] = np.linspace(0.0, 1.0, attack, endpoint=True, dtype=np.float32)
        if release > 0:
            env[-release:] *= np.linspace(1.0, 0.0, release, endpoint=True, dtype=np.float32)
        audio *= env[None, :]

        # Gain and deterministic stereo pan. Center remains unity on both channels.
        audio *= 10.0 ** (spec["gain_db"] / 20.0)
        if audio.shape[0] == 1:
            audio = np.repeat(audio, 2, axis=0)
        elif audio.shape[0] > 2:
            audio = audio[:2]
        pan = spec["pan"]
        left = 1.0 if pan <= 0 else 1.0 - pan
        right = 1.0 if pan >= 0 else 1.0 + pan
        audio[0] *= left
        audio[1] *= right

        with AudioFile(str(wav_path), "w", sr, audio.shape[0]) as out:
            out.write(audio)

    processor = {
        "pipeline_revision": PROCESSING_PIPELINE_REVISION,
        "mode": "neutral-byte-copy" if is_neutral(spec) else "pedalboard-offline",
        "pedalboard_version": None if is_neutral(spec) else importlib.metadata.version("pedalboard"),
        "numpy_version": importlib.metadata.version("numpy"),
    }
    meta = {
        "variant_id": f"VAR-{key}",
        "variant_key": key,
        "line_id": line_id,
        "asset_id": dry["asset_id"],
        "dry_wav_sha256": dry["wav_sha256"],
        "processing": spec,
        "processing_hash": processing_hash(spec),
        "processor": processor,
        "status": "READY",
        "wav_path": str(wav_path.relative_to(ROOT)).replace("\\", "/"),
        "wav_sha256": sha256_bytes(wav_path.read_bytes()),
        "duration_ms": duration_ms(wav_path),
        "prepared_at": now_iso(),
        "fixture": bool(dry.get("fixture")),
    }
    atomic_write_json(meta_path, meta)
    return meta
