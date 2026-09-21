# 05 — Decision and Supersession Ledger

## Closed product/design decisions

### DEC-001 — fixed authored text only
v0.1 uses Path A. No LLM generation, free typing or live text selection.

### DEC-002 — TTS is prototype material, not final Voice identity
Synthetic speech is authorized for the prototype; final source body remains GATE-OWNER-02.

### DEC-003 — primary-witness source file is authoritative for prototype text and read-only in UI
`data/source/voice_lines.primary_witness.json` contains 17 ordered Voice units reconstructed from the primary PDF's indexed text with every non-trivial extraction repair declared. The UI has no hidden text-authoring workflow.

### DEC-004 — render TTS before run
Inference latency is preparation cost, never authored score timing.

### DEC-005 — processing variants are separate from dry assets
Dry source is immutable; event processing is reproducible/replaceable.

### DEC-006 — absolute timeline
`start_ms` is absolute score time. No clip chaining.

### DEC-007 — event lifecycle is explicit
Add, duplicate, enable/disable, delete, select and numeric onset editing are v0.1 product operations.

### DEC-008 — timeline is not drag-edited in v0.1
Numeric timing editing is intentional: lower implementation ambiguity, higher precision, easier QA. Drag editing can be explored later.

### DEC-009 — dry bypass preserves score timing
Dry/processed comparison changes sound body, not event timing.

### DEC-010 — no Pause semantics
Full play, rehearsal-start play, stop/reset only.

### DEC-011 — stereo/default OS output
No device picker or stage speaker topology in v0.1.

### DEC-012 — research evidence/export belongs to the prototype
Score revisions, compact notes and WAV+sidecar export are not optional polish; they make rehearsal comparisons recoverable.

### DEC-013 — desktop-only acceptance
1024px minimum acceptance; mobile excluded.

## Technical selection decisions — implementation-level but frozen for this intake

### DEC-014 — supported Python + local standard-library web workbench
Use Python 3.10–3.13 for the verified Piper/Pedalboard dependency intersection. The supplied app itself uses a localhost-only Python standard-library HTTP service with vanilla HTML/CSS/JS; no Flask/React/Node/Electron/database/account/cloud runtime is required.

### DEC-015 — Piper current upstream + Mana first bench model
Use current `OHF-Voice/piper1-gpl` / `piper-tts`; bench `MahtaFetrat/Mana-Persian-Piper` first. Model quality remains evidence, not authority.

### DEC-016 — Pedalboard prepares event variants offline
Use Pedalboard for bounded offline pitch/reverb/delay processing; envelope/pan/gain may be applied in the same preparation module. The processed WAV is cache/evidence, not source truth.

### DEC-017 — Web Audio schedules playback
Use `AudioBufferSourceNode.start(when)` against one `AudioContext` clock. UI timers do not schedule sound.

### DEC-018 — OfflineAudioContext is the temporal QA harness
Use the same scheduler logic against `OfflineAudioContext` with deterministic tone fixtures so onset/overlap tests do not depend on speakers/microphone capture.

### DEC-019 — SuperCollider deferred from v0.1
SuperCollider remains a strong later candidate for live mutable DSP/multi-bus stage routing, but adding a second audio runtime now increases installation and integration surface without answering the current research need.

### DEC-020 — prepared dry WAV is the fallback
Web Speech fallback is dropped. A central Voice layer must continue through already-local material.

## Superseded claims

- archived `rhasspy/piper` is not current upstream;
- prior `~1–2s` TTS latency is not a temporal-run requirement;
- `PlayBuf rate × pitchRatio` is not accepted as duration-preserving pitch shift;
- Pedalboard/Rubber Band licensing cannot be summarized as `ticketed = prohibited`;
- fixed 0.3/0.6/1.0s offsets are test coordinates, not hidden defaults.

## Human / later-production gates

### GATE-SOURCE-FIDELITY-01 — visual PDF confirmation
Engineering source reconstruction is complete. Before calling the transcription a diplomatic/final textual edition, a human should compare the 17 stored Voice units and the declared repairs against the visible PDF pages. This is a source-fidelity review, not an implementation blocker.

### GATE-HUMAN-VOICE-01 — final source body
Synthetic vs human/recorded/live/hybrid belongs to later rehearsal/convergence.

**Status:** `PRODUCT_DESIGN_AUTHORITY_CLOSED_WITH_HUMAN_REVIEW_GATES`

## v0.6.1 amendments (2026-09-21, owner-instructed)

### DEC-016 — vocalized reading text is a synthesis layer, not a source replacement
`text_fa_vocalized` (اعراب short-vowel diacritics) is added beside `text_fa` in the primary witness file. Synthesis reads the vocalized field when present; `text_fa` remains the authoritative witness and the UI remains read-only for both. Vocalization is agent-authored (declared in-file) and stays subject to the human Persian listening gate; it never upgrades source authority.

### DEC-017 — punctuation pause semantics are part of the Voice read
Sentence terminals (`. ! ? ؟ …`) insert a 420 ms silence; clause marks (`، , ; :`) insert 190 ms, applied between synthesis chunks in the dry render. Pause lengths are recorded in each asset's `synthesis_pipeline` evidence. This is authored reading behavior, not event timing; DEC-006 (absolute timeline) is untouched.

### DEC-018 — tempo is an event-processing parameter
New `tempo_scale` field, range 0.5–2.0, default 1.0, pitch-preserving time-stretch (pedalboard `time_stretch`, high quality). >1 reads faster, <1 slower; pitch identity is unchanged. It participates in `processing_hash`, so changing it stales the variant (OBJ-005 rule intact). "DRY" (neutral) now includes `tempo_scale == 1.0`.

### DEC-019 — LCA phonemizer (option 3) evaluated: NOT adopted in v0.6.1
Machine-fit verdict (lane-B-LCA-eval.md, 2026-09-21): feasible on CPU but requires a forked Piper build (no Windows wheel), torch+transformers (~200+ MB over the owner's slow/flaky connection), and a boot-time HuggingFace fetch that breaks local-only operation; benefit for the fixed 17-line corpus is unquantified. Any future adoption must be an optional, default-OFF path with offline-cached models, gated on audible homograph/ezafe defects found in listening.
