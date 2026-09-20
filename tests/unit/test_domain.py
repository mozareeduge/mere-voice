from voice_proto.domain import PROCESSING_DEFAULTS, ValidationError, processing_hash, sha256_text, validate_processing, validate_score


def test_text_hash_changes_on_punctuation():
    assert sha256_text('صدا') != sha256_text('صدا.')


def test_processing_range_rejects_out_of_bounds():
    bad = dict(PROCESSING_DEFAULTS, pan=1.5)
    try:
        validate_processing(bad)
    except ValidationError:
        pass
    else:
        raise AssertionError('expected ValidationError')


def test_processing_hash_independent_of_key_order():
    a = dict(PROCESSING_DEFAULTS)
    b = dict(reversed(list(a.items())))
    assert processing_hash(a) == processing_hash(b)


def test_score_allows_same_line_and_same_onset_but_unique_event_ids():
    e = {'line_id':'VOICE-001','start_ms':100,'enabled':True,'route_id':'STEREO_MAIN','processing':PROCESSING_DEFAULTS}
    score={'score_id':'S','revision':0,'name':'x','events':[dict(e,event_id='EV-001'),dict(e,event_id='EV-002')]}
    out=validate_score(score,{'VOICE-001'})
    assert len(out['events'])==2


def test_duplicate_event_id_is_rejected():
    e = {'event_id':'EV-001','line_id':'VOICE-001','start_ms':0,'enabled':True,'route_id':'STEREO_MAIN','processing':PROCESSING_DEFAULTS}
    try:
        validate_score({'events':[e,e]}, {'VOICE-001'})
    except ValidationError:
        pass
    else:
        raise AssertionError('expected duplicate ID failure')
