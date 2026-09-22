"""Copy the Pocket-TTS Farsi v2 dry renders into bench/audio/pocket-fa-v2/<VOICE-ID>.wav.

Companion to prepare_bench.py for the pocket_fa_v2 condition only. Kept separate
because the currently-active dry asset for a line reflects whichever provider last
rendered it (piper-tts vs pocket-tts-farsi-v2) -- prepare_bench.py's mana-canonical
check requires the piper-tts engine, so the two scripts must not be merged without
first deciding how "current provider per line" should be tracked.

Voice-clone note: Pocket-TTS Farsi v2 is conditioned on a reference sample
(data/reference/pocket_voice_prompt.wav) that is itself derived from the human's
own VOICE-009 recording, so this condition sounds like a clone of the human's
voice, not a generic TTS voice. Recorded in provenance for the record.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINES = ["VOICE-004", "VOICE-001", "VOICE-009"]
CONDITION = "pocket-fa-v2"
PROVENANCE_KEYS = (
    "asset_id", "wav_sha256", "duration_ms", "engine", "provider_revision",
    "model_id", "model_revision", "g2p_id", "g2p_revision", "reference_sha256",
    "spoken_text_is_canonical",
)


def copy(src: Path, line: str, provenance: dict) -> None:
    dst_dir = ROOT / "bench" / "audio" / CONDITION
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst_dir / f"{line}.wav")
    (dst_dir / f"{line}.provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    for line in LINES:
        meta = json.loads((ROOT / "data" / "assets" / "dry" / f"{line}.json").read_text(encoding="utf-8"))
        if meta.get("fixture") or meta.get("engine") != "pocket-tts-farsi-v2":
            print(f"{line}: current asset is not a real Pocket-TTS Farsi v2 render; run "
                  f"scripts/prepare_pocket.py --diagnostic --dry-only first", file=sys.stderr)
            return 1
        if not meta.get("spoken_text_is_canonical"):
            print(f"{line}: current asset was not synthesized from canonical text_fa", file=sys.stderr)
            return 1
        provenance = {k: meta[k] for k in PROVENANCE_KEYS if k in meta}
        provenance["voice_clone_reference_is_human_own_recording"] = True
        provenance["license"] = "CC BY-NC 4.0 (Pocket-TTS Farsi v2 model) -- non-commercial only"
        copy(ROOT / meta["wav_path"], line, provenance)
        print(f"{line}: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
