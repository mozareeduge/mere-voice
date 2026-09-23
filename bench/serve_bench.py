"""Independent local source-body bench server (port 8766). Never selects a winner.

GET  /                  bench page
GET  /api/bench         manifest: lines (canonical text) x conditions (file or null)
GET  /audio/<cond>/<f>  dry audio
POST /upload?line=&ext=  raw body -> bench/audio/human-recorded/<line>.<ext> (previous take is kept, never overwritten)
POST /save              JSON results -> evidence/bench/results_<UTC>.json (+ results_latest.json)
"""
from __future__ import annotations

import json
import mimetypes
import os
import re
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench"
AUDIO = BENCH / "audio"
RESULTS = ROOT / "evidence" / "bench"
SESSION = BENCH / "bench_session.json"
DEFAULT_LINES = [("VOICE-004", "pharmaceutical / long clinical stress case"), ("VOICE-001", "colloquial rejection relation"), ("VOICE-009", "memory / lyrical register")]
DEFAULT_CONDITIONS = ["mana-canonical", "human-recorded", "mana-pre-v061", "mana-v061-vocalized", "pocket-fa-v2"]
AUDIO_EXTS = {"wav", "mp3", "m4a", "flac", "ogg", "webm", "aac", "opus"}
UPLOAD_LIMIT = 100 * 1024 * 1024
PORT = int(os.environ.get("BENCH_PORT", "8766"))


def session() -> dict:
    """Optional bench/bench_session.json. Without it the bench behaves exactly as before.

    {"auto_conditions": true, "exclude": [...], "labels": {cond: label},
     "lines": [{"line_id": "...", "why": "...", "text_fa": "optional, else from the primary witness"}]}
    With auto_conditions, every folder in bench/audio/ is a condition unless it starts with "_" or is excluded.
    """
    try:
        return json.loads(SESSION.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def conditions() -> list[str]:
    s = session()
    if not s.get("auto_conditions"):
        return list(DEFAULT_CONDITIONS)
    skip = set(s.get("exclude") or [])
    return sorted(p.name for p in AUDIO.iterdir() if p.is_dir() and not p.name.startswith("_") and p.name not in skip)


def lines() -> list[dict]:
    rows = session().get("lines")
    if not rows:
        return [{"line_id": lid, "why": why} for lid, why in DEFAULT_LINES]
    return [{"line_id": r["line_id"], "why": r.get("why", ""), **({"text_fa": r["text_fa"]} if r.get("text_fa") else {})} for r in rows]


def find_audio(cond: str, line: str) -> str | None:
    folder = AUDIO / cond
    if not folder.is_dir():
        return None
    for p in sorted(folder.glob(f"{line}.*")):
        if p.suffix.lower().lstrip(".") in AUDIO_EXTS:
            return f"/audio/{cond}/{p.name}"
    return None


def manifest() -> dict:
    src = json.loads((ROOT / "data" / "source" / "voice_lines.primary_witness.json").read_text(encoding="utf-8"))
    text = {r["line_id"]: r["text_fa"] for r in src["lines"]}
    conds = conditions()
    return {
        "conditions": conds,
        "labels": session().get("labels") or {},
        "lines": [{"line_id": l["line_id"], "why": l["why"], "text_fa": l.get("text_fa") or text.get(l["line_id"], ""),
                   "files": {c: find_audio(c, l["line_id"]) for c in conds}} for l in lines()],
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "MereVoiceBench/1"

    def log_message(self, fmt, *args):
        pass

    def _send(self, status, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, doc):
        self._send(status, json.dumps(doc, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path in ("/", "/index.html"):
            return self._send(HTTPStatus.OK, (BENCH / "index.html").read_bytes(), "text/html; charset=utf-8")
        if path == "/api/bench":
            return self._json(HTTPStatus.OK, manifest())
        m = re.fullmatch(r"/audio/([A-Za-z0-9_-]+)/([A-Z]+-[0-9A-Za-z]+\.[a-z0-9]+)", path)
        if m and m.group(1) in conditions():
            f = AUDIO / m.group(1) / m.group(2)
            if f.is_file():
                return self._send(HTTPStatus.OK, f.read_bytes(), mimetypes.guess_type(f.name)[0] or "application/octet-stream")
        self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self):
        url = urlparse(self.path)
        n = int(self.headers.get("Content-Length") or 0)
        if n > UPLOAD_LIMIT:
            return self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "too large"})
        body = self.rfile.read(n)
        if url.path == "/upload":
            q = parse_qs(url.query)
            line = (q.get("line") or [""])[0]
            ext = (q.get("ext") or [""])[0].lower().lstrip(".")
            if line not in {l["line_id"] for l in lines()} or ext not in AUDIO_EXTS or not body:
                return self._json(HTTPStatus.BAD_REQUEST, {"error": "line/ext/body invalid"})
            d = AUDIO / "human-recorded"
            d.mkdir(parents=True, exist_ok=True)
            for old in d.glob(f"{line}.*"):
                stamp = datetime.fromtimestamp(old.stat().st_mtime, timezone.utc).strftime("%Y%m%dT%H%M%S")
                old.rename(d / f"_previous_{stamp}_{old.name}")
            (d / f"{line}.{ext}").write_bytes(body)
            return self._json(HTTPStatus.OK, {"saved": f"/audio/human-recorded/{line}.{ext}", "bytes": len(body)})
        if url.path == "/save":
            try:
                doc = json.loads(body.decode("utf-8"))
            except Exception:
                return self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid json"})
            RESULTS.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            doc["saved_at"] = stamp
            out = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
            (RESULTS / f"results_{stamp}.json").write_text(out, encoding="utf-8")
            (RESULTS / "results_latest.json").write_text(out, encoding="utf-8")
            return self._json(HTTPStatus.OK, {"saved": f"evidence/bench/results_{stamp}.json"})
        self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})


if __name__ == "__main__":
    print(f"Source-body bench on http://127.0.0.1:{PORT}/  (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
