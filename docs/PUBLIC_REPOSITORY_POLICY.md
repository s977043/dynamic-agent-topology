# Public repository policy

This document defines the **intended GitHub repository settings** for Dynamic Agent Topology (DAT). These settings live outside Git, so this file is a target-state policy, not proof that the settings are currently enforced.

## Compliance semantics

- A merged change to this file does **not** apply GitHub repository settings.
- Current state must be audited against GitHub repository settings, rulesets, branch protection, Actions permissions, and security settings.
- A difference between this policy and GitHub's current configuration is configuration drift and should be handled explicitly.
- Do not claim repository compliance based only on the presence of this document.

## Metadata

- Description: `Provider-agnostic specifications, experiments, and evidence for adaptive AI agent team topologies in software engineering.`
- Homepage: unset until a stable project site exists.
- Topics:
  - `ai-agents`
  - `multi-agent-systems`
  - `agentic-ai`
  - `software-engineering`
  - `ai-engineering`
  - `evaluation`
  - `benchmarking`
  - `llm`
  - `agent-topology`
- Wiki: disabled while `docs/` is the documentation source of truth.
- Discussions: disabled until community traffic justifies another support surface.

## Merge policy

- Squash merge: enabled.
- Merge commits: disabled.
- Rebase merge: disabled unless a concrete contributor workflow requires it.
- Automatically delete head branches: enabled.
- Auto-merge: enabled.
- Update branch: enabled.
- Squash commit title: prefer the pull request title.

## Default-branch rules

Protect `main` with a GitHub Repository Ruleset:

- require changes through pull requests;
- block force pushes;
- block branch deletion;
- require `validate`;
- require `Analyze Python`;
- require review conversations to be resolved;
- require branches to be up to date when the CI cost remains acceptable.

While DAT has only one active maintainer, do not require one approving review: authors cannot approve their own pull requests. Revisit this when an independent maintainer or reviewer is consistently available.

Any maintainer bypass should be narrow and reserved for recovery or urgent security remediation. Normal changes still use pull requests and CI.

## Safe application order

Repository settings are applied outside Git, so apply them in stages rather than changing every control at once.

1. **Metadata and collaboration surfaces**
   - set the repository description and topics;
   - keep the homepage unset;
   - disable Wiki;
   - keep Discussions disabled.
2. **Merge behavior**
   - keep squash merge enabled;
   - disable merge commits and rebase merge;
   - enable automatic branch deletion, auto-merge, update-branch, and PR-title-based squash titles.
3. **Re-audit before protection**
   - run the read-only settings audit again;
   - confirm the intended CI check names still resolve to `validate` and `Analyze Python`;
   - do not create a ruleset while the expected required-check identities are ambiguous.
4. **Default-branch ruleset**
   - target `main`;
   - require pull requests, conversation resolution, `validate`, and `Analyze Python`;
   - block force pushes and branch deletion;
   - keep the exact required approving-review count at `0` while there is only one active maintainer;
   - if a maintainer bypass is configured, keep it narrow and recovery-only; do not use it to make the normal merge path appear healthy;
   - require the branch to be up to date only after confirming the normal PR path still completes successfully.
5. **Verify with a disposable documentation PR**
   - confirm the PR can run both required checks;
   - confirm unresolved review conversations block merge when applicable;
   - confirm a current branch can be merged through the intended squash path;
   - confirm ordinary work completes without a maintainer bypass; if the test needs bypass to merge, treat the ruleset as misconfigured and stop.
6. **Security settings**
   - enable and verify the controls listed below with appropriately privileged account access.
7. **Strict re-audit**
   - after the staged changes, run the settings audit with `--strict`;
   - resolve `DRIFT` and investigate `UNKNOWN` rather than changing the target to match an accidental weaker state.

This sequence is an operational safety procedure, not a weaker target state. If a stage would lock out the normal PR + CI path, stop there, preserve the observed evidence, and correct that stage before applying later controls.

## Security settings

Enable and periodically verify:

- private vulnerability reporting;
- secret scanning;
- push protection;
- dependency graph;
- Dependabot alerts;
- Dependabot security updates.

Repository workflows should use least-privilege permissions and immutable action SHAs. OpenSSF Scorecard is evidence for improving supply-chain posture, not a target score to maximize.

## Release consistency

A version advertised in README or `CITATION.cff` must map to an immutable Git tag and GitHub Release. Never move an existing release tag to include later fixes; publish a new version instead.

Repository policy, release metadata, and the actual GitHub Release must describe the same boundary. If `main` has moved beyond the latest release, document that work as unreleased rather than rewriting the historical release point.

See [Release readiness](RELEASE_READINESS.md) for the candidate-to-publication gate.

## Audit checklist

The machine-readable target for settings that can be compared through the GitHub repository API is [`.github/repository-settings-target.yaml`](../.github/repository-settings-target.yaml). It is validated against [`schemas/repository-settings-target.schema.json`](../schemas/repository-settings-target.schema.json) in `spec-lint` and again when the audit command loads the target.

Run the read-only audit with:

```bash
python scripts/audit_repository_settings.py \
  --repository s977043/dynamic-agent-topology
```

Use `--strict` when drift or unavailable evidence should fail the command.

The audit distinguishes:

- `PASS` — observed state matches the target;
- `DRIFT` — observed state differs from the target;
- `UNKNOWN` — the API or current token cannot provide the required evidence.

The script covers repository metadata, collaboration surfaces, merge-policy switches, the default-branch protected flag, and observable default-branch ruleset semantics: pull-request enforcement, approving-review count, review-thread resolution, deletion and force-push blocking, required status checks, and strict/up-to-date status-check policy. Ambiguous ref patterns remain `UNKNOWN` rather than being guessed. It intentionally does **not** claim to verify security controls that require stronger permissions.

During an audit, also verify manually or with an appropriately privileged GitHub API token:

1. maintainer bypass scope and any ruleset behavior not represented in `.github/repository-settings-target.yaml`;
2. Actions workflow permissions and immutable action references;
3. private vulnerability reporting, secret scanning, push protection, dependency graph, Dependabot alerts, and security updates;
4. release tag / GitHub Release / `CITATION.cff` consistency.

Record configuration drift as an actionable issue or PR; do not silently update this document to match a weaker accidental state.

## Automated audit evidence

The [`Repository settings audit`](../.github/workflows/repository-settings-audit.yml) workflow runs the same read-only audit on a weekly schedule and through manual dispatch.

The scheduled workflow intentionally runs in non-strict mode:

- `DRIFT` remains visible evidence without making the workflow red simply because known configuration work is still open;
- `UNKNOWN` remains visible when the workflow token cannot prove a setting;
- repository metadata/API retrieval or audit execution failure still fails the workflow;
- the text report is written to the GitHub Actions job summary and retained as an artifact for 14 days.

The workflow does **not** mutate repository settings and does not close Issue #31 by itself. Before a stable release or when repository compliance is a release gate, run the audit with `--strict` using credentials that can observe the required settings, and review the manual security controls listed above.

## Audit cadence

Re-audit these settings:

- weekly through the read-only workflow;
- after initial public-repository setup;
- after changing maintainership or merge policy;
- after a material security finding;
- after the first external contribution;
- before a stable release.
