# Niravana Voice Temporal Workbench — near-final v0.6

A local/offline rehearsal instrument for composing fixed Persian **Voice** text in explicit time: prepare speech assets, place independent events on an absolute timeline, overlap them, process each event, compare dry/processed runs, record research notes, and export reproducible stereo evidence.

## Fast path

```text
RUN_WORKBENCH.bat       run the supplied 17-line / 17-event candidate
VERIFY_LOCAL.bat        verify runnable local state
FINAL_ACCEPTANCE.bat    package/compiler acceptance with available local QA
VERIFY_DEVELOPER.bat    strict acceptance: pytest + Node + Chromium required
FINALIZE_REAL_VOICE.bat target setup + Mana/Piper render + processing + release evidence
```

The ZIP ships with explicitly labelled eSpeak Persian fixture WAVs so the complete workbench runs immediately. The authored source is not a fixture: `data/source/voice_lines.primary_witness.json` contains 17 ordered Voice units reconstructed from the primary five-page play witness.

## Product architecture

```text
primary-witness Voice source
        ↓
immutable dry speech asset + byte hash
        ↓
processed event variant + processor provenance
        ↓
absolute-ms temporal score
        ↓
Web Audio single-clock scheduler
        ↓
default stereo/headphones
        ↓
revision + research note + WAV/JSON evidence
```

No cloud, account, database, React runtime, live TTS during playback, generated text, or final stage-speaker topology is required.

## v0.6 product corrections

Compiler-style review against the closed authority found and fixed behavior that v0.5 QA had not challenged:

- invalid onset/processing values are rejected inline; the previous valid value remains and no invalid score write is queued;
- Add Event now uses `start_ms = 0`, DRY/default processing, enabled=true, and a new stable event ID;
- Duplicate Event preserves source line, exact start time and processing before later independent edits;
- deleting while the current score is dirty requires confirmation and does not erase the prior saved revision.

The existing v0.5 race hardening remains: processing mutations/new unprepared events synchronously invalidate processed readiness, and Prepare/Audition/Save/Export flush the newest score before server-dependent work.

## Compiler-shaped validation layer

`chatgpt_executable_handoff_v2.0` added value where v0.5 was implicit:

- `voice_proto/version.py` is the single runtime candidate/version authority;
- `quality/ARTIFACT_CATALOG.json` compiles to fingerprinted `quality/ARTIFACT_REGISTRY.json`;
- `quality/SCENARIO_TRACEABILITY.json` classifies all 32 scenarios + 8 cross-factor guards without equating implementation with proof;
- `scripts/final_acceptance.py` checks authority closure, identity consistency, registry integrity, traceability, executable QA and local release state;
- downstream agents remain thin executors: run target gates and repair only reproduced oracle-backed defects.

## Current checked evidence

- **23 Python tests pass**.
- JavaScript syntax passes.
- Node scheduler lifecycle harness passes play-from-selection deltas, disabled-event exclusion, and active-source stop/disconnect cleanup.
- Chromium QA passes at **1440×900** and **1024×768** with zero page horizontal overflow, temporal onset/overlap negative canaries, stale-state/flush ordering, invalid-input, Add/Duplicate/Delete semantics.
- Artifact registry: **8/8 logical artifacts fingerprinted**.
- Scenario traceability: **40/40 classified** — 25 automated-proven, 1 partial-automated, 12 implemented/partial-proof, 2 target-smoke-pending.
- Strict final acceptance: **PASS** for the runnable fixture candidate.

## Real-Voice preparation

The selected target path remains `piper-tts 1.8.x` + `MahtaFetrat/Mana-Persian-Piper` medium + Pedalboard offline processing. `FINALIZE_REAL_VOICE.bat` is the target entry point and writes machine-readable local release evidence.

The package deliberately does not label fixture success as real-Voice success. Human Persian listening and actual Windows/audio-device evidence remain separate gates.
