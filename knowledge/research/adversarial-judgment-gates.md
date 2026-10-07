# Adversarial judgment role and sparse decision gates

## Status

**Research note / deferred Judgment and Escalation evaluation candidate.**

This note does not change EXP-001, its frozen artifacts, DAT schemas, canonical topologies, routing policies, Runtime Adapter behavior, or evaluation semantics.

DAT is currently in the EXP-001 evidence-acquisition phase. Any canonical Role / Topology / Routing change derived from this pattern is deferred until the EXP-001 Feature Freeze is completed.

Tracking: [Issue #82](https://github.com/s977043/dynamic-agent-topology/issues/82)

## Discovery source

- @thedelost: [Codex team pattern with Luna workers, Sol lead, Astra adversary, and sparse challenge gates](https://x.com/thedelost/status/2107210980392640878)
- Observed: 2026-10-07

The post labels the pattern an "Official OpenAI tip." DAT does **not** preserve that phrase as an official endorsement claim. The specific three-gate operating pattern is treated as practitioner guidance unless an OpenAI source explicitly recommends those gates.

## Officially verified primitives

OpenAI documentation supports the underlying Codex mechanisms needed to express variants of this pattern:

- custom multi-agent roles under `agents.<name>`;
- role-specific config files;
- default subagent model selection;
- default subagent reasoning-effort selection;
- approval review using `approvals_reviewer = "auto_review"`.

References:

- OpenAI: [Codex subagents](https://developers.openai.com/codex/subagents)
- OpenAI: [Codex configuration reference](https://developers.openai.com/ja-JP/docs/config-file/config-reference)
- OpenAI: [Agents API multi-agent guidance](https://developers.openai.com/api/docs/guides/agents-api/multi-agent)

OpenAI's multi-agent guidance recommends clear independent tasks and coordination when agents edit the same files. It does not establish a universal "never edit the same file" rule.

These are product capabilities and coordination guidance. They are **not** evidence that a Sol / Luna / Astra mapping, an Adversary role, the three proposed gates, or strict file partitioning improve DAT outcomes.

## Source pattern

The practitioner pattern can be summarized as:

```text
Lead / integration
    |
    +-- scoped implementation workers
    |
    +-- read-only adversary, spawned only at selected decision points
```

The proposed adversary is not a normal implementation worker. Its job is to challenge assumptions and completion claims at three candidate points:

1. before an interface / contract locks;
2. when a relevant test or error repeats twice;
3. before declaring the task done.

The source also proposes keeping implementation ownership disjoint between parallel workers and using automatic approval review.

These are source-level design choices, not DAT requirements.

## Problem / unknowns

DAT has not yet observed repository-backed evidence that requires a distinct Adversary role.

The first post-freeze task is diagnosis, not role creation: identify a concrete failure or decision boundary, test whether existing Reviewer / Verifier contracts and smaller Prompt / Context / Harness interventions are sufficient, and only then evaluate a new role or trigger.

Affected Engineering Layers: **Evaluation / Loop**.

Routing / Escalation are DAT concepts used when diagnosing the Loop layer; they are not separate Engineering Layers.

Candidate Work Units: **adversarial review objective / escalation trigger**, pending empirical diagnosis after EXP-001.

## DAT interpretation

The useful abstraction is potentially **role + trigger + permission + evidence**, not a fixed model tree.

DAT should therefore separate:

```text
Role       != Model
Role       != Permission
Trigger    != Permission escalation
Review     != Verification
Judgment   != Ground Truth
Adapter    != Core contract
```

The closest existing DAT concepts are:

- **Reviewer** — independently judges specification, design, or change quality;
- **Verifier** — evaluates externalized Evidence against a required outcome;
- **Routing / Escalation** — decides when additional capability or attention is justified;
- **Runtime Mapping** — binds provider/model/runtime-specific mechanisms to provider-agnostic intent;
- **Evaluation** — measures whether added coordination actually improves outcomes.

A candidate **Adversary** role would be narrower than Reviewer:

```text
Reviewer  -> Is the proposal/change acceptable?
Verifier  -> Does Evidence support the required outcome?
Adversary -> What credible falsification would break the current claim?
```

The role should remain optional unless empirical evidence shows that ordinary Reviewer / Verifier contracts are insufficient.

## Candidate gates

### 1. Contract gate

Before a boundary becomes expensive to change, challenge:

- interface compatibility;
- schema assumptions;
- ownership boundaries;
- hidden coupling;
- failure / rollback semantics.

Candidate trigger:

```text
high-cost-to-reverse contract about to lock
    -> read-only adversarial challenge
```

This is not equivalent to requiring an Adversary on every design change.

### 2. Repeated-failure gate

After the same relevant failure recurs, challenge whether the current repair loop is addressing the cause or merely suppressing symptoms.

The source uses a threshold of two failures. DAT should treat that threshold as a hypothesis, not a universal constant.

Potential questions:

- Is the repeated failure actually the same failure class?
- Is the latest fix hiding evidence?
- Is the diagnosis anchored to the wrong Engineering Layer?
- Should execution stop instead of consuming another iteration?

### 3. Completion gate

Before declaring completion, challenge the strongest remaining completion assumption.

Potential targets:

- skipped edge cases;
- missing negative tests;
- unverifiable claims;
- unresolved UNKNOWN evidence;
- permission or scope drift;
- unreviewed interface consequences.

An Adversary opinion is still Judgment. Completion must continue to rely on the appropriate Evidence and Verification contract.

## Relationship to existing Reviewer and Verifier roles

Adding a role merely because its name is intuitive would create coordination cost without evidence.

The first post-freeze question should be:

> Can the existing Reviewer contract be parameterized with an adversarial objective at selected gates?

If yes, a new canonical Role may be unnecessary.

A distinct Adversary role is justified only if there is a stable responsibility gap, for example:

- normal Reviewer instructions systematically optimize for acceptance rather than falsification;
- sparse invocation requires materially different context or permission;
- separate measurement is needed to evaluate challenge quality or false-positive cost;
- combining the responsibilities weakens role clarity or auditability.

## Hypotheses

### H1 — sparse adversarial review

For high-value decision boundaries, a read-only falsification-focused agent invoked sparsely may improve defect discovery or decision quality relative to the existing review path.

### H2 — lower coordination cost than continuous strongest-model review

Sparse escalation may capture much of the value of a stronger reviewer while avoiding the latency, token, and coordination cost of using it on every turn.

### H3 — role separation improves interpretability

Separating adversarial falsification from ordinary Review and Verification may make observed decisions easier to attribute and evaluate.

### H4 — model mapping is secondary

The effect, if any, may come from objective / context / trigger / permission rather than from a specific Luna / Sol / Astra assignment.

If so, model-specific routing should remain Runtime Mapping rather than a DAT core contract.

## Cheapest useful verification after EXP-001

Do not add a canonical `Adversary` role or a three-gate topology first.

Start from one observed DAT failure mode or high-cost decision boundary and choose exactly one candidate gate. Then decompose the candidate so objective, role separation, and model assignment are not changed at the same time.

Candidate staged comparison:

```text
A: existing Reviewer behavior
B: same Reviewer + adversarial objective at the selected gate
C: separate read-only Adversary + same adversarial objective
D: C + stronger runtime-local model/capability binding
```

Control intent:

- **A → B** estimates the effect of the adversarial objective without adding a new Role.
- **B → C** estimates the added value and coordination cost of independent Role/context separation. Keep model, effort, input Evidence package, and practical budget matched where the runtime permits.
- **C → D** estimates the incremental effect of stronger model/capability routing after the Role/objective treatment already exists.

If B performs as well as C, a distinct canonical Adversary Role is not justified by that evidence. If C adds value but D does not, the useful abstraction is more likely Role/context separation than a stronger model binding.

For each stage:

1. keep the baseline topology unchanged except for the tested treatment;
2. keep Scenario, repository state, Verification commands, practical budget, and human decision boundary controlled where practical;
3. verify that the candidate treatment actually activated before interpreting outcome differences;
4. measure:
   - independently corroborated defects or decision risks found;
   - false-positive challenges;
   - rework avoided or added;
   - human interventions and human-facing fan-out;
   - latency;
   - token / runtime cost;
   - verified completion quality;
5. repeat across enough paired cases to separate task variance from treatment effect;
6. classify missing, non-activated, or ambiguous evidence as `UNKNOWN` / `INCONCLUSIVE`.

The three candidate gates should be evaluated independently before testing them as one bundled policy.

### Gate eligibility and selection bias

Do not choose a gate or task because an adversarial pass already appears likely to find something.

For each evaluation slice, define the gate eligibility rule **before** seeing the candidate outcome and apply the same rule to baseline and candidate conditions.

Examples of candidate eligibility rules:

- **contract gate** — a predeclared class of change crosses a public interface, schema, permission, or ownership boundary that is expensive to reverse;
- **repeated-failure gate** — the same predeclared failure class is observed for the configured count; similarity must be based on observable failure identity, not a subjective "still seems broken" judgment;
- **completion gate** — every selected task reaching the ordinary completion criterion receives the same gate treatment.

Record non-triggered cases rather than silently dropping them. A gate that rarely activates, activates only after subjective judgment, or cannot be applied consistently may be operationally unsuitable even if individual challenges are useful.

Within a paired block, gate eligibility and trigger timing must not depend on whether the treatment is A, B, C, or D.

## Permission boundary

The candidate Adversary should default to read-only capability for an initial evaluation.

This is an evaluation control, not a claim that read-only access is always required.

Initial invariant:

```text
Adversary may challenge and propose
Adversary must not directly mutate the implementation under review
```

This keeps Builder ownership and Judgment evidence easier to separate.

## Automatic approval review is a separate mechanism

OpenAI documents `approvals_reviewer = "auto_review"` as a way to review approval prompts.

DAT must not conflate this with adversarial design review.

```text
approval review != design review
approval review != verification
approval review != completion evidence
```

The mechanisms may coexist, but they solve different problems.

## Parallel file ownership

The source recommends that two implementation agents should not edit the same file.

OpenAI's current multi-agent guidance is weaker: agents that edit the same files must coordinate their changes. DAT should therefore not present strict disjoint file ownership as an OpenAI requirement and should not promote the source's stronger recommendation to a core invariant without evidence.

Potential benefits:

- lower merge conflict;
- clearer ownership;
- simpler attribution.

Potential costs:

- artificial task partitioning;
- cross-cutting changes become awkward;
- file boundary may not match semantic ownership.

Treat file ownership as a separate Graph / coordination candidate, not as part of the Adversary role hypothesis.

## Relationship to Loop / Graph evolution

Issue [#42](https://github.com/s977043/dynamic-agent-topology/issues/42) separately evaluates whether DAT needs new machine-readable Loop / Graph execution contracts.

The boundary is:

- **#82** — evaluate the value of an adversarial Judgment objective and sparse invocation at selected gates;
- **#42** — evaluate whether observed runtime friction requires new generic retry / termination / trigger / state / graph semantics.

A repeated-failure gate in #82 should first be tested with existing Routing / Escalation mechanisms. It does not justify a new Loop contract by itself. If the experiment shows that existing contracts cannot represent an evidenced trigger or stop condition without ad-hoc runtime logic, that contract gap belongs in #42.

## Challenge evidence semantics

Keep activation, Judgment, and verified effect separate:

```text
challenge emitted
    != challenge accepted
    != defect/risk independently corroborated
    != verified outcome improvement
```

- **challenge emitted** is activation evidence;
- **challenge accepted** is Reviewer / Human Judgment;
- **corroborated defect or risk** requires deterministic/observable Evidence or independent Verification appropriate to the claim;
- **outcome improvement** requires the corrected result to satisfy the relevant Verification / regression checks.

Do not count a persuasive adversarial argument as a discovered defect solely because the Builder or Reviewer agreed with it. Also record false-positive challenges and accepted-but-unverified challenges so an agent cannot appear effective merely by generating more objections.

These distinctions are evaluation guidance for the post-freeze experiment. They do not add a required field to the current EXP-001 schema or evaluation contract.

## Rejection / deferral evidence

Reject or defer a distinct Adversary role when:

- existing Reviewer instructions can provide equivalent falsification behavior;
- deterministic Verification already catches the target failure class;
- added challenge mostly produces false positives;
- coordination or latency cost exceeds measured benefit;
- the useful behavior depends on one provider/model and has no stable provider-agnostic contract;
- sparse gates cannot be defined from observable state;
- the proposed gate merely hides a Prompt, Context, Harness, or Evaluation defect;
- evidence is too sparse to distinguish benefit from task variance.

## What is retained during the freeze

During EXP-001, retain only these research hypotheses:

- adversarial falsification may be useful as a distinct Judgment objective;
- sparse high-value gates may be more efficient than continuous strongest-model review;
- repeated failure can be a candidate escalation signal;
- completion claims may benefit from a final falsification pass;
- model identity should remain separate from Role intent;
- approval review is not adversarial design review.

No canonical Role, Topology, Routing rule, runtime configuration, or EXP-001 artifact is changed during the active freeze.

Accordingly, the related sources remain recorded with `adopted: []`.

## Adoption gate

Revisit this note only after EXP-001 unfreeze conditions are satisfied.

The first post-freeze review should start from observed DAT evidence. If Reviewer / Verifier contracts already cover the relevant failures with lower complexity, close Issue #82 without introducing a new Role.
