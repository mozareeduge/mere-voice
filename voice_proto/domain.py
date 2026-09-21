from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

PROCESSING_DEFAULTS = {
    "gain_db": 0.0,
    "pan": 0.0,
    "tempo_scale": 1.0,
    "pitch_semitones": 0.0,
    "reverb_mix": 0.0,
    "delay_ms": 0,
    "delay_feedback": 0.0,
    "attack_ms": 0,
    "release_ms": 0,
}

PROCESSING_RANGES = {
    "gain_db": (-60.0, 12.0),
    "pan": (-1.0, 1.0),
    "tempo_scale": (0.5, 2.0),
    "pitch_semitones": (-12.0, 12.0),
    "reverb_mix": (0.0, 1.0),
    "delay_ms": (0.0, 2000.0),
    "delay_feedback": (0.0, 0.95),
    "attack_ms": (0.0, 5000.0),
    "release_ms": (0.0, 5000.0),
}

class ValidationError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_processing(spec: dict[str, Any] | None) -> dict[str, float | int]:
    spec = {**PROCESSING_DEFAULTS, **(spec or {})}
    out: dict[str, float | int] = {}
    for key, (lo, hi) in PROCESSING_RANGES.items():
        if key not in spec:
            raise ValidationError(f"missing processing field: {key}")
        try:
            value = float(spec[key])
        except (TypeError, ValueError):
            raise ValidationError(f"{key} must be numeric")
        if not lo <= value <= hi:
            raise ValidationError(f"{key} out of range [{lo}, {hi}]: {value}")
        if key == "tempo_scale":
            value = round(value, 3)
        out[key] = int(value) if key in {"delay_ms", "attack_ms", "release_ms"} else value
    unknown = set(spec) - set(PROCESSING_RANGES)
    if unknown:
        raise ValidationError(f"unknown processing fields: {sorted(unknown)}")
    return out


def processing_hash(spec: dict[str, Any]) -> str:
    return sha256_text(canonical_json(validate_processing(spec)))


def validate_event(event: dict[str, Any], known_lines: set[str]) -> dict[str, Any]:
    event_id = str(event.get("event_id", "")).strip()
    line_id = str(event.get("line_id", "")).strip()
    if not event_id:
        raise ValidationError("event_id is required")
    if line_id not in known_lines:
        raise ValidationError(f"unknown line_id: {line_id}")
    try:
        start_ms = int(event.get("start_ms", 0))
    except (TypeError, ValueError):
        raise ValidationError("start_ms must be an integer")
    if start_ms < 0:
        raise ValidationError("start_ms must be >= 0")
    return {
        "event_id": event_id,
        "line_id": line_id,
        "start_ms": start_ms,
        "enabled": bool(event.get("enabled", True)),
        "route_id": str(event.get("route_id", "STEREO_MAIN")),
        "processing": validate_processing(event.get("processing")),
    }


def validate_score(score: dict[str, Any], known_lines: set[str]) -> dict[str, Any]:
    events = [validate_event(e, known_lines) for e in score.get("events", [])]
    ids = [e["event_id"] for e in events]
    if len(ids) != len(set(ids)):
        raise ValidationError("event_id values must be unique")
    return {
        "score_id": str(score.get("score_id") or "SCORE-VOICE-LAB"),
        "revision": int(score.get("revision", 0)),
        "name": str(score.get("name") or "Voice temporal laboratory"),
        "events": events,
        "notes_summary": str(score.get("notes_summary") or ""),
    }


def score_semantic_hash(score: dict[str, Any], known_lines: set[str]) -> str:
    normalized = validate_score(score, known_lines)
    normalized = {k: v for k, v in normalized.items() if k != "revision"}
    return sha256_text(canonical_json(normalized))



def variant_key(dry_meta: dict, spec: dict) -> str:
    payload = {"dry_wav_sha256": dry_meta["wav_sha256"], "processing": validate_processing(spec)}
    return sha256_text(canonical_json(payload))[:24]

def make_event(event_id: str, line_id: str, start_ms: int) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "line_id": line_id,
        "start_ms": int(start_ms),
        "enabled": True,
        "route_id": "STEREO_MAIN",
        "processing": dict(PROCESSING_DEFAULTS),
    }
