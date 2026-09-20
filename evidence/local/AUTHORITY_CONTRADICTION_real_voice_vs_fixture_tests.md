# Authority contradiction — real-voice state vs. fixture-baseline tests

Recorded 2026-09-20 on the target Windows machine, per `AGENTS.md` rule 5 (record, do not silently change expected behavior).

## Observation
After `local_release.py --prepare-real` (17/17 lines rendered by real Mana/Piper, `real_voice_engineering_pass=true`, `piper_lines=17`, `fixture_lines=0`), the strict package check `final_acceptance.py` reports `ENGINEERING_ACCEPTANCE_FAIL`.
The only failing checks are two tests that pin the *shipped fixture-audio baseline*:

- `tests/integration/test_prebuilt_candidate.py::test_primary_witness_candidate_is_immediately_runnable_with_explicit_fixture_audio` — asserts `state['audio_fixture_mode'] is True`
- `tests/integration/test_v05_release_hardening.py::test_local_release_report_separates_runnable_baseline_from_real_voice_gate` — asserts `report["audio"]["fixture_line_count"] == 17`

The other 21 tests, the scheduler/browser QA, artifact registry and traceability checks pass.

## Contradiction
`AGENTS.md` and `00_START_HERE.md` prescribe `VERIFY_LOCAL` → `FINALIZE_REAL_VOICE` → human gates → `FINAL_ACCEPTANCE`. Those two tests can only pass while the audio is still fixture audio, so the prescribed sequence cannot end green.

## Decision taken (no authority changed)
- Tests were **not** edited to fit real-voice state.
- Real-voice artifacts are kept on a separate branch (`real-voice-render-2026-09-20`) so the fixture baseline on `claude/stoic-bardeen-5vm8rj` (and its CI) stays intact.
- Open for the owner: either (a) make those two tests state-aware (accept fixture *or* Piper state, still failing on mixed/partial), or (b) accept that strict acceptance is run on the fixture baseline and real-voice state is gated only by `local_release_report` (`real_voice_engineering_pass`).

## Only other repair made
`tests/integration/test_api_smoke.py`: per-request timeouts raised (0.2 s → 5 s, `/` 1 s → 10 s; startup retries 50 → 100). This machine answers `/api/state` in 0.4–0.7 s; the server itself was healthy. Timing tolerance only, no behavior change.
