# Primary Voice Source Closure — v0.5

**Status:** `PRIMARY_WITNESS_SOURCE_LAYER_BUILT`  
**Source:** `چرا که تو بذل عشق می_کنی..pdf` — primary five-page play witness.  
**Runnable source:** `data/source/voice_lines.primary_witness.json`

## What changed from v0.3

The previous 14-line dossier fixture was useful for UI/timing construction but was not complete source authority. The primary PDF witness is available in the project corpus, so v0.5 replaces that fixture with 17 ordered Voice units. The v0.3 fixture is preserved under `history/v0.3/`.

The correction matters because the dossier fixture had four source losses:

1. `VOICE-001` omitted the second clause in which the eye rejects the body.
2. `VOICE-008` and `VOICE-010` omitted their second sentences.
3. the `ذهن در تاریخ...` Voice unit was absent.
4. the late slashed passage merged `لامسه...`, `خواستن...`, and `میل...` into one line even though the play presents them as separate Voice entries.

## Source handling rule

For each unit the JSON preserves:

- `text_fa` — spoken Voice material used by the prototype;
- `source_raw_excerpt` — the indexed PDF text before cleanup;
- `source_segments` where stage directions interrupt speech;
- `normalization_notes` — every declared repair;
- `source_page` and primary-witness provenance.

Only extraction-level repairs are authorized: whitespace/ZWNJ joins, obvious split glyphs, separation of stage directions from spoken material, and the explicitly recorded `المسه → لامسه` repair supported by the dossier witness and Persian lexical context. No new Voice wording is generated.

## Remaining human source gate

The indexed PDF text is sufficient for this functional TTS prototype. A later visual comparison against the PDF pages should confirm punctuation/typography before treating this transcription as a final textual edition. That check does not require an engineering redesign.
