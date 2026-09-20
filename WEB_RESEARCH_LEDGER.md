# Web Research Ledger — decision-relevant facts only

Verified 2026-09-20.

| Source | Verified fact | Package consequence |
|---|---|---|
| OHF-Voice `piper1-gpl` Python API | `pip install piper-tts`; `PiperVoice.load` + `synthesize_wav`; `SynthesisConfig` supports volume/length/noise controls | `voice_proto/tts.py` uses the current local Python API; no live HTTP/service dependency |
| PyPI `piper-tts` | release 1.8.0 (2026-09-04), Python >=3.9, classifiers through 3.13, Windows x86-64 wheel | setup accepts supported intersection rather than hard-coding Python 3.11 |
| PyPI `pedalboard` | release 0.9.25 (2026-09-09), Python >=3.10, Windows support, classifiers through 3.15 | target setup resolves the current 0.9.x release; package compatibility floor remains `>=0.9.23,<0.10` because the candidate was also regression-tested on 0.9.23; Python intersection with Piper remains 3.10–3.13 |
| Mana-Persian-Piper model | MIT; `fa_IR-mana-medium.onnx`, 63,531,379 bytes, SHA-256 `e390c0e74ba71fd97c49ba662ee0c6e1724b462ba2d4561698af4f564840f126` | downloader pins exact ONNX SHA |
| Mana config raw file | sample rate 22050; language `fa`; eSpeak voice `fa`; `phoneme_type=espeak`; one speaker | downloader/runtime validate semantic config invariants instead of trusting filename |
| Web Audio API | buffer sources schedule against audio-context time; OfflineAudioContext can render deterministic graph/timing | production scheduler uses audio clock; QA uses same scheduler with offline context |

No web source is used as authority for Niravana's play wording. The current source layer comes from the primary play witness in the project corpus.
