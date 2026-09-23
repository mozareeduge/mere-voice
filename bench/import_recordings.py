"""Sort performer recordings from recordings_inbox/ into the bench and the voice-training store.

Expected file names (case-insensitive; "_", "-" or space as separators):
  <CODE>_<LINE>_<TAKE>.<ext>   e.g. P1_VOICE-001_A.m4a   -> bench/audio/rec-p1-a/VOICE-001.m4a
  <CODE>_<LINE>.<ext>          e.g. P1_GM-02.wav         -> bench/audio/rec-p1-a/GM-02.wav (take A assumed)
  <CODE>_GM-01a.<ext>          grammar donor line        -> voice_training/p1/donors/GM-01a.<ext>
  <CODE>_READING.<ext>, <CODE>_FREE.<ext>, <CODE>_ROOMTONE -> voice_training/p1/
  <CODE>_manifest.json                                     -> voice_training/p1/
ZIP packages saved by the recorder pages are read directly (no need to unzip).
Files are copied, never moved or overwritten; anything unrecognised is listed at the end.
"""
from __future__ import annotations

import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "recordings_inbox"
AUDIO = ROOT / "bench" / "audio"
TRAINING = ROOT / "voice_training"
EXTS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm", ".aac", ".opus"}
SEP = r"[ _-]+"
PAT_LINE = re.compile(rf"^(?P<code>[A-Za-z]+\d+){SEP}(?P<line>VOICE{SEP}\d{{3}}|GM{SEP}\d{{2}})(?:{SEP}(?P<take>[A-Za-z]))?$", re.I)
PAT_DONOR = re.compile(rf"^(?P<code>[A-Za-z]+\d+){SEP}GM{SEP}(?P<n>\d{{2}})(?P<d>[ab])$", re.I)
PAT_TRAIN = re.compile(rf"^(?P<code>[A-Za-z]+\d+){SEP}(?P<kind>READING|FREE|ROOMTONE)(?:{SEP}(?P<part>\d+))?$", re.I)


def norm_line(raw: str) -> str:
    kind, num = re.split(SEP, raw, maxsplit=1)
    return f"{kind.upper()}-{num}"


def place(src, dst: Path, done: list[str], label: str | None = None) -> None:
    """src is a Path, or bytes read from a ZIP package (then label names it)."""
    label = label or src.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        done.append(f"  kept existing  {dst.relative_to(ROOT)}  (not overwritten by {label})")
        return
    if isinstance(src, bytes):
        dst.write_bytes(src)
    else:
        shutil.copy2(src, dst)
    done.append(f"  {label}  ->  {dst.relative_to(ROOT)}")


def route(stem: str, ext: str) -> Path | None:
    if m := PAT_DONOR.match(stem):
        return TRAINING / m["code"].lower() / "donors" / f"GM-{m['n']}{m['d'].lower()}{ext}"
    if m := PAT_LINE.match(stem):
        return AUDIO / f"rec-{m['code'].lower()}-{(m['take'] or 'a').lower()}" / f"{norm_line(m['line'])}{ext}"
    if m := PAT_TRAIN.match(stem):
        part = f"_{m['part']}" if m["part"] else ""
        return TRAINING / m["code"].lower() / f"{m['kind'].upper()}{part}{ext}"
    if m := re.match(r"^(?P<code>[A-Za-z]+\d+)[ _-]+manifest$", stem, re.I):
        return TRAINING / m["code"].lower() / f"manifest{ext}"
    return None


def main() -> int:
    if not INBOX.is_dir():
        INBOX.mkdir()
        print(f"Created {INBOX}. Put the received recordings there (sub-folders are fine) and run again.")
        return 0
    done: list[str] = []
    unknown: list[str] = []
    for f in sorted(INBOX.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(f) as z:
                    for info in z.infolist():
                        name = Path(info.filename).name
                        if info.is_dir() or not name or name.startswith("."):
                            continue
                        ext = Path(name).suffix.lower()
                        dst = route(Path(name).stem.strip(), ext) if ext in EXTS | {".json"} else None
                        if dst and dst.name == "manifest.json":
                            dst = dst.with_name(f"manifest_{f.stem}.json")
                        if dst:
                            place(z.read(info), dst, done, f"{f.name}:{name}")
                        else:
                            unknown.append(f"  {f.relative_to(INBOX)} : {name}")
            except zipfile.BadZipFile:
                unknown.append(f"  {f.relative_to(INBOX)}  (damaged ZIP)")
            continue
        if f.suffix.lower() not in EXTS:
            continue
        dst = route(f.stem.strip(), f.suffix.lower())
        if dst:
            place(f, dst, done)
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
