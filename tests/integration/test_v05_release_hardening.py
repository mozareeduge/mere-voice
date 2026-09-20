import json
from pathlib import Path

from scripts.local_release import build_report
from voice_proto.domain import variant_key
from voice_proto.export import export_run
from voice_proto.storage import ROOT, inspect_dry_asset, load_score, read_json, variant_meta_path
from voice_proto.version import CANDIDATE_ID


def test_prebuilt_processed_variants_record_processor_identity():
    for event in load_score()["events"]:
        dry = inspect_dry_asset(event["line_id"])
        key = variant_key(dry, event["processing"])
        meta = read_json(variant_meta_path(key))
        assert meta["processor"]["pipeline_revision"] == "PEDALBOARD-OFFLINE-V1"
        assert meta["processor"]["mode"] in {"pedalboard-offline", "neutral-byte-copy"}
        assert meta["processor"]["numpy_version"]
        if meta["processor"]["mode"] == "pedalboard-offline":
            assert meta["processor"]["pedalboard_version"]


def test_export_sidecar_binds_candidate_source_model_and_runtime():
    result = export_run("processed")
    sidecar = json.loads((ROOT / result["sidecar"]).read_text(encoding="utf-8"))
    assert sidecar["candidate"] == CANDIDATE_ID
    assert sidecar["source"]["source_mode"] == "PRIMARY_PDF_WITNESS"
    assert sidecar["source"]["source_sha256"]
    assert sidecar["model_profile"]["profile_id"] == "PIPER-MANA-FA-IR-MEDIUM"
    assert sidecar["export_runtime"]["numpy"]
    assert sidecar["export_runtime"]["pedalboard"]


def test_local_release_report_separates_runnable_baseline_from_real_voice_gate():
    report = build_report(do_prepare=False, do_dev_verify=False, do_export_smoke=False)
    assert report["base_candidate_pass"] is True
    assert report["audio"]["ready_line_count"] == 17
    assert report["audio"]["fixture_line_count"] == 17
    assert report["real_voice_engineering_pass"] is False
    assert len(report["external_human_gates"]) == 4
