# AGENTS.md

Guidance for coding agents working in this repository. Tool-specific additions live in `CLAUDE.md`, `.claude/`, and `.codex/`.

## What this repo is

Dynamic Agent Topology (DAT): a provider-agnostic **specification + experiment base** for choosing and evaluating AI agent team structures, also distributed as two skills (`skills/`) packaged as a plugin. It is not an agent runtime and does not auto-apply runtime configuration (adapters are manual). Content is YAML specs validated against JSON Schemas, Python validators in `scripts/`, and Japanese-first docs (`README.md` ↔ `README_en.md` must stay in sync).

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

Tests are standalone scripts, not pytest: `python scripts/test_<area>.py`. `PYTHONDONTWRITEBYTECODE=1` keeps runs from leaving `__pycache__` inside frozen fixtures; tool settings already set it, and in environments without them set it yourself. Verify new or changed scripts with Python 3.12 (CI's version) before reporting them as passing; for example, `Path.glob` with a trailing `**` returns only directories on 3.12, and 3.13+ APIs such as `PurePath.full_match` are unavailable.

When adding a new artifact kind, add its schema in `schemas/`, a semantic check if it has cross-file references, and wire both into `spec-lint.yml`. Schema validity alone is not sufficient.

## Architecture boundaries

`docs/ARCHITECTURE.md` separates five planes: Desired Organization (`topologies/`, `roles/`, `baselines/`) → Control Plane (`policies/`) → Runtime Mapping (`adapters/<runtime>/`) → Observed Execution (traces) → Evaluation (`experiments/`). Do not merge concerns across them: Topology ≠ Routing Policy, Role ≠ Permission, Role ≠ Model, Runtime ≠ Model Provider, Reviewer ≠ Verifier. Runtime-specific details belong only in `adapters/`.

`skills/` holds distribution skills in the runtime-shared SKILL.md format: they summarize the relevant parts of the specification as usage procedures and link to the canonical files, but never redefine topologies, routing/escalation rules, or RunObservation decision rules; the canonical files win on any conflict. `.claude-plugin/` and `.codex-plugin/` are distribution packaging only, not Runtime Mapping. Runtime-specific ways of obtaining values stay in `adapters/`.

## EXP-001 Feature Freeze

EXP-001 Feature Freeze is completed at revision 3; its historical experiment inputs remain immutable. `pilot/freeze.yaml` lists the frozen files (experiment, prompts, scenarios, `fixtures/exp-001/`, T0/T1 topologies, worker/verifier roles, schemas, pilot scripts) and `validate_experiment_freeze.py` enforces blob SHAs while the freeze is active; after completion, `audit_exp001_completed_snapshot.py` checks the original snapshot blob SHAs. Non-listed files such as `pilot/FREEZE.md`, `OPERATOR.md`, `RUNBOOK.md`, and `runs/` are not frozen.

- Do not edit frozen files or rewrite EXP-001 evidence. Stop affected EXP-001 execution on a blocking defect and follow the exception procedure in `pilot/FREEZE.md`, which records the completed freeze. General post-pilot work is not automatically blocked by the historical freeze; new research follows its own applicable Gates and the autonomy boundaries below.
- Pilot runs are executed by an Operator in a fresh external workspace and a fresh model session using the runtime fixed by the pilot spec (`docs/EXP-001_EXECUTION.md`, `experiments/EXP-001-t0-vs-t1/pilot/OPERATOR.md`). Normal runs are executed by the Operator. Agents must not start that session in the Operator's place, except for the EXP-001 one-time retry model launch (consuming the retry allowance) under all HOTL conditions in `docs/AGENT_HARNESS.md`: every Gate and preflight in the procedure passes mechanical checks, a Reviewer Judgment is recorded, the retry is unconsumed, Runtime/Model/Effort are fixed, duplicate launches are prevented, and the attestation, trace, and Evidence are preserved; on any anomaly the Agent stops and makes no further launch. Agents must not re-prepare an existing `runId`; the only exceptions are Operator-controlled operations under the documented procedures (the #48 pre-measurement recovery and the #51 limited retry in `OPERATOR.md` §3 and `docs/EXP-001_RETRY_51.md`, and the T1 r01 one-time retry in `docs/EXP-001_RETRY_T1_R01.md`). Agents must not create result artifacts without a real run.
- Issue #15 is the live run status; docs only record checkpoints and may lag behind it.

## Evidence discipline

- Keep source claims, observed evidence, DAT interpretation, and decisions separate. A citation is not evidence that a design works.
- Never fabricate evidence or fill unknowns with guesses; failed, aborted, and inconclusive runs stay distinguishable from successes.
- `knowledge/research/` notes are candidates, not adopted contracts. Adopting a source requires DAT-side evidence and updating `knowledge/sources.yaml` plus the affected artifacts in the same change.
- `docs/PUBLIC_REPOSITORY_POLICY.md` describes target GitHub settings; it does not apply them. Compliance is checked by `scripts/audit_repository_settings.py`.

## Changes and PRs

- Record recurring failures and review findings in the Learning ledger of `docs/AGENT_HARNESS.md`.
- Autonomy follows the HOTL rules in `docs/AGENT_HARNESS.md` (the source of truth; this is a summary). Agents may merge a PR other than a rule-change PR (docs, experiments, code, and dependency additions included) when all required CI passes, an independent review in a session other than the one that created the PR (preferably a different model; required for dependency additions) has no unresolved required findings, and it includes nothing human-only. Rule-change PRs change `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.codex/`, the rules in `docs/AGENT_HARNESS.md`, `scripts/validate_agent_guidance.py`, or guard hooks or check scripts; agents draft them, get an independent review by a different model, state in the PR body when a change weakens a check, and link the PR in issue #159, and a human merges them, because the same actor could otherwise arrange its own review and merge. Revisit this when GitHub protection rules can enforce a review by another actor. For every PR, record the reviewed head, diff, verdict, and CI result in the PR. Human-only: merging rule-change PRs, Feature Freeze revisions and frozen-file changes, creating releases/tags, force pushes, deleting branches/files/issues, creating/rotating/deleting/exposing secrets or granting access to them, changing GitHub branch protection/rulesets/required checks, and approving budgets or launching billed model sessions (Operator); the EXP-001 retry exceptions above still apply, limited to the documented retry procedures. Ask a human only for these or when a STOP condition in `docs/AGENT_HARNESS.md` is hit; otherwise decide, proceed, and report. Humans can order a stop or a revert at any time; agents record each merged PR and the basis for the decision in the PR or issue.
- Never approve what your own session produced. Hand an independent review to a fresh session, passing the decision material as files or links, not summaries.
- Commit messages and PR titles start with a conventional prefix such as `docs:`, `schema:`, `audit:`, `ci:`, `fix:`, `chore:`. Write PR titles, PR bodies, issues, and review comments in Japanese; keep the prefix and code identifiers as-is.
- One branch, one agent. Shared refs can still be touched by others: fetch right before pushing, confirm the current branch, push with `--force-with-lease=<branch>:<known sha>`, and stop if the worktree has changes you did not make.
- Do not switch the global CLI or auth account; pass credentials per command.
- After editing, check `git diff` for unintended changes (for example, a formatting hook rewriting a hash table).
- Fill `.github/pull_request_template.md`, including the freeze check. Topology/routing/role/verifier/experiment-method changes need a falsifiable hypothesis.
- Releases follow `docs/RELEASE_READINESS.md`: never move a published tag.
- Never commit secrets, private source code, confidential prompts, or unsanitized traces; report vulnerabilities via `SECURITY.md`.
