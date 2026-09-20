# Agentic Execution Intake — Near-final v0.6

**Candidate:** `NIRAVANA-VOICE-NEARFINAL-0.6`  
**Downstream role:** target executor / reproduced-defect repairer, not product designer.

The source layer, local API/UI, timing model, audio cache, persistence/export, candidate identity, artifact registry, traceability, release classifier and acceptance canaries are implemented. Start with root commands; do not reconstruct architecture or product behavior.

## Authority order

1. current owner instruction;
2. `product_design/*` + primary-source closure;
3. `qa/*` + `quality/SCENARIO_TRACEABILITY.json`;
4. verified external contracts;
5. executable v0.6 behavior;
6. historical planning/lineage only.

## Valid remaining work

Run `execution/TASK_DAG.yaml`. Use `FINALIZE_REAL_VOICE.bat` for target setup/render/prepare. Use `FINAL_ACCEPTANCE.bat` after any repair. If real evidence contradicts current authority, record an authority contradiction instead of silently changing expected behavior.
