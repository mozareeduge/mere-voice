from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .domain import processing_hash, sha256_bytes, sha256_text, score_semantic_hash, validate_score

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCE_PATH = DATA / "source" / "voice_lines.primary_witness.json"
CURRENT_SCORE = DATA / "scores" / "current.json"
REVISIONS = DATA / "scores" / "revisions"
NOTES = DATA / "notes" / "research_notes.jsonl"
DRY_DIR = DATA / "assets" / "dry"
PROCESSED_DIR = DATA / "assets" / "processed"
EXPORTS = ROOT / "exports"
MODEL_PROFILE = DATA / "config" / "model_profile.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, value: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_lines() -> list[dict[str, Any]]:
    doc = read_json(SOURCE_PATH, {"lines": []})
    lines = doc.get("lines", [])
    for row in lines:
        row["text_sha256"] = sha256_text(row["text_fa"])
    return lines


def known_line_ids() -> set[str]:
    return {row["line_id"] for row in load_lines()}


def source_document() -> dict[str, Any]:
    doc = read_json(SOURCE_PATH, {"lines": []})
    doc["source_sha256"] = sha256_bytes(SOURCE_PATH.read_bytes()) if SOURCE_PATH.exists() else None
    return doc


def load_score() -> dict[str, Any]:
    score = read_json(CURRENT_SCORE)
    if score is None:
        score = {"score_id": "SCORE-VOICE-LAB", "revision": 0, "name": "Voice temporal laboratory", "events": [], "notes_summary": ""}
    return validate_score(score, known_line_ids())


def save_current_score(score: dict[str, Any]) -> dict[str, Any]:
    normalized = validate_score(score, known_line_ids())
    normalized["updated_at"] = now_iso()
    atomic_write_json(CURRENT_SCORE, normalized)
    return normalized


def saved_revision_info() -> dict[str, Any] | None:
    files = sorted(REVISIONS.glob("rev-*.json"))
    if not files:
        return None
    doc = read_json(files[-1])
    return {"revision": doc["revision"], "score_hash": doc["score_hash"], "path": str(files[-1].relative_to(ROOT))}


def save_revision() -> dict[str, Any]:
    score = load_score()
    latest = saved_revision_info()
    next_rev = (latest["revision"] if latest else 0) + 1
    score["revision"] = next_rev
    score_hash = score_semantic_hash(score, known_line_ids())
    snapshot = {**score, "score_hash": score_hash, "saved_at": now_iso()}
    path = REVISIONS / f"rev-{next_rev:04d}.json"
    atomic_write_json(path, snapshot)
    atomic_write_json(CURRENT_SCORE, score)
    return {"revision": next_rev, "score_hash": score_hash, "path": str(path.relative_to(ROOT))}


def score_dirty() -> bool:
    latest = saved_revision_info()
    if not latest:
        return True
    return score_semantic_hash(load_score(), known_line_ids()) != latest["score_hash"]


def asset_meta_path(line_id: str) -> Path:
    return DRY_DIR / f"{line_id}.json"


def asset_wav_path(line_id: str) -> Path:
    return DRY_DIR / f"{line_id}.wav"


def load_asset_meta(line_id: str):
    return read_json(asset_meta_path(line_id))


def variant_meta_path(variant_key: str) -> Path:
    return PROCESSED_DIR / f"{variant_key}.json"


def variant_wav_path(variant_key: str) -> Path:
    return PROCESSED_DIR / f"{variant_key}.wav"


def inspect_dry_asset(line_id: str) -> dict[str, Any]:
    """Return candidate-bound dry asset state, validating bytes rather than trusting metadata."""
    meta = load_asset_meta(line_id)
    if not meta:
        return {"status": "MISSING", "reason": "metadata missing"}
    out = dict(meta)
    line = next((row for row in load_lines() if row["line_id"] == line_id), None)
    if line is None:
        return {**out, "status": "STALE", "reason": "source line no longer exists"}
    expected_text = sha256_text(line["text_fa"])
    if out.get("source_text_sha256") != expected_text:
        return {**out, "status": "STALE", "reason": "source text changed"}
    rel = out.get("wav_path")
    if not rel:
        return {**out, "status": "MISSING", "reason": "wav_path missing"}
    path = ROOT / rel
    if not path.exists() or not path.is_file():
        return {**out, "status": "MISSING_FILE", "reason": "WAV file missing"}
    actual = sha256_bytes(path.read_bytes())
    if actual != out.get("wav_sha256"):
        return {**out, "status": "HASH_MISMATCH", "reason": "WAV SHA-256 differs from metadata", "actual_wav_sha256": actual}
    if out.get("status") != "READY":
        return out
    return {**out, "verified_wav_sha256": actual}


def inspect_variant(variant_key_value: str, dry_meta: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Validate a processed variant against current dry bytes, processing identity and its own WAV bytes."""
    meta = read_json(variant_meta_path(variant_key_value))
    if not meta:
        return {"status": "MISSING", "variant_key": variant_key_value, "reason": "metadata missing"}
    out = dict(meta)
    if dry_meta.get("status") != "READY":
        return {**out, "status": "STALE", "reason": "dry asset is not ready"}
    if out.get("dry_wav_sha256") != dry_meta.get("wav_sha256"):
        return {**out, "status": "STALE", "reason": "dry WAV identity changed"}
    if out.get("processing_hash") != processing_hash(spec):
        return {**out, "status": "STALE", "reason": "processing parameters changed"}
    rel = out.get("wav_path")
    if not rel:
        return {**out, "status": "MISSING", "reason": "wav_path missing"}
    path = ROOT / rel
    if not path.exists() or not path.is_file():
        return {**out, "status": "MISSING_FILE", "reason": "processed WAV file missing"}
    actual = sha256_bytes(path.read_bytes())
    if actual != out.get("wav_sha256"):
        return {**out, "status": "HASH_MISMATCH", "reason": "processed WAV SHA-256 differs from metadata", "actual_wav_sha256": actual}
    if out.get("status") != "READY":
        return out
    return {**out, "verified_wav_sha256": actual}


def append_note(note: dict[str, Any]) -> dict[str, Any]:
    NOTES.parent.mkdir(parents=True, exist_ok=True)
    row = {"recorded_at": now_iso(), **note}
    with NOTES.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row
