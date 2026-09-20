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
