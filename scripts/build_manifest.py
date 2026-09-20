from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from voice_proto.version import CANDIDATE_ID, PACKAGE_NAME
OUT = ROOT / "MANIFEST.json"
SKIP_PARTS = {".git", ".pytest_cache", "__pycache__", ".venv"}
SKIP_NAMES = {"MANIFEST.json"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def included(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    return path.name not in SKIP_NAMES and not any(part in SKIP_PARTS for part in rel.parts)


def main() -> int:
    files = sorted(p for p in ROOT.rglob("*") if p.is_file() and included(p))
    rows = []
    total = 0
    for path in files:
        size = path.stat().st_size
        total += size
        rows.append({
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": size,
            "sha256": sha256(path),
        })
    manifest = {
        "candidate": CANDIDATE_ID,
        "package": PACKAGE_NAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hash_algorithm": "sha256",
        "file_count_excluding_manifest": len(rows),
        "total_bytes_excluding_manifest": total,
        "files": rows,
    }
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ["candidate", "file_count_excluding_manifest", "total_bytes_excluding_manifest"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
