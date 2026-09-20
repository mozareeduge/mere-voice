# Agent QA Contract

**QA state:** candidate-bound partial QA; see `QA_STATE.yaml`. The prebuilt candidate has executed unit/integration/API, export, Chromium temporal and responsive/geometry evidence. Target-machine Piper/Windows/audio/human pronunciation proof remains.  
**Target after remaining configuration:** `CANDIDATE_READY_FOR_REHEARSAL_REVIEW`. Source content is already present; only target-environment/human proof remains.

## 1. Candidate freeze

Before QA, record:

```text
candidate_id
branch
HEAD
working_tree_clean? yes/no
python_version
browser_version
installed dependency versions
active model filename + SHA-256
primary-witness source SHA-256
```

Do not mix evidence across candidates.

## 2. Critical proof obligations

### QA-CRIT-01 — source → dry asset provenance
**Oracles:** ORACLE-001–004  
**Path:** load primary-witness source → render dry → inspect metadata + actual WAV hash → mutate source punctuation → confirm stale → corrupt/delete disposable WAV bytes while metadata remains READY → confirm readiness turns red → restore/rerender.  
**Positive proof:** source hash, WAV existence and actual WAV SHA agree with metadata; immutable prior asset remains traceable.  
**Negative proof:** source-staleness canary plus byte-corruption/missing-file canaries (ORACLE-028).  
**Evidence:** JSON metadata, file hashes, targeted test output.

### QA-CRIT-02 — temporal scheduling and polyphony
**Oracles:** ORACLE-006, 007, 025  
**Path:** SCORE-FIX-01/02/03 using production scheduler against OfflineAudioContext.  
**Positive proof:** onset samples/deltas; overlap exists; silence remains silence.  
**Negative proof:** CANARY-001.  
**Evidence:** rendered-buffer analysis + scheduler event log. UI playhead is supplementary only.

### QA-CRIT-03 — pitch semantic integrity
**Oracle:** ORACLE-008  
**Path:** process known tone/voice at non-zero `pitch_semitones`. Compare duration and spectral/frequency evidence to control.  
**Positive proof:** pitch changes while duration stays within processor-expected tolerance; no generic playback-rate implementation.  
**Negative proof:** CANARY-003.

### QA-CRIT-04 — readiness and offline run
**Oracles:** ORACLE-009, 010, 015  
**Path:** stale one variant → processed mode blocked; dry bypass allowed; prepare → processed ready; then disable network and rerun/audition/save/export.  
**Evidence:** browser state + network-denied run + produced files.

### QA-CRIT-05 — stop/reset cleanup
**Oracle:** ORACLE-013  
**Path:** overlapping/tail fixture → start → Stop/reset → verify all active source handles stopped/cleared and next run clean.  
**Negative proof:** CANARY-004.

### QA-CRIT-06 — revision/export atomic truth
**Oracles:** ORACLE-016–018, 023  
**Path:** save revision → force write failure on disposable copy → verify previous revision intact and UI still dirty → successful export → compare sidecar hashes/mode.  
**Evidence:** before/after hashes and exported WAV/JSON.

## 3. Required normal proof set

- Event add/duplicate/disable/delete independence: ORACLE-005.
- Play-from-selection semantics: ORACLE-012.
- Runtime failure preserves research data: ORACLE-014.
- 1024×768 + dense score: ORACLE-020 with CANARY-005.
- Keyboard/focus path: ORACLE-021.
- Causal copy/disabled reasons: ORACLE-022.
- Stereo-only boundary: ORACLE-024.

## 4. Human/artistic evidence

Do not convert these into automated release defects:

### HUMAN-01 — canonical Persian pronunciation
Listen to representative primary-witness lines after Mana/Piper rendering on the target machine. Record intelligibility, mispronunciation, unwanted prosody and whether render-input adjustment/model change is needed. Basis: ORACLE-027 HEURISTIC.

### HUMAN-02 — masking/polyphony relation
At rehearsal volume compare sequential, simultaneous and offset overlaps, dry first then processed. Record whether language relation is exposed or destroyed. Basis: ORACLE-026 HEURISTIC and dossier R-VOICE-03.

Technical QA may pass while either human test says the chosen sound is artistically poor. That is an experimental finding, not hidden failure.

## 5. Browser/UI proof

Use a real browser automation path where available. Required acceptance viewports:
- 1440×900
- 1024×768

Prove:
- no page horizontal overflow;
- timeline internal scrolling;
- transport reachable;
- state changes visible through actual controls;
- source text RTL + timing LTR remain legible;
- keyboard path and focus restoration.

## 6. Test-system challenge

Two canaries (temporal onset + page overflow) were already executed here and turned red as required. Run the remaining canaries from `FIXTURE_CANARY_AND_EVIDENCE_SPEC.md` on a disposable branch/copy, plus rerun the existing ones after any scheduler/layout repair. A canary must turn the relevant test red. Restore clean candidate before final full gate.

## 7. Gate sequence

```text
GATE-TARGETED
  unit/domain + changed module tests

GATE-AUDIO-TEMPORAL
  deterministic fixture scheduler/processing proofs

GATE-BROWSER
  critical workbench journeys + viewport/focus

GATE-OFFLINE
  network-denied prepared-run proof

GATE-CANARY
  test harness mutation sensitivity

GATE-FULL
  entire automated suite on unchanged tree

GATE-WINDOWS-SMOKE
  actual Windows launch + one dry render + one overlap run + export
```

Primary-witness text is now included. Run `GATE-HUMAN-PERSIAN-SMOKE` after real Mana/Piper rendering before rehearsal review.

## 8. Finding classification

Use only:

`PRODUCT_DEFECT | QUALITY_RISK | PROOF_GAP | STALE_TEST | STALE_DOCUMENTATION | HARNESS_FAILURE | INFRASTRUCTURE_TEST_FAILURE | ORACLE_UNRESOLVED`

A fix claim never closes a defect. Freeze the new candidate and rerun the unchanged oracle first.

## 9. Completion rule

QA may declare `CANDIDATE_READY_FOR_REHEARSAL_REVIEW` only when:
- critical AUTH/DERIVED/STANDARD oracles have sufficient candidate-bound evidence;
- canaries demonstrate the critical tests can fail;
- no open high-risk product defect remains;
- proof gaps are limited to explicit human/owner gates;
- exact candidate identity and full-gate command/results are recorded.

Source content is no longer an engineering gate. Without target-machine Mana/Piper + Windows/audio smoke, the maximum terminal state is `READY_FOR_TARGET_PIPER_AND_WINDOWS_AUDIO_VERIFICATION`.
