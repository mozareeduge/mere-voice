from __future__ import annotations

import json
import importlib.util
import mimetypes
import os
import traceback
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from voice_proto.domain import processing_hash, score_semantic_hash, sha256_text, validate_score, variant_key
from voice_proto.version import APP_VERSION, DISPLAY_VERSION
from voice_proto.storage import (
    PROCESSED_DIR,
    ROOT,
    append_note,
    known_line_ids,
    inspect_dry_asset,
    inspect_variant,
    load_lines,
    load_score,
    read_json,
    save_current_score,
    save_revision,
    saved_revision_info,
    score_dirty,
    source_document,
    variant_meta_path,
)

HOST = "127.0.0.1"
PORT = int(os.environ.get("VOICE_PORT", "8765"))
WEB = ROOT / "web"


def current_state() -> dict:
    lines = load_lines()
    line_by_id = {x["line_id"]: x for x in lines}
    line_states = []
    for line in lines:
        asset = inspect_dry_asset(line["line_id"])
        line_states.append({**line, "asset": asset})

    score = load_score()
    event_states = []
    processed_ready = True
    dry_ready = True
    for event in score["events"]:
        line = line_by_id[event["line_id"]]
        asset = inspect_dry_asset(event["line_id"])
        asset_ok = bool(asset and asset.get("status") == "READY")
        if event["enabled"] and not asset_ok:
            dry_ready = False
            processed_ready = False
        variant = None
        if asset_ok:
            key = variant_key(asset, event["processing"])
            variant = inspect_variant(key, asset, event["processing"])
            variant_ok = bool(variant and variant.get("status") == "READY")
            if event["enabled"] and not variant_ok:
                processed_ready = False
        event_states.append({**event, "line_text_fa": line["text_fa"], "asset": asset or {"status": "MISSING"}, "variant": variant or {"status": "MISSING"}})

    latest = saved_revision_info()
    source = source_document()
    model_profile = read_json(ROOT / "data" / "config" / "model_profile.json", {})
    model_path = ROOT / model_profile.get("model_path", "")
    config_path = ROOT / model_profile.get("config_path", "")
    piper_ready = bool(importlib.util.find_spec("piper") and model_path.is_file() and config_path.is_file())
    return {
        "app_version": APP_VERSION,
        "source": {k: v for k, v in source.items() if k != "lines"},
        "lines": line_states,
        "score": {**score, "events": event_states},
        "readiness": {
            "dry_ready": dry_ready,
            "processed_ready": processed_ready,
            "state": "READY_PROCESSED" if processed_ready else ("READY_DRY_BYPASS" if dry_ready else "BLOCKED"),
        },
        "dirty": score_dirty(),
        "latest_saved_revision": latest,
        "fixture_mode": source.get("source_mode") == "DOSSIER_FIXTURE",
        "source_primary_witness": source.get("source_mode") == "PRIMARY_PDF_WITNESS",
        "audio_fixture_mode": bool(lines) and all((x.get("asset") or {}).get("fixture") for x in line_states if (x.get("asset") or {}).get("status") == "READY"),
        "tts": __import__("voice_proto.tts_router", fromlist=["provider_status"]).provider_status(piper_ready=piper_ready),
    }


def safe_path(rel: str) -> Path:
    rel = unquote(rel).lstrip("/")
    path = (ROOT / rel).resolve()
    root = ROOT.resolve()
    if path != root and root not in path.parents:
        raise ValueError("path traversal blocked")
    return path


class Handler(BaseHTTPRequestHandler):
    server_version = f"NiravanaVoicePrototype/{DISPLAY_VERSION}"

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def _json(self, value, status=200):
        payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _file(self, path: Path):
        if not path.exists() or not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith("text/") or ctype in {"application/javascript", "application/json"} else ""))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/state":
                return self._json(current_state())
            if path == "/":
                return self._file(WEB / "index.html")
            if path.startswith("/web/"):
                return self._file(safe_path(path[1:]))
            if path.startswith("/files/"):
                return self._file(safe_path(path[len("/files/"):]))
            if path.startswith("/tests/browser/"):
                return self._file(safe_path(path[1:]))
            return self.send_error(404)
        except Exception as exc:
            traceback.print_exc()
            return self._json({"error": str(exc)}, 500)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            body = self._read_json()
            if path == "/api/score":
                saved = save_current_score(body.get("score", body))
                return self._json({"ok": True, "score": saved, "state": current_state()})
            if path == "/api/render-dry":
                line_ids = body.get("line_ids")
                from voice_proto.tts_router import render_dry, load_provider_config
                mode = body.get("mode") or load_provider_config().get("active_provider", "piper")
                result = render_dry(mode, line_ids)
                return self._json({"ok": True, "assets": result, "state": current_state()})
            if path == "/api/prepare":
                from voice_proto.processing import prepare_variant
                score = load_score()
                requested = set(body.get("event_ids") or [])
                result = []
                for event in score["events"]:
                    if not event["enabled"]:
                        continue
                    if requested and event["event_id"] not in requested:
                        continue
                    result.append({"event_id": event["event_id"], "variant": prepare_variant(event["line_id"], event["processing"])})
                return self._json({"ok": True, "variants": result, "state": current_state()})
            if path == "/api/save-revision":
                info = save_revision()
                return self._json({"ok": True, **info, "state": current_state()})
            if path == "/api/note":
                allowed = {"KEEP", "RETRY", "DROP", "HOLD"}
                disposition = str(body.get("disposition", "HOLD")).upper()
                if disposition not in allowed:
                    raise ValueError(f"disposition must be one of {sorted(allowed)}")
                row = append_note({
                    "score_revision": load_score().get("revision"),
                    "disposition": disposition,
                    "note": str(body.get("note", "")),
                    "listening_setup": str(body.get("listening_setup", "local stereo/default output")),
                    "mode": str(body.get("mode", "processed")),
                })
                return self._json({"ok": True, "note": row})
            if path == "/api/export":
                if score_dirty():
                    return self._json({"error": "Save a revision before export so provenance is unambiguous."}, 409)
                from voice_proto.export import export_run
                result = export_run(body.get("mode", "processed"))
                return self._json({"ok": True, **result})
            if path == "/api/reload-source":
                return self._json({"ok": True, "state": current_state()})
            return self.send_error(404)
        except Exception as exc:
            traceback.print_exc()
            return self._json({"error": str(exc)}, 400)


def main():
    print(f"Niravana Voice Prototype v{DISPLAY_VERSION} — http://{HOST}:{PORT}")
    print("Local-only server. Ctrl+C to stop.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
