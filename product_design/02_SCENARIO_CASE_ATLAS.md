# 02 — Scenario / Case Atlas

Each `SCN-*` is a materially distinct consequence class.

## A. Source and dry rendering

### SCN-001 — First open with fixture/canonical lines but no audio
Full playback disabled; exact count needing render visible; `RENDER DRY` is the repair action.

### SCN-002 — Successful Persian dry render
Creates immutable WAV + asset/hash/duration metadata; dry audition becomes available.

### SCN-003 — One line render fails
Successful assets survive; failing line is named and retryable; readiness remains truthful.

### SCN-004 — Canonical source changes
Only dependent current assets become STALE; old files remain provenance; affected run modes block until repair.

### SCN-005 — Model/profile changes
Affected dry assets/variants stale; score event/timing structure remains intact.

## B. Event lifecycle

### SCN-006 — Add event from line
New stable event ID, DRY processing, start 0 unless explicitly supplied, enabled true.

### SCN-007 — Duplicate event
New event ID; same line/timing/processing; changing duplicate later cannot mutate original.

### SCN-008 — Disable event
Event remains visible/saved but is excluded from preparation/playback/export sound.

### SCN-009 — Delete event
Removed from current score after confirmation if current edits would be lost; prior saved revision remains recoverable.

### SCN-010 — Invalid parameter/onset
Value rejected inline; last valid value remains; no silent clamp unless the UI explicitly states the clamp rule.

## C. Processing and audition

### SCN-011 — Dry audition
One dry asset only; no score timing or processing.

### SCN-012 — Processed event audition
Current variant used; stale/missing variant is prepared first with visible preparation state; score onset ignored for solo audition.

### SCN-013 — One-parameter sweep
Changing one parameter stales only the selected event variant; unrelated values/assets remain unchanged.

### SCN-014 — Pitch semantic guard
`pitch_semitones` changes pitch without becoming an accidental duration/speed control. Any rate-coupled effect must have a different name.

## D. Temporal score

### SCN-015 — Two-event overlap
B begins at its authored absolute onset while A is sounding; neither waits for the other.

### SCN-016 — Exact simultaneous onset
Equal `start_ms` is valid and scheduled against the same audio-clock origin.

### SCN-017 — Authored silence
Empty interval remains silent; system never compacts/chains the timeline.

### SCN-018 — Dense polyphony
At least 12 clustered/overlapping events remain operable; timeline owns horizontal scroll.

### SCN-019 — Same revision rerun
Same source/variant hashes and onset data resolve again; no random rendering enters playback.

### SCN-020 — Play from selection
Selected onset becomes rehearsal zero; future deltas preserved; prior events/tails not reconstructed; visible `REHEARSAL START` state.

## E. Preparation, run and recovery

### SCN-021 — Processed run with stale variant
Processed `PLAY FULL` disabled; affected event named; `PREPARE SCORE` repairs only stale/missing variants.

### SCN-022 — Dry-bypass run with stale processed variants
Allowed if every required dry asset is current. Timing identical; processing substituted with dry sound.

### SCN-023 — Stop during overlap/effect tails
All active sources stop; no orphan audio; playhead resets; next run starts cleanly.

### SCN-024 — Audio output/runtime failure
Run becomes FAILED; score/revisions/notes survive; explicit reinitialize/retry required.

### SCN-025 — Offline after preparation
Disconnect network after READY; audition, processed run, dry-bypass run, save note/revision and export still work.

## F. Persistence and evidence

### SCN-026 — Atomic score save
New revision written completely or not at all; prior saved revision survives failed write; unsaved state remains visible.

### SCN-027 — Research note
Note binds to exact score revision and listening mode; technical success is never mislabeled artistic approval.

### SCN-028 — Export processed run
Export is blocked while the score is dirty. From a saved current revision it produces audible stereo WAV and sidecar metadata that names revision, mode, source/variant hashes and generated-at time.

### SCN-029 — Export dry-bypass run
Same score timing; dry source identity in sidecar; processing not falsely represented as applied.

## G. Experience/accessibility

### SCN-030 — Compact desktop
At 1024×768 transport remains reachable; timeline owns horizontal overflow; no page-level horizontal scroll.

### SCN-031 — Keyboard-only operation
Core commands and selected-event editing are reachable in logical order with visible focus; Space transport shortcut never fires while typing in a field.

### SCN-032 — Causal disabled state
Every disabled primary action exposes a nearby reason/repair route; no generic error when affected line/event is known.

## Cross-factor guards

| ID | Combination | Required consequence |
|---|---|---|
| SCN-X-01 | stale dry × processed run | blocked; rerender then reprepare |
| SCN-X-02 | stale variant × dry bypass | dry run allowed if dry assets current |
| SCN-X-03 | overlap × stop | all active sources stop |
| SCN-X-04 | overlap × dry bypass | onset relations unchanged |
| SCN-X-05 | dense score × 1024px | timeline internal scroll only |
| SCN-X-06 | source change × saved revision | previous revision still references old immutable asset |
| SCN-X-07 | offline × READY | complete rehearsal workflow continues |
| SCN-X-08 | failed save × current edits | prior revision intact; current edits not falsely reported saved |

## Historical defect guards

### HIST-VOICE-001 — live TTS contaminates authored timing
Guard: HZN-002 + SCN-025.

### HIST-VOICE-002 — pitch control secretly changes duration
Guard: SCN-014.

### HIST-VOICE-003 — archived Piper upstream treated as current
Guard: technical ledger + frozen dependency provenance.

### HIST-VOICE-004 — licensing reduced to “ticketed = forbidden”
Guard: factual dependency/license ledger; later distribution review if packaging changes.

### HIST-VOICE-005 — UI timeline becomes the timing engine
Guard: temporal scheduling oracle uses audio-clock evidence, never playhead animation.

### HIST-VOICE-006 — lightweight executor invents event authoring behavior
Guard: SCN-006–010 + explicit no-drag v0.1 rule.
