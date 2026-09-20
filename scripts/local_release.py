from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import current_state
from voice_proto.storage import ROOT as STORAGE_ROOT, load_score, read_json, saved_revision_info
from voice_proto.version import APP_VERSION, CANDIDATE_ID, DISPLAY_VERSION

REPORT_DIR = ROOT / "evidence" / "local"
PROFILE_PATH = ROOT / "data" / "config" / "model_profile.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def model_probe() -> dict:
    profile = read_json(PROFILE_PATH, {})
    model = ROOT / profile.get("model_path", "")
    config = ROOT / profile.get("config_path", "")
    out = {
        "profile_id": profile.get("profile_id"),
        "model_path": str(model.relative_to(ROOT)) if model != ROOT else None,
        "config_path": str(config.relative_to(ROOT)) if config != ROOT else None,
        "model_present": model.is_file(),
        "config_present": config.is_file(),
        "model_hash_ok": False,
        "config_invariants_ok": False,
    }
    if model.is_file():
        actual = file_sha256(model)
        out["model_sha256"] = actual
        out["model_hash_ok"] = actual == profile.get("expected_model_sha256")
    if config.is_file():
        doc = read_json(config, {})
        actual_cfg = {
            "sample_rate": (doc.get("audio") or {}).get("sample_rate"),
            "language_code": (doc.get("language") or {}).get("code"),
            "espeak_voice": (doc.get("espeak") or {}).get("voice"),
            "phoneme_type": doc.get("phoneme_type"),
            "num_speakers": doc.get("num_speakers"),
        }
        out["config_invariants"] = actual_cfg
        out["config_invariants_ok"] = actual_cfg == profile.get("expected_config_invariants", {})
        out["config_sha256"] = file_sha256(config)
    return out


def dependency_probe() -> dict:
    return {
        "python": platform.python_version(),
        "python_supported": (3, 10) <= sys.version_info[:2] <= (3, 13),
        "piper-tts": package_version("piper-tts"),
        "pedalboard": package_version("pedalboard"),
        "numpy": package_version("numpy"),
        "pytest": package_version("pytest"),
        "playwright": package_version("playwright"),
        "node": shutil.which("node"),
        "os": platform.platform(),
    }


def real_voice_probe(state: dict) -> dict:
    ready = [x for x in state["lines"] if (x.get("asset") or {}).get("status") == "READY"]
    engines = sorted({(x.get("asset") or {}).get("engine") for x in ready if (x.get("asset") or {}).get("engine")})
    fixture_count = sum(1 for x in ready if (x.get("asset") or {}).get("fixture"))
    piper_count = sum(1 for x in ready if (x.get("asset") or {}).get("engine") == "piper-tts" and not (x.get("asset") or {}).get("fixture"))
    return {
        "ready_line_count": len(ready),
        "fixture_line_count": fixture_count,
        "piper_line_count": piper_count,
        "engines": engines,
        "all_17_real_piper": len(state["lines"]) == 17 and piper_count == 17,
    }


def run_cmd(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-12000:],
        "stderr": proc.stderr[-12000:],
        "pass": proc.returncode == 0,
    }


def dev_verification() -> dict:
    checks = {}
    if package_version("pytest"):
        checks["pytest"] = run_cmd([sys.executable, "-m", "pytest", "-q"])
    else:
        checks["pytest"] = {"pass": None, "skipped": "pytest not installed"}
    node = shutil.which("node")
    if node:
        checks["node_app"] = run_cmd([node, "--check", "web/app.js"])
        checks["node_scheduler"] = run_cmd([node, "--check", "web/audio-scheduler.js"])
    else:
        checks["node"] = {"pass": None, "skipped": "node not installed"}
    if package_version("playwright"):
        checks["browser_qa"] = run_cmd([sys.executable, "tests/browser/run_candidate_browser_qa.py"])
    else:
        checks["browser_qa"] = {"pass": None, "skipped": "playwright not installed"}
    executed = [v["pass"] for v in checks.values() if isinstance(v, dict) and v.get("pass") is not None]
    checks["executed_all_pass"] = all(executed) if executed else None
    return checks


def prepare_real_voice() -> dict:
    model = model_probe()
    if not (model["model_present"] and model["config_present"] and model["model_hash_ok"] and model["config_invariants_ok"]):
        raise RuntimeError("Verified Mana model/config are not ready. Run scripts/fetch_model.py first.")
    if not package_version("piper-tts"):
        raise RuntimeError("piper-tts is not installed. Run SETUP_ONCE.bat first.")
    if not package_version("pedalboard") or not package_version("numpy"):
        raise RuntimeError("pedalboard/numpy are not installed. Run SETUP_ONCE.bat first.")
    from voice_proto.tts import render_with_piper
    from voice_proto.processing import prepare_variant

    assets = render_with_piper()
    score = load_score()
    variants = []
    for event in score["events"]:
        if event["enabled"]:
            variants.append(prepare_variant(event["line_id"], event["processing"]))
    return {"dry_assets": len(assets), "processed_variants": len(variants)}


def export_smoke() -> dict:
    try:
        from voice_proto.export import export_run
        if saved_revision_info() is None:
            return {"pass": False, "reason": "no saved revision"}
        result = export_run("processed")
        return {"pass": True, **result}
    except Exception as exc:
        return {"pass": False, "reason": str(exc)}


def build_report(*, do_prepare: bool, do_dev_verify: bool, do_export_smoke: bool) -> dict:
    preparation = None
    preparation_error = None
    if do_prepare:
        try:
            preparation = prepare_real_voice()
        except Exception as exc:
            preparation_error = str(exc)

    state = current_state()
    model = model_probe()
    deps = dependency_probe()
    real_voice = real_voice_probe(state)
    score = load_score()
    base_ok = (
        state.get("source_primary_witness") is True
        and len(state.get("lines", [])) == 17
        and len(score.get("events", [])) >= 17
        and state["readiness"]["dry_ready"] is True
        and state["readiness"]["processed_ready"] is True
    )
    report = {
        "generated_at": now_iso(),
        "candidate": CANDIDATE_ID,
        "platform": deps,
        "source": state.get("source"),
        "score": {"score_id": score.get("score_id"), "revision": score.get("revision"), "events": len(score.get("events", []))},
        "readiness": state.get("readiness"),
        "audio": real_voice,
        "model": model,
        "preparation": preparation,
        "preparation_error": preparation_error,
        "base_candidate_pass": base_ok,
        "real_voice_engineering_pass": base_ok and real_voice["all_17_real_piper"] and model["model_hash_ok"] and model["config_invariants_ok"],
        "external_human_gates": [
            "Persian pronunciation/prosody listening acceptance",
            "actual Windows/default-audio-device smoke",
            "optional visual PDF punctuation/typography confirmation",
            "final performance Voice / physical speaker-field artistic decision",
        ],
    }
    if do_export_smoke:
        report["export_smoke"] = export_smoke()
    if do_dev_verify:
        report["developer_verification"] = dev_verification()
    return report


def write_report(report: dict) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    j = REPORT_DIR / "local_release_report.json"
    m = REPORT_DIR / "local_release_report.md"
    j.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# Local Release Report — v{DISPLAY_VERSION}",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Candidate baseline: **{'PASS' if report['base_candidate_pass'] else 'FAIL'}**",
        f"Real Mana/Piper engineering state: **{'PASS' if report['real_voice_engineering_pass'] else 'NOT YET PROVEN'}**",
        "",
        "## Current audio",
        f"- ready lines: {report['audio']['ready_line_count']}/17",
        f"- real Piper lines: {report['audio']['piper_line_count']}/17",
        f"- fixture lines: {report['audio']['fixture_line_count']}/17",
        f"- engines: {', '.join(report['audio']['engines']) or 'none'}",
        "",
        "## Model",
        f"- model present: {report['model']['model_present']}",
        f"- model hash valid: {report['model']['model_hash_ok']}",
        f"- config invariants valid: {report['model']['config_invariants_ok']}",
        "",
        "## Remaining human/target gates",
    ]
    lines.extend(f"- {x}" for x in report["external_human_gates"])
    if report.get("preparation_error"):
        lines += ["", "## Preparation blocker", f"`{report['preparation_error']}`"]
    if "export_smoke" in report:
        lines += ["", "## Export smoke", f"- pass: {report['export_smoke'].get('pass')}"]
    if "developer_verification" in report:
        lines += ["", "## Developer verification", f"- executed checks all pass: {report['developer_verification'].get('executed_all_pass')}"]
    m.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return j, m


def main() -> int:
    ap = argparse.ArgumentParser(description="Prepare and evidence-bind the Niravana local candidate without agent interpretation.")
    ap.add_argument("--prepare-real", action="store_true", help="Render all 17 lines with verified Mana/Piper and rebuild enabled variants.")
    ap.add_argument("--dev-verify", action="store_true", help="Also run pytest/Node/browser QA when those tools are installed.")
    ap.add_argument("--export-smoke", action="store_true", help="Create one processed export as a functional smoke test.")
    args = ap.parse_args()
    report = build_report(do_prepare=args.prepare_real, do_dev_verify=args.dev_verify, do_export_smoke=args.export_smoke)
    j, m = write_report(report)
    print(json.dumps({
        "candidate": report["candidate"],
        "base_candidate_pass": report["base_candidate_pass"],
        "real_voice_engineering_pass": report["real_voice_engineering_pass"],
        "piper_lines": report["audio"]["piper_line_count"],
        "fixture_lines": report["audio"]["fixture_line_count"],
        "report_json": str(j.relative_to(ROOT)),
        "report_md": str(m.relative_to(ROOT)),
        "preparation_error": report.get("preparation_error"),
    }, indent=2))
    if args.prepare_real and not report["real_voice_engineering_pass"]:
        return 2
    return 0 if report["base_candidate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
