import json, os, socket, subprocess, sys, time
from pathlib import Path
from urllib.request import urlopen, Request

ROOT=Path(__file__).resolve().parents[2]


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0)); return s.getsockname()[1]


def test_local_api_and_ui_smoke():
    port=free_port(); env={**os.environ,'VOICE_PORT':str(port)}
    proc=subprocess.Popen([sys.executable,'app.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                with urlopen(f'http://127.0.0.1:{port}/api/state',timeout=5) as r:
                    state=json.load(r); break
            except Exception: time.sleep(.05)
        else: raise AssertionError('server did not start')
        assert state['readiness']['processed_ready'] is True
        with urlopen(f'http://127.0.0.1:{port}/',timeout=10) as r:
            html=r.read().decode('utf-8')
        assert 'Temporal Workbench' in html
        assert 'PLAY FULL' in html
    finally:
        proc.terminate(); proc.wait(timeout=5)
