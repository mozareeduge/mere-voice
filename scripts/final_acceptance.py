\
from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import current_state
from scripts.build_artifact_registry import build_registry, verify_registry, write_registry
from scripts.local_release import build_report as build_local_release, write_report as write_local_release
from voice_proto.manifest import build_manifest as build_runtime_manifest
from voice_proto.version import APP_VERSION, CANDIDATE_ID, DISPLAY_VERSION

OUT = ROOT / "evidence" / "final"
TRACE = ROOT / "quality" / "SCENARIO_TRACEABILITY.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def run_cmd(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-14000:],
        "stderr": proc.stderr[-14000:],
        "pass": proc.returncode == 0,
    }


def ids(text: str, pattern: str) -> list[str]:
    return sorted(set(re.findall(pattern, text)))


def authority_probe() -> dict:
    horizon = (ROOT / "product_design" / "00_PRODUCT_HORIZON.md").read_text(encoding="utf-8")
    objects = (ROOT / "product_design" / "01_OBJECT_STATE_AND_FLOW_MODEL.md").read_text(encoding="utf-8")
    scenarios = (ROOT / "product_design" / "02_SCENARIO_CASE_ATLAS.md").read_text(encoding="utf-8")
    oracles = (ROOT / "qa" / "QA_ORACLE_REGISTER.md").read_text(encoding="utf-8")
    source = json.loads((ROOT / "data" / "source" / "voice_lines.primary_witness.json").read_text(encoding="utf-8"))
    result = {
        "horizons": ids(horizon, r"\bHZN-\d{3}\b"),
        "objects": ids(objects, r"\bOBJ-\d{3}\b"),
        "scenarios": ids(scenarios, r"\bSCN-\d{3}\b"),
        "cross_scenarios": ids(scenarios, r"\bSCN-X-\d{2}\b"),
        "oracles": ids(oracles, r"\bORACLE-\d{3}\b"),
        "source_units": len(source.get("lines", [])),
        "unique_source_ids": len({x.get("line_id") for x in source.get("lines", [])}),
        "authority_closed_marker": "PRODUCT_DESIGN_AUTHORITY_CLOSED_WITH_HUMAN_REVIEW_GATES" in horizon,
    }
    result["pass"] = (
        len(result["horizons"]) == 12
        and len(result["objects"]) == 11
        and len(result["scenarios"]) == 32
        and len(result["cross_scenarios"]) == 8
        and len(result["oracles"]) == 28
        and result["source_units"] == 17
        and result["unique_source_ids"] == 17
        and result["authority_closed_marker"]
    )
    return result


def identity_probe() -> dict:
    state = current_state()
    runtime_manifest = build_runtime_manifest()
    checks = {
        "state_app_version": state.get("app_version") == APP_VERSION,
        "runtime_manifest_version": runtime_manifest.get("implementation_version") == APP_VERSION,
        "catalog_candidate": json.loads((ROOT / "quality" / "ARTIFACT_CATALOG.json").read_text(encoding="utf-8")).get("candidate") == CANDIDATE_ID,
        "traceability_candidate": json.loads(TRACE.read_text(encoding="utf-8")).get("candidate") == CANDIDATE_ID,
        "html_dynamic_version_slot": 'id="appVersion"' in (ROOT / "web" / "index.html").read_text(encoding="utf-8"),
    }
    active_paths = [
        "app.py", "voice_proto/export.py", "voice_proto/manifest.py", "voice_proto/version.py",
        "scripts/local_release.py", "scripts/build_manifest.py", "scripts/fetch_model.py",
        "web/index.html", "qa/QA_STATE.yaml", "qa/QA_ORACLE_REGISTER.md",
        "00_START_HERE.md", "README.md", "MIDDLE_LAYER_INDEX.md", "PACKAGE_VALIDATION.md",
        "PREBUILT_IMPLEMENTATION_STATE.md", "execution/AGENTIC_EXECUTION_INTAKE.md",
        "execution/TASK_DAG.yaml", "execution/STATE_TEMPLATE.json",
    ]
    stale = []
    for rel in active_paths:
        path = ROOT / rel
        if not path.exists():
            stale.append({"path": rel, "reason": "missing active identity file"})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "NIRAVANA-VOICE-NEARFINAL-0.5" in text or '"0.5.0"' in text:
            stale.append({"path": rel, "reason": "stale v0.5 active identity"})
    return {"pass": all(checks.values()) and not stale, "checks": checks, "stale_active_identity": stale}


def traceability_probe() -> dict:
    scenario_text = (ROOT / "product_design" / "02_SCENARIO_CASE_ATLAS.md").read_text(encoding="utf-8")
    expected = set(ids(scenario_text, r"\bSCN-\d{3}\b") + ids(scenario_text, r"\bSCN-X-\d{2}\b"))
    trace = json.loads(TRACE.read_text(encoding="utf-8"))
    actual = set(trace.get("scenarios", {}))
    qa_text = (ROOT / "qa" / "QA_STATE.yaml").read_text(encoding="utf-8")
    known_evidence = set(re.findall(r"\bid:\s*(EV-[A-Z0-9-]+)", qa_text))
    unknown_evidence = []
    for sid, row in trace.get("scenarios", {}).items():
        for ev in row.get("evidence_ids", []):
            if ev not in known_evidence:
                unknown_evidence.append({"scenario": sid, "evidence_id": ev})
    statuses = {}
    for row in trace.get("scenarios", {}).values():
        statuses[row["proof_status"]] = statuses.get(row["proof_status"], 0) + 1
    return {
        "pass": expected == actual and not unknown_evidence,
        "expected_count": len(expected),
        "classified_count": len(actual),
        "missing": sorted(expected - actual),
        "extra": sorted(actual - expected),
        "unknown_evidence": unknown_evidence,
        "proof_status_counts": statuses,
    }


def dev_qa(strict: bool) -> dict:
    checks: dict[str, dict] = {}
    if package_version("pytest"):
        checks["pytest"] = run_cmd([sys.executable, "-m", "pytest", "-q"])
    else:
        checks["pytest"] = {"pass": None, "skipped": "pytest not installed"}
    node = shutil.which("node")
    if node:
        checks["node_app"] = run_cmd([node, "--check", "web/app.js"])
        checks["node_scheduler"] = run_cmd([node, "--check", "web/audio-scheduler.js"])
        checks["scheduler_lifecycle"] = run_cmd([node, "tests/browser/stop_harness.mjs"])
    else:
        checks["node"] = {"pass": None, "skipped": "node not installed"}
    if package_version("playwright"):
        checks["browser_qa"] = run_cmd([sys.executable, "tests/browser/run_candidate_browser_qa.py"])
    else:
        checks["browser_qa"] = {"pass": None, "skipped": "playwright not installed"}
    executed = [v.get("pass") for v in checks.values() if v.get("pass") is not None]
    missing_required = strict and any(v.get("pass") is None for v in checks.values())
    return {
        "strict": strict,
        "pass": bool(executed) and all(executed) and not missing_required,
        "checks": checks,
        "executed_count": len(executed),
        "missing_required": missing_required,
    }


def build_report(strict_dev: bool) -> dict:
    # Registry is generated from the current bytes before it is verified.
    reg = build_registry()
    write_registry(reg)
    registry = verify_registry(reg)
    authority = authority_probe()
    identity = identity_probe()
    traceability = traceability_probe()
    qa = dev_qa(strict_dev)
    local = build_local_release(do_prepare=False, do_dev_verify=False, do_export_smoke=False)
    write_local_release(local)
    qa_dir = ROOT / "evidence" / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    (qa_dir / "api_state_snapshot.json").write_text(json.dumps(current_state(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    engineering_pass = all([
        authority["pass"],
        identity["pass"],
        registry["pass"],
        traceability["pass"],
        qa["pass"],
        local["base_candidate_pass"],
    ])
    return {
        "generated_at": now_iso(),
        "candidate": CANDIDATE_ID,
        "app_version": APP_VERSION,
        "compiler_source": "chatgpt_executable_handoff_v2.0",
        "engineering_acceptance_pass": engineering_pass,
        "release_state": "CHATGPT_CRAFT_PASS_EXTERNAL_GATES_REMAIN" if engineering_pass else "ENGINEERING_ACCEPTANCE_FAIL",
        "authority_closure": authority,
        "identity_consistency": identity,
        "artifact_registry": registry,
        "scenario_traceability": traceability,
        "component_integration_reality_qa": qa,
        "local_release": {
            "base_candidate_pass": local["base_candidate_pass"],
            "real_voice_engineering_pass": local["real_voice_engineering_pass"],
            "audio": local["audio"],
            "model": local["model"],
        },
        "external_gates": local["external_human_gates"],
    }


def write_report(report: dict) -> tuple[Path, Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    jp = OUT / "FINAL_ACCEPTANCE_REPORT.json"
    mp = OUT / "FINAL_ACCEPTANCE_REPORT.md"
    jp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    t = report["scenario_traceability"]["proof_status_counts"]
    lines = [
        f"# Final Acceptance Report — v{DISPLAY_VERSION}",
        "",
        f"Candidate: `{report['candidate']}`",
        f"Engineering acceptance: **{'PASS' if report['engineering_acceptance_pass'] else 'FAIL'}**",
        f"Release state: `{report['release_state']}`",
        "",
        "## Compiler gates",
        f"- product authority closure: {'PASS' if report['authority_closure']['pass'] else 'FAIL'}",
        f"- candidate/version identity consistency: {'PASS' if report['identity_consistency']['pass'] else 'FAIL'}",
        f"- artifact registry fingerprints: {'PASS' if report['artifact_registry']['pass'] else 'FAIL'} ({report['artifact_registry']['artifact_count']} logical artifacts)",
        f"- scenario traceability completeness: {'PASS' if report['scenario_traceability']['pass'] else 'FAIL'} ({report['scenario_traceability']['classified_count']}/{report['scenario_traceability']['expected_count']})",
        f"- executable dev QA: {'PASS' if report['component_integration_reality_qa']['pass'] else 'FAIL'}",
        f"- runnable local candidate: {'PASS' if report['local_release']['base_candidate_pass'] else 'FAIL'}",
        "",
        "## Proof classification",
    ]
    lines.extend(f"- {k}: {v}" for k, v in sorted(t.items()))
    lines += [
        "",
        "## Truthful unresolved gates",
        f"- real Mana/Piper engineering state in this package: {'PASS' if report['local_release']['real_voice_engineering_pass'] else 'NOT YET PROVEN'}",
    ]
    lines.extend(f"- {x}" for x in report["external_gates"])
    mp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return jp, mp


def main() -> int:
    ap = argparse.ArgumentParser(description="Compiler-shaped final acceptance for the near-final local Voice workbench.")
    ap.add_argument("--strict-dev", action="store_true", help="Require pytest, Node and Playwright/browser QA to be installed and pass.")
    args = ap.parse_args()
    report = build_report(args.strict_dev)
    jp, mp = write_report(report)
    print(json.dumps({
        "candidate": report["candidate"],
        "engineering_acceptance_pass": report["engineering_acceptance_pass"],
        "release_state": report["release_state"],
        "report": str(mp.relative_to(ROOT)),
    }, indent=2))
    return 0 if report["engineering_acceptance_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
