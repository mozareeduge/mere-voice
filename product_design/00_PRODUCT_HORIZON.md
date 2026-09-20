# 00 — Product Horizon

## 1. Product purpose

Build the smallest rehearsal instrument that lets Mozare **hear temporal relations among fixed authored Voice lines** rather than merely discuss them.

The prototype turns fixed Persian text into local speech assets, lets the operator place multiple instances on an explicit timeline, overlap them, apply bounded sonic transformation, compare dry/processed versions, run the score offline, and preserve each experiment as reproducible evidence.

It is a research instrument for rehearsal. It is not the final performance system and does not decide what the Voice ultimately is.

## 2. Target horizon

### HZN-001 — Primary-witness Voice text is immutable product input
The prototype now ships a 17-unit Persian Voice source layer transcribed from the primary five-page play witness. The local source file records the primary raw extraction, declared normalization repairs, and embedded stage directions separately from spoken Voice material. The workbench displays the spoken source read-only and never rewrites, paraphrases, translates, autocompletes, or silently normalizes it.

### HZN-002 — Rendering is a preparation stage
TTS occurs before a temporal run. A run never waits for inference. Every dry asset records the exact source-text hash, model/profile identity, output hash, duration, and render time.

### HZN-003 — Processing is separate from source rendering
A dry asset remains intact. Event processing creates a separate reproducible processed variant. Processing parameters can change without changing the source line or dry asset.

### HZN-004 — Time is explicit
Every event has an absolute onset `start_ms >= 0` relative to run start. Events are never implicitly chained end-to-start. Silence and overlap are authored states.

### HZN-005 — Polyphony is first-class
Any number of enabled events may overlap within practical machine limits. The same line may appear more than once with independent timing and processing.

### HZN-006 — Event lifecycle is operable without code
The operator can add an event from a line, duplicate it, enable/disable it, delete it from the current score, select it, and edit its timing/processing numerically.

### HZN-007 — Dry comparison is always recoverable
Every processed event retains a traceable dry source. Dry audition and whole-score `DRY BYPASS` remain available without re-rendering TTS.

### HZN-008 — Preparation/readiness is truthful
Processed playback is READY only when every enabled event references a current dry asset and current processed variant. Dry-bypass playback requires only current dry assets. Missing/stale/failed items are named causally.

### HZN-009 — Playback can be fully offline
Once required assets/variants are prepared, a full run, dry-bypass run, revision save, note capture, and export require no network access.

### HZN-010 — The timeline is visible but not a hidden editor
The timeline visualizes event onsets, durations, silence, overlap and playhead. v0.1 does **not** require drag-to-move editing. Exact onset editing happens in the inspector so timing remains explicit and testable.

### HZN-011 — Experiments persist as evidence
A saved score revision freezes event data plus exact asset/variant references. A research note can attach perceived result and `KEEP | RETRY | DROP | HOLD`. An export can produce an audible stereo run plus machine-readable sidecar metadata.

### HZN-012 — The room remains unresolved
v0.1 monitors through the OS/default stereo output. A logical route field is preserved, but speaker count, location, interface channel count, and final spatial Voice design remain outside this product authority.

## 3. Platform horizon

- Windows 10/11 x64 rehearsal laptop.
- Desktop browser/workbench at `>=1024px`; `>=1280px` preferred.
- OS/default stereo or headphones.
- Local files only; no account/auth/cloud/database.
- One operator at a time.
- Mobile/tablet production use is out of scope.

## 4. Protected artistic/research boundaries

- fixed authored text ≠ generated text;
- canonical wording ≠ TTS pronunciation/rendering behavior;
- sound-body choice ≠ processing;
- processing ≠ temporal score;
- temporal score ≠ physical spatial address;
- technical success ≠ artistic acceptance;
- exact experimental parameters ≠ final aesthetic truth.

## 5. Explicit non-goals

Live generation, free typing, live operator text selection, actor/audience sensing, biometrics, ECG integration, final cue/show-control integration, final stage speaker routing, mobile design, cloud hosting, collaboration, accounts, remote control, production deployment.

## 6. Completion condition

An executor can implement the prototype without deciding the meaning of source fidelity, stale audio, processed variant, event lifecycle, overlap, silence, readiness, dry bypass, score revision, research evidence, or export.

**Status:** `PRODUCT_DESIGN_AUTHORITY_CLOSED_WITH_HUMAN_REVIEW_GATES`
