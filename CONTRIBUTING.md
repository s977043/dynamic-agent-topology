# Contributing to Dynamic Agent Topology

Thanks for contributing to DAT.

DAT is an evidence-driven specification and experiment repository. Contributions should preserve the distinction between:

- external source claims;
- DAT interpretation;
- experiment evidence;
- normative specification;
- implementation decisions.

Untested topology choices must not be presented as universal best practices.

## Before opening a change

Check the current repository state first:

- read `docs/NORTH_STAR.md` and `docs/ARCHITECTURE.md`;
- check open Issues and Pull Requests for overlapping work;
- if your change touches an active experiment, read its freeze policy before editing anything.

For EXP-001 specifically, `experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md` is authoritative while the freeze is active. Do not change frozen prompts, scenarios, fixtures, topology definitions, schemas, metrics, matrix generation, or evaluation semantics unless the blocking-defect procedure is explicitly being followed.

## Choose the smallest useful contribution

Prefer a focused change with one clear purpose.

Good contributions include:

- correcting documentation without changing semantics;
- fixing reproducible validation defects;
- adding well-scoped research sources while separating source claims from DAT adoption;
- improving examples or adoption guidance;
- proposing a topology or policy together with a hypothesis and evaluation plan;
- adding tests for an existing contract.

Avoid combining unrelated refactors, research claims, topology changes, and experiment changes in one Pull Request.

## Evidence requirements

When proposing a behavior or design change, state:

1. the problem or observed friction;
2. the hypothesis;
3. the smallest useful change;
4. how the change can be evaluated;
5. what evidence would cause the proposal to be rejected.

For research-derived changes, distinguish:

- what the source actually claims;
- what DAT infers from it;
- what DAT adopts now;
- what remains a hypothesis.

A source citation is not evidence that a DAT design is effective.

## Experiment integrity

For controlled experiments:

- do not tune prompts, roles, topologies, scenarios, models, effort, metrics, or decision rules based on partial results;
- do not discard failed or inconclusive runs merely because they hurt the result;
- do not replace missing measurements with zeroes or estimates;
- do not treat agent self-assessment as stronger than deterministic or observable evidence;
- keep Builder / Reviewer / Verifier responsibilities separate where the experiment requires it.

If an active freeze has a blocking defect, stop the experiment and use the documented defect procedure instead of silently repairing the frozen artifact.

## Local validation

CI is the final repository-wide validation gate. For a typical change, install the validation dependencies with:

```bash
python -m pip install check-jsonschema jsonschema pyyaml
```

Then run the relevant checks. The broad semantic/test set is:

```bash
python scripts/validate_semantics.py
python scripts/validate_project.py --project examples/brownfield --dat-root .
python scripts/test_validate_project.py
python scripts/validate_experiments.py
python scripts/validate_fixtures.py
python scripts/test_validate_pilot.py
python scripts/test_operator_kit.py
python scripts/validate_experiment_freeze.py
python scripts/test_validate_experiment_freeze.py
```

Schema-specific changes should also run the corresponding `check-jsonschema` commands from `.github/workflows/spec-lint.yml`.

## Pull Request expectations

A Pull Request should explain:

- what changed;
- why it changed;
- what did not change;
- validation performed;
- evidence or source material used;
- whether any active experiment or freeze is affected.

If the change is experimental, include the hypothesis and expected evaluation method.

Do not claim improvement only because CI is green. Validation proves contract consistency; it does not prove that a topology, agent, or policy is more effective.

## Security and privacy

Follow `SECURITY.md`.

Do not commit:

- credentials or tokens;
- private source code or unrelated user data;
- private environment dumps;
- chain-of-thought or hidden reasoning;
- confidential prompts;
- unsanitized execution traces.

## Getting help

Use `SUPPORT.md` to choose the appropriate public support path. Security-sensitive reports must follow `SECURITY.md`.

## License

By contributing, you agree that your contribution is provided under this repository's MIT License.
