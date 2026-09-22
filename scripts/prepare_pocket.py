from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from voice_proto.tts_pocket_fa import render_with_pocket
from voice_proto.processing import prepare_variant
from voice_proto.storage import load_score

p=argparse.ArgumentParser(description="Render Mere Voice with Pocket-TTS Farsi v2")
p.add_argument("--diagnostic",action="store_true",help="render only VOICE-001, VOICE-004, VOICE-009")
p.add_argument("--dry-only",action="store_true",help="do not rebuild processed event variants")
a=p.parse_args()
ids=["VOICE-001","VOICE-004","VOICE-009"] if a.diagnostic else None
assets=render_with_pocket(ids)
variants=[]
if not a.dry_only:
    selected = set(ids or [x["line_id"] for x in assets])
    for e in load_score()["events"]:
        if e["enabled"] and e["line_id"] in selected:
            variants.append(prepare_variant(e["line_id"],e["processing"]))
print(json.dumps({"provider":"pocket_fa_v2","dry_assets":len(assets),"processed_variants":len(variants),"line_ids":[x["line_id"] for x in assets]},indent=2))
