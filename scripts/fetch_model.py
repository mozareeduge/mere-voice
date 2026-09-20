from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from voice_proto.version import DISPLAY_VERSION
MODELS=ROOT/'models'; MODELS.mkdir(exist_ok=True)
MODEL_URL='https://huggingface.co/MahtaFetrat/Mana-Persian-Piper/resolve/main/fa_IR-mana-medium.onnx?download=true'
CONFIG_URL='https://huggingface.co/MahtaFetrat/Mana-Persian-Piper/resolve/main/fa_IR-mana-medium.onnx.json?download=true'
MODEL_SHA='e390c0e74ba71fd97c49ba662ee0c6e1724b462ba2d4561698af4f564840f126'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def download(url,path):
    tmp=path.with_suffix(path.suffix+'.part')
    req=urllib.request.Request(url,headers={'User-Agent':f'niravana-voice-prototype/{DISPLAY_VERSION}'})
    with urllib.request.urlopen(req) as r, tmp.open('wb') as f:
        total=int(r.headers.get('Content-Length') or 0); done=0
        while True:
            chunk=r.read(1024*1024)
            if not chunk: break
            f.write(chunk); done+=len(chunk)
            if total: print(f'\r{path.name}: {done/total:5.1%}',end='',flush=True)
    print()
    tmp.replace(path)

model=MODELS/'fa_IR-mana-medium.onnx'; config=MODELS/'fa_IR-mana-medium.onnx.json'
if not model.exists() or sha(model)!=MODEL_SHA:
    print('Downloading Mana Persian Piper model (63.5 MB)…'); download(MODEL_URL,model)
actual=sha(model)
if actual!=MODEL_SHA: raise SystemExit(f'Model SHA-256 mismatch: {actual}')
expected_cfg={'sample_rate':22050,'language_code':'fa','espeak_voice':'fa','phoneme_type':'espeak','num_speakers':1}

def read_config_invariants(path):
    try:
        doc=json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None
    return {
        'sample_rate':(doc.get('audio') or {}).get('sample_rate'),
        'language_code':(doc.get('language') or {}).get('code'),
        'espeak_voice':(doc.get('espeak') or {}).get('voice'),
        'phoneme_type':doc.get('phoneme_type'),
        'num_speakers':doc.get('num_speakers'),
    }

actual_cfg=read_config_invariants(config) if config.exists() else None
if actual_cfg != expected_cfg:
    if config.exists():
        print('Existing model config is missing/corrupt/incompatible; replacing it…')
        config.unlink(missing_ok=True)
    else:
        print('Downloading model config…')
    download(CONFIG_URL,config)
    actual_cfg=read_config_invariants(config)
config_sha=sha(config)
if actual_cfg != expected_cfg:
    raise SystemExit(f'Model config invariant mismatch after download: expected {expected_cfg}, got {actual_cfg}')
print(json.dumps({'model':str(model),'model_sha256':actual,'config':str(config),'config_sha256':config_sha,'config_invariants':actual_cfg,'status':'OK'},indent=2))
