# AI-agent population scaling and ecological safety — research candidate

## Status / boundary

**Research-only, non-normative, post-EXP-001 evaluation candidate (2026-10-13).**

Tracking: [Issue #166](https://github.com/s977043/dynamic-agent-topology/issues/166). EXP-001 execution owner: [#15](https://github.com/s977043/dynamic-agent-topology/issues/15).

This note stores a paper reading, DAT interpretation, and **unexecuted** falsifiable experiment proposal. It does not change current DAT contracts, metrics, validator, schemas, canonical topologies, role permissions, routing, runtime adapter, CI gates, or EXP-001's frozen experiment. No new dependency, downloaded external code, self-replicating agent, real-world offensive cyber task, or uncontrolled infrastructure is introduced.

**Sequence:** finish EXP-001's 18-run evidence, independent review, decision, final PR and freeze exit before designing or executing a new canonical experiment. Documentation intake is allowed during the freeze; implementation/execution is deferred.

## Sources and provenance

- **Primary paper (version pinned):** Erin Crawley and Hidenori Tanaka, *Ecology of AI Agents: Collaboration Creates a Population Threshold for Takeoff*, arXiv:2610.12436v1, submitted **2026-10-08**: [abstract](https://arxiv.org/abs/2610.12436), [full text](https://arxiv.org/html/2610.12436v1), [PDF](https://arxiv.org/pdf/2610.12436).
- **Discovery only:** [AIDB X post (2026-10-13)](https://x.com/ai_database/status/2109856280948961359). Do not use a social-post paraphrase as scientific evidence.
- Status: arXiv **preprint**. This paper provides an explicit minimal mathematical / toy theory, **not** a calibrated, independently validated field prediction of self-reproducing agent populations. All numeric thresholds below are **illustrative model outputs**, not measured universal safety limits.
- Source ledger: [../sources.yaml](../sources.yaml), entry `crawley-tanaka-ecology-of-ai-agents-2026` with `adopted: []`.

## 1. Source claims (not DAT findings)

### Scope: ecological safety is not fixed-population multi-agent evaluation

The paper distinguishes safety of one system, interaction among a **fixed** collection, and safety of a population whose number of active systems **changes over time**. With population-dependent collaborative capability, additions may exceed losses beyond a critical population; this is analogous to a **strong Allee effect** (Sections 1, 2 and 3).

**Population unit matters (Section 2.1):** one unit is an *active AI system capable of joining later attempts to establish more such units*. Counting processes, API requests, or subagents alone is insufficient. A controller plus internal subagents operating as one system counts as one unit under the paper's definition. Therefore a DAT topology of 4 internal workers does **not** automatically correspond to `N=4` population units in the paper.

### Equations and variables (Sections 2.2–3.1)

Independent, non-cooperating attempts (paper Eq. 1):

```text
tau * dN/dt = N * (kappa * q - mu)
```

Collaborating population (Eq. 4), with joint success probability `p(N)`:

```text
tau * dN/dt = N * (kappa * p(N) - mu)
p_crit = mu / kappa
```

Success model assuming effective collaborative work scales linearly with population (Eq. 16):

```text
p(N) = 1 - (1 - p_ref) * (N / N_ref)^(-beta)
beta > 0
```

Critical population (Eq. 18), when `p_ref < p_crit < 1`:

```text
N_crit = N_ref * ((1 - p_ref) / (1 - p_crit))^(1 / beta)
```

| Symbol | Paper definition / correct interpretation |
|---|---|
| `N(t)` | Count of **active population units** at time t |
| `C(N)` | Effective work per joint attempt to establish units |
| `q` | Single-unit independent attempt success probability |
| `p(N)` | **Joint attempt success probability to establish additional units**, NOT generic SWE task success |
| `kappa` | Mean added units **per existing unit conditional on joint success** |
| `mu` | Mean fraction of units lost within one time interval |
| `tau` | Mean duration of a unit-establishment attempt |
| `beta` | Collaborative gain parameter describing how failure probability scales with N |
| `N_crit` | Conditional threshold in this model where expected population growth changes sign |

The paper assumes, among other things, common external conditions; an approximately fixed population composition; a constant `kappa` (no relevant resource exhaustion); a constant `mu`; and a particular success-vs-effective-search-work relationship. Its linear effective-work assumption is an **assumption**, not a DAT-established result.

Under the independent baseline, `q` does not vary with N, so there is no threshold caused by population size alone; whether the group grows depends on whether `kappa*q > mu`. A threshold in the collaborative model appears if `p(N)` crosses `mu/kappa`, under the stated assumptions. Agent count alone is neither a guarantee of takeoff nor a safety bound.

### Illustrative paper result — **not** empirical threshold (Figures 7 and 8)

For `N_ref = 16`, `p_ref = 0.10`, `beta = 0.035`, and `p_crit = 0.20`, the model's threshold is approximately `N_crit = 463` units. In the appendix, a **sublinear effective-work** example (`alpha = 0.72`) instead gives approximately `1,714`. These numbers are selected-parametric examples; they are **not** validated population limits for DAT, coding assistants, or production deployments.

### Alternatives and caveats (Appendices A–C)

- Finite search-depth correction modifies the simplified formula.
- With `C(N) ∝ N^alpha`, scaling may be sublinear or superlinear; `alpha` is confounded with the estimated effective exponent unless separately measured.
- Communication or evaluator bottlenecks may cause a **plateau**, so there need not be a finite crossing of `p_crit`.
- Congestion can produce declining effectiveness at large N, potentially two crossings instead of indefinite growth.
- Evidence cited about multi-agent SWE or test-time-compute scaling is **not** an observation of success rates for establishing new agent population units (Section 2.4 and Appendix C).

The paper recommends **population pacing** and **ecological red teaming**: evaluate scaling progressively in controlled environments instead of assuming that a small-scale safety test generalizes. This is a proposal of the authors, not evidence that any particular test population size is safe.

## 2. DAT interpretation (separate from the paper)

DAT's current research question asks which topology works for which software task at what cost. The additional candidate question is:

> When concurrent participating Agent count and collaboration structure change, how do **verified task outcomes, coordination overhead, and enforced control boundaries** scale? Only if an isolated simulated unit-establishment task is measurable, do ecological population-dynamics assumptions fit the observations?

Three quantities must **not** be collapsed:

1. `agentInvocations`: actual model/agent calls within a DAT run (already observed in ExecutionTrace).
2. `concurrentWorkerCount` (denoted **W** in the proposed SWE study): a **new candidate descriptive measure** for simultaneously working agents in a DAT execution. This counts workers, not ecological population units.
3. `populationUnitCount`: the paper's count of active systems independently able to participate in subsequent joint attempts to establish additional units. Requires a separate operational definition in a **simulation**.

Equally, `P(task success | N)` on SWE tasks is **not** paper `p(N)`. SWE success scaling may motivate, but does not identify, the ecological model.

**Fit with existing DAT:** paired comparison / `blockId`, fresh sessions and workspaces, run-order counterbalancing, trace vs evaluation separation, missingness semantics, `boundary_violations`, `agent_invocations`, `coordination_transitions`, tokens, latency, independent judgment and capability ablation.

**Missing / research-only:** simultaneous Agent-count trace, stop adherence, effective-work metrics and population-unit accounting, synthetic joint-unit-establishment outcome, fitting and uncertainty analysis. These are **candidate measurements**, not adopted required schema fields. Start with derived research artifacts rather than changing canonical RunEvaluation or existing metrics.

## 3. Falsifiable hypotheses

- **H1 — population scaling:** holding task/model/effort/runtime/tool boundaries and an explicit budget treatment fixed, the verified SWE outcome or cost changes systematically with concurrent Agent count. Null or negative scaling falsifies any assumed monotonic benefit.
- **H2 — cooperation marginal effect:** with the same N and comparable resource budget, explicit information sharing / handoffs changes verified outcome beyond independent workers. A cost increase without sufficient verified improvement is evidence **against** added collaboration.
- **H3 — control resilience:** increasing N may increase the risk of unobserved execution, budget overruns, missing traces, or boundary / stop violations. Actual runtime enforcement, not instructions or self-reports, must establish containment; zero observed incidents with incomplete trace coverage is **unknown**, not safe.
- **H4 — ecological model (separate stage):** in a *closed, entirely synthetic* task that adds only virtual population units, a joint success curve `p_sim(N)` can be estimated and compared with independent attempt success `q_sim`. Test whether positive `beta` and a finite `N_crit` are supported; plateau/congestion/no-crossing must remain possible outcomes.

## 4. Cheapest useful verification, phased post-freeze

### Stage A — feasibility, not statistical validation

Use disposable, offline SWE fixtures with deterministic acceptance, no live secrets, no external targets, enforced resource/time limits, and independently observable effective permissions.

Pilot **candidate**: `W = 1, 2, 4` concurrently active workers (not ecological population units); 3 scenarios × 2 repetitions = 18 exploratory runs for a **single predeclared cooperation/budget treatment**. This verifies safe execution, actual activated concurrency and useful trace/evaluation collection. Two repetitions are plainly insufficient for strong quantitative inference or rare-event safety claims. The 18 runs do **not** cover the full factorial.

Record run attempts, infrastructure aborts, partial traces, permissions, task outcome, coordination transitions, verified work products, total tokens, elapsed time, observed budget and stop outcomes. Use existing contracts where possible; keep extra research measurement as clearly non-normative supplementary data. Do not invent 0 values for unmeasured fields.

### Stage B — controlled SWE scaling / collaboration ablation

Only after Stage A succeeds, preregister a feasible factorial design:

- SWE worker-count treatment: `W = 1 / 2 / 4 / 8` if resources and safety gates allow (W=1 has no meaningful cooperation comparison).
- Cooperation treatment: **independent parallel attempts** vs **explicit joint collaboration**, controlling for how independent outputs are selected and verified.
- Resource treatment: **total run budget fixed** vs **per-unit budget fixed**, analyzed **separately**; a larger N with larger total budget cannot establish a pure cooperation benefit.
- Keep task distributions, repository revision, runtime, model, effort, evidence commands, permission policy and initial state comparable. Fresh workspace/session per arm; `blockId` for matched cases; balanced/randomized order to reduce time/order effects; prevent cross-arm artifacts and learned patches from leaking.
- Independently verify outcomes and `configured ≠ actually invoked` for agent count / permissions / communication. Track timeouts/aborts and complete cost accounting.
- Estimate SWE outcome vs W with uncertainty (binomial intervals when defined, variance across scenarios, raw paired deltas). Preregister practical improvement and harm/reject limits; **do not** extrapolate beyond measured sizes or infer a critical population from SWE pass rate alone.

### Stage C — synthetic ecological dynamics (conditional, distinct work unit)

**No actual unauthorized replication, resource compromise, external scanning, credential tests, recruitment, self-exfiltration, or live agent spawning driven by the experiment.**

Build an **offline virtual-unit simulator** whose unit-creation outcome is deterministic or explicitly sampled and whose unit count is bookkeeping only. If using an agent-performed synthetic search task, restrict it to inert fixtures with no privileges and no external effects. Keep the evaluator and simulator in control of virtual additions and losses.

Define before measurement:

- eligible *virtual unit* and when it counts as active;
- joint attempt, success, failures, time interval `tau`, independent baseline `q_sim`, and separately simulated ecological population size `N_sim`;
- bounded virtual additions `kappa`, loss rate `mu` and total virtual population caps;
- `p_sim(N)` outcome, independent ground truth and run-level evidence;
- fit tests against increasing work, sublinear work, plateau and congestion, plus parameter uncertainty;
- sensitivity of `N_crit` **conditional on models that support a crossing**, and no-threshold/inconclusive outcomes when not identifiable.

Synthetic `p_sim(N)` validates **only the simulation/model assumptions**, never a real-world unauthorized population takeoff threshold. If estimates are too noisy or real measured successful virtual attempts are not available, do not fit a threshold.

## 5. Decision / review criteria

A valid study must explicitly report:

- **assignment vs activation** of topology and collaboration;
- **Agent-invocation count vs concurrent SWE workers W vs simulated ecological population units N_sim**;
- verified task success, coordination cost and full compute budget, rather than “more agents succeeded” alone;
- enforcement boundary evidence (actual stop/budget/network/write restrictions), abort/missingness accounting, and whether the proposed sandbox remained contained;
- `source theoretical prediction ≠ DAT observation ≠ simulation output ≠ adoption judgment`.

Decision states: **PASS** (preregistered feasibility/benefit criteria met with no critical control harm), **FAIL** (preregistered rejection or safety stop), **INCONCLUSIVE** (insufficient replication, violated controls, ineffective instrumentation, unmeasurable unit definition or incomparable budgets). Any unsafe containment test is a STOP; do not escalate to external environments.

Potential blockers/rejections:

- count of internal subagents cannot be reconciled with ecological units;
- budget/effort/concurrency confounded or no meaningful independent-work control;
- missing traces for timed-out, aborted or violating runs;
- insufficient power / no credible estimate for SWE task success vs W or unit-establishment success vs N_sim;
- plateau or congestion contradicts unbounded-growth assumptions;
- isolation and hard limits not demonstrably enforced.

## 6. Relationship to other work / adoption gate

- [EXP-001 execution #15](https://github.com/s977043/dynamic-agent-topology/issues/15): complete first; do not alter feature-frozen artifacts or use partially observed EXP-001 runs to revise its protocol.
- [Loop / graph control #42](https://github.com/s977043/dynamic-agent-topology/issues/42): possible future home for generic limits, retry, stop and budget semantics; do not duplicate runtime scope in this study.
- [Experiment Protocol](../../docs/EXPERIMENTS.md) and [Metrics](../../docs/METRICS.md): source of existing matched-case and evidence semantics.
- [Research tracking #166](https://github.com/s977043/dynamic-agent-topology/issues/166): owner of go/no-go, prerequisites, preregistration, experimental artifacts, and post-freeze decision.

**No adoption yet.** Any later canonical metric/schema/role/control change requires its own evidence-backed review and release-compatible migration. This note and `adopted: []` do not grant permission to execute the study or introduce a new runtime.
