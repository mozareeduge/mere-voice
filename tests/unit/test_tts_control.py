import json
import unicodedata

from voice_proto import tts
from voice_proto.storage import ROOT


def _lines():
    return json.loads((ROOT / "data/source/voice_lines.primary_witness.json").read_text(encoding="utf-8"))["lines"]


def _strip_marks(s):
    n = unicodedata.normalize("NFD", s)
    return unicodedata.normalize("NFC", "".join(ch for ch in n if unicodedata.category(ch) != "Mn"))


def test_spoken_text_is_always_canonical_text_fa():
    for line in _lines():
        assert tts._spoken_text(line) == line["text_fa"]


def test_vocalized_field_cannot_drive_synthesis():
    line = {"line_id": "X", "text_fa": "صدا", "text_fa_vocalized": "صَدا"}
    assert tts._spoken_text(line) == "صدا"


def test_default_is_single_native_span_with_commas_inside():
    text = "سلام، حال شما چطور است؟ خوب هستم."
    spans = tts._synthesis_spans(text, 0)
    assert spans == [{"text": text, "pause_after_ms": 0}]


def test_sentence_gap_splits_only_at_sentence_terminals():
    text = "سلام، حال شما چطور است؟ خوب هستم؛ ممنون. تمام"
    spans = tts._synthesis_spans(text, 300)
    assert [s["text"] for s in spans] == ["سلام، حال شما چطور است؟", "خوب هستم؛ ممنون.", "تمام"]
    assert [s["pause_after_ms"] for s in spans] == [300, 300, 0]


def test_override_replaces_exact_nth_span_with_raw_phoneme_block():
    entry = {"id": "P1", "source": "کلمه", "occurrence": 2, "raw_espeak_ipa": "kalame"}
    assert tts.apply_overrides("کلمه و کلمه", [entry]) == "کلمه و [[ kalame ]]"


def test_override_missing_span_fails_loudly():
    entry = {"id": "P1", "source": "غایب", "occurrence": 1, "raw_espeak_ipa": "x"}
    try:
        tts.apply_overrides("متن", [entry])
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError")


def test_shipped_overrides_empty_or_only_valid_and_drafts_ignored(tmp_path):
    f = tmp_path / "o.json"
    f.write_text(json.dumps({"lines": {"VOICE-001": [{"id": "d", "source": "a", "raw_espeak_ipa": "b", "status": "draft"}]}}), encoding="utf-8")
    assert tts.load_overrides(f) == {}


def test_asset_key_changes_with_override_and_gap():
    line = {"line_id": "V", "text_fa": "متن"}
    ident0 = {"synthesis": tts._synthesis_identity({}, 0)}
    ident1 = {"synthesis": tts._synthesis_identity({}, 300)}
    ov = [{"id": "P", "source": "متن", "occurrence": 1, "raw_espeak_ipa": "matn"}]
    keys = {tts._asset_key(line, ident0), tts._asset_key(line, ident1), tts._asset_key(line, ident0, ov)}
    assert len(keys) == 3
