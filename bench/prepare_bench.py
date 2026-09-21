"""Copy the dry synthetic comparison files into bench/audio/<condition>/<VOICE-ID>.wav.

Conditions (all DRY, no event processing; originals in data/assets/dry are never modified):
  mana-canonical      current v2 control: exact text_fa, native clause prosody
  mana-v061-vocalized historical reference from tag/commit cba031f (unsafe full-line vocalization)
  mana-pre-v061       historical reference from commit 920a479 (first real render, canonical text)
  human-recorded      filled by the human via the bench page (never written by this script)
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINES = ["VOICE-004", "VOICE-001", "VOICE-009"]
HISTORICAL = {"mana-v061-vocalized": "cba031f", "mana-pre-v061": "920a479"}


def git_show(rev: str, path: str) -> str:
    return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True).stdout


def copy(src: Path, cand: str, line: str, provenance: dict) -> None:
    dst_dir = ROOT / "bench" / "audio" / cand
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst_dir / f"{line}.wav")
    (dst_dir / f"{line}.provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    for line in LINES:
        meta = json.loads((ROOT / "data" / "assets" / "dry" / f"{line}.json").read_text(encoding="utf-8"))
        if meta.get("fixture") or meta.get("engine") != "piper-tts":
            print(f"{line}: current asset is not real Piper; run scripts/local_release.py --prepare-real first", file=sys.stderr)
            return 1
        if not meta.get("spoken_text_is_canonical"):
            print(f"{line}: current asset was not synthesized from canonical text_fa", file=sys.stderr)
            return 1
        copy(ROOT / meta["wav_path"], "mana-canonical", line, {k: meta[k] for k in ("asset_id", "wav_sha256", "duration_ms", "synthesis_pipeline", "model_sha256", "engine_version")})
        for cand, rev in HISTORICAL.items():
            old = json.loads(git_show(rev, f"data/assets/dry/{line}.json"))
            src = ROOT / old["wav_path"]
            if not src.exists():
                print(f"{line}/{cand}: historical wav {old['wav_path']} missing on disk (skipped)")
                continue
            copy(src, cand, line, {"git_rev": rev, **{k: old.get(k) for k in ("asset_id", "wav_sha256", "duration_ms")}})
        print(f"{line}: ok")
    (ROOT / "bench" / "audio" / "human-recorded").mkdir(parents=True, exist_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
