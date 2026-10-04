# Dynamic Agent Topology (DAT)

[日本語](README.md) | [English](README_en.md)

> **Adaptive, evidence-driven agent topologies for AI software engineering.**  
> **Which agent topology works, under what conditions, and at what cost?**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status: v0.1 Foundation](https://img.shields.io/badge/Status-v0.1%20Foundation-orange.svg)](docs/NORTH_STAR.md)

**Dynamic Agent Topology (DAT)** is a provider-agnostic specification and experimentation foundation for designing, selecting, evaluating, and evolving AI agent team structures.

DAT starts from one rule:

> **Use the simplest topology that reliably solves the task.**  
> **Add coordination only when evidence justifies its cost.**

## What DAT is trying to do

DAT is not only about arranging multiple agents.

```text
Knowledge & Benchmarks
        ↓
Hypothesis
        ↓
Topology Specification
        ↓
Runtime Mapping
        ↓
Execution
        ↓
Evidence & Trace
        ↓
Evaluation
        ↓
Ablation
        ↓
Adopt / Reject / Evolve
```

A topology should not be adopted only because it looks reasonable. DAT treats it as a hypothesis to test.

## What DAT is not

- **Not another static topology catalog.** Canonical topologies are hypotheses and baselines, not universal best practices.
- **Not another agent runtime.** DAT is intended to work across existing runtimes such as Claude Code, Codex, Gemini CLI, and Antigravity.
- **Not multi-agent maximalism.** Deterministic pipelines and single-agent execution are first-class baselines.
- **Not agent confidence as ground truth.** Deterministic and observable evidence outrank self-assessment wherever available.

## Core topology dimensions

1. **Role Contract** — responsibility and expected outputs
2. **Permission Boundary** — separate prompt intent from enforced capability
3. **Context Boundary** — scope context and artifacts per agent
4. **Explicit Dependencies** — model auditable handoffs and dependencies
5. **Evidence** — deterministic, observable, and judgment evidence
6. **Routing & Escalation** — separate topology definition from topology selection
7. **Topology Adherence** — compare declared organization with observed execution

## Canonical topologies

| ID | Shape | Purpose |
|---|---|---|
| P0 | Deterministic Pipeline | Non-agent simplicity baseline |
| T0 | Single Agent | Default low-coordination baseline |
| T1 | Worker → Verifier | Measure independent verification value |
| T2 | Worker → Reviewer → Verifier | Measure independent judgment value |
| T3 | Specialized Team | Test specialization on higher-complexity tasks |

Dynamic routing is modeled separately under `policies/`; it is not itself a topology.

## What “dynamic” means

Dynamic does not mean “use more agents.”

```text
Select
→ Observe
→ Escalate / De-escalate
→ Recompose
→ Evaluate
```

v0.1 focuses first on topology selection and escalation. Later versions may evaluate runtime de-escalation and recomposition.

## Brownfield adoption

Adopting DAT does **not** mean immediately adopting multi-agent execution.

```text
A0 Assess
→ A1 Bind Evidence
→ A2 Observe
→ A3 Recommend
→ A4 Canary
→ A5 Dynamic
```

A5 is not the goal by itself. A project may intentionally remain at A2, A3, or a fixed T0/T1 topology when the evidence supports that choice.

See [docs/ADOPTION.md](docs/ADOPTION.md).

## Target runtimes

Initial targets:

- Claude Code
- Codex
- Gemini CLI
- Antigravity

Runtime-specific differences belong in `adapters/`, while canonical topology definitions remain runtime-independent.

## Repository layout

```text
docs/         North Star, architecture, glossary, metrics, adoption
knowledge/    Research, official guidance, adopted principles
schemas/      Machine-readable DAT contracts
roles/        Canonical role contracts
baselines/    Non-agent execution baselines
topologies/   Canonical agent topology hypotheses
policies/     Routing and escalation policies
adapters/     Runtime-specific mappings
experiments/  Experimental protocol
harness/      Future execution/evaluation harness
examples/     Brownfield adoption examples
```

## Evidence base

DAT separates source claims from DAT interpretations and implementation decisions.

The initial knowledge base includes:

- OpenCollab
- TeamBench
- AsynCodeBench
- Anthropic multi-agent research

See [knowledge/sources.yaml](knowledge/sources.yaml).

## Status

**v0.1 Foundation**

The repository currently provides:

- North Star, architecture, and glossary
- Role / topology / runtime / evaluation schemas
- Canonical P0–T3 topologies
- Routing and escalation policies
- Brownfield adoption protocol
- Runtime adapter contracts
- Initial knowledge base
- Schema validation CI

Runtime adapter implementations and the execution/evaluation harness will be added incrementally after the contracts and evaluation protocol stabilize.

## Guiding principle

> **Do not assume a topology is better. Test it.**

## License

MIT
