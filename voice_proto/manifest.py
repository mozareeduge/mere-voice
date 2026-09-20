from __future__ import annotations

from pathlib import Path
from .domain import sha256_bytes
from .storage import ROOT, load_asset_meta, load_lines, load_score, saved_revision_info
from .version import APP_VERSION


def file_hash(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def build_manifest() -> dict:
    lines = load_lines()
    return {
        "project": "niravana-voice-prototype",
        "implementation_version": APP_VERSION,
        "score": load_score(),
        "latest_saved_revision": saved_revision_info(),
        "lines": [
            {
                "line_id": row["line_id"],
                "text_sha256": row["text_sha256"],
                "source_status": row.get("source_status"),
                "asset": load_asset_meta(row["line_id"]),
            }
            for row in lines
        ],
    }
