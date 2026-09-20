# Fixture, Canary and Evidence Specification

This file exists so timing/source QA does not depend on subjective listening or on the final Persian text.

## 1. Deterministic audio fixtures

Generate in test code; do not commit binary fixtures unless useful.

### FIX-A
- mono sine burst, 440 Hz
- 48,000 Hz sample rate
- 250 ms audible duration
- 5 ms fade-in/out

### FIX-B
- mono sine burst, 880 Hz
- same duration/rate

### FIX-C
- mono impulse/short burst used for delay/reverb/tail stop tests

## 2. Score fixtures

### SCORE-FIX-01 — offset overlap
- A start `1000 ms`
- B start `1600 ms`
- expected delta `600 ms`

### SCORE-FIX-02 — simultaneous
- A/B start `1000 ms`

### SCORE-FIX-03 — authored silence
- A start `0 ms`
- B start `2000 ms`
- A finishes by ~250 ms; middle remains silent

### SCORE-FIX-04 — density
- 12 events clustered between 0–3000 ms with overlaps

### SCORE-FIX-05 — dry/processed parity
Same onset data in processed and dry-bypass modes.

## 3. Temporal proof

Use the production scheduler function with an `OfflineAudioContext` or equivalent injected audio context.

Required evidence:
- scheduled event log: `event_id`, requested `start_ms`, resolved context start time;
- rendered audio buffer or extracted onset samples;
- assertion that relative onset matches authored offset within one render quantum plus test measurement tolerance;
- for 48 kHz, default acceptance ceiling: **10 ms relative-onset error** in browser harness; common output latency is not part of this relative timing oracle.

Do not infer temporal PASS from playhead pixels or `setTimeout` logs.

## 4. Source/provenance and byte-integrity fixtures

The shipped source is now `PRIMARY_PDF_WITNESS`; temporary **audio** fixtures remain eSpeak. Source tests operate on a disposable copy/mutation of the primary-witness JSON and restore it after the canary.

Required hash/readiness tests:
- mutate punctuation → source hash changes → dry asset stale;
- corrupt/delete dry WAV bytes while leaving JSON `READY` → dry + processed readiness turn red;
- delete/corrupt processed WAV while dry is intact → processed turns red while dry remains usable;
- alter only `start_ms` → processed variant remains current;
- alter processing value → only affected event variant stale;
- swap model/profile hash after real Piper preparation → affected dry identity becomes stale/re-render-required.

## 5. Required canaries

At least one run of each canary is required before trusting critical green tests.

### CANARY-001 — chain instead of absolute scheduling
Temporarily mutate scheduler so B starts after A ends. `ORACLE-006/007` tests must fail.

### CANARY-002 — stale-source leak
Temporarily suppress stale transition after source text mutation. Source/provenance tests must fail.

### CANARY-003 — playback-rate masquerades as pitch
Mutate pitch implementation to rate scaling. Pitch-duration guard must fail.

### CANARY-004 — incomplete stop
Leave one scheduled/active source registered after Stop. Stop-cleanup test must fail.

### CANARY-005 — page overflow
Introduce an over-wide inspector/timeline child. 1024px object/page overflow test must fail.

A canary that remains green means `HARNESS_FAILURE`; affected PASS results cannot close the risk.

## 6. Evidence naming

Store candidate-bound evidence outside source where practical:

```text
evidence/<candidate_id>/
  env.json
  test-results/
  browser/
  temporal/
  hashes/
  screenshots/
  export-smoke/
```

Every evidence record includes candidate commit/tree identity and command/tool that produced it.
