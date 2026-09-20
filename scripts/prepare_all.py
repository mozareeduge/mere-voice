from __future__ import annotations
import argparse
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from voice_proto.storage import load_score
from voice_proto.tts import render_fixture_espeak, render_with_piper
from voice_proto.processing import prepare_variant

p=argparse.ArgumentParser(); p.add_argument('--fixture',action='store_true',help='rebuild explicit espeak fixture instead of Piper'); args=p.parse_args()
assets=render_fixture_espeak() if args.fixture else render_with_piper()
print(f'dry assets ready: {len(assets)}')
score=load_score(); count=0
for event in score['events']:
    if event['enabled']:
        prepare_variant(event['line_id'],event['processing']); count+=1
print(f'processed variants ready: {count}')
