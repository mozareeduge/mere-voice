# Prebuilt Implementation State — near-final v0.6

**Candidate:** `NIRAVANA-VOICE-NEARFINAL-0.6`  
**Product state:** functional local rehearsal workbench, compiler-checked  
**Supplied sound state:** complete fixture corpus; real Mana/Piper corpus prepared on target by one command

## Product already built

`primary-witness Persian Voice text → immutable dry assets → event-specific processed variants → absolute-ms score → single-clock Web Audio playback → revision / notes / WAV+JSON evidence`

The package contains the complete local server/browser workbench, 17 primary-witness units, 17-event baseline score, fixture audio for immediate operation, temporal/processing controls, overlap/silence behavior, dry bypass, persistence, revision saving, note capture, export, target finalizer, and release evidence.

## v0.6 closure added from the executable-handoff compiler

- candidate/version identity is centralized rather than repeated as independent runtime constants;
- 8 logical release artifacts have IDs, byte fingerprints, scenario links, evidence links and known limits;
- every authoritative scenario/cross-factor case is classified against actual evidence;
- product-authority divergences in invalid-input, Add, Duplicate and dirty Delete behavior were fixed and given browser canaries;
- atomic-write failure, pitch semantics, deterministic rerun, note binding, scheduler lifecycle and compiler integrity now have direct executable checks;
- a single final-acceptance runner distinguishes engineering acceptance from target/human gates.

## Checked automated proof

`python -m pytest -q` → **23 passed**. Node scheduler lifecycle → PASS. Chromium geometry/timing/interaction QA → PASS. Strict compiler acceptance → PASS.

The package intentionally retains unproven classifications where evidence cannot truthfully be produced here. No further general redesign phase is required for this prototype scope.
