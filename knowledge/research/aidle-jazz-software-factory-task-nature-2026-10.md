# AIDLE Jazz / Software Factory: task-nature-conditioned topology study

> **Status**: research-only, **not adopted** (2026-10-18).
> **Primary source**: [AIDLE Extended 2026 report (part 1)](https://note.com/ai_dev_leaders/n/ndd23a2abf5be), AIDLE organizers, published 2026-10-15.
> **Issue owner**: [#93](https://github.com/s977043/dynamic-agent-topology/issues/93) (post-EXP-001 strategy / selector), related [#88](https://github.com/s977043/dynamic-agent-topology/issues/88). This note creates no new project or execution permission.

## Source claim versus DAT interpretation

Event-report claim: Max Schoening describes three kinds of engineering work: exploratory unknowns, replication of successful patterns, and tasks with known solutions. The speakers discuss Factory-like workflows and cross-functional “Jazz” collaboration. The report does **not** provide independently reproducible comparative measurements, task-level success rates, or a controlled economic evaluation.

DAT hypothesis: **task nature might help predict when to spend coordination cost on an agent team, rather than defaulting to multi-agent execution**. The three types are candidate workload strata, not canonical `ExecutionStrategy` values, Role names, Topologies, permission profiles, or inferred truth labels.

## Falsifiable hypotheses

- H1: On predeclared exploratory tasks, a bounded-discovery or independent-verifier treatment improves independently checked outcomes enough to justify its added total cost versus T0. Test these as separate interventions where feasible.
- H2: On pattern replication or well-specified tasks, T0 or deterministic P0 remains competitive on quality and cheaper on coordination cost; specialized teams may be unnecessary.
- H3: A task-nature-informed selector improves whole-workload **verified quality at acceptable total cost**, compared with a fixed minimal topology and a fixed stronger topology. Treatment effect and selector accuracy are evaluated separately.

Counterexamples: the labels fail inter-rater reproducibility; the selector misses safety-critical work; outcomes do not improve after controlling task difficulty; total cost or Human Attention increases without compensating verified quality.

## Cheapest useful verification (after current release/approval gates)

1. **Pre-register** a mixed workload with all three task types, a held-out evaluation subset, reproducible AC / expected outcome, a fixed repository revision, and at least some examples where stronger treatment should *not* be needed. Do not select only prior failures.
2. Human annotators label task type based on source evidence **without reading model outcomes**; record disagreement, unclear cases, and inter-rater reliability. Treat `unknown` as a decision to gather evidence, not an automatic escalation permission.
   Keep **risk / required Human approval** as separate, pre-recorded variables. Include negative contrasts (a high-risk known-solution task and a low-risk exploratory task) so task-nature labels cannot silently stand in for risk or permission.
3. Run matched, fresh-state blocks for **baseline T0/P0** vs bounded candidate topology where technically feasible; fix runtime/model/effort and use the **same independent outcome evaluation** for all arms. Account for candidate-only discovery/reviewer/verification work as treatment cost, not as a free shared evaluator. Record control deviations. Use DAT's existing `docs/EXPERIMENTS.md` rules; do not modify schemas.
4. Evaluate **treatment** conditional on eligibility (task success/regression, false accept, interventions, tokens, latency, coordination transitions), then **shadow selector quality** across the complete mixed population, including unnecessary and missed escalations. Include routing, failed legs, review and verification cost.
5. Use independent outcome evaluation; no post-hoc threshold tuning. Missing counterfactuals, evaluator leakage, failure to activate or unpaired conditions yield `INCONCLUSIVE`.

## Boundaries / adoption gate

- EXP-001 findings remain pilot-scoped. Keep T0 was the recorded pilot decision, not a universal claim.
- Respect [#186](https://github.com/s977043/dynamic-agent-topology/pull/186) release / Human finalization and current post-EXP-001 gates. No new experiment starts and no frozen files, runtime, configs, canonical policies or schemas change in this PR.
- Outcome evidence is not the author/reviewer/selector's assertion. Source claims are not DAT results.
- Promote nothing until a separate preregistered experiment, independent review, acceptance criteria, and Human adoption decision. This note is not approval to run agents or merge.
- PlanGate owns execution approvals ([#911](https://github.com/s977043/PlanGate/issues/911)); River Review owns review recommendation ([#2034](https://github.com/s977043/river-review/issues/2034)); DAT owns comparative evidence.

## Three critical self-review questions

1. Does the task label leak outcome or change multiple factors in one arm?
2. Can success be distinguished from lower review depth, skipped checks, or AI self-attestation?
3. Does a small positive effect generalize to an entire workload? If not, report a conditional/inconclusive result.
