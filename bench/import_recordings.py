"""Sort performer recordings from recordings_inbox/ into the bench and the voice-training store.

Expected file names (case-insensitive; "_", "-" or space as separators):
  <CODE>_<LINE>_<TAKE>.<ext>   e.g. P1_VOICE-001_A.m4a   -> bench/audio/rec-p1-a/VOICE-001.m4a
  <CODE>_<LINE>.<ext>          e.g. P1_GM-02.wav         -> bench/audio/rec-p1-a/GM-02.wav (take A assumed)
  <CODE>_GM-01a.<ext>          grammar donor line        -> voice_training/p1/donors/GM-01a.<ext>
  <CODE>_READING.<ext>, <CODE>_FREE.<ext>                -> voice_training/p1/
Files are copied, never moved or overwritten; anything unrecognised is listed at the end.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "recordings_inbox"
AUDIO = ROOT / "bench" / "audio"
TRAINING = ROOT / "voice_training"
EXTS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm", ".aac", ".opus"}
SEP = r"[ _-]+"
PAT_LINE = re.compile(rf"^(?P<code>[A-Za-z]+\d+){SEP}(?P<line>VOICE{SEP}\d{{3}}|GM{SEP}\d{{2}})(?:{SEP}(?P<take>[A-Za-z]))?$", re.I)
PAT_DONOR = re.compile(rf"^(?P<code>[A-Za-z]+\d+){SEP}GM{SEP}(?P<n>\d{{2}})(?P<d>[ab])$", re.I)
PAT_TRAIN = re.compile(rf"^(?P<code>[A-Za-z]+\d+){SEP}(?P<kind>READING|FREE)(?:{SEP}(?P<part>\d+))?$", re.I)


def norm_line(raw: str) -> str:
    kind, num = re.split(SEP, raw, maxsplit=1)
    return f"{kind.upper()}-{num}"


def place(src: Path, dst: Path, done: list[str]) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        done.append(f"  kept existing  {dst.relative_to(ROOT)}  (not overwritten by {src.name})")
        return
    shutil.copy2(src, dst)
    done.append(f"  {src.name}  ->  {dst.relative_to(ROOT)}")


def main() -> int:
    if not INBOX.is_dir():
        INBOX.mkdir()
        print(f"Created {INBOX}. Put the received recordings there (sub-folders are fine) and run again.")
        return 0
    done: list[str] = []
    unknown: list[str] = []
    for f in sorted(INBOX.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in EXTS:
            continue
        stem, ext = f.stem.strip(), f.suffix.lower()
        if m := PAT_DONOR.match(stem):
            place(f, TRAINING / m["code"].lower() / "donors" / f"GM-{m['n']}{m['d'].lower()}{ext}", done)
        elif m := PAT_LINE.match(stem):
            take = (m["take"] or "a").lower()
            place(f, AUDIO / f"rec-{m['code'].lower()}-{take}" / f"{norm_line(m['line'])}{ext}", done)
        elif m := PAT_TRAIN.match(stem):
            part = f"_{m['part']}" if m["part"] else ""
            place(f, TRAINING / m["code"].lower() / f"{m['kind'].upper()}{part}{ext}", done)
        else:
            unknown.append(f"  {f.relative_to(INBOX)}")
    print("Imported:" if done else "Nothing new to import.")
    print("\n".join(done))
    if unknown:
        print("\nNot recognised (rename like P1_VOICE-001_A.m4a, or ask Claude to sort them):")
        print("\n".join(unknown))
    return 0


if __name__ == "__main__":
    sys.exit(main())
