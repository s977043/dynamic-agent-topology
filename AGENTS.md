# AGENTS.md

This file provides guidance to coding agents (Claude Code, Codex, Gemini CLI, etc.) when working in this repository.

## What this repo is

Dynamic Agent Topology (DAT): a provider-agnostic **specification + experiment base** for choosing and evaluating AI agent team structures. It is not an agent runtime. Most content is YAML specs validated against JSON Schemas, plus Python validator scripts. Docs are primarily Japanese (`README.md`), with `README_en.md` as the English counterpart — keep both in sync when changing user-facing content.

Core principle: use the simplest topology that reliably solves the task (P0 Deterministic Pipeline, T0 Single Agent are first-class baselines; T1 Worker→Verifier, T2 +Reviewer, T3 Specialized Team).

## Commands

Python 3.12. Setup: `python -m pip install -r requirements-ci.txt` (check-jsonschema, jsonschema, PyYAML).

The full validation suite is the step list in `.github/workflows/spec-lint.yml`; run the relevant steps locally. Common ones:

```bash
check-jsonschema --check-metaschema schemas/*.json
check-jsonschema --schemafile schemas/topology.schema.json topologies/canonical/*.yaml
python scripts/validate_semantics.py
python scripts/validate_experiments.py
python scripts/validate_fixtures.py
python scripts/validate_project.py --project examples/brownfield --dat-root .
python scripts/validate_experiment_freeze.py
```

Tests are plain executable scripts (no pytest); run a single one directly, e.g. `python scripts/test_validate_pilot.py`. Test files: `scripts/test_*.py`.

## Architecture

Five planes kept strictly separate (see `docs/ARCHITECTURE.md`):

| Plane                | Directory                                                                            |
| -------------------- | ------------------------------------------------------------------------------------ |
| Desired Organization | `topologies/`, `roles/`, `baselines/`                                                |
| Control Plane        | `policies/routing/`, `policies/escalation/`                                          |
| Runtime Mapping      | `adapters/<runtime>/capabilities.yaml` (claude-code, codex, gemini-cli, antigravity) |
| Observed Execution   | execution traces (`schemas/execution-trace.schema.json`)                             |
| Evaluation           | `schemas/evaluation.schema.json`, `experiments/`                                     |

Separation rules: Topology ≠ Routing Policy, Role ≠ Permission, Role ≠ Model, Runtime ≠ Model Provider, Reviewer ≠ Verifier. Dynamic routing is a policy, never a topology.

Every YAML kind has a schema in `schemas/`; schema validity is necessary but `scripts/validate_*.py` add cross-file semantic checks. When adding a new YAML kind or directory, wire it into `spec-lint.yml`.

`fixtures/` holds intentionally-failing inputs that validators must reject. `examples/brownfield/.dat/` demonstrates external-project adoption (A0–A5 stages, `docs/ADOPTION.md`).

## Experiment freeze (important)

`experiments/EXP-001-t0-vs-t1/` is under **Feature Freeze**, enforced by `scripts/validate_experiment_freeze.py` against blob SHAs in `pilot/freeze.yaml`. Do not change experiment inputs, evaluation semantics, prompts, roles, scenarios, fixtures, or frozen validators without checking the freeze; propose post-freeze changes separately. `pilot/run-matrix.yaml` must match `generate_pilot_matrix.py` output deterministically.

The EXP-001 pilot is executed by an Operator in a fresh external workspace and a fresh Codex session (`docs/EXP-001_EXECUTION.md`, `pilot/OPERATOR.md`). Do not launch Codex yourself as a substitute, re-prepare an existing runId, or generate result artifacts without a real run.

## Contribution rules (from CONTRIBUTING.md)

- Separate external source claims, observed evidence, DAT interpretation, and decisions. A citation is not evidence a design works.
- Never fabricate evidence or fill unknown values with guesses; failed/aborted/inconclusive runs must stay distinguishable from successes.
- Topology/routing/role/verifier/experiment-method changes need a falsifiable hypothesis.
- Releases follow `docs/RELEASE_READINESS.md`: never move a published tag; keep README / `CHANGELOG.md` / `CITATION.cff` / tag / GitHub Release on the same boundary.
- Use `.github/pull_request_template.md` for PRs.
