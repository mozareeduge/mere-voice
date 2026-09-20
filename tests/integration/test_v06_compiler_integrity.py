import inspect
import json
import re

import voice_proto.processing as processing
import voice_proto.storage as storage
import app as app_module
from app import current_state
from voice_proto.export import export_run
from scripts.build_artifact_registry import build_registry
from voice_proto.manifest import build_manifest
from voice_proto.version import APP_VERSION, CANDIDATE_ID


def test_candidate_identity_is_centralized_across_runtime_surfaces():
    assert current_state()["app_version"] == APP_VERSION
    assert build_manifest()["implementation_version"] == APP_VERSION
    assert build_registry()["candidate"] == CANDIDATE_ID


def test_atomic_write_failure_preserves_previous_file(tmp_path, monkeypatch):
    target = tmp_path / "state.json"
    target.write_text('{"old": true}\n', encoding="utf-8")

    def fail_replace(src, dst):
        raise OSError("injected replace failure")

    monkeypatch.setattr(storage.os, "replace", fail_replace)
    try:
        storage.atomic_write_json(target, {"new": True})
    except OSError as exc:
        assert "injected" in str(exc)
    else:
        raise AssertionError("failure injection did not fire")

    assert target.read_text(encoding="utf-8") == '{"old": true}\n'
    assert not list(tmp_path.glob("state.json.*.tmp"))


def test_pitch_semantics_use_pitchshift_not_playback_rate():
    source = inspect.getsource(processing.prepare_variant)
    assert "PitchShift" in source
    assert "playback_rate" not in source
    assert "playbackRate" not in source


def test_every_authoritative_scenario_has_a_traceability_classification():
    root = storage.ROOT
    atlas = (root / "product_design" / "02_SCENARIO_CASE_ATLAS.md").read_text(encoding="utf-8")
    expected = set(re.findall(r"\bSCN-\d{3}\b", atlas)) | set(re.findall(r"\bSCN-X-\d{2}\b", atlas))
    trace = json.loads((root / "quality" / "SCENARIO_TRACEABILITY.json").read_text(encoding="utf-8"))
    assert set(trace["scenarios"]) == expected
    assert all(row.get("proof_status") for row in trace["scenarios"].values())


def test_same_saved_score_rerun_exports_identical_audio_bytes():
    first = export_run("processed")
    second = export_run("processed")
    assert first["wav_sha256"] == second["wav_sha256"]


def test_research_note_api_binds_current_revision_and_mode(monkeypatch):
    captured = {}
    monkeypatch.setattr(app_module, "load_score", lambda: {"revision": 42})

    def fake_append(row):
        captured["row"] = dict(row)
        return {"recorded_at": "qa", **row}

    monkeypatch.setattr(app_module, "append_note", fake_append)
    handler = object.__new__(app_module.Handler)
    handler.path = "/api/note"
    handler._read_json = lambda: {"disposition": "KEEP", "note": "qa-note", "mode": "dry", "listening_setup": "qa-headphones"}
    handler._json = lambda value, status=200: captured.update(response=value, status=status) or value
    app_module.Handler.do_POST(handler)

    row = captured["row"]
    assert captured["status"] == 200
    assert row["score_revision"] == 42
    assert row["mode"] == "dry"
    assert row["disposition"] == "KEEP"
    assert row["listening_setup"] == "qa-headphones"
