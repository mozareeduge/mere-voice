# v0.4 → v0.5 GPT-Chat Near-Finalization Audit

## Verdict

v0.4 was already a working local product, not merely a specification. The useful remaining GPT-side work was therefore **hardening and removing downstream-agent interpretation**, not rebuilding the architecture. v0.5 closes every material engineering gap reproduced in this environment; the remaining gates require target-machine execution or human/artistic judgment.

## Material gaps found and closed

### 1. Debounced client/server race
A processing change could be followed immediately by Prepare, event audition, Save Revision, or Export while the 120 ms score write was still pending. The UI could briefly depend on stale server state / stale processed audio.

**Closed:** local processing mutations invalidate processed readiness immediately; score writes are serialised; dependent operations flush the newest score before acting. A browser canary proves API ordering.

### 2. Newly duplicated event could falsely retain global processed readiness
A duplicated event intentionally has no prepared variant, but the pre-v0.5 duplicate path did not synchronously invalidate the processed-ready state.

**Closed:** duplication now marks its variant `STALE`, blocks processed playback immediately, and is covered by browser QA.

### 3. Audio preparation provenance was too weak
Processed files were content-addressed but did not explicitly identify the processing implementation/dependency versions that produced the bytes.

**Closed:** variant metadata records pipeline revision, execution mode, NumPy version, and Pedalboard version when used. Real Piper dry assets record `piper-tts` version as part of render identity.

### 4. Export evidence did not bind enough runtime context
The WAV sidecar already captured score/event data but did not bind the release candidate, complete source identity, model profile, and export dependency versions strongly enough for later reconstruction.

**Closed:** export sidecars now bind candidate, source provenance/hash, model profile, runtime versions, exact event-audio metadata, and final WAV hash.

### 5. Target preparation still required a lighter model to interpret instructions
The package had correct granular setup/render/prepare steps, but a downstream agent still had to decide whether setup was actually complete.

**Closed:** `FINALIZE_REAL_VOICE.bat` + `scripts/local_release.py` implement the deterministic target work and emit machine-readable PASS/NOT-YET-PROVEN evidence. The model downloader now also repairs a missing/corrupt/incompatible config before validating semantic invariants.

## Current evidence

- Python/domain/API/integration: **17 passed**.
- Browser/layout: **PASS** at 1440×900 and 1024×768.
- Temporal oracle and negative canary: **PASS**.
- Processing-edit stale-state canary: **PASS**.
- Duplicate-event stale-state canary: **PASS**.
- Flush-before-revision canary: **PASS**.
- Local supplied candidate: **PASS with fixture audio**.
- All-17 Mana/Piper engineering state in this sandbox: **NOT YET PROVEN** because the model binary cannot be downloaded here.

## Remaining gates

1. run `FINALIZE_REAL_VOICE.bat` on the target Windows machine until `real_voice_engineering_pass=true` and `piper_line_count=17`;
2. listen to the 17 Persian lines and reject/fix pronunciation or prosody defects if any;
3. run the workbench through the actual default audio device and perform one save/export smoke;
4. optional editorial PDF visual check and later stage-Voice/speaker-field artistic decisions.

These are target/human gates. They are not missing construction work for the current prototype.
