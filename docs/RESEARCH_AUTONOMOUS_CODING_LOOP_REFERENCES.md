# Recoverable Autonomous Coding Loop — external design reference (2026-10-10)

Status: **research candidate only**. No external package, SDK, hosted service, copied code, or runtime contract is adopted.

## Goal and boundaries

Study Serena, LangGraph, E2B, and Langfuse as *reference architectures* for a recoverable, bounded autonomous coding loop. DAT remains a provider-independent experiment/specification project, **not** a new agent runtime. Avoid reimplementing a full framework. Current priority is EXP-001 empirical evidence acquisition; its Feature Freeze, prompts, fixtures, schema, role/topology, evaluator, retry allowance and run matrix remain untouched.

## Sources and transferable patterns

| Reference | Primary repository | Pattern to study | DAT candidate, not implementation commitment |
| --- | --- | --- | --- |
| Serena | https://github.com/oraios/serena | Symbol-level definitions/references, selective code context; read-only exploration | Compare scoped symbol-first retrieval vs existing search, with LSP coverage and dynamic-code limitations recorded |
| LangGraph | https://github.com/langchain-ai/langgraph | Explicit state transitions, checkpoints, pending writes, recovery; side-effect discipline | Distinguish logical state checkpoint from Git/workspace/artifact state; bounded retry and idempotent resume contract only if needed |
| E2B | https://github.com/e2b-dev/e2b ; https://github.com/e2b-dev/runtime | Isolated execution lifecycle, ephemeral workspaces, artifact extraction, network/secret boundaries | Define *properties* for existing runtime sandbox rather than adding E2B or building a VM platform |
| Langfuse | https://github.com/langfuse/langfuse | Traces, prompts, observations, evaluation datasets/scores | Use existing ExecutionTrace/RunEvaluation; preserve observed action vs evidence vs independent judgment |

Sources are design inputs, **not** measured DAT improvements. Check upstream revisions/licenses before citing implementation specifics or deriving code. Do not copy source code.

## Fit with current DAT

- `docs/ARCHITECTURE.md` already separates Desired Organization, Control Plane, Runtime Mapping, Observed Execution, and Evaluation. Keep these boundaries.
- `docs/EXPERIMENTS.md` already defines paired comparison, capability ablation, independent evaluation, contamination control, and PASS/FAIL/INCONCLUSIVE. Reuse rather than create duplicate scoring.
- `docs/AGENT_HARNESS.md` already defines human-owned authority, separate-session independent review, and scoped agent merge permissions. Research does not authorize bypass.
- EXP-001 (#15) is Feature Frozen. A new experimental treatment or execution semantics must wait for unfreeze. This note is not an EXP-001 run result.

## Three review passes (design review, not independent agent execution)

1. **Architecture / minimalism:** A four-service stack would add avoidable dependencies and obscure attribution. Keep all four as external references; reuse current schemas and adapters. No new canonical enum.
2. **Scientific validity / fast feedback:** Compare one factor at a time on matched tasks and fresh states; capture activation, verified task outcome, latency, token/infra cost, human interventions, and failures. Avoid selecting only failed tasks then claiming whole-workload gains. No changes to frozen EXP-001.
3. **Security / governance:** A checkpoint cannot roll back external effects; a sandbox does not imply unrestricted network/secret safety; a trace is not verified evidence. Require bounded attempts, fail-closed stop, scoped permissions, independent verification, and human-controlled sensitive changes.

## Post-freeze candidate studies (not authorized runs)

- **R1 Retrieval:** baseline search vs symbol-scoped retrieval, same task/runtime/model/effort, compare verified quality, retrieved context size and cost. Do not infer benefit from token reduction alone.
- **R2 Recovery:** same controlled injected transient failure with and without stateful recovery; measure recovery success, duplicate side effects, retries, cost and time. Predeclare stop and safety criteria.
- **R3 Isolation:** verify workspace/network/secret boundary and artifact provenance using existing sandbox. Record negative tests; do not equate configuration with runtime attestation.
- **R4 Observability:** check trace-to-artifact linkage, missing events, redaction, and independent evaluator reproducibility using DAT-native evidence formats.

Do not bundle R1–R4 into a single treatment. Preserve the P0/T0 baselines and distinguish selector validity from treatment effectiveness.

## Next decision

1. Complete EXP-001 empirical runs and lift Feature Freeze through the existing authority path.
2. Review #42 (loop/retry/recovery ownership) and existing evidence/metrics contracts before proposing schema changes.
3. Choose the cheapest useful post-freeze study; reject additional machinery unless evidence justifies it.
4. Record measured results separately from source claims and author-led design review.

## Explicit non-goals

- Installing Serena, LangGraph, E2B, or Langfuse, or their dependencies.
- Implementing a generic orchestrator, hosted telemetry, VM platform, or production deployment.
- Altering current experiment artifacts, granting new retry/merge authority, or treating author review as independent reviewer approval.
