# Brownfield Adoption Protocol

DAT should enter existing projects without forcing a multi-agent rewrite.

| Stage | Name | Purpose |
|---|---|---|
| A0 | Assess | Inspect repository, CI, runtimes, existing agent config |
| A1 | Bind | Connect tests, lint, build, and other evidence |
| A2 | Observe | Measure current workflow without execution changes |
| A3 | Recommend | Produce topology recommendations only |
| A4 | Canary | Run constrained topology experiments |
| A5 | Dynamic | Enable evidence-based adaptation |

A5 is not the goal. The optimal steady state may be A2, A3, or a fixed T0/T1 topology.

## Project binding

```text
.dat/
├── project.yaml
├── policy.yaml
├── evidence.yaml
├── runtimes.yaml
├── dat.lock.yaml
├── overrides/
├── generated/
└── state/
```

`generated/` and `state/` should normally be excluded from Git.

Each stage should define entry, exit, and rollback criteria. Dynamic coordination must have explicit budgets for agents, transitions, tokens, and time.
