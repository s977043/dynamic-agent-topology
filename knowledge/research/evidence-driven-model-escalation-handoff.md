# Evidence-driven model escalation and compact handoff

## Status

**Research note / deferred Context, Harness, Loop, and Evaluation candidate.**

This note does not change EXP-001, its frozen artifacts, DAT schemas, canonical topologies, routing policies, Runtime Adapter behavior, or evaluation semantics.

DAT is currently in the EXP-001 evidence-acquisition phase. Any canonical escalation rule, handoff contract, or model-routing behavior derived from this pattern is deferred until the EXP-001 Feature Freeze is completed.

Tracking: [Issue #88](https://github.com/s977043/dynamic-agent-topology/issues/88)

## Discovery source

- @fleyta88: [Sonnet 5.5 → Opus 5.5 routing with early verification and compact handoff](https://x.com/fleyta88/status/2107518541054230717)
- Observed: 2026-10-07

The post proposes a practical routing loop:

```text
clear / scoped task
    ↓
start on Sonnet 5.5
    ↓
run a real check before context grows large
    ├─ PASS → continue
    └─ FAIL → stop the cheap loop
                 ↓
        fresh Opus 5.5 session
                 ↓
          compact handoff
```

It also argues that long agent loops should be priced by **cost per completed / passed task**, not by model list price alone, because cache-read pricing can materially change the effective ratio between models.

These are practitioner claims and workload-specific arithmetic. They are not DAT benchmark results.

## Officially verified facts

Anthropic's [Claude Sonnet 5.5 launch page](https://www.anthropic.com/claude-sonnet-5-5) describes:

- Sonnet 5.5 as a faster, lower-cost complement to Opus 5.5 for well-scoped everyday work;
- Opus 5.5 as intended for more complex work requiring careful judgment;
- the launch page's displayed Sonnet 5.5 pricing rows: $2/M input, $10/M output, $2.50/M cache write, and $0.20/M cache read;
- the launch page's displayed Opus 5.5 pricing rows: $4/M input, $20/M output, $5/M cache write, and $0.20/M cache read.

Anthropic's [Claude 5.5 family webinar](https://www.anthropic.com/webinars/building-with-the-claude-5-5-family-choosing-the-right-model-and-getting-more-from-every-token) explicitly frames model choice around task evals, cost per task, effort levels, prompt caching, and orchestration.

These official sources support evaluating cache-aware model selection and task-level economics. They do **not** establish that:

- a fixed turn number should trigger escalation;
- 20K tokens is the correct handoff budget;
- a failed check should always route to Opus;
- a full transcript should never be transferred;
- the source's example ratios generalize to DAT workloads.

## Problem / unknowns

DAT already separates Routing / Escalation from Topology and treats Model as independent from Role. What remains unknown is how a runtime should decide that continuing with the current model is no longer the smallest effective intervention.

Affected Engineering Layers: **Context / Harness / Loop / Evaluation**.

Candidate Work Units:

- escalation trigger;
- cross-session handoff artifact;
- runtime/model mapping;
- cost-per-verified-success evaluation.

Key unknowns:

1. Is deterministic / observable Verification failure a useful escalation signal?
2. Can a compact handoff preserve enough decision-critical state to avoid correctness loss?
3. Is context rebuild cost material in real DAT tasks?
4. Should escalation select a specific model, a capability class, or another runtime-local policy?
5. Does the observed failure actually require a stronger model, or a Prompt / Context / Harness fix?
6. When should execution stop rather than continue or escalate?

## DAT interpretation

The useful abstraction is not a fixed Sonnet → Opus graph.

Keep these separations explicit:

```text
Role != Model
Model escalation != Topology escalation
Verification evidence != Model self-assessment
Handoff artifact != Full transcript
Cache behavior != Core topology semantics
Source cost example != DAT benchmark result
```

A provider-independent candidate flow is:

```text
scoped Worker
    ↓
objective Verification
    ├─ PASS → continue / complete
    └─ FAIL
         ↓
diagnose smallest broken Work Unit
         ↓
smaller Prompt / Context / Harness correction sufficient?
    ├─ YES → correct and re-verify
    └─ NO
         ↓
evidence-backed escalation gate
         ↓
compact evidence handoff
         ↓
stronger runtime-local model / capability
         ↓
Verification
```

This preserves DAT's existing diagnosis rule: do not interpret every failure as evidence that the model is too weak.

## Candidate escalation evidence

Before evaluating model escalation, classify the observed failure. A failed command caused by missing executables, unavailable services, permissions, corrupted fixtures, or other infrastructure / environment faults is not evidence that the current model lacks capability. Fix or stop on the smallest broken Work Unit first.

Potential signals to evaluate after EXP-001:

- a deterministic test / lint / build / typecheck failure persists after one correctly scoped repair **and the failure is classified as task/implementation-related rather than infrastructure-related**;
- the same failure class repeats after the relevant work unit was changed;
- required acceptance evidence remains UNKNOWN after the current model has exhausted the bounded attempt budget;
- an explicit high-risk judgment boundary requires stronger reasoning under a runtime-local policy;
- the current context has become expensive to carry while the task state can be externalized safely.

Candidate triage before escalation:

| Observed state | Smallest default action |
|---|---|
| Verification passes | continue / complete |
| reproducible implementation failure after a correctly scoped repair | model/capability escalation candidate |
| missing executable, service, permission, or environment dependency | repair Harness / infrastructure or stop |
| required context/artifact is missing or stale | repair / rebind Context before escalating model |
| failure class remains UNKNOWN | gather discriminating Evidence; do not auto-escalate |
| high-risk Judgment boundary | evaluate Reviewer / stronger reasoning under an explicit policy |

Signals that should **not** be sufficient by themselves:

- "the model seems confused";
- turn count alone;
- context size alone;
- elapsed time alone;
- a model's self-report that the task is difficult.

A fixed "turn 6" check is therefore a source hypothesis, not a DAT invariant.

## Candidate handoff

The source's important idea is not the exact 20K number. It is that escalation should transfer **task state and evidence**, not blindly inherit all conversational history.

Candidate fields to evaluate:

```yaml
goal: ...
repository_state:
  revision: ...
  dirty_state: ...
acceptance_criteria:
  - ...
failure:
  class: implementation | context | harness | infrastructure | unknown
  evidence: ...
failing_verification:
  command: ...
  observed_output: ...
execution_environment:
  runtime: ...
  model: ...
  effort: ...
  relevant_tool_versions: ...
relevant_artifacts:
  - path: ...
    range_or_identifier: ...
attempts:
  - intervention: ...
    observed_result: ...
unknowns:
  - ...
evidence_provenance:
  - artifact: ...
    source: ...
constraints:
  - ...
budget:
  max_attempts: ...
  stop_condition: ...
```

The artifact should be bounded, auditable, and sufficient for the receiving agent to reproduce the current failure.

"Compact" must be measured by information sufficiency and cost, not by one universal token count.

## Hypotheses

### H1 — evidence-driven escalation

Observable verification failure plus bounded repair evidence produces better routing decisions than a fixed turn threshold or subjective difficulty judgment.

### H2 — compact handoff

A bounded evidence handoff can reduce context rebuild cost while retaining enough state for a stronger model to solve the task at comparable or better verified success rate.

### H3 — cost per verified success

For long agent loops, routing policies optimized on cost / latency per **verified successful task** outperform policies optimized on model list price or per-turn cost alone.

### H4 — provider-independent core

The stable DAT contract, if any, should define escalation evidence and handoff requirements. Sonnet / Opus bindings should remain Runtime Mapping.

### H5 — escalation is not always the smallest fix

A material share of apparent "model failures" may actually be Prompt, Context, Harness, Loop, or Evaluation defects. Diagnosis-first routing should outperform unconditional stronger-model escalation.

## Evaluation population and claim scope

The initial recovery study may intentionally select tasks where the baseline reaches a reproducible, task-related Verification failure. That answers a **conditional recovery question**:

> given that the baseline has already reached the declared escalation-eligible failure state, which continuation / handoff / capability treatment performs best?

It does **not** by itself answer:

> should the routing policy escalate more tasks in the overall workload?

Keep these populations separate:

```text
all eligible workload
    ↓
escalation gate classification
    ├─ no escalation
    └─ escalation-eligible failure
             ↓
       recovery treatment study
```

When sampling only from the lower branch, report conclusions as conditional-on-eligibility. Do not extrapolate recovery success rates, cost savings, or model preference to tasks that never reached the gate.

To evaluate the routing policy itself, a later study must include both escalation-needed and escalation-not-needed cases so unnecessary escalation and missed escalation are observable.

## Cheapest useful verification after EXP-001

Do not implement an automatic Sonnet → Opus router first.

Select reproducible tasks where the baseline model reaches an observable failure and compare:

| Arm | Behavior | Primary contrast |
|---|---|---|
| A | continue baseline model in the current session within a bounded attempt budget | control |
| B | same baseline model in a fresh session from compact evidence handoff | A vs B isolates fresh-session / handoff effect |
| C | stronger runtime-local model/capability in a fresh session from the **same compact handoff** | B vs C isolates model/capability escalation effect |
| D | stronger runtime-local model/capability in a fresh session with the fullest transferable prior context the runtime can reproduce | C vs D estimates compact-vs-full context payload effect |

For Arms B/C/D, use equivalent fresh-session conditions where the runtime permits. If a runtime cannot reproduce one arm faithfully, record the arm as unavailable rather than silently substituting another condition.

Where practical, hold constant:

- task and repository state;
- acceptance criteria;
- verification command;
- runtime tooling and permission boundary;
- effort setting;
- overall task budget;
- compact handoff artifact for Arms B/C.

A/B, B/C, and C/D answer different questions. Do not collapse them into one "routing improved" result.

Capture:

- verified task success;
- regression;
- number of turns / attempts to pass;
- fresh input tokens;
- cache-read tokens;
- cache-write tokens;
- output tokens;
- latency;
- total cost;
- human intervention;
- failure classification and misclassification;
- handoff reconstruction work;
- failures caused by missing handoff context;
- provider billing / usage evidence sufficient to recompute the observed cost.

Repeat enough paired runs to separate routing effect from task variance.

Classify insufficient evidence as `UNKNOWN` / `INCONCLUSIVE`.

## Cost interpretation

The source gives example ratios such as Opus becoming relatively less expensive per turn as cached context grows and shows a large difference between rebuilding hundreds of thousands of tokens versus a compact handoff.

DAT should preserve only the testable implication:

> **Cache state and handoff size can materially affect task-level routing economics.**

Do not infer actual cache-hit/write behavior from model identity or prompt shape alone. When possible, retain provider usage/billing evidence for the run and recompute cost from observed token categories.

Do not preserve the specific ratios as general expectations. They depend on fresh input, output, cache-hit rate, cache-write behavior, effort, turn count, and actual task success.

Useful outcome metrics include:

```text
cost / verified successful task
latency / verified successful task
turns / verified successful task
cache-rebuild cost
handoff reconstruction cost
human interventions / successful task
```

Per-turn cost remains diagnostic data, not the primary adoption criterion.

## Cache portability boundary

Do not assume that prompt-cache state is portable across models, runtimes, sessions, providers, regions, or pricing modes.

A DAT evaluation should treat cache reuse as **observed runtime/billing evidence**, not as a core semantic guarantee. A model switch may require rebuilding some or all reusable context; the exact behavior must be measured for the runtime under test.

This also means "keep the cache warm" is an optimization hypothesis, not an escalation invariant.

## Security and privacy boundary

A compact handoff is still an execution artifact. It should carry only the evidence necessary to reproduce and continue the task.

Do not place secrets, credentials, private source code, confidential prompts, or unsanitized execution traces into a handoff intended for persistence or publication. When raw failure output contains sensitive material, retain a sanitized summary plus the minimum provenance needed for auditability.

Compactness is not a substitute for data minimization.

## Relationship to Issue #82

[Issue #82](https://github.com/s977043/dynamic-agent-topology/issues/82) evaluates a sparse **Adversarial Judgment role** and decision gates.

This note evaluates a different question:

```text
#82: Should a distinct adversarial Judgment objective be invoked at selected gates?
#88: When should execution escalate model/capability, and what state should cross that boundary?
```

The two may share observable triggers such as repeated failure, but they must not be bundled automatically. An adversarial review can run on the same model, and a model escalation can occur without introducing a new role.

## Rejection / deferral evidence

Reject or defer this candidate when:

- the baseline succeeds after a smaller Prompt / Context / Harness correction;
- compact handoff causes material correctness loss;
- full-context transfer is cheaper or more reliable for the tested workload;
- stronger-model escalation does not improve cost per verified success;
- infrastructure / environment failures are frequently misclassified as model-capability failures;
- the proposed trigger produces too many unnecessary escalations;
- trigger quality depends on subjective model self-assessment;
- the useful behavior is provider/model-specific and has no stable provider-independent contract;
- evidence is too sparse to distinguish benefit from task variance.

## What is retained during the freeze

During EXP-001, retain only these research hypotheses:

- objective Verification can be a candidate escalation signal;
- diagnosis should precede model escalation;
- compact evidence handoff may be preferable to full transcript transfer;
- cost per verified task is more meaningful than list price alone;
- fixed turn counts and token budgets are hypotheses, not invariants;
- model identity remains separate from Role and Topology;
- cache reuse across a model/runtime boundary must be observed, not assumed;
- handoff artifacts must preserve repository security/privacy boundaries.

No canonical Topology, Routing rule, Runtime Adapter, handoff schema, or EXP-001 artifact changes during the active freeze.

Accordingly, related sources remain recorded with `adopted: []`.

## Adoption gate

Revisit this note only after EXP-001 unfreeze conditions are satisfied.

Adopt a core contract only if paired evidence shows a stable improvement in verified task outcomes and task-level economics, and the behavior can be expressed without hard-coding one provider's model family.
