from __future__ import annotations

import hashlib
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from voice_proto.domain import PROCESSING_DEFAULTS, sha256_text
from voice_proto.processing import prepare_variant
from voice_proto.storage import inspect_dry_asset, inspect_variant, load_lines, now_iso
from voice_proto.tts_router import provider_status, render_dry


def _has_terminal_runaway(value) -> bool:
    if isinstance(value, dict):
        if value.get("terminal_runaway") is True:
            return True
        return any(_has_terminal_runaway(v) for v in value.values())
    if isinstance(value, list):
        return any(_has_terminal_runaway(v) for v in value)
    return False


def main() -> int:
    outdir = ROOT / "evidence/pocket_fa_v2"
    outdir.mkdir(parents=True, exist_ok=True)
    result = {"generated_at": now_iso(), "line_id": "VOICE-009", "pass": False, "checks": {}}
    try:
        line = next(x for x in load_lines() if x["line_id"] == "VOICE-009")
        status = provider_status()
        result["provider_status"] = status
        result["checks"]["provider_ready"] = bool(status["providers"]["pocket_fa_v2"]["ready"])
        result["checks"]["provider_recommended"] = status["recommended_render_mode"] == "pocket_fa_v2"

        asset = render_dry("pocket_fa_v2", ["VOICE-009"])[0]
        verified = inspect_dry_asset("VOICE-009")
        result["dry_asset"] = asset
        result["checks"]["dry_engine"] = asset.get("engine") == "pocket-tts-farsi-v2"
        result["checks"]["canonical_text_bound"] = (
            asset.get("spoken_text_is_canonical") is True
            and asset.get("source_text_sha256") == sha256_text(line["text_fa"])
        )
        result["checks"]["dry_storage_verified"] = verified.get("status") == "READY" and bool(verified.get("verified_wav_sha256"))
        result["checks"]["no_terminal_runaway"] = not _has_terminal_runaway(asset.get("generation_evidence", []))
        result["checks"]["audio_nontrivial"] = int(asset.get("duration_ms") or 0) > 500

        variant = prepare_variant("VOICE-009", PROCESSING_DEFAULTS)
        checked_variant = inspect_variant(variant["variant_key"], verified, PROCESSING_DEFAULTS)
        result["neutral_processed_variant"] = checked_variant
        result["checks"]["processing_path_verified"] = (
            checked_variant.get("status") == "READY"
            and checked_variant.get("dry_wav_sha256") == verified.get("wav_sha256")
        )

        import app
        app_state = app.current_state()
        result["app_tts_state"] = app_state.get("tts")
        result["checks"]["app_integration"] = app_state.get("tts", {}).get("recommended_render_mode") == "pocket_fa_v2"

        wav_path = ROOT / asset["wav_path"]
        result["wav_sha256"] = hashlib.sha256(wav_path.read_bytes()).hexdigest()
        result["pass"] = all(result["checks"].values())
    except Exception as exc:
        result.update({"error": str(exc), "traceback": traceback.format_exc()})

    report = outdir / "install_verification.json"
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
