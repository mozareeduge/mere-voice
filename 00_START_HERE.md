# START HERE — Niravana Voice Temporal Workbench v0.6

**Candidate:** `NIRAVANA-VOICE-NEARFINAL-0.6`  
**Local state:** `RUNNABLE_NOW_WITH_FIXTURE_AUDIO`  
**Engineering acceptance:** `CHATGPT_CRAFT_PASS_EXTERNAL_GATES_REMAIN`

## Use the product now

- Windows: double-click `RUN_WORKBENCH.bat`.
- Linux/macOS/dev: run `python app.py`, then open `http://127.0.0.1:8765/`.
- The supplied candidate contains the 17 primary-witness Voice units, 17 baseline events, fixture dry audio and prepared variants, so the complete temporal/UI workflow is immediately usable.

## Verify the package

- `VERIFY_LOCAL.bat` checks the runnable candidate and writes `evidence/local/local_release_report.*`.
- `FINAL_ACCEPTANCE.bat` applies the package-level compiler checks: product-authority closure, candidate identity, artifact fingerprints, scenario traceability, available executable QA, and local readiness.
- `VERIFY_DEVELOPER.bat` runs the same acceptance in strict developer mode and requires pytest + Node + Playwright/browser QA.

The checked v0.6 package passed strict acceptance in the build runtime.

## Convert fixture audio to the selected real Persian Voice path

Double-click `FINALIZE_REAL_VOICE.bat` on the target Windows machine. It installs/uses the supported environment, verifies/downloads the Mana/Piper model, renders all 17 lines, rebuilds processed variants, runs export smoke, and rewrites local release evidence.

## What v0.6 changed beyond v0.5

The uploaded `chatgpt_executable_handoff_v2.0` was used as a **craft/validation compiler**, not merged as generic documentation. It caused four concrete product corrections: invalid numeric edits now preserve the prior valid value; Add Event starts at the authority-defined `0 ms`; Duplicate preserves line/timing/processing exactly; dirty-score Delete requires confirmation and keeps the saved revision recoverable.

It also adds one canonical candidate/version identity, a fingerprinted logical artifact registry, complete 40/40 scenario classification, and a final acceptance runner. See `V0.6_COMPILER_AUDIT.md` and `quality/COMPILER_APPLIED.md`.

## Remaining truthful gates

Real Mana/Piper execution in this sandbox is not claimed. Human Persian pronunciation/prosody acceptance, actual Windows/default-audio-device smoke, optional page-by-page PDF typography confirmation, and the final artistic Voice/speaker-field decision remain external gates.
