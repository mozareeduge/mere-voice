from pathlib import Path

from app import current_state
from voice_proto.export import export_run
from voice_proto.domain import variant_key
from voice_proto.storage import ROOT, SOURCE_PATH, inspect_dry_asset, load_asset_meta, load_lines, load_score, read_json, saved_revision_info, variant_meta_path


def test_primary_witness_candidate_is_immediately_runnable_with_explicit_fixture_audio():
    state=current_state()
    assert state['fixture_mode'] is False
    assert state['source_primary_witness'] is True
    assert state['audio_fixture_mode'] is True
    assert len(state['lines']) == 17
    assert len(state['score']['events']) == 17
    assert state['readiness']['dry_ready'] is True
    assert state['readiness']['processed_ready'] is True


def test_primary_witness_includes_full_previously_missing_or_merged_voice_units():
    by_id={x['line_id']:x['text_fa'] for x in load_lines()}
    assert 'چشم' in by_id['VOICE-001']
    assert 'ذهن، زندگی در بدن را پس می‌زند' in by_id['VOICE-008']
    assert 'کلمات بیان را پس می‌زنند' in by_id['VOICE-010']
    assert by_id['VOICE-012'].startswith('ذهن در تاریخ')
    assert by_id['VOICE-014'] == 'لامسه دست را پس می‌زند.'
    assert by_id['VOICE-015'] == 'خواستن میل را پس می‌زند.'
    assert by_id['VOICE-016'] == 'میل خواهش را پس می‌زند.'


def test_start_time_is_not_part_of_variant_identity():
    score=load_score(); event=score['events'][0]; dry=load_asset_meta(event['line_id'])
    a=variant_key(dry,event['processing'])
    event2={**event,'start_ms':event['start_ms']+1234}
    b=variant_key(dry,event2['processing'])
    assert a==b


def test_prebuilt_variants_exist_and_reference_current_dry_hash():
    for event in load_score()['events']:
        dry=inspect_dry_asset(event['line_id'])
        assert dry['status']=='READY'
        key=variant_key(dry,event['processing'])
        meta=read_json(variant_meta_path(key))
        assert meta['status']=='READY'
        assert meta['dry_wav_sha256']==dry['wav_sha256']
        assert (ROOT/meta['wav_path']).exists()


def test_export_processed_and_dry_are_created():
    assert saved_revision_info() is not None
    a=export_run('processed'); b=export_run('dry')
    assert (ROOT/a['wav']).exists() and (ROOT/a['sidecar']).exists()
    assert (ROOT/b['wav']).exists() and (ROOT/b['sidecar']).exists()


def test_source_mutation_marks_existing_asset_stale_and_blocks_readiness():
    import json
    original = SOURCE_PATH.read_bytes()
    try:
        doc=json.loads(original.decode('utf-8')); doc['lines'][0]['text_fa'] += '،'
        SOURCE_PATH.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        mutated=current_state(); first=next(x for x in mutated['lines'] if x['line_id']=='VOICE-001')
        assert first['asset']['status']=='STALE'
        assert mutated['readiness']['dry_ready'] is False
        assert mutated['readiness']['processed_ready'] is False
    finally:
        SOURCE_PATH.write_bytes(original)
    assert current_state()['readiness']['processed_ready'] is True


def test_missing_or_corrupt_dry_bytes_cannot_claim_ready():
    dry=load_asset_meta('VOICE-001'); path=ROOT/dry['wav_path']; original=path.read_bytes()
    try:
        path.write_bytes(original + b'corruption-canary')
        state=current_state(); first=next(x for x in state['lines'] if x['line_id']=='VOICE-001')
        assert first['asset']['status']=='HASH_MISMATCH'
        assert state['readiness']['dry_ready'] is False
        assert state['readiness']['processed_ready'] is False
    finally:
        path.write_bytes(original)
    assert inspect_dry_asset('VOICE-001')['status']=='READY'


def test_missing_processed_bytes_cannot_claim_processed_ready():
    event=load_score()['events'][0]; dry=inspect_dry_asset(event['line_id']); key=variant_key(dry,event['processing'])
    meta=read_json(variant_meta_path(key)); path=ROOT/meta['wav_path']; backup=path.read_bytes()
    try:
        path.unlink()
        state=current_state(); ev=next(x for x in state['score']['events'] if x['event_id']==event['event_id'])
        assert ev['variant']['status']=='MISSING_FILE'
        assert state['readiness']['dry_ready'] is True
        assert state['readiness']['processed_ready'] is False
    finally:
        path.write_bytes(backup)
    assert current_state()['readiness']['processed_ready'] is True
