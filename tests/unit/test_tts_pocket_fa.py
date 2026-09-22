from voice_proto import tts_pocket_fa as p


def test_source_sentence_boundaries_are_preserved_for_planning():
    assert p._source_sentences("اول. دوم؟ سوم!") == ["اول.", "دوم؟", "سوم!"]


def test_clause_boundaries_are_preferred_not_authored_source_rewrites():
    assert p._source_clauses("الف، ب؛ ج: د") == ["الف،", "ب؛", "ج:", "د"]
    assert not hasattr(p, "rewrite_source_text")


def test_exact_model_normalizer_spells_digits_instead_of_dropping_them():
    got = p._normalize_persian("تا سال ۲۰۳۰ تغییر دهد.")
    assert "۲۰۳۰" not in got and "2030" not in got
    assert len(got) > len("تا سال ")


def test_reference_prompt_is_bounded_to_model_training_condition():
    cfg = p._cfg()
    ref = p.ROOT / cfg["reference_audio"]
    assert ref.is_file()
    import wave
    with wave.open(str(ref), "rb") as w:
        seconds = w.getnframes() / float(w.getframerate())
    assert 2.0 <= seconds <= float(cfg["max_prompt_seconds"])


def test_resolved_model_resources_exist_and_recovery_is_bounded():
    cfg = p._cfg()
    assert (p.ROOT / cfg["pinned_model_config"]).is_file()
    assert (p.ROOT / cfg["normalizer_path"]).is_file()
    assert cfg["model_revision"] and cfg["g2p_revision"]
    assert 0 < float(cfg["cap_ratio"]) < 1
    assert 0 <= int(cfg["max_split_depth"]) <= 4


def test_runtime_and_model_revisions_are_frozen():
    cfg = p._cfg()
    assert cfg["transformers_version"] == "5.17.0"
    assert cfg["model_revision"] == "e87097ed98edb8bd9c9bcabe9b575a51a466d0e4"
    assert cfg["g2p_revision"] == "e314087bc761e323d127ee7899cb34f7c7d697cd"
    assert len(cfg["model_revision"]) == 40
    assert len(cfg["g2p_revision"]) == 40
