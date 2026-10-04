# Raven: Evidence-gated executable configuration evolution

## Status

**Research note / deferred design candidate.**

This note does not change EXP-001, its frozen artifacts, DAT schemas, canonical topologies, routing policies, or runtime behavior.

DAT is currently in the EXP-001 evidence-acquisition phase. Any normative architecture or schema change described here is deferred until the EXP-001 feature freeze is completed.

## Source

- Paper: [Raven: The Harness of Harnesses for Composable Agentic Intelligence](https://arxiv.org/abs/2609.33439)
- Reference implementation: [EverMind-AI/Raven](https://github.com/EverMind-AI/Raven)
- Harness evolution source: [Self-Evolving Agent Harnesses via Gated Semantic Quality-Diversity](https://arxiv.org/abs/2607.13683)
- Raven published: 2026-09-27
- Repository status when reviewed on 2026-10-05: pre-alpha

## Source claims

The Raven paper treats an executable **model–harness pair** as a composable unit of intelligence.

Its Host Agent decomposes goals, assigns subtasks to specialized agents, coordinates execution dependencies, and integrates results. Raven also describes self-evolution of harnesses: candidate changes are generated from experience, evaluated, and only accepted when they pass validation.

These are source claims, not DAT benchmark results.

### Evidence provenance

Raven's published harness self-evolution benchmark table is reproduced from HarnessBank rather than being an independent Raven orchestration experiment.

The evidence therefore supports the **harness-evolution method** separately from Raven's **multi-agent orchestration** claims. DAT should not use the HarnessBank gains as evidence that Raven orchestration itself is superior.

Raven also notes that the reproduced harness-evolution results do not provide a complete per-run manifest for every screening subset, proposal order, and run-specific setting. DAT should treat those results as external evidence with reproducibility limits, not as a drop-in benchmark baseline.

## Terminology boundary

DAT already uses `harness/` for the minimal Experiment Artifact validation and summary harness. Raven uses **Harness** more broadly for agent execution capabilities such as tools, skills, context, policy, and workflow behavior.

These are different concepts.

This note therefore uses **Raven-style harness** only when describing the source. DAT-side design discussion uses **Executable Configuration** and does not redefine the existing `harness/` directory or its responsibility.

## DAT interpretation

DAT should not copy Raven's `Harness` as a new monolithic architectural plane.

DAT already separates responsibilities that Raven groups under a harness:

- Topology and Role Contracts
- Control Plane policies
- Runtime Mapping and capabilities
- Context and artifact boundaries
- Observed Execution
- Evidence and Evaluation

For DAT, a Raven-style harness is better interpreted as a **versioned executable configuration under evaluation**, composed from existing DAT concerns rather than replacing them.

Conceptually:

```text
Executable Configuration
=
Model
+ Runtime
+ Topology
+ Role Contracts
+ Policy
+ Context strategy
+ Tools / Skills
+ Effort / budget
```

This preserves existing separation rules such as `Role != Model`, `Topology != Routing Policy`, and `Verifier != Evidence`.

## Candidate principle: configuration-dependent capability

Observed agent capability should not be attributed to the model alone.

A capability claim is conditional on the executable configuration and task distribution used to produce the evidence.

A model upgrade may eliminate the marginal value of a previously useful Role, Skill, Verifier, or Topology. Conversely, an executable-configuration change may improve outcomes without changing the model.

DAT's existing capability-level ablation and re-evaluation triggers already support this interpretation.

## Candidate evolution lifecycle

A future DAT evolution layer may use the following lifecycle:

```text
Execution
  ↓
Evidence
  ↓
Evaluation
  ↓
Diagnosis
  ↓
Candidate Change
  ↓
Controlled Evaluation
  ↓
Promotion Gate
  ├─ Reject
  └─ Adopt
```

Candidate changes may include:

- Prompt / instruction
- Skill
- Role Contract
- Tool capability
- Context strategy
- Policy
- Runtime Mapping
- Topology

A generated candidate is not evidence of improvement.

## Evaluation guardrails

A future promotion mechanism should preserve DAT's current experimental discipline:

1. Compare the candidate against a previous configuration under controlled conditions.
2. Keep unrelated variables fixed where practical.
3. Confirm that the changed capability actually activated before interpreting effectiveness.
4. Prefer deterministic or observable evidence over agent self-assessment.
5. Use held-out / regression scenarios when available.
6. Treat insufficient evidence as `INCONCLUSIVE`, not as improvement.
7. Allow simplification and de-escalation when quality is preserved at lower coordination cost.

A useful responsibility split is:

```text
Candidate Generator != Evaluator != Promotion Authority
```

This extends DAT's existing `Builder != Judge` principle without requiring a new runtime abstraction.

## What is retained during the freeze

No Raven-derived design is normatively adopted while EXP-001 is frozen. The following are retained only as post-freeze hypotheses to evaluate:

- agent capability is configuration-dependent, not model-only;
- candidate improvements require independent evidence before promotion;
- out-of-sample / regression evidence should be preferred for promotion decisions;
- successful changes should remain ablatable and reversible.

Accordingly, `knowledge/sources.yaml` keeps Raven at `adopted: []`. No current canonical topology, schema, metric, routing policy, or Runtime Adapter changes are adopted from Raven during EXP-001.

## Deferred questions

After EXP-001 completes, review whether DAT needs explicit contracts for:

- configuration snapshots;
- improvement candidates;
- diagnosis evidence;
- promotion decisions;
- shadow / canary evaluation;
- rollback and re-evaluation triggers.

Do not introduce these contracts before observed EXP-001 friction demonstrates that they are needed.

## Adoption gate

Revisit this note only after the EXP-001 unfreeze conditions are satisfied.

The first post-freeze design review should start from EXP-001 evidence and observed operational friction, then decide whether any Raven-inspired abstraction earns implementation.
