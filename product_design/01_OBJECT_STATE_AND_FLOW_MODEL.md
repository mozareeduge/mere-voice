# 01 — Object, State and Flow Model

## 1. Actors

### ACT-001 — Artist / rehearsal operator
Goal: construct, hear, compare and document temporal Voice configurations without editing code.

### ACT-002 — Local preparation system
Validates source/profile state, renders immutable dry TTS, creates processed event variants, hashes outputs and reports readiness. It never authors text.

### ACT-003 — Local playback system
Loads prepared audio, schedules enabled events against one audio clock, stops/reset cleanly, exposes run state and produces playback evidence. It never renders TTS mid-run.

## 2. Core objects

### OBJ-001 — VoiceLine
Persistent canonical source unit.

```text
line_id            stable ID: VOICE-001...
text_fa            exact UTF-8 Persian text
order_hint         source order
source_ref         optional page/section reference
text_sha256        exact UTF-8 hash
```

The UI is read-only for `text_fa`. Source changes happen by replacing/editing the local canonical source file and reloading it.

### OBJ-002 — VoiceModelProfile
Replaceable rendering identity.

```text
profile_id
engine_id
engine_version
model_name
model_path
model_sha256
config_sha256
render_parameters
```

One active profile is enough in v0.1; profile switching need not be a UI feature.

### OBJ-003 — DrySpeechAsset
Immutable TTS result for one source/profile/render-input combination.

```text
asset_id
line_id
profile_id
source_text_sha256
wav_path
wav_sha256
sample_rate
channels
duration_ms
rendered_at
status = MISSING | RENDERING | READY | FAILED | STALE
```

A READY asset is never silently overwritten. New inputs produce a new asset revision.

v0.6.1: the render input is the vocalized reading text (`text_fa_vocalized` when present, else `text_fa`) chunked on sentence/clause punctuation with recorded inter-chunk pauses; asset evidence carries `spoken_text_sha256`, `synthesis_pipeline` and `pause_chunks`. Source authority remains `text_fa` (DEC-016, DEC-017).

### OBJ-004 — ProcessingSpec
Named semantic event-processing values.

```text
gain_db          -60 .. +12
pan               -1.0 .. +1.0
tempo_scale        0.5 .. 2.0 (pitch-preserving reading speed; v0.6.1)
pitch_semitones  -12 .. +12
reverb_mix         0.0 .. 1.0
delay_ms           0 .. 2000
delay_feedback     0.0 .. 0.95
attack_ms           0 .. 5000
release_ms          0 .. 5000
```

`DRY` means all transformations neutral/zero. `pitch_semitones` must not be implemented by merely changing playback rate. A future `playback_rate` effect would require its own field/name.

### OBJ-005 — ProcessedEventVariant
A cacheable rendered sound-body for one dry asset + processing spec.

```text
variant_id
asset_id
processing_hash
wav_path
wav_sha256
duration_ms
status = MISSING | PREPARING | READY | FAILED | STALE
```

Changing `start_ms`, enabled state or event identity does **not** stale a variant. Changing any processing value or its dry asset does.

### OBJ-006 — ScoreEvent
One sounding instance.

```json
{
  "event_id": "EV-003",
  "line_id": "VOICE-007",
  "asset_id": "ASSET-VOICE-007-R1",
  "variant_id": "VAR-EV-003-R2",
  "start_ms": 12600,
  "processing": {
    "gain_db": -3.0,
    "pan": 0.0,
    "pitch_semitones": -2.0,
    "reverb_mix": 0.45,
    "delay_ms": 120,
    "delay_feedback": 0.18,
    "attack_ms": 80,
    "release_ms": 600
  },
  "route_id": "STEREO_MAIN",
  "enabled": true
}
```

Rules: duplicate line use is legal; same-onset events are legal; list order never changes onset semantics.

### OBJ-007 — TemporalScore
Persistent research object.

```text
score_id
revision
name
events[]
notes_summary
created_at
modified_at
```

Current-score validity: IDs unique; numeric values in range; enabled event line/asset references valid.

### OBJ-008 — PreparationState
Derived state, never independent authority.

```text
SOURCE_READY
DRY_READY
PROCESSED_READY
READY_PROCESSED
READY_DRY_BYPASS
BLOCKED
```

The UI must state exactly what blocks readiness.

### OBJ-009 — Run
Transient playback instance.

```text
IDLE
  prepare/preload -> READY
  invalid -> BLOCKED
READY
  play -> PLAYING
  mutation -> IDLE
PLAYING
  stop -> STOPPED
  natural end -> COMPLETE
  playback failure -> FAILED
STOPPED | COMPLETE | FAILED
  reset/reprepare -> READY
```

No pause/resume in v0.1.

### OBJ-010 — ResearchNote
Linked to score revision/run.

Required: timestamp/context, source/profile, processing/timing mode, listening setup, perceived result, masking/failure, `KEEP|RETRY|DROP|HOLD`, optional free note.

### OBJ-011 — ExportBundle
A reproducible rehearsal artifact:

```text
stereo WAV (processed or dry-bypass)
score revision JSON
asset/variant hash manifest
run/export metadata
optional note references
```

Export does not mean artistic approval.

## 3. Commands

| ID | Command | Product meaning |
|---|---|---|
| CMD-001 | Reload source | Re-read canonical lines and derive stale state. |
| CMD-002 | Render dry | Render all required MISSING/STALE/FAILED dry assets. |
| CMD-003 | Add event | Add one DRY-default event from selected line. |
| CMD-004 | Duplicate event | Copy line/timing/processing into new stable event ID. |
| CMD-005 | Enable/disable | Preserve event while controlling whether it sounds. |
| CMD-006 | Delete event | Remove from current unsaved score; prior saved revision survives. |
| CMD-007 | Prepare score | Create/update processed variants needed for processed playback. |
| CMD-008 | Audition dry | Play one dry asset alone. |
| CMD-009 | Audition event | Prepare selected variant if stale, then play it alone. |
| CMD-010 | Play full | Schedule all enabled events from score t=0. |
| CMD-011 | Play from selection | Selected onset becomes rehearsal t=0; earlier events are not reconstructed. |
| CMD-012 | Stop/reset | Stop all active sources and reset playhead/run state. |
| CMD-013 | Toggle DRY BYPASS | Keep timing, substitute dry assets for processed variants. |
| CMD-014 | Save revision | Atomically persist a new score revision. |
| CMD-015 | Record note | Append structured evidence for current revision/run. |
| CMD-016 | Export run | Produce stereo WAV + sidecar evidence for current mode/revision. |

## 4. Major flows

### FLOW-001 — First usable fixture run
Open → source present → render dry → add/inspect fixture events → prepare → READY → play full → stop/complete → note.

### FLOW-002 — Build a temporal score
Select line → add event → set `start_ms` numerically → duplicate/add more events → inspect timeline overlap/silence → save revision.

### FLOW-003 — Sonic experiment
Select event → dry audition → change exactly one parameter → variant becomes stale → audition event prepares/plays it → compare → save/note.

### FLOW-004 — Overlap experiment
Create at least two events → assign equal or offset starts → prepare → processed run → dry-bypass run → compare masking/intelligibility → note.

### FLOW-005 — Source correction
Canonical file changes → reload → affected dry assets stale → processed variants stale → processed and dry playback blocked for affected events → rerender → reprepare → rerun.

### FLOW-006 — Failure recovery
Named preparation/playback failure → prior successful files/revisions remain → repair/retry affected item → readiness recomputed → rerun.

### FLOW-007 — Rehearsal handoff
Save revision → export run → bundle includes audible WAV + exact machine-readable state → listen outside workbench without losing provenance.

## 5. Temporal invariants

- One audio clock controls a run.
- `start_ms` is absolute score time.
- Same onset means scheduled same score time, not sequential callbacks.
- No TTS/network request occurs after playback starts.
- UI animation/playhead never drives sound scheduling.
- A full rerun of one saved revision resolves the same source/variant hashes and onset data.
- `PLAY FROM SELECTION` preserves future deltas but does not reconstruct already-started events.
