# Changelog

All notable user-facing changes to Dynamic Agent Topology (DAT) are documented here.

This project uses SemVer-style `MAJOR.MINOR.PATCH` version identifiers while the compatibility policy is still evolving. Repository `main` may contain unreleased work; a version is considered published only when an immutable Git tag and matching GitHub Release exist.

## Unreleased

## 0.3.0 — release candidate (unpublished)

Content candidate: `24fa06b1f7580205be56d7d1adc4634f8545d385`.

Previous boundary: historical content point `717a03fa389fb77a47694b9cf8a0c6e97ac0888b` (`0.2.1`, unpublished).

### Experiment status

- EXP-001 (T0 vs T1 pilot) completed 18 / 18 runs with recorded Run Artifacts; `DECISION.md` records **Keep T0**. This is a pilot-scope experiment conclusion, not a change to project adoption status and not evidence that T1, a Verifier, or any other Topology/Capability is effective or ineffective in general.

### Added

- EXP-001 pilot execution, artifact-capture, freeze, and operator guidance.
- EXP-001 18-run aggregation, `DECISION.md`, completed-snapshot audit, and documented one-time retry / recovery procedures.
- Pilot preparation and execution-attestation schemas and tooling.
- Deferred research notes for Raven / evidence-gated executable-configuration evolution, Claude Code Mods runtime guardrails, evidence-backed compiled-knowledge integrity, adversarial judgment gates, evidence-driven model escalation with compact handoff, and HydraFusion adaptive execution strategy.
- Knowledge Base navigation that separates source claims, deferred research candidates, and adopted design principles, plus an indexed Research Note intake/tracking surface.
- Dogfooding and EXP-001 execution/measurement guidance.
- Public contribution, support, research-proposal, and security-reporting paths.
- CodeQL, Dependabot, and OpenSSF Scorecard supply-chain checks.
- Scheduled read-only repository-settings drift audit with GitHub Actions summary/artifact evidence.
- Schema-validated repository-settings target contract for earlier configuration-error detection.
- Git-tracked public repository policy and release discipline.
- Engineering Layer Diagnostics for Prompt / Context / Harness / Loop / Graph / Evaluation failure localization.
- Documentation navigation and document-role guidance under `docs/README.md`.
- Development harness: agent guidance validation, a schema-validated Learning ledger (`schemas/learning-ledger.schema.json`), read-only harness metrics, scheduled Observe/Promote draft-PR workflows, and independent-review package tooling.
- Optional A0 Workflow Brief adoption guide, Fast Feedback workflow, practice-evolution policy, and environment / knowledge-ownership guidance.

### Changed

- EXP-001 preparation provenance is separated from runtime execution attestation.
- Security reporting and coordinated-disclosure expectations are explicit.
- GitHub Actions use least-privilege permissions and immutable action SHAs.
- Current README/CITATION metadata no longer advertises an unpublished version; version metadata is added only with an immutable tag and GitHub Release.
- Brownfield adoption now documents an evidence-based complexity-promotion rule instead of treating additional agents, loops, or graph structure as default progress.
- Human-facing supervision is clarified as a coordination cost: experiments should control or disclose materially different human-facing concurrency, while `human_interventions` remains a count rather than a cognitive-load metric.
- Agent operation follows a Human-on-the-loop (HOTL) autonomy boundary documented in `docs/AGENT_HARNESS.md`.
- The repository-settings target key `requiredApprovingReviewCount` is deprecated (still accepted) in favor of `requiredApprovingReviewCountExact`.
- Documentation terminology, source-of-truth boundaries, evidence claims, experiment semantics, and release-boundary wording were reviewed and hardened.

### Security

- Added CodeQL scanning and OpenSSF Scorecard reporting.
- Hardened workflow credentials and dependency pinning.
- Clarified that prompts and role names are not permission-enforcement boundaries.

## 0.2.1 — historical content point (unpublished)

Metadata date: `2026-10-04`.

Historical content point: `717a03fa389fb77a47694b9cf8a0c6e97ac0888b`.

### Added

- Manual brownfield adoption kit.
- Complete `.dat/` reference layout.
- Runtime Binding and DAT Lock contracts.
- External project validator.
- GitHub Actions integration example.
- Quick Start and manual-adapter guidance for supported runtimes.

### Changed

- Project adoption status moved to **Manual adoption-ready**.
- README and citation metadata moved to version `0.2.1`.

> Note: no immutable `v0.2.1` Git tag or GitHub Release had been published when this changelog was introduced. If the historical release is published later, the tag must point to the historical content point above rather than current `main`.

## Release integrity

Do not move a published version tag. If a released version needs additional fixes, publish a new patch or minor version.

See [Public repository policy](docs/PUBLIC_REPOSITORY_POLICY.md) and [Contributing](CONTRIBUTING.md) for the release process.
