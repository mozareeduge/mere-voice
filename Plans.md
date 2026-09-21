# Plans.md — mere-voice (Niravana Voice Temporal Workbench v0.6)

Purpose: finish the remaining target-machine work from `execution/TASK_DAG.yaml` without redesigning the product.
Authority order: `product_design/*` > `qa/*` + `quality/SCENARIO_TRACEABILITY.json` > executable behavior (see `AGENTS.md`).

- team_validation_mode: not_required_lightweight (architecture closed; plan only sequences an existing DAG)
- Spec skip reason: no product behavior changes; product contract is frozen in `product_design/*`. Only reproduced defects may be repaired, each recorded as an authority-checked fix.
- Lint/format baseline: none configured; no new source code planned (repairs only) → no setup task.

## Phase 1 — Reproduce baseline on this machine

| Task | 内容 | DoD | Depends | Status |
|------|------|-----|---------|--------|
| 1.1 | [lane:fast] TASK-R00: repo placed at `Documents/.../digital art/mere-voice`, on `claude/stoic-bardeen-5vm8rj`, equal to cloud | `git status -sb` shows branch tracking origin with 0 ahead/behind; folder exists | - | cc:完了 |
| 1.2 | [lane:gate] TASK-R00: run `python scripts/local_release.py --export-smoke` | `evidence/local/local_release_report.json` has `base_candidate_pass=true` and 17 fixture lines | 1.1 | cc:完了 |
| 1.3 | [lane:gate] Install pinned deps (piper-tts, pedalboard, numpy) into `.venv` | `.venv\Scripts\python.exe -c "import piper, pedalboard, numpy"` exits 0 | 1.1 | cc:完了 |
| 1.4 | [lane:gate] Full `pytest` green in `.venv` (3 tests failed on system Python only because pedalboard was missing) | `.venv\Scripts\python.exe -m pytest -q` → 23 passed (needed one test-timing fix: smoke test's 0.2 s/1 s request timeouts raised to 5 s/10 s because this machine answers in 0.4–0.7 s; product code untouched) | 1.3 | cc:完了 |

## Phase 2 — Real Persian voice (TASK-R01)

| Task | 内容 | DoD | Depends | Status |
|------|------|-----|---------|--------|
| 2.1 | [lane:gate] Fetch Mana/Piper model (SHA-pinned) via `scripts/fetch_model.py` | `models/fa_IR-mana-medium.onnx` exists and script's SHA-256 check passes | 1.3 | cc:完了 |
| 2.2 | [lane:gate] Render 17 lines + processed variants + export smoke (`local_release.py --prepare-real --export-smoke`) | report says `real_voice_engineering_pass=true` and `piper_lines=17` | 2.1, 1.4 | cc:完了 |
| 2.3 | [lane:gate] Strict acceptance: `python scripts/final_acceptance.py` (+ `--strict` if supported) after any repair | `evidence/final/FINAL_ACCEPTANCE_REPORT.json` shows engineering pass, remaining items only external gates | 2.2 | cc:完了 (result: FAIL on 2 fixture-baseline tests only — recorded as authority contradiction, see evidence/local/AUTHORITY_CONTRADICTION_real_voice_vs_fixture_tests.md) |
| 2.4 | [lane:fast] Commit regenerated evidence (+ model/audio only if consistent with repo policy) on the work branch and push | `git status` clean; `git log origin/<branch>` contains the commit | 2.3 | cc:完了 (work branch: plan + test-timing fix + contradiction note; branch `real-voice-render-2026-09-20`: real audio + evidence) |

## Phase 3 — Human/physical gates (TASK-R02) — cannot be done by an agent

| Task | 内容 | DoD | Depends | Status |
|------|------|-----|---------|--------|
| 3.1 | Mohammad/Niravana listens to clinical, rejection, late-overlap passages for Persian pronunciation/prosody | Written verdict per passage in `evidence/local/` notes | 2.4 | blocked (needs a human ear) |
| 3.2 | Play processed + DRY BYPASS through real Windows output; confirm VOICE-014/015/016 audibly separate; save a revision, note, export | Checklist ticked by a human | 2.4 | blocked (needs a human + speakers) |
| 3.3 | Optional: visually check PDF punctuation/typography; any source correction is explicit and followed by audio regeneration | Human decision recorded | 3.1 | blocked (optional, human) |
| 3.4 | Open the workbench once so the human can do 3.1–3.2 (`RUN_WORKBENCH.bat`), with a 1-page listening checklist prepared by the agent | Server answers on `http://127.0.0.1:8765/`; checklist file exists | 2.4 | cc:完了 (`evidence/local/LISTENING_CHECKLIST.md`) |

## 事前確認
- 事項: external-send — download of Python packages (PyPI) and the Mana Persian Piper model (Hugging Face, SHA-256 pinned)
  理由: required by TASK-R01 in `execution/TASK_DAG.yaml`
  scope: Phase 1 / Task 1.3, Phase 2 / Task 2.1
- 事項: external-send — `git push` of the work branch `claude/stoic-bardeen-5vm8rj` (new commit, no force)
  理由: keep local repo and cloud repo in sync
  scope: Phase 2 / Task 2.4

## Phase 4 — v0.6.1: اعراب + pauses + tempo + guide (owner-instructed 2026-09-21, Hermes)

| Task | DoD | Status |
|------|-----|--------|
| 4.1 Vocalize 17 lines (`text_fa_vocalized`, source untouched) | field present 17/17 + provenance block; text_fa unchanged | done |
| 4.2 Pause-aware synthesis | chunks on sentence/clause punctuation; 420 ms / 190 ms silences in dry WAV; evidence in asset meta | done (code) |
| 4.3 Tempo control end-to-end | `tempo_scale` 0.5–2.0 in domain/processing/UI; cached by processing_hash; guide documents it | done (code) |
| 4.4 In-product settings guide | `? GUIDE` in right panel explains every control | done |
| 4.5 Option-3 (LCA phonemizer) machine-fit verdict | lane-B-LCA-eval.md: feasible but NOT adopted now (fork build, ~340 MB risky downloads, boot-time HF fetch breaks local-only; default-OFF if ever) | done |
| 4.6 Re-render 17 dry + variants at v0.6.1 | local_release --prepare-real passes; piper_lines=17 | in progress |
| 4.7 Verify | pytest (no new failures vs baseline 19/23; 2 pre-recorded contradiction failures), VERIFY_LOCAL, node --check, browser QA | pending |
| 4.8 Deliver | commit+push; restart workbench; listening checklist for new voice | pending |

Notes:
- DEC-016..019 recorded in product_design/05 ledger; 01 object model amended (tempo_scale, spoken-text layer).
- Version/candidate: 0.6.1 / NIRAVANA-VOICE-NEARFINAL-0.6.1.
- The two fixture-baseline test failures remain an owner decision (AUTHORITY_CONTRADICTION note), not touched.

## Phase 5 — Continuation handoff v2.0 (Voice Laboratory; supersedes the "perfect Mana" direction of Phase 4)

Source: `mere-voice-continuation-handoff-v2.0-2026-09-21.zip` (decisions A–I). Verified locally 2026-09-21: `text_fa_vocalized` breaks lexical invariance on 11/17 lines (001–010, 012). Target: `VOICE_LAB_CANDIDATE_FROZEN`. Rule: never reset a legitimate descendant of `cba031f`; preserve the 18-event artistic score and all tempo/timeline/export behaviour.

| Task | 内容 | DoD | Depends | Status |
|------|------|-----|---------|--------|
| 5.0 | Freeze v0.6.1 evidence (score, processed variants, vocalized text kept as history only) | tag/commit `v0.6.1-frozen`; audit tool output saved in `evidence/local/` | – | cc:完了 (tag `v0.6.1-frozen`; audit in `evidence/local/VOCALIZATION_INVARIANCE_AUDIT_v0.6.1.json`) |
| 5.1 | Stop `text_fa_vocalized` driving synthesis (`voice_proto/tts.py::_spoken_text` → `text_fa` only) | 17 assets built from exact `text_fa`; test asserts strip-marks invariant | 5.0 | cc:TODO |
| 5.2 | Prosody baseline: keep commas inside sentence-level spans; optional sentence gap only; drop 190 ms clause hard-chunking as default | asset meta records span policy; A/B against commit `920a479` assets | 5.1 | cc:TODO |
| 5.3 | Exact-span pronunciation override layer (Piper raw `[[phoneme]]` blocks), empty by default | schema from handoff `pronunciation_overrides.example.json`; unit tests | 5.1 | cc:TODO |
| 5.4 | Re-render 17 dry lines + variants; state `SYNTHETIC_CONTROL_READY` | `local_release --prepare-real` passes, `piper_lines=17` | 5.2, 5.3 | cc:TODO |
| 5.5 | Source-body bench (independent local page, not in main UI): VOICE-004, 001, 009; slots canonical-Mana dry / recorded-human dry / v0.6.1 reference; non-destructive level normalisation; fields intelligibility, bodily presence, distance, unwanted connotation, latency, Man–Voice reach, KEEP/RETRY/DROP/HOLD | bench opens locally; results saved as structured JSON | 5.4 | cc:TODO |
| 5.6 | **HUMAN GATE** — record/read the same 3 lines dry, drop in bench, log verdicts | state `VOICE_SOURCE_DIRECTION_SELECTED` | 5.5 | blocked (needs Mohammad's voice + ears) |
| 5.7a | If TTS kept: 17-line listening manifest; failed-span overrides only; LCA/Gooya only if corrections are contextual/recurrent | affected lines re-rendered | 5.6 | conditional |
| 5.7b | If recorded human wins: minimal `import_recorded_dry` provider, same cache/processing path | imported WAV processed like synthetic dry | 5.6 | conditional |
| 5.8 | Temporal truth: `buffer_duration_ms` + `audible_duration_ms` (energy-derived); timeline shows audible length; scheduler keeps full buffer | Hermes samples with 2.2–4.6 s silent tails display correct audible duration | 5.6 | cc:TODO |
| 5.9 | QA/state cleanup: fix 2 fixture-vs-real acceptance tests, regression tests, unify docs, model/asset policy, strict final acceptance | `VOICE_LAB_CANDIDATE_FROZEN` | 5.7*, 5.8 | cc:TODO |

Notes:
- 5.0–5.5 and 5.8 are agent-owned and can run now; 5.6 is the only step software cannot decide.
- LCA stays deferred; ParsVoice-XTTS is a later artistic branch only.
