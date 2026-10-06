# AGENTS.md

Guidance for coding agents working in this repository. Tool-specific additions live in `CLAUDE.md`, `.claude/`, and `.codex/`.

## What this repo is

Dynamic Agent Topology (DAT): a provider-agnostic **specification + experiment base** for choosing and evaluating AI agent team structures. It is not an agent runtime and does not auto-apply runtime configuration (adapters are manual). Content is YAML specs validated against JSON Schemas, Python validators in `scripts/`, and Japanese-first docs (`README.md` ↔ `README_en.md` must stay in sync).

Core principle: use the simplest topology that reliably solves the task. P0 Deterministic Pipeline and T0 Single Agent are first-class baselines; T1 Worker→Verifier, T2 +Reviewer, T3 Specialized Team are hypotheses to test, not best practices.

## Validation

Python 3.12; `python -m pip install -r requirements-ci.txt`. `.github/workflows/spec-lint.yml` is the source of truth for the validation suite — run the steps relevant to what you touched. Frequently needed:

```bash
python scripts/validate_semantics.py
python scripts/validate_experiments.py
python scripts/validate_fixtures.py
python scripts/validate_experiment_freeze.py
python scripts/validate_project.py --project examples/brownfield --dat-root .
```

Tests are standalone scripts, not pytest: `python scripts/test_<area>.py`. Set `PYTHONDONTWRITEBYTECODE=1` so runs do not leave `__pycache__` inside frozen fixtures.

When adding a new artifact kind, add its schema in `schemas/`, a semantic check if it has cross-file references, and wire both into `spec-lint.yml`. Schema validity alone is not sufficient.

## Architecture boundaries

`docs/ARCHITECTURE.md` separates five planes: Desired Organization (`topologies/`, `roles/`, `baselines/`) → Control Plane (`policies/`) → Runtime Mapping (`adapters/<runtime>/`) → Observed Execution (traces) → Evaluation (`experiments/`). Do not merge concerns across them: Topology ≠ Routing Policy, Role ≠ Permission, Role ≠ Model, Runtime ≠ Model Provider, Reviewer ≠ Verifier. Runtime-specific details belong only in `adapters/`.

## EXP-001 Feature Freeze

`experiments/EXP-001-t0-vs-t1/` is frozen; `pilot/freeze.yaml` lists every frozen file (experiment, prompts, scenarios, `fixtures/exp-001/`, T0/T1 topologies, worker/verifier roles, schemas, pilot scripts) and `validate_experiment_freeze.py` enforces blob SHAs.

- Do not edit frozen files. A blocking defect stops execution and follows the freeze exception procedure in `pilot/FREEZE.md`; everything else is a post-EXP-001 proposal tracked in an issue.
- Pilot runs are executed by an Operator in a fresh external workspace and fresh Codex session (`docs/EXP-001_EXECUTION.md`, `pilot/OPERATOR.md`). Agents must not start that session in the Operator's place, re-prepare an existing `runId`, or create result artifacts without a real run.
- Issue #15 is the live run status; docs only record checkpoints and may lag behind it.

## Evidence discipline

- Keep source claims, observed evidence, DAT interpretation, and decisions separate. A citation is not evidence that a design works.
- Never fabricate evidence or fill unknowns with guesses; failed, aborted, and inconclusive runs stay distinguishable from successes.
- `knowledge/research/` notes are candidates, not adopted contracts. Adopting a source requires DAT-side evidence and updating `knowledge/sources.yaml` plus the affected artifacts in the same change.
- `docs/PUBLIC_REPOSITORY_POLICY.md` describes target GitHub settings; it does not apply them. Compliance is checked by `scripts/audit_repository_settings.py`.

## Changes and PRs

- Commit/PR titles are English with prefixes such as `docs:`, `schema:`, `audit:`, `ci:`, `fix:`, `chore:`.
- Fill `.github/pull_request_template.md`, including the freeze check. Topology/routing/role/verifier/experiment-method changes need a falsifiable hypothesis.
- Releases follow `docs/RELEASE_READINESS.md`: never move a published tag.
- Never commit secrets, private source code, confidential prompts, or unsanitized traces; report vulnerabilities via `SECURITY.md`.
