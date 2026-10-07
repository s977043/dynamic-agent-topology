# HydraFusion adaptive execution strategy

## Status

**Research note / deferred Routing, Loop, Evaluation, and Runtime Mapping candidate.**

This note does not change EXP-001, its frozen artifacts, DAT schemas, canonical topologies, routing policies, Runtime Adapter behavior, or evaluation semantics.

DAT is currently in the EXP-001 evidence-acquisition phase. Any canonical Execution Strategy abstraction, workflow taxonomy, routing rule, or multi-model runtime behavior derived from HydraFusion is deferred until the EXP-001 Feature Freeze is completed.

Tracking: [Issue #93](https://github.com/s977043/dynamic-agent-topology/issues/93)

## Discovery source and primary sources

Discovery:

- Publickey, 2026-10-07: [マイクロソフト、VS CodeにAIモデルのオーケストレーションで高品質低コストなAIを実現する「HydraFusion」をプレビュー実装](https://www.publickey1.jp/blog/26/vs_codeaiaihydrafusion.html)

Primary:

- GitHub, 2026-09-04: [Project HydraFusion: Frontier quality via multi-model orchestration](https://github.blog/ai-and-ml/github-copilot/project-hydrafusion-frontier-quality-via-multi-model-orchestration/)
- GitHub Changelog, 2026-09-30: [HydraFusion in VS Code and the GitHub Copilot app](https://github.blog/changelog/2026-09-30-hydrafusion-in-vs-code-and-the-github-copilot-app/)
- Visual Studio Code 1.140 release notes: [HydraFusion model orchestration](https://code.visualstudio.com/updates/v1_140)

Publickey is retained as the discovery source. DAT interpretation should rely on the primary GitHub / VS Code descriptions when claims overlap.

## Source claims

GitHub describes HydraFusion as an adaptive model orchestration system that chooses both models and a workflow for a coding task.

The published workflow patterns are:

```text
Single
  one selected model solves the task

Cascade
  efficient solver
      ↓
  quality gate
      ├─ accept
      └─ escalate to stronger model

Critique
  solver drafts
      ↓
  independent read-only critic from a different model family
      ↓
  solver revises once
```

GitHub distinguishes HydraFusion from Auto model selection: Auto selects a model for a request, while HydraFusion may coordinate multiple models and workflow legs within the request.

GitHub also describes five operating principles for dependable compound execution:

1. **Complete accounting** — include drafting, critique, revision, escalation, retry, and fallback in cost / usage accounting.
2. **Bounded execution** — each leg has explicit timeout and cancellation behavior.
3. **Isolated review** — review runs in an isolated, tool-less context while solver steps use the permission-aware workspace.
4. **Fail-safe application** — do not apply a patch when the workflow is cancelled or fails validation.
5. **Validated routing** — validate workflow definitions, model bindings, fallback behavior, and model availability before execution.

These are source claims about HydraFusion. They are not adopted DAT invariants.

## Source evaluation results

GitHub reports controlled offline results for the best tuned HydraFusion configuration, relative to an evaluated Opus 5 baseline at the same medium reasoning level:

| Benchmark | Estimated cost vs. Opus 5 | Verified quality vs. Opus 5 |
|---|---:|---:|
| TerminalBench 2.1 | 67% lower | +4.9 points |
| DeepSWE | 36% lower | -1.5 points |
| CheckpointBench | 65% lower | -0.1 points |

GitHub explicitly scopes these results to the evaluated benchmark revisions, workflow configuration, model pool, pricing assumptions, and reasoning setting.

DAT therefore treats the figures as **source evidence that selective orchestration is worth evaluating**, not as evidence that DAT should adopt HydraFusion's taxonomy or that the same cost / quality trade-off will reproduce in DAT workloads.

## Product-status boundary

As of the referenced sources:

- HydraFusion is a **Research Preview**;
- VS Code 1.140 exposes it through the model picker for eligible users with preview features enabled;
- the GitHub source says first-turn, single-prompt coding tasks are the best current fit;
- longer iterative multi-turn behavior is still an active development focus.

Product availability and behavior may change. DAT must not encode preview availability, model pool membership, or provider-specific product UI into core contracts.

## Problem / unknowns

DAT already separates:

```text
Topology != Routing Policy
Role != Model
Role != Permission
Reviewer != Verifier
Runtime != Model Provider
```

HydraFusion raises a narrower question that is not yet represented as a first-class DAT contract:

> Is **Execution Strategy / compound workflow** a stable abstraction distinct from Topology, Routing Policy, Role, and Model binding?

Candidate Engineering Layers:

- primary: **Loop / Evaluation**
- secondary: **Harness / Context**
- Runtime Mapping where concrete model families, tool access, and isolation mechanics are bound

Candidate Work Units:

- strategy selection;
- quality gate;
- critique leg;
- revision leg;
- escalation leg;
- retry / fallback / cancellation behavior;
- per-leg accounting;
- patch-application gate.

These remain candidates until DAT-side evidence demonstrates a gap.

## DAT interpretation

The useful abstraction is not a fixed HydraFusion implementation.

Keep the separations explicit:

```text
Role / Topology
    !=
Execution Strategy / compound workflow
    !=
Model / capability binding
    !=
Judgment objective
    !=
Verification evidence
```

A provider-independent research vocabulary may be:

```text
single
  one solver leg

cascade
  solver -> quality gate -> optional capability/model escalation

critique
  solver -> isolated read-only critic -> solver revision
```

The names are useful for experiment design, but they are **not canonical enum values** during the freeze.

### Why this is not simply a new Topology

A Topology describes the desired organization and dependency structure of Roles.

A compound execution strategy may instead describe how one task is *executed* under a policy:

- a Worker-only Topology could still be executed as one direct solver call;
- a review/revision leg might be runtime-selected rather than always-present organization;
- model escalation can occur without introducing a new semantic Role;
- a read-only critic may test independent judgment while Verification remains externalized Evidence.

If DAT later cannot express these distinctions using existing Topology + Routing Policy without ambiguity, that is evidence for a new contract. The existence of HydraFusion alone is not.

## Relationship to existing DAT work

### Issue #42 — Loop / Graph execution control

[#42](https://github.com/s977043/dynamic-agent-topology/issues/42) owns generic retry, stop, budget, state, branch/join, and recovery semantics.

HydraFusion's bounded execution, cancellation, retry, and fallback principles are evidence inputs for #42 if DAT observes an actual control-contract gap.

Do not turn #93 into a generic workflow engine issue.

### Issue #82 — adversarial Judgment

[#82](https://github.com/s977043/dynamic-agent-topology/issues/82) evaluates whether a distinct adversarial falsification objective and sparse Judgment gates add value.

HydraFusion Critique is narrower and different: it uses an isolated read-only critic to review a solver result before one revision. An adversarial objective may or may not be present.

Do not equate:

```text
isolated critic == Adversary
review == Verification
critic judgment == Ground Truth
```

### Issue #88 — model / capability escalation

[#88](https://github.com/s977043/dynamic-agent-topology/issues/88) owns evidence-driven model/capability escalation and compact handoff.

HydraFusion Cascade provides an independent primary-source example of a quality gate deciding whether a stronger model is needed.

The stable question for DAT remains whether escalation evidence and task-state transfer improve verified outcomes under controlled comparison.

## Candidate invariants to evaluate

The following are **candidate invariants**, not adopted contracts:

### I1 — simplest sufficient strategy

Use the least complex execution strategy expected to meet the verified quality bar.

This extends DAT's existing "simplest topology that reliably solves the task" principle to runtime execution only if evidence shows that strategy selection is a distinct Work Unit.

### I2 — complete per-leg accounting

Any compound strategy must account for every invoked leg, including discarded / failed legs, retries, fallbacks, and revision.

Primary outcome metrics should remain task-level:

```text
cost / verified successful task
latency / verified successful task
human interventions / verified successful task
```

Per-leg metrics are diagnostic and attribution evidence.

### I3 — independent review isolation

If an independent critique treatment is being evaluated, the isolation boundary must be observable:

- critic context;
- write/tool permissions;
- input artifact;
- output judgment;
- model/capability binding.

Calling a Reviewer is activation evidence, not proof that independence was achieved.

### I4 — bounded execution

Each compound leg should have an explicit execution bound or an externally enforced termination mechanism.

A timeout or cancellation must remain distinguishable from task failure and from Verification failure.

### I5 — fail-safe application

A workflow that is cancelled, structurally invalid, or fails the required application gate must not silently apply a partial patch.

This is an application-safety hypothesis. It does not imply that every review finding blocks every patch.

### I6 — validated routing

Routing should fail before execution when required workflow definitions, model/capability bindings, permissions, or fallback targets are unavailable.

"Model unavailable" and "solver incapable" are different failure classes.

## Hypotheses

### H1 — execution strategy is a distinct Work Unit

For at least one observed task class, changing the compound execution strategy while holding Role / Topology and model/capability binding constant produces a measurable outcome difference that cannot be explained by prompt or context differences alone. If a distinct critic necessarily changes Role / Topology, record that dependency as a confound instead of claiming the strategy was isolated.

### H2 — selective compound execution

A task-conditioned strategy selector can improve verified outcome per cost / latency compared with both always-single and always-review policies **over a mixed target workload**. The per-arm effects on critique-eligible or escalation-eligible tasks alone cannot establish this claim.

### H3 — isolated critique effect

An isolated read-only critique leg can discover independently corroborated defects or improve verified completion quality beyond same-context self-review, after controlling for prompt and model effects.

### H4 — cascade effect is not just stronger-model effect

A quality-gated escalation policy can improve task-level economics relative to always-strong-model execution, after separating gate quality from model capability.

### H5 — accounting and bounds are necessary observability

Without per-leg accounting and explicit termination outcomes, apparent strategy improvements become difficult to attribute or compare reproducibly.

## Cheapest useful verification after EXP-001

Do not implement a generic strategy schema first.

Choose a small, reproducible task class where an extra critique or escalation leg is plausible and compare staged arms.

### Critique study

| Arm | Behavior | Primary contrast |
|---|---|---|
| A | single solver | baseline |
| B | solver + same-context self-review/revision | review-prompt effect |
| C | solver + isolated read-only critic + revision, same model/capability where possible | isolation / independent-role effect |
| D | C + different model family or stronger capability | model-family/capability effect |

A/B, B/C, and C/D answer different questions. In particular, B/C changes **both** context isolation and the independent critic Role/agent boundary; it is not an isolation-only estimate unless an additional matched control separates these changes. Similarly, C/D estimates the deployed model/capability package, not model family and capability strength as two separately identified effects. Match the review objective, evidence input, and revision opportunity where possible; disclose deviations as confounders. Do not collapse the arms into one "Critique worked" result.

Apply the common Capability-ablation validity controls in [Experiment Protocol](../../docs/EXPERIMENTS.md#capability-level-ablation):

- start comparison arms from equivalent fresh state where practical and prevent cross-arm feedback contamination;
- predeclare practical adoption / regression / `INCONCLUSIVE` boundaries before observing outcomes;
- keep treatment activation separate from effectiveness;
- use an independent evaluation path for corroboration where practical.

These controls are experiment-design guidance for post-freeze work and do not modify EXP-001.

### Cascade study

| Arm | Behavior | Primary contrast |
|---|---|---|
| E | baseline model/capability only, bounded attempts | control |
| F | stronger capability from the start | always-strong baseline |
| G | baseline capability -> objective quality gate -> optional stronger capability | routing / selective escalation effect |

E/F/G compares **execution treatments** on eligible tasks. G also exercises a within-cascade quality gate, but an outcome advantage for G is not by itself evidence that a workload-wide strategy selector knows when to choose Single, Critique, or Cascade. Keep its gate decisions, false escalations, missed escalations, and counterfactual evidence separate from the global selector study.

### Strategy-selection study (separate from per-arm efficacy)

The Critique and Cascade studies above establish whether their **treatments** are promising, not whether a task-conditioned **strategy selector** selects them appropriately. To test H2 after EXP-001, use a separate staged policy evaluation aligned with [Experiment Protocol — Selector quality vs downstream treatment effect](../../docs/EXPERIMENTS.md#selector-quality-vs-downstream-treatment-effect) and [Eligibility-conditioned conclusions](../../docs/EXPERIMENTS.md#eligibility-conditioned-conclusions).

1. **Define the target population in advance.** Include tasks plausibly needing a compound treatment **and** tasks for which Single should suffice. Record inclusion, exclusion, task class, and baseline failure/risk conditions before seeing treatment outcomes. A treatment-only set cannot support an all-workload policy claim.
2. **Predeclare the policy and reference.** Fix candidate selector inputs, strategy choices, abstain/fallback behavior, practical improvement/regression thresholds, and security/cost constraints before evaluation. Base the reference for a beneficial strategy choice on matched, independently verified outcomes and the predeclared decision rule, **not** the selector's own judgment.
3. **Shadow-evaluate selection before activation.** On each eligible task, record the selector's choice and evidence before revealing treatment outcomes. Where feasible, collect matched Single/compound arm outcomes using fresh-state/counterbalanced controls, including tasks the selector would *not* escalate. Do not use earlier arm outcomes to tune the selector on the held-out evaluation cases.
4. **Then evaluate end-to-end policy economics.** Compare predeclared always-Single, always-compound (where supported), and selector-conditioned policies over the same target population. Include selector calls, rejected/discarded legs, retries, routing overhead, fallback, independent Verification, and Human Intervention in task-level cost/latency. Do not report cost per verified success as finite when the successful-task denominator is zero.

Keep a case-level confusion record for the selector:

| Reference from matched verified outcomes | Selector chooses compound | Selector chooses Single |
|---|---|---|
| Compound has predeclared net benefit | correctly selected | missed beneficial selection |
| Compound lacks predeclared net benefit | unnecessary selection | correctly avoided |

Report unknown reference labels separately; missing counterfactual evidence is **not** a correctly avoided selection. With sparse data, report case counts and limitations rather than unstable precision/recall estimates. Treatment activation, selector correctness, downstream task quality, and task-level economics remain four different observations.

If shadow decisions, matched outcomes, independent adjudication, or both selection classes cannot be observed, label the policy conclusion `INCONCLUSIVE` and retain any valid treatment-only findings as conditional-on-eligibility.

Where practical, hold constant:

- task and immutable repository state;
- acceptance criteria;
- Verification commands;
- solver prompt / role contract;
- runtime tooling and permission boundary;
- effort setting;
- practical total budget.

Capture:

- verified task success;
- regression;
- task-level and per-leg latency / cost / tokens;
- model/capability per leg;
- critique findings and independently corroborated defects;
- false positives;
- quality-gate decision and later outcome;
- retry / fallback count;
- timeout / cancellation / stop reason;
- patch application / non-application outcome;
- human intervention;
- treatment activation and isolation evidence;
- selector choice, decision time, abstention/fallback, and whether selection was correct against matched outcome evidence;
- target-population coverage and policy overhead, including zero-success denominators.

Classify unsupported arms and missing evidence as `UNKNOWN` / `INCONCLUSIVE`.

## Cost interpretation

HydraFusion's published benchmark table shows that compound execution can be economically competitive under some tuned conditions.

DAT should preserve only the testable implication:

> **Selective workflow composition may outperform a fixed "always strongest model" policy on cost per verified task.**

Do not infer expected savings from the published percentages.

DAT workloads, model pools, pricing, cache behavior, runtime overhead, and quality gates may differ materially.

## Security and permission boundary

An isolated critic is useful only if the isolation is real enough to support the intended treatment.

At minimum, evaluation should record whether the critic can:

- mutate the repository;
- invoke tools;
- access external network resources;
- inspect solver-private context;
- approve or apply changes.

If the runtime cannot enforce the intended isolation, record the treatment as emulated / degraded / unavailable rather than claiming native isolation.

No research artifact should persist secrets, credentials, private source code, confidential prompts, or unsanitized traces.

## Rejection / deferral evidence

Reject or defer a new Execution Strategy abstraction when:

- existing Topology + Routing Policy expresses the needed behavior without ambiguity;
- apparent gains are explained by stronger model selection alone;
- apparent gains are explained by prompt/context differences;
- isolated critique adds coordination cost without corroborated quality benefit;
- the quality gate cannot be evaluated independently from the model it selects;
- runtime-specific orchestration details dominate and no stable provider-independent contract remains;
- strategy labels do not generalize across task classes;
- per-leg accounting or treatment activation cannot be observed;
- evidence is too sparse to separate effect from task variance;
- treatment improvement is observed only on a preselected eligible subset while the strategy selector has not been validated on the broader target workload.

A valid outcome is to keep these concepts as Runtime Adapter behavior rather than DAT core.

## What is retained during the freeze

During EXP-001, retain only these research candidates:

- Execution Strategy may be distinct from Topology, Role, and Model;
- `single / cascade / critique` are useful experimental labels, not canonical enums;
- selective compound execution is worth controlled evaluation;
- critique independence must be measured, not assumed from naming;
- complete per-leg accounting and task-level economics matter for evaluation;
- timeout / cancel / fallback / application outcomes must stay distinguishable;
- invalid or cancelled compound execution should not silently apply partial state;
- routing validity should be checked before execution where the runtime can expose it.

No canonical Schema, Topology, Routing Policy, Runtime Adapter, or EXP-001 artifact changes are adopted during the active freeze.

Accordingly, related sources remain recorded with `adopted: []`.

## Adoption gate

Revisit only after EXP-001 unfreeze conditions are satisfied.

Adopt a core Execution Strategy contract only if DAT-side paired evidence shows:

1. a recurring problem that existing Topology + Routing Policy does not represent clearly;
2. treatment activation and per-leg evidence are observable, and selector claims (if made) have separate mixed-population shadow/matched evidence;
3. the abstraction improves verified outcomes, reproducibility, safety, or task-level economics;
4. the contract remains provider-independent;
5. simpler alternatives have been tested and rejected with Evidence.
