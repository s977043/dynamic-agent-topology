# Anthropic Claude Quickstarts: reliability patterns for post-EXP-001 evaluation (2026-10-18)

## Status and source provenance

**Non-normative research; adopted: none; no runtime/schema/fixture change.**

- Primary source: [anthropics/claude-quickstarts](https://github.com/anthropics/claude-quickstarts), inspected at [upstream commit 9ec32b9](https://github.com/anthropics/claude-quickstarts/commit/9ec32b91df50b0d4906cae64b13c6298055ff40d) (2026-10-07).
- Inspected: `autonomous-coding/README.md`, `computer-use-best-practices/README.md`, `browser-toolset/README.md`, `managed-agents/knowledge-wiki/README.md`, `managed-agents/mcp-server-typescript/README.md`, and `managed-agents/mcp-server-typescript/src/scope.ts`.
- Source descriptions and inspected snippets are **not** DAT empirical outcomes. The quickstarts were not executed in DAT; no benchmark, sandbox, billing result, or actual tool-permission enforcement was reproduced.
- Root license says MIT, while `autonomous-coding/README.md` ends with `Internal Anthropic use.`; copying code or third-party dependencies requires a separate license assessment. This note imports no code or dependencies.
- EXP-001 completed under [Issue #15](https://github.com/s977043/dynamic-agent-topology/issues/15). Its immutable pilot evidence, frozen files, and decision are not changed; follow-up comparisons require their own preregistered fixture and Operator authorization.

## Source claims vs interpretation

| Source observation | DAT interpretation, not yet evidenced |
| --- | --- |
| `autonomous-coding` resumes Coding Agent sessions using a feature list and Git while refreshing the context | Compact handoff may lower redundant context reading, but state validity, ownership and final verification need independently enforced gates |
| `computer-use-best-practices` describes screenshot pruning, prompt caching, server compaction, batch tools and trajectory JSONL | Compare **quality-adjusted total cost** and latency, not raw cache hit rate alone; trajectory existence is not trusted attestation |
| `browser-toolset` has a small CDP driver and model-free exercises for allowed and blocked actions | A deterministic driver probe can test tool mechanics separately from language-model reasoning; URL policy must be tested negatively |
| `knowledge-wiki` extracts provenance-stamped claims, resolves open questions, consolidates and queries read-only | Compiled knowledge may save repeated reads, but unsupported facts, document revisions and false citations need independent oracle checks |
| MCP server offers nine session tools; `src/scope.ts` treats absent `ALLOWED_AGENT_IDS` as unrestricted in the credential's workspace | An API-scope claim is not proof of isolation. Design default-deny, session-to-agent authorization and impersonation negative probes before any integration |

## Candidates with falsifiable hypotheses

### H1: Checkpoint + compact handoff (existing #88)

Hypothesis: for the same task/fixture and runtime settings, a verified compact handoff reduces **total billable tokens or elapsed time** without increasing unsuccessful continuations, unverifiable claims, or reviewer effort.

- Baseline: current DAT T0-style continuation without the candidate context treatment, evaluated only in a **new** experiment.
- Treatment: canonical state + evidence pointers; never raw hidden reasoning or the agent's passing self-report as completion.
- Probe: one clean resume, then stale checkpoint, conflicting revision, missing evidence pointer and duplicate resume requests. Fail closed before work on invalid context.
- Rejection: any unauthorized execution or increased outcome failures; insufficient paired data remains INCONCLUSIVE.

### H2: Screenshot/context cost policy (existing #93; cost crossover #88)

Hypothesis: cache-aware pruning/compaction and batching reduce quality-adjusted total cost with no significant loss of task accuracy.

- Pair on identical workload and environment; freeze model, effort, browser fixture, tool rights, verifier and attempt cap.
- Observe input/output/cache-read/cache-write tokens, SDK/billing prices, retries, verifier work, human minutes, latency and correctness.
- Keep context minimization, batching and model escalation as **separate treatments** first; do not attribute a combined effect to one mechanism.
- Rejection: degraded success/security or cost transfer to retries/verification, even if prompt tokens decrease.

### H3: Evidence-backed compiled knowledge (existing #63)

Hypothesis: source-bound extraction and revision checks improve repeated query cost **without lowering attribution correctness** relative to raw source lookup.

- Fixture: explicit contradictory documents, missing fact, stale revision, forged citation and updated source. Use a separately prepared ground-truth oracle; do not derive it from candidate outputs.
- Measure correct answer, correct abstention, exact source/revision link, contradictory claim detection, build amortization and incremental refresh cost.
- Keep provenance metadata separate from a **verified** truth claim. A valid hash only proves byte identity under its verification procedure.
- Rejection: unsupported citation accepted, stale facts promoted, or quality loss; no preview-only Dreaming feature required for the first local pilot.

## Smallest useful verification and boundaries

1. Register each hypothesis under its **existing** Issue (#63/#88/#93), choose work unit, independent verifier, comparison block and stop/cost budget before execution.
2. Perform model-free mechanics and negative probes first where possible; then a few strictly bounded paired runs.
3. Record fixed input hashes, Runtime/Model/Effort, observed tool permissions, exact raw evidence pointers, and separately the evaluator verdict.
4. Interpret a positive result only inside the measured population. Do not promote a candidate into `topologies/`, `roles/`, `adapters/`, `policies/`, `experiments/`, or `knowledge/sources.yaml adopted` without a subsequent separately reviewed adoption change.
5. Never start Operator-only model runs, mutate EXP-001 artifacts, merge release changes, or infer authority from a source README.

**Current decision:** retain as post-EXP-001 research candidates. No feature enablement and no claims of savings, reliability gains or security assurance.
