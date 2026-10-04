# Dynamic Agent Topology (DAT)

> **Adaptive, evidence-driven agent topologies for AI software engineering.**  
> **Which agent topology works, under what conditions, and at what cost?**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status: v0.1 Foundation](https://img.shields.io/badge/Status-v0.1%20Foundation-orange.svg)](docs/NORTH_STAR.md)

Dynamic Agent Topology (DAT) is a provider-agnostic specification and testbed for designing, selecting, evaluating, and evolving AI agent team structures.

> **Use the simplest topology that reliably solves the task. Escalate coordination only when evidence justifies its cost.**

## What DAT is not

- **Not another static topology catalog.** Canonical topologies are hypotheses and baselines, not universal best practices.
- **Not another agent runtime.** DAT targets existing runtimes such as Claude Code, Codex, Gemini CLI, and Antigravity.
- **Not multi-agent maximalism.** Deterministic pipelines and single-agent execution are first-class baselines.
- **Not agent confidence as ground truth.** Deterministic and observable evidence outrank self-assessment wherever available.

## Evidence Loop

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

## Core dimensions

1. Role contract
2. Permission boundary
3. Context boundary
4. Explicit dependencies
5. Evidence
6. Routing & escalation
7. Topology adherence

## Canonical baselines

| ID | Shape | Purpose |
|---|---|---|
| P0 | Deterministic pipeline | Non-agent simplicity baseline |
| T0 | Single agent | Default low-coordination baseline |
| T1 | Worker → Verifier | Independent verification value |
| T2 | Worker → Reviewer → Verifier | Independent judgment value |
| T3 | Specialized team | High-complexity specialization hypothesis |

Dynamic routing is defined separately under `policies/`; it is not itself a topology.

## Brownfield adoption

```text
A0 Assess
→ A1 Bind evidence
→ A2 Observe
→ A3 Recommend
→ A4 Canary
→ A5 Dynamic
```

DAT adoption does **not** mean immediate multi-agent adoption. A project may intentionally stop at any stage.

See [docs/ADOPTION.md](docs/ADOPTION.md).

## Repository layout

- `docs/` — North Star, architecture, vocabulary, metrics, adoption
- `knowledge/` — evidence registry and adopted principles
- `schemas/` — machine-readable contracts
- `roles/` — canonical role contracts
- `topologies/` — baselines and topology hypotheses
- `policies/` — routing and escalation
- `adapters/` — runtime mappings
- `experiments/` — experimental protocol
- `harness/` — future execution/evaluation harness
- `examples/` — brownfield adoption examples

## Status

v0.1 is a **specification and testbed foundation**. Runtime adapters and the execution harness are intentionally incomplete until the contracts and evaluation protocol stabilize.

## License

MIT.
