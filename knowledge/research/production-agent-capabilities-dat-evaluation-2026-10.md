# Production-agent capabilities: DAT applicability and post-EXP-001 evaluation candidates

**Status:** RESEARCH CANDIDATE / NOT ADOPTED  
**Checkpoint:** 2026-10-14 JST  
**Input:** User-provided Japanese synthesis of 15 suggested AI engineering projects. This is a **secondary proposal**, not an independently verified primary-source bibliography. Do not infer that named vendors recommend these precise implementations.  
**Execution authority:** The current [EXP-001 Feature Freeze](../../experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md) is ACTIVE revision 3 until its Human-owned unfreeze is merged; [Draft #183](https://github.com/s977043/dynamic-agent-topology/pull/183) is a proposal, not permission.  
**Reference:** [EXP-001 decision](../../experiments/EXP-001-t0-vs-t1/DECISION.md), [Experiment Protocol](../../docs/EXPERIMENTS.md), [North Star](../../docs/NORTH_STAR.md), [Engineering Layer Diagnostics](../../docs/ENGINEERING_LAYERS.md).

## Question and scope

DAT asks **which Agent Topology works, under which conditions, and at what cost**. Production-agent capabilities are valuable **when they can be operationalized as a reproducible, provider-independent evaluation**; they are not automatically DAT features.

In scope: non-normative hypotheses, comparison controls, evidence semantics, negative test scenarios, and explicit ownership by existing Issues.

Out of scope: a new general-purpose Agent Runtime, payment or PII gateway, Temporal/LangGraph/MCP implementation, voice or browser fallback engine, DPO training pipeline, auto-routing deployment, SDK/OSS dependency imports, modification of frozen EXP-001 input/evaluation, automatic permission escalation, and self-approval.

Source claims, DAT hypotheses, runtime enforcement, experimental observations and Human adoption decisions are separate. In particular:

- Declared permission != runtime enforcement; missing violation evidence != zero violations.
- Trace != independent attestation; attestation != verification; AI reviewer judgment != Human permission.
- Selection quality != treatment effect; treatment activation != outcome improvement.
- Observed correlation != causal topology improvement.
- Candidate != adopted; feature freeze release != automatic deployment permission.

## Existing evidence and why the order matters

[EXP-001](../../experiments/EXP-001-t0-vs-t1/DECISION.md): 18/18 accepted, 9 paired blocks, T0 and T1 task success each 1.0, regression and human interventions each 0. T1 used 2.206× mean total tokens vs T0 (2.220× after excluding one environment-confounded pair). This is a **3-scenario Codex / gpt-6.1-sol / high pilot**, not a generalized T1 rejection. Ceiling effects and context/environment differences limit conclusions.

Current DAT already separates `ExecutionTrace` and `RunEvaluation`, has routing/escalation specifications, and defines paired ablation and shadow selector-vs-treatment separation. These foundations must be **tested**, not recreated or treated as proof that live policy enforcement is present.

**Preferred progression:** verify evidence provenance [#57](https://github.com/s977043/dynamic-agent-topology/issues/57) → consider trajectory invariants as a minimal downstream experiment → shadow selector/treatment evaluation [#93](https://github.com/s977043/dynamic-agent-topology/issues/93) → model/effort/routing and cost evaluation [#88](https://github.com/s977043/dynamic-agent-topology/issues/88), [#162](https://github.com/s977043/dynamic-agent-topology/issues/162). All execution/contract work requires the Feature Freeze to be officially completed.

## Fifteen-item triage

Priority **A** = direct DAT evaluation/control-plane relevance; **B** = experiment candidate when a demonstrated gap exists; **C** = not a DAT implementation goal. A is **not** implementation authorization.

| # | Topic | Priority | DAT interpretation / smallest useful unit | Existing owner |
| --- | --- | --- | --- | --- |
| 1 | Dynamic Context Assembler | B | Compare bounded/relevant/provenance-preserving context with fixed context; avoid building middleware | [#88](https://github.com/s977043/dynamic-agent-topology/issues/88), [#63](https://github.com/s977043/dynamic-agent-topology/issues/63) |
| 2 | Durable State Machine | B | Inject stop/restart and duplicate-side-effect simulations to evaluate recovery semantics; no new orchestrator | [#42](https://github.com/s977043/dynamic-agent-topology/issues/42) |
| 3 | Raw MCP server/client | C | Evaluate adapter capability/authorization evidence only when a runtime needs MCP; no protocol reimplementation | [#59](https://github.com/s977043/dynamic-agent-topology/issues/59) (adjacent, not owner of MCP) |
| 4 | Model Router | A | Compare model, effort, topology and selector quality as **distinct interventions** | [#88](https://github.com/s977043/dynamic-agent-topology/issues/88), [#93](https://github.com/s977043/dynamic-agent-topology/issues/93), [#162](https://github.com/s977043/dynamic-agent-topology/issues/162) |
| 5 | Self-correcting RAG | C | Optional retrieval-quality/answer-quality fixture; bounded retry; no production RAG | [#63](https://github.com/s977043/dynamic-agent-topology/issues/63) |
| 6 | Multi-tier memory | B | Evaluate stale/provenance-less memory and context leakage, not mandatory number of tiers | [#63](https://github.com/s977043/dynamic-agent-topology/issues/63) |
| 7 | Trajectory CI | A | Validate observable invariants and permissible paths; exact trace-DAG matching is not a global gate | [#57](https://github.com/s977043/dynamic-agent-topology/issues/57) first; separate issue only if distinct gap confirmed |
| 8 | Agent-to-agent sanitization | A | Test permission/context boundary and runtime denial evidence; prompt filtering alone insufficient | [#59](https://github.com/s977043/dynamic-agent-topology/issues/59) |
| 9 | Real-time voice interruption | C | Outside current software-development topology scope | no issue |
| 10 | DPO feedback training | C | Model-weight training outside scope; only quality-controlled feedback as candidate evidence | [#21](https://github.com/s977043/dynamic-agent-topology/issues/21) (feedback/promotion analogy, not DPO owner) |
| 11 | Cost kill switch | A | Assess budget compliance, bounded retry/stop and actual total cost; enforcement belongs to runtime | [#42](https://github.com/s977043/dynamic-agent-topology/issues/42), [#88](https://github.com/s977043/dynamic-agent-topology/issues/88) |
| 12 | Shadow routing | A | Compare candidate selection with independent matched counterfactual outcome, no external effects | [#93](https://github.com/s977043/dynamic-agent-topology/issues/93), [#21](https://github.com/s977043/dynamic-agent-topology/issues/21) |
| 13 | Computer-use fallback | C | Only adapter/permission tests for approved capability; HTTP 404 must not trigger implicit UI permission | [#59](https://github.com/s977043/dynamic-agent-topology/issues/59) (adjacent) |
| 14 | PII masking / proxy | B | Safe fixture/redacted published evidence with reversible mapping and reidentification review; do not build proxy | [#59](https://github.com/s977043/dynamic-agent-topology/issues/59), [#31](https://github.com/s977043/dynamic-agent-topology/issues/31) (publication) |
| 15 | Architecture / ADR publication | A | Record source claim → hypothesis → evidence → judgment → revision, and counterexamples; no fixed article count | [#21](https://github.com/s977043/dynamic-agent-topology/issues/21), [#31](https://github.com/s977043/dynamic-agent-topology/issues/31) |

A/B/C denotes contribution to DAT, **not** the importance of these topics for other production systems. In particular, durable execution and access control are essential in some applications, but implementing those runtime systems would change DAT's North Star.

## Candidate H1: independent provenance and trajectory invariant evaluation (#57)

**Hypothesis:** Cross-artifact provenance and observable invariants catch corrupt or misleading experiments without rejecting valid alternate execution routes.

**Baseline:** Current `schemas/execution-trace.schema.json`, `schemas/evaluation.schema.json`, `scripts/validate_pilot.py` and independent manual reviews. Do not alter historical EXP-001 artifacts/criteria.

**Candidate:** A **separate read-only audit** over copied, disposable fixtures. Start with observed fields before proposing any new required schema properties.

- Same runId/blockId/scenario/condition across attestation, trace and evaluation; exact source/run identity where observable.
- Consistent session identity and `freshSession` / `crossRunFeedbackUsed` declarations **where independently observable**.
- Timestamp chronology and token totals; ambiguous timestamps or token scope yield UNKNOWN, not manufactured precision.
- Required evidence presence; malformed reference or incomplete events cannot silently become PASS.
- Permission/approval tests require runtime-enforced denial or verified side-effect absence; a lack of `violation` events alone is not proof.
- Valid handoff/review permutations with identical authorization/outcome are allowed; Golden DAG edit distance is descriptive, not a universal failure condition.

**Negative fixtures:** mismatched sessionId, forged attestation without verifiable source, unequal trace/evaluation token totals, missing required event, unauthorized write with no violation event, legitimate alternate event order.

**Decision rule:** compare detection of seeded faults, false rejects on valid paths, audit overhead, false confidence from missing data. If old validator already catches faults, prefer no new mechanism. On unobservable permission outcome: INCONCLUSIVE, not PASS.

## Candidate H2: safe shadow selector and treatment comparison (#93, #21)

**Hypothesis:** A shadow selector can identify cases where conditional topology escalation improves verified outcomes or saves *total* cost compared with always-T0 or always-T1.

**Protocol:** A predeclared **mixed workload**, including simple successes, difficult failures and cases where escalation should be avoided. Use fresh state, same task revisions, evidence commands, budgets and evaluator; record execution order. Keep training/tuning data separate from held-out evaluation.

Compare in **two distinct estimands**:

1. **Selector quality**: Which condition was recommended for every case, including unnecessary escalation and missed beneficial escalation? Do not score only triggered or successful cases.
2. **Treatment effect**: For the same case under matched controls, how do T0/T1 and any later treatment actually differ? Prefer paired counterfactual runs where authorized.

**Safety:** A shadow candidate cannot call live mutating tools. A fake response or an isolated disposable environment **does not by itself prove** external-effect isolation; verify effective runtime permissions, tool adapters and actual side effects before a shadow run. No production traffic/personal data reuse without authority.

**Outcome:** pre-registered success/regression/safety; verifier false accept; missing evidence; retries; latency; coordination and Human attention; budget and real monetary cost when attributable. Compute quality per full workload as well as eligible subgroup. A fixed 95:5 selection ratio is not a goal.

**Stop/Reject:** unisolated write, unauthorized data, selector evaluated with its own judgments as Ground Truth, contaminated paired arms, or absence of cost and outcome comparability.

## Candidate H3: cost-aware model/effort/topology routing (#88, #93, #162)

**Hypothesis:** Condition-dependent model or effort changes may have favorable cost per *verified* success while preserving quality/safety; a more elaborate policy can still lose to fixed T0.

**Staged arms, not a mandatory 6-arm build:**

- R0: fixed model, effort, T0.
- R1: change **only model**.
- R2: change **only effort**.
- R3: change **only topology** with matched model/effort.
- R4: combined model+effort only if earlier single-factor arms justify it.
- R5: combined selector/topology only after establishing separable effects.

Keep model migration/revalidation [#162](https://github.com/s977043/dynamic-agent-topology/issues/162) distinct from failure-triggered model escalation [#88](https://github.com/s977043/dynamic-agent-topology/issues/88). Capturing `token counts` alone is **not** enough for monetary cost: collect provider price/version, cache-read/write treatment, retries, verification, human time and latency windows where known; unavailable cost stays UNKNOWN.

Candidate comparison:
`cost_per_verified_success = (cost_all_attempts + cost_routing + cost_verification + cost_recovery + cost_attributed_human_time) / verified_successes`, only where denominator > 0 and units/cost provenance are comparable. Maintain **separate non-compensatory safety constraints**; low cost never offsets violations.

**Reject:** statistically/operationally uninformative runs, regression beyond predeclared bound, or no benefit after full coordination and assessment cost.

## Limits and review questions

1. What new failure class is not already covered by #57, #93 or existing experiment validation? If none, **do not create schema or Issue**.
2. Can the scenario be made reproducible and deterministic enough for a negative test without using confidential production data?
3. Is runtime control enforced or merely declared? Can missing telemetry lead to a false PASS?
4. Can changes in Model, Effort, Context, Topology and Environment be isolated or honestly labelled confounded?
5. Are Task success, legitimate alternative paths, human review cost and failed/retried attempts counted consistently?
6. Does the next step require new external dependencies, new runtime privileges, or a Human-owned change? If yes, stop and seek a separate decision rather than silently broadening scope.

## Adoption gate / current disposition

**Disposition: RESEARCH-ONLY. NO CANONICAL CONTRACT OR RUNTIME CHANGE.**

1. Verify [#15](https://github.com/s977043/dynamic-agent-topology/issues/15) and PR #183 state at execution time; unfreeze requires explicit Human merge.
2. Review existing #57 evidence gaps. Use small negative fixtures for H1 first.
3. Propose H2 only after safety + evidence provenance are validated.
4. Propose H3 staged arms after H2 yields credible selector and treatment evidence.
5. Require independently reviewed results, checked CI and appropriate Human authority for any later promotion.
6. A valid conclusion is **KEEP T0 / REJECT / INCONCLUSIVE**. A research note, successful mock test or self-assessed improvement is not acceptance evidence.

No sources.yaml entry is added for the unverified secondary 15-project synthesis. If later supporting primary sources are independently verified, register each separately with `adopted: []` until an actual DAT contract adopts a specific claim.
