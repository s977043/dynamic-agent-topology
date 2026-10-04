# Dynamic Agent Topology (DAT)

[日本語](README.md) | [English](README_en.md)

> **Adaptive, evidence-driven agent topologies for AI software engineering.**  
> **Which agent topology works, under what conditions, and at what cost?**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status: v0.2.1 Manual adoption-ready](https://img.shields.io/badge/Status-v0.2.1%20Manual%20adoption--ready-green.svg)](docs/NORTH_STAR.md)
[![CI](https://github.com/s977043/dynamic-agent-topology/actions/workflows/spec-lint.yml/badge.svg)](https://github.com/s977043/dynamic-agent-topology/actions/workflows/spec-lint.yml)
[![CodeQL](https://github.com/s977043/dynamic-agent-topology/actions/workflows/codeql.yml/badge.svg)](https://github.com/s977043/dynamic-agent-topology/actions/workflows/codeql.yml)

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

## Baselines and canonical topologies

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

The current scope focuses first on topology selection and escalation. Later versions may evaluate runtime de-escalation and recomposition.

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

Start with the [Quick Start](docs/QUICKSTART.md), then see the [Brownfield Adoption Protocol](docs/ADOPTION.md).

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
experiments/  Experiment definitions and scenario sets
fixtures/     Small reproducible scenario fixtures
harness/      Experiment artifact validation and summary harness
examples/     Brownfield adoption examples
```

## First experiment

[EXP-001: T0 vs T1](experiments/EXP-001-t0-vs-t1/README.md) compares a Single Agent with Worker + independent Verifier under controlled Task / Runtime / Model / Effort conditions.

The evaluation considers not only task success, but regression, human intervention, tokens, latency, topology adherence, and verifier false accepts.

DAT also evaluates the **marginal contribution of internal capabilities** such as roles, skills, and verifiers through paired ablation. Being invoked is activation evidence, not effectiveness evidence. See [Experiment Protocol](docs/EXPERIMENTS.md#capability-level-ablation) and [Metrics](docs/METRICS.md#capability-contributionderived-comparison).

## Current focus

The highest priority is now **collecting empirical evidence for EXP-001**.

- Execution tracking: Issue #15
- Empirical runs: **live progress is tracked in Issue #15**
- Feature Freeze: **ACTIVE**
- `DECISION.md`: **NOT RUN**
- New topologies, routing extensions, and Research/Production profile design: **deferred until EXP-001 completes**

Freeze policy: [EXP-001 Feature Freeze](experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md)

Execution handoff: [EXP-001 Execution Handoff](docs/EXP-001_EXECUTION.md)

Artifact capture: [EXP-001 Artifact Capture Guide](docs/EXP-001_ARTIFACT_CAPTURE.md)

DAT is currently in an **evidence-acquisition phase**, not a specification-expansion phase.

## Evidence base

DAT separates source claims from DAT interpretations and implementation decisions.

The initial knowledge base includes:

- OpenCollab
- TeamBench
- AsynCodeBench
- Anthropic multi-agent research

See [knowledge/sources.yaml](knowledge/sources.yaml).

## Status

**v0.2.1 Manual adoption-ready**

The repository currently provides:

- North Star, architecture, and glossary
- Role / topology / runtime / evaluation schemas
- P0 execution baseline and canonical T0–T3 topologies
- Routing and escalation policies
- Brownfield adoption protocol
- External project validator
- Runtime Binding / DAT Lock
- GitHub Actions integration template
- Runtime adapter contracts
- Initial knowledge base
- Schema and semantic validation CI
- EXP-001: T0 vs T1
- ExecutionTrace / RunEvaluation schemas
- Per-condition RunEvaluation summary

Manual adoption into external repositories is supported. Automatic runtime compile/apply and agent execution orchestration remain out of scope.

## Guiding principle

> **Do not assume a topology is better. Test it.**

## Contributing, support, and security

See [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Use the repository issue forms for bugs, proposals, and usage questions, and include reproducible evidence where possible.

For adoption and usage questions, see [SUPPORT.md](SUPPORT.md). Do not disclose sensitive vulnerabilities in a public issue; follow [SECURITY.md](SECURITY.md) instead.

## License

MIT
