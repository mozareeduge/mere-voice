# Agentic Execution Intake
## Niravana × Mozare — Voice Temporal Prototype v0.2

**execution_intake_revision:** `VOICE-PROTOTYPE-EXEC-2026-09-17-R1`  
**product_authority:** `VOICE-PROTOTYPE-PD-2026-09-17-R2`  
**qa_authority:** `VOICE-PROTOTYPE-QA-2026-09-17-R1`  
**status:** `READY_FOR_CODE_EXECUTION`

---

# A. START HERE

## Objective

Create a runnable local Windows rehearsal workbench that makes this path real:

`fixed Persian Voice source → local dry TTS → prepared event variants → explicit temporal score → overlapping stereo run → revision/note/export`

The implementation must be useful with fixture text immediately and accept the confirmed Niravana Voice line file later without architecture changes.

## Authorized terminal states

If canonical Voice text is present and human Persian smoke is recorded:

`CANDIDATE_READY_FOR_REHEARSAL_REVIEW`

If canonical Voice text is not present:

`ENGINEERING_READY_OWNER_CONTENT_REQUIRED`

Do not claim production/show readiness.

## Greenfield baseline

No repository/candidate is assumed. If the active workspace is empty, initialize Git early and create the minimal vertical slice first. If a repo already exists, freeze its HEAD/status before editing and reconcile only the relevant differences.

---

# B. AUTHORITY / CONFLICT RULE

Precedence:

1. explicit current owner instruction;
2. `product_design/*`;
3. `qa/*`;
4. applicable external API/platform contract;
5. current executable/repository truth as baseline;
6. evidence;
7. claims/proposals/history.

Do not redesign the product because a library makes another behavior easier.

If repo/runtime evidence makes an accepted requirement infeasible, record:

```text
AUTHORITY_CONTRADICTION
requirement
conflicting evidence
smallest decision required
safe work that can continue
```

Continue independent safe tasks.

---

# C. WORK MODE

`GREENFIELD + FEATURE + ARTISTIC_SOFTWARE + RESEARCH_INSTRUMENT + LOCAL_OFFLINE_APP`

Launch topology: `NO_DEPLOYMENT`.

No cloud, database, auth, secret, remote API, multi-user service, installer, mobile app, or stage network is required.

---

# D. CLOSED TECHNICAL ARCHITECTURE

## Runtime

- Python **3.11 x64**.
- Flask local service bound to `127.0.0.1`, not `0.0.0.0`.
- Vanilla HTML/CSS/JavaScript frontend; no React/Vue/Svelte/Node build.
- Browser target for acceptance: current Chromium/Chrome on Windows 10/11.
- Web Audio API for event scheduling/playback.
- Piper Python API for dry Persian TTS preparation.
- Pedalboard for offline processed event variants.
- Local JSON/WAV filesystem persistence only.

## Dependency baseline

Pin through a requirements/lock mechanism after confirming installability on the execution machine:

```text
piper-tts == 1.4.2              # current selected upstream release at planning time
pedalboard == 0.9.25            # selected planning-time version
Flask >=3,<4
numpy >=1.26,<3
pytest >=8,<9
playwright >=1,<2               # dev/QA only
```

Do not silently upgrade major versions during the same candidate. If exact current package resolution differs, record the resolved version and reason; product behavior/oracles remain unchanged.

## Model

First bench model:

```text
MahtaFetrat/Mana-Persian-Piper
fa_IR-mana-medium.onnx
planning-time SHA256: e390c0e74ba71fd97c49ba662ee0c6e1724b462ba2d4561698af4f564840f126
sample rate in config: 22050
```

Model binaries are local runtime material, not committed source. Verify hash after acquisition and write model metadata into project evidence/config.

## Why this architecture

It keeps the v0.1 system in two runtime surfaces only: Python preparation/persistence + browser workbench/playback. It satisfies deterministic overlap without introducing SuperCollider/OSC/second audio-runtime complexity. SuperCollider stays deferred for later live DSP/multi-output work.

---

# E. SOURCE-OF-TRUTH LAYOUT

Create approximately this shape; rename internals only when there is a concrete engineering reason.

```text
/
  AGENTS.md
  CLAUDE.md
  README.md
  requirements.txt
  .gitignore
  app.py
  scripts/
    setup.ps1
    run.ps1
    fetch_model.py
    generate_fixtures.py
  voice_proto/
    domain.py
    validation.py
    storage.py
    tts.py
    processing.py
    manifest.py
    export.py
  web/
    index.html
    app.js
    audio-scheduler.js
    styles.css
  data/
    source/
      voice_lines.fixture.json
      voice_lines.json              # owner content when supplied; may be ignored until present
    config/
      model_profile.json
    models/                         # gitignored binary models
    assets/
      dry/
      processed/
    scores/
      revisions/
    notes/
    exports/
  tests/
    unit/
    integration/
    browser/
    fixtures/
  docs/intake/                      # copy this handoff packet here if not already in repo
```

Semantic source files are Python/JS/HTML/CSS/JSON. Generated WAV/export/evidence files are not hand-edited.

---

# F. DATA CONTRACTS

## Canonical source file

`data/source/voice_lines.json`

```json
{
  "source_id": "NIRAVANA-VOICE-V1",
  "source_status": "CANONICAL",
  "lines": [
    {
      "line_id": "VOICE-001",
      "text_fa": "...",
      "order_hint": 1,
      "source_ref": "page/section if known"
    }
  ]
}
```

Fixture file uses `source_status: "FIXTURE"` and IDs `FIXTURE-VOICE-*`. UI visibly shows fixture warning.

Never mutate `text_fa` in the workbench.

## Model profile

```json
{
  "profile_id": "PIPER-MANA-01",
  "engine_id": "piper",
  "engine_version": "1.4.2",
  "model_name": "fa_IR-mana-medium.onnx",
  "model_sha256": "...",
  "config_sha256": "...",
  "render_parameters": {
    "length_scale": 1.0,
    "noise_scale": 0.667,
    "noise_w_scale": 0.8
  }
}
```

Record actual resolved values from the installed/model config; do not invent unavailable fields.

## Score revision

Use schema versioning from the first commit:

```json
{
  "schema_version": 1,
  "score_id": "VOICE-SCORE-001",
  "revision": 3,
  "name": "Voice temporal test",
  "source_id": "NIRAVANA-VOICE-V1",
  "events": [],
  "created_at": "ISO-8601",
  "modified_at": "ISO-8601"
}
```

Event shape follows OBJ-006. Persist stable IDs, integers for milliseconds and explicit processing values.

## Asset metadata

Metadata may live in sidecar JSON or a compact asset index. It must preserve `asset_id/variant_id`, source/profile/processing hashes, WAV hash, duration/sample rate/channels and status.

---

# G. STORAGE / ATOMICITY

- JSON writes use temp file in same filesystem + flush/close + `os.replace`.
- Never overwrite a READY dry asset path with different bytes.
- Score save creates a new revision file; prior revisions remain.
- Current unsaved UI state is not called saved.
- Export requires clean/saved current revision.
- `data/models`, rendered assets and exports are gitignored; fixture source/config/tests are committed.

No SQLite/database in v0.1.

---

# H. LOCAL API CONTRACT

Exact path names may vary slightly, but keep responsibilities separated.

### `GET /api/project`
Returns source status, lines, dry readiness, latest saved score, model profile summary and fixture/canonical warning.

### `POST /api/source/reload`
Rehashes source; computes affected stale dry assets/variants; does not render automatically.

### `POST /api/render/dry`
Body optionally names line IDs; otherwise required stale/missing/failed lines. Returns per-line result without deleting prior successful files.

### `POST /api/events/prepare`
Body contains one complete event + current dry asset identity. Creates/reuses variant by dry hash + processing hash.

### `POST /api/score/prepare`
Body contains current unsaved score. Prepares only enabled stale/missing variants. Returns updated event variant refs/readiness; does not save a score revision.

### `POST /api/score/save`
Validates current score, writes next immutable revision atomically and returns revision identity.

### `POST /api/notes`
Appends structured note bound to saved revision/run mode.

### `POST /api/export`
Requires saved clean revision. The browser renders the selected saved run through the **same scheduler** using `OfflineAudioContext`, encodes the rendered buffer as stereo WAV, then posts the WAV + sidecar metadata to this endpoint for atomic local storage. The server verifies revision/mode/hash fields before writing.

### `POST /api/run-manifest`
Body: saved or current validated score payload + mode (`processed|dry`). Returns enabled events with `event_id`, absolute `start_ms`, media URL, duration/hash and score identity. It makes **no audio playback call** itself.

### media route
Serve only known generated WAVs under the app's data roots. Prevent path traversal; do not expose arbitrary filesystem paths.

---

# I. AUDIO PREPARATION CONTRACT

## Dry TTS

- Use `PiperVoice.load` once per render job/process where practical.
- `synthesize_wav` writes a new temp WAV; hash it; move into immutable final asset path only after successful completion.
- A failed line leaves existing successful assets unchanged.
- TTS preparation may require network only for initial model acquisition; synthesis itself is local.

## Processing variant

Input: dry WAV + ProcessingSpec.

Implement semantic stages clearly rather than as an opaque chain:

1. load audio;
2. pitch shift when non-zero using true pitch-shift processor;
3. delay/reverb as specified;
4. attack/release envelope;
5. gain;
6. stereo pan;
7. write processed WAV;
8. hash + metadata.

Neutral parameters should preserve a dry-equivalent result except for unavoidable encoding/container differences. Do not silently normalize loudness.

If an effect needs tail room, pad/retain effect tail intentionally and document the rule in code/tests. Do not truncate tails accidentally.

A processing variant key derives from at least:

`dry_wav_sha256 + canonicalized_processing_spec + processor_version`

Changing only `start_ms` must reuse the same variant.

---

# J. PLAYBACK / TEMPORAL CONTRACT

Create one scheduler module, `web/audio-scheduler.js`, with minimal dependence on the DOM.

Conceptual API:

```text
scheduleScore(audioContext, runManifest, baseTime, mode)
stopAll()
```

Rules:

- preload/decode every required buffer before entering READY;
- choose a small fixed lead time after user presses Play (e.g. 100 ms) and define `baseTime = audioContext.currentTime + lead`;
- each event source starts at `baseTime + start_ms / 1000`;
- create all schedule calls from score data before/at run start, not chained from `ended` events;
- same-onset events receive the same `when` value;
- UI playhead uses audio context time but never triggers audio;
- track every active/scheduled `AudioBufferSourceNode` so Stop can call `stop()` safely and clear references;
- no pause/resume semantics;
- Play-from-selection transforms only time origin: events with starts before selection are omitted; future event delta = `start_ms - selected_start_ms`;
- on browser/audio context failure, stop/clear and surface FAILED.

The scheduling function must be reusable with `OfflineAudioContext` for QA.
The same path is also used for export rendering so live playback, QA rendering and exported timing do not become three independent timing implementations.

---

# K. UI/UX CONTRACT

Implement `product_design/03_DESIGN_UIUX_BLUEPRINTS.md` and `04_COPY_DECK.md` literally where consequential.

Important anti-invention rules for lighter models:

- source text read-only;
- no drag/drop timeline editing required;
- no waveform editor;
- no mobile workflow;
- no DAW-style mixer/channel-strip expansion;
- no theme switch;
- no auto-save claim;
- no “AI” features;
- no final-performance imagery/ECG integration.

Minimum event operations: Add, Duplicate, Enable/Disable, Delete, numeric `start_ms`, processing inputs, Dry audition, Event audition.

---

# L. QA CONTRACT

The executor owns implementation **and** proof, but product meaning/oracles come from `qa/*`.

Before code, read:
- `qa/QA_STATE.yaml`
- `qa/QA_ORACLE_REGISTER.md`
- `qa/AGENT_QA_CONTRACT.md`
- `qa/FIXTURE_CANARY_AND_EVIDENCE_SPEC.md`

Do not declare runtime PASS from this pre-code package. Create candidate-bound evidence.

Core chain:

`SCN-* → ORACLE-* → test/proof → TASK-* → GATE-*`

---

# M. TEST ARCHITECTURE

## Python unit/integration

Cover:
- hashes/staleness;
- schema/range validation;
- asset/variant identity;
- atomic revision writes;
- processing-cache semantics;
- export sidecar truth;
- path traversal/media allowlist.

## Browser/Playwright

Cover actual user paths:
- first-open fixture state;
- render/prepare state transitions via API fixtures/mocks where necessary;
- add/duplicate/edit/disable/delete;
- processed vs dry readiness;
- Play/Stop state;
- 1440×900 and 1024×768 overflow/visibility;
- keyboard/focus.

## Temporal browser harness

Use deterministic tone fixtures and production scheduler against `OfflineAudioContext`.

Do not use `setTimeout` precision or playhead screenshots as temporal proof.

## Real Windows smoke

One real app launch, one real Piper render, one two-event overlap run through default audio, one stop, one saved revision, one export. Record environment/version evidence.

---

# N. LAUNCH MANIFEST

## Source control

Initialize Git if absent. Primary worktree single writer. Commit coherent verified phases.

## Build/runtime

No compiled frontend build. Local Python environment + static files.

## Environments

`local` only.

## Hosting/DNS/TLS

`NOT_APPLICABLE`.

## Database/auth/secrets

`NOT_APPLICABLE`.

## External services

None during operation. Model acquisition is setup-only.

## Network

App binds localhost. Prepared rehearsal run must succeed with network disabled.

## Observability

Local structured logs are sufficient. Do not log full arbitrary external paths unnecessarily. Log event/preparation errors with stable IDs.

## Rollback

Git revert/reset to previous verified commit plus immutable score revisions/assets. Do not destroy owner content.

---

# O. PREFLIGHT

If Git repo exists:

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git log --oneline -12
git diff --stat
```

If uncommitted work exists, preserve it; never reset/clean destructively.

Then:

1. verify Python 3.11 availability;
2. inspect only current project/intake files;
3. initialize execution state from `execution/STATE_TEMPLATE.json` under `.git/voice-prototype-execution/state.json`;
4. start TASK-P00.

---

# P. TASK DAG

Canonical machine-readable order is `execution/TASK_DAG.yaml`.

High-level phases:

- **TASK-P00** baseline/repo/runtime scaffold.
- **TASK-P01** domain schemas, validation, fixtures, hashes.
- **TASK-P02** Piper dry renderer + source stale logic.
- **TASK-P03** offline processed-variant pipeline.
- **TASK-P04** Web Audio scheduler + deterministic temporal tests.
- **TASK-P05** workbench UI + event lifecycle/readiness.
- **TASK-P06** revisions/notes/export + offline workflow.
- **TASK-P07** browser/accessibility/density + canaries.
- **TASK-P08** real Windows/audio/model smoke.
- **TASK-P09** final freeze/evidence/docs.

Do not build all layers first. Each phase should end in a runnable/provable increment.

---

# Q. PER-TASK EXECUTION LOOP

For every task:

1. load only the task's referenced authority/oracles;
2. inspect smallest relevant code area;
3. make the smallest coherent implementation;
4. run targeted proof;
5. run adjacent regression;
6. update execution state/evidence;
7. commit only after task/batch gate passes.

If a new defect clearly violates accepted authority, fix it and add a regression proof. If it reveals a real authority trade-off, stop only that branch and report the precise contradiction.

Never weaken a test threshold to get green.

---

# R. GATES

### GATE-TARGETED
Task-specific unit/integration/browser proof.

### GATE-AUDIO-TEMPORAL
OfflineAudioContext fixtures + pitch guard + stop cleanup.

### GATE-BROWSER
Critical user journeys, 1440×900 + 1024×768, keyboard/focus.

### GATE-OFFLINE
Disable network after preparation; run/audition/save/export.

### GATE-CANARY
Run specified mutations on disposable copy/branch; relevant tests must fail.

### GATE-FULL
All automated tests on unchanged tree; no unexpected skips.

### GATE-WINDOWS-SMOKE
Actual Windows app/model/audio/export smoke.

### GATE-HUMAN-PERSIAN-SMOKE
Only when canonical text supplied; human listening result recorded separately from automated QA.

---

# S. CONCURRENCY SAFETY

Primary worktree: one writer.

Parallel agents may do read-only research/audit or use isolated worktrees. Do not let background workers edit/reset/clean the main tree.

Before parallel mutation, preserve status/diff in `.git/voice-prototype-execution/logs/`.

---

# T. SCOPE-FIDELITY AUDIT

Before final freeze, map every changed tracked file to TASK ID and intended effect. Any unexplained tracked file is a finding.

Ask:
- did source text become editable/rewritten?
- did live TTS sneak into playback?
- did clip chaining replace absolute time?
- did pitch become rate?
- did dry bypass change timing?
- did mobile/cloud/multi-speaker scope appear?
- did a visual playhead become timing authority?
- was a requirement “satisfied” by hiding/removing functionality?

---

# U. FINAL FREEZE

1. all authorized tasks complete or explicit owner-content gate remains;
2. no unexplained tracked changes;
3. GATE-TARGETED/AUDIO-TEMPORAL/BROWSER/OFFLINE/CANARY/FULL green;
4. GATE-WINDOWS-SMOKE disposition recorded;
5. exact commit/tree + dependency/model/source hashes recorded;
6. candidate evidence bound to that exact tree;
7. README run/setup commands verified from a clean-ish environment;
8. fixture warning remains if canonical text absent;
9. final response uses an honest terminal state.

Do not edit tracked source after the evidence/freeze without creating a new candidate identity.

---

# V. FINAL RESPONSE FORMAT FOR EXECUTOR

```text
TERMINAL STATE
CANDIDATE ID / HEAD
WHAT NOW WORKS
OWNER GATES (if any)
GATES EXECUTED + RESULT
EVIDENCE PATHS
KNOWN QUALITY RISKS / PROOF GAPS
RUN COMMAND
```

No generic “done” claim.

---

# W. ONE-LINE DIRECTIVE

Execute this intake against the current workspace through its authorized terminal state; treat product/design authority as meaning, QA authority as proof obligation, and the repository as implementation baseline, without reopening closed decisions unless new evidence creates a documented authority contradiction.
