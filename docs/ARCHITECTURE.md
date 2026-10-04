# Architecture

DAT separates five planes.

```text
Desired Organization
  topology + role contracts + constraints
            │
            ▼
Control Plane
  routing + escalation policy
            │
            ▼
Runtime Mapping
  adapter + capability resolution
            │
            ▼
Observed Execution
  trace + handoffs + violations
            │
            ▼
Evaluation
  evidence + metrics + decision
```

## Separation rules

- Topology ≠ routing policy
- Role ≠ permission
- Role ≠ model
- Runtime ≠ model provider
- Reviewer ≠ verifier
- Verifier ≠ evidence
- Declared topology ≠ observed execution

A topology defines nodes, relationships, dependencies, and structural constraints. Runtime-specific models, commands, and configuration belong in adapters/project bindings.
