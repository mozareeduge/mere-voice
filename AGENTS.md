# Agent entry — Niravana Voice Prototype v0.6

This repository is an implemented, compiler-checked near-final local product. **Do not redesign or rebuild it.**

1. Read `00_START_HERE.md`, then `V0.6_COMPILER_AUDIT.md`.
2. Run root commands before manual work; `FINAL_ACCEPTANCE.bat` is the package-level acceptance entry point.
3. Execute only the remaining target tasks in `execution/TASK_DAG.yaml`.
4. Treat `data/source/voice_lines.primary_witness.json`, current `product_design/*`, `qa/*`, and `quality/SCENARIO_TRACEABILITY.json` as active authority/evidence.
5. If a command fails, reproduce the exact divergence, identify the cited scenario/oracle, and make the smallest repair; never reinterpret product behavior merely to make a test green.

Preferred target sequence: `VERIFY_LOCAL.bat` → `FINALIZE_REAL_VOICE.bat` → human Windows/listening gates → `FINAL_ACCEPTANCE.bat`.
