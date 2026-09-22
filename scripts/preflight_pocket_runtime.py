from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voice_proto.storage import now_iso
from voice_proto.tts_pocket_fa import _cfg, _runtime, _phonemise_segment, synthesize_text

SMOKE_TEXT = "بدن زندگی رو پس می‌زنه، غذا و هوا رو پس می‌زنه."


def main() -> int:
    outdir = ROOT / "evidence/pocket_fa_v2"
    outdir.mkdir(parents=True, exist_ok=True)
    report = outdir / "runtime_preflight.json"
    wav = outdir / "runtime_preflight.wav"
    result = {"generated_at": now_iso(), "pass": False, "checks": {}}
    try:
        cfg = _cfg()
        rt = _runtime()
        result["runtime"] = {
            "transformers_version": rt.transformers_version,
            "model_revision": cfg["model_revision"],
            "g2p_revision": cfg["g2p_revision"],
            "pocket_tts_fork_commit": cfg.get("pocket_tts_fork_commit"),
        }
        result["checks"]["transformers_exact"] = (
            rt.transformers_version == str(cfg.get("transformers_version"))
        )

        phon = _phonemise_segment(SMOKE_TEXT)
        result["g2p_phonemes"] = phon
        result["checks"]["g2p_nonempty"] = bool(phon and phon.strip())

        synth = synthesize_text(SMOKE_TEXT, wav, line_id="PREFLIGHT")
        result["synthesis"] = {
            "duration_ms": synth.get("duration_ms"),
            "sample_rate": synth.get("sample_rate"),
            "chunks": len(synth.get("plan") or []),
        }
        result["checks"]["pocket_audio_nontrivial"] = int(synth.get("duration_ms") or 0) > 500
        result["checks"]["pocket_audio_written"] = wav.is_file() and wav.stat().st_size > 1000

        result["pass"] = all(result["checks"].values())
    except Exception as exc:
        result.update({"error": str(exc), "traceback": traceback.format_exc()})

    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
