# QA Oracle Register

**authority:** `VOICE-PROTOTYPE-PD-2026-09-17-R2`  
**candidate:** `NIRAVANA-VOICE-NEARFINAL-0.6`  
**status:** executable local proofs partially executed; target Windows/Piper/audio and human listening remain external gates

| Oracle | Basis | Product refs | Risk | Statement / divergence condition |
|---|---|---|---|---|
| ORACLE-001 | AUTH | HZN-001, DEC-003 | high | Frozen primary-witness `text_fa` is displayed read-only and hash-bound after the declared source-closure normalization step; UI/runtime cannot silently rewrite/translate it. |
| ORACLE-002 | AUTH | HZN-002, SCN-001–005 | high | TTS happens only in preparation. Divergence: synthesis/network call after run begins. |
| ORACLE-003 | AUTH | OBJ-003, SCN-002–005 | high | Dry assets immutable and hash-bound to source/profile. Divergence: overwrite or stale asset shown current. |
| ORACLE-004 | AUTH | HZN-003, OBJ-005 | high | Processed variant is separate/cacheable and traceable to dry asset + processing hash. |
| ORACLE-005 | AUTH | DEC-007, SCN-006–010 | normal | Event add/duplicate/enable/delete/numeric edit semantics match authority and IDs remain independent. |
| ORACLE-006 | AUTH | HZN-004, DEC-006 | critical | Event onset derives from absolute `start_ms`; never previous-clip completion. |
| ORACLE-007 | AUTH | HZN-005, SCN-015–018 | critical | Equal/overlapping onsets produce real polyphony; silence remains empty time. |
| ORACLE-008 | AUTH | SCN-014, HIST-VOICE-002 | high | `pitch_semitones` is not implemented as generic playback-rate change. |
| ORACLE-009 | AUTH | HZN-008, SCN-021–022 | high | Readiness differs by processed vs dry-bypass mode and names exact blockers. |
| ORACLE-010 | AUTH | HZN-007, DEC-009 | high | DRY BYPASS preserves event timing and line identity; only processed sound-body changes. |
| ORACLE-011 | AUTH | SCN-019 | high | One saved revision resolves same source/variant hashes and onset data on rerun. |
| ORACLE-012 | AUTH | SCN-020 | normal | Play-from-selection preserves future deltas and does not reconstruct earlier events/tails. |
| ORACLE-013 | AUTH | SCN-023 | high | Stop/reset ends all active sources/tails and returns a clean reproducible start. |
| ORACLE-014 | AUTH | SCN-024 | high | Runtime/audio failure preserves score/revisions/notes and requires explicit recovery. |
| ORACLE-015 | AUTH | HZN-009, SCN-025 | high | Once ready, core rehearsal workflow runs with network unavailable. |
| ORACLE-016 | AUTH | SCN-026 | high | Revision save is atomic; failure cannot corrupt prior saved revision or claim success. |
| ORACLE-017 | AUTH | SCN-027 | normal | Note binds exact revision/run/mode and uses KEEP/RETRY/DROP/HOLD without implying approval. |
| ORACLE-018 | AUTH | SCN-028–029 | high | Export WAV sidecar truthfully names revision, mode and hashes; dry export cannot claim processing. |
| ORACLE-019 | AUTH | HZN-010, DEC-008 | normal | Timeline visualizes time but v0.1 timing editing is numeric; no hidden drag semantics required. |
| ORACLE-020 | AUTH | SCN-030 | normal | At 1024×768 no page horizontal overflow; timeline owns its horizontal scroll. |
| ORACLE-021 | AUTH | SCN-031 | normal | Core path keyboard reachable; Space shortcut inert inside editable controls; focus visible/restored. |
| ORACLE-022 | AUTH | SCN-032, COPY-* | normal | Disabled/error state is causal and object-specific when cause is known. |
| ORACLE-023 | DERIVED | HZN-011, OBJ-011 | high | Evidence/export remains candidate-bound; no `final/approved/production` claim from technical success. |
| ORACLE-024 | AUTH | HZN-012, DEC-011 | low | v0.1 uses default stereo only; no accidental multi-speaker/remote-routing product scope. |
| ORACLE-025 | STANDARD | DEC-017/018 | critical | Audio scheduling uses audio-context time; UI timers/playhead do not trigger event sound. |
| ORACLE-026 | HEURISTIC | dossier R-VOICE tests | normal | Processing/overlap remains intelligible enough to compare artistically; masking is recorded rather than hidden. Human/rehearsal judgment only. |
| ORACLE-027 | HEURISTIC | GATE-HUMAN-VOICE-01 | normal | Mana/Piper Persian pronunciation/intelligibility is usable for the experiment. Human listening only; poor result is a model/material finding, not automatically an app defect. |

| ORACLE-028 | DERIVED | HZN-008, OBJ-003/005 | critical | READY requires the referenced WAV to exist and its actual SHA-256 to match metadata. Missing/corrupt bytes must block the affected readiness mode even when JSON metadata says READY. |

## Oracle revision rule

Once a candidate test begins, the cited oracle revision is immutable. A genuine authority change creates a new oracle revision and the affected proofs rerun; expected behavior is never edited merely to turn a failure green.
