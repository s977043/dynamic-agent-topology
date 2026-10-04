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

During an audit, verify at least:

1. repository metadata and enabled collaboration surfaces;
2. allowed merge methods and branch cleanup behavior;
3. `main` ruleset / branch protection and required checks;
4. Actions workflow permissions and immutable action references;
5. security features and Dependabot configuration;
6. release tag / GitHub Release / `CITATION.cff` consistency.

Record configuration drift as an actionable issue or PR; do not silently update this document to match a weaker accidental state.

## Audit cadence

Re-audit these settings:

- after initial public-repository setup;
- after changing maintainership or merge policy;
- after a material security finding;
- after the first external contribution;
- before a stable release.
