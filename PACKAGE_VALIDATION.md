# Package Validation — Near-final v0.6

**candidate:** `NIRAVANA-VOICE-NEARFINAL-0.6`  
**validation date:** `2026-09-20`  
**status:** `CHATGPT_CRAFT_PASS_EXTERNAL_GATES_REMAIN`

## Executed engineering evidence

| Layer | Evidence | Result |
|---|---|---:|
| Product authority | 12 horizons, 11 core objects, 32 scenarios, 8 cross-factor guards, 28 QA oracles, 17 unique source units | PASS |
| Component/integration | `python -m pytest -q` — 23 tests | PASS |
| Browser/temporal | Chromium 1440×900 + 1024×768; onset/overlap + negative canary; geometry + interaction canaries | PASS |
| Scheduler lifecycle | play-from-selection deltas, disabled-event exclusion, active-source stop/disconnect | PASS |
| Artifact integrity | 8 logical artifacts fingerprinted; registry verifies current bytes | PASS |
| Traceability | 40/40 authoritative scenario IDs classified | PASS |
| Package acceptance | `python scripts/final_acceptance.py --strict-dev` | PASS |
| Runnable candidate | 17/17 dry and processed fixture-backed readiness | PASS |

## Authority divergences found and closed in v0.6

1. Invalid onset/processing values previously could alter local state or be silently clamped; they now reject inline and retain the previous valid value.
2. Add Event previously placed itself after the current score; authority requires a new event at `0 ms`.
3. Duplicate Event previously added `250 ms`; authority requires exact line/timing/processing duplication before independent editing.
4. Dirty-score Delete previously removed immediately; it now requires confirmation and keeps the saved revision recoverable.
5. Candidate/version identity was duplicated across runtime/release surfaces; it is now centralized and acceptance checks stale identity.

## Proof classification

`quality/SCENARIO_TRACEABILITY.json` currently classifies 25 cases `AUTOMATED_PROVEN`, 1 `PARTIAL_AUTOMATED`, 12 `IMPLEMENTED_PARTIAL_PROOF`, and 2 `ARCHITECTURAL_PROOF_TARGET_SMOKE_PENDING`. This is intentionally conservative: implemented behavior is not promoted to proof without cited evidence.

## External gates

- real Mana/Piper rendering cannot be claimed from this sandbox package state;
- Persian pronunciation/prosody requires human listening;
- actual Windows 10/11 browser/default-audio-device playback requires the target machine;
- optional page-by-page PDF punctuation/typography comparison remains editorial proof;
- final performance Voice identity and physical speaker field remain artistic authority.

These are external/human gates, not missing general product construction.
