\
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voice_proto.version import CANDIDATE_ID

CATALOG = ROOT / "quality" / "ARTIFACT_CATALOG.json"
OUT = ROOT / "quality" / "ARTIFACT_REGISTRY.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def expand(patterns: list[str]) -> list[Path]:
    found: dict[str, Path] = {}
    for pattern in patterns:
        for path in ROOT.glob(pattern):
            if path.is_file():
                found[path.relative_to(ROOT).as_posix()] = path
    return [found[k] for k in sorted(found)]


def group_fingerprint(rows: list[dict]) -> str:
    payload = "\n".join(f"{r['path']}\0{r['sha256']}\0{r['bytes']}" for r in rows)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_registry() -> dict:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if catalog.get("candidate") != CANDIDATE_ID:
        raise RuntimeError(f"Artifact catalog candidate drift: {catalog.get('candidate')} != {CANDIDATE_ID}")
    artifacts = []
    for item in catalog["artifacts"]:
        paths = expand(item["paths"])
        if not paths:
            raise RuntimeError(f"{item['artifact_id']} resolved to no files: {item['paths']}")
        rows = [
            {
                "path": p.relative_to(ROOT).as_posix(),
                "bytes": p.stat().st_size,
                "sha256": sha256(p),
            }
            for p in paths
        ]
        artifacts.append({
            **item,
            "fingerprint_algorithm": "sha256(path\\0sha256\\0bytes rows)",
            "fingerprint": group_fingerprint(rows),
            "members": rows,
        })
    return {
        "schema_version": 1,
        "candidate": CANDIDATE_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }


def write_registry(registry: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verify_registry(existing: dict | None = None) -> dict:
    existing = existing or json.loads(OUT.read_text(encoding="utf-8"))
    current = build_registry()
    old = {x["artifact_id"]: x for x in existing.get("artifacts", [])}
    new = {x["artifact_id"]: x for x in current["artifacts"]}
    mismatches = []
    if existing.get("candidate") != CANDIDATE_ID:
        mismatches.append({"type": "candidate", "actual": existing.get("candidate"), "expected": CANDIDATE_ID})
    if set(old) != set(new):
        mismatches.append({"type": "artifact_ids", "actual": sorted(old), "expected": sorted(new)})
    for aid in sorted(set(old) & set(new)):
        if old[aid].get("fingerprint") != new[aid].get("fingerprint"):
            mismatches.append({"type": "fingerprint", "artifact_id": aid, "actual": old[aid].get("fingerprint"), "expected": new[aid].get("fingerprint")})
    return {"pass": not mismatches, "mismatches": mismatches, "artifact_count": len(new)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="Verify the saved registry against current package bytes.")
    args = ap.parse_args()
    if args.verify:
        result = verify_registry()
        print(json.dumps(result, indent=2))
        return 0 if result["pass"] else 1
    reg = build_registry()
    write_registry(reg)
    print(json.dumps({"candidate": reg["candidate"], "artifact_count": reg["artifact_count"], "output": str(OUT.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
