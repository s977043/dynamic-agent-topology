# North Star

## Core question

> **Which agent topology works, under what conditions, and at what cost?**

> **Do not assume a topology is better. Test it.**

## Ten engineering principles

1. **Minimal Team First** — default to P0 or T0; added coordination must earn its cost.
2. **Dynamic means Select, Escalate, De-escalate, Recompose** — v0.1 focuses on selection and escalation.
3. **Role ≠ Model ≠ Runtime** — responsibility, model choice, and execution engine are independent.
4. **Role Contract ≠ Permission Enforcement** — prompts express intent; runtime capabilities enforce boundaries.
5. **Builder ≠ Judge** — non-trivial work separates authoring from independent judgment.
6. **Verifier ≠ Ground Truth** — evidence outranks verifier confidence where stronger checks exist.
7. **Context Isolation by Default** — use scoped context and explicit artifacts.
8. **Explicit Dependency Modeling** — make handoffs auditable.
9. **Observable Collaboration** — measure adherence, violations, handoffs, cost, and outcomes.
10. **Ablation Before Adoption** — roles and topologies earn standard status through measured marginal value.

## Non-goals

DAT is not a generic agent framework, prompt library, model benchmark, or mandate to maximize agent count.

## v0.1 scope

Vocabulary, schemas, baseline topologies, evidence sources, brownfield adoption stages, and runtime adapter contracts.

## v0.2 scope

Reproducible experiment definitions, train/test/regression scenario separation, ExecutionTrace and RunEvaluation contracts, EXP-001 (T0 vs T1), and a minimal artifact validation/summary harness.
