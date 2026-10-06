# Repository Guidelines

## Project Structure & Module Organization

DAT is a provider-agnostic specification and experiment repository, not an agent runtime. `schemas/` defines artifact contracts; `roles/`, `topologies/`, `policies/`, and `baselines/` hold machine-readable designs. `adapters/` describes runtime capabilities. `scripts/` contains Python validators and pilot utilities; `experiments/`, `fixtures/`, and `examples/` contain experiment plans, test inputs, and sample projects. Architecture and contributor decisions live in `docs/`, `knowledge/`, and `CONTRIBUTING.md`.

## Build, Test, and Development Commands

CI uses Python 3.12. Install validation tools with `python -m pip install -r requirements-ci.txt`. Run relevant checks from `.github/workflows/spec-lint.yml`; common checks are:

```bash
python scripts/validate_semantics.py
python scripts/validate_experiments.py
python scripts/validate_experiment_freeze.py
python scripts/test_validate_pilot.py
```

Run standalone tests as `python scripts/test_<area>.py`. Set `PYTHONDONTWRITEBYTECODE=1` when running Python against frozen fixtures.

## Coding & Artifact Conventions

Use four spaces in Python and descriptive `snake_case` names. Preserve existing YAML/JSON formatting and schema-first artifact conventions. Keep runtime-specific details in `adapters/`; do not mix topology, routing policy, role, permission, model, execution evidence, or evaluation responsibilities. Add deterministic validation when introducing a new artifact contract.

## Testing and Experiment Safety

Schema validity alone is insufficient; run semantic validators for affected artifacts. `experiments/EXP-001-t0-vs-t1/` is under Feature Freeze. Check the freeze before work and do not alter frozen prompts, roles, topologies, scenarios, fixtures, schemas, validators, or evaluation semantics without the documented blocking-defect process. EXP-001 runs require an Operator-created fresh external workspace and a fresh Codex session; do not substitute a regular Codex task or fabricate run artifacts.

## Commits and Pull Requests

Use concise conventional prefixes such as `docs:`, `schema:`, `fix:`, or `chore:`. Keep PRs focused and describe the problem, scope boundaries, exact validation results, compatibility or experiment impact, and supporting evidence. For design changes, state a falsifiable hypothesis. Follow `.github/pull_request_template.md` and `CONTRIBUTING.md`.

## Evidence and Security

Separate source claims, observed evidence, interpretation, and decisions. Preserve failed, aborted, and inconclusive runs as distinct outcomes. Never commit secrets, confidential prompts, private source code, or unsanitized traces; report security findings using `SECURITY.md`.
