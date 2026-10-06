# Changelog

All notable user-facing changes to Dynamic Agent Topology (DAT) are documented here.

This project uses SemVer-style `MAJOR.MINOR.PATCH` version identifiers while the compatibility policy is still evolving. Repository `main` may contain unreleased work; a version is considered published only when an immutable Git tag and matching GitHub Release exist.

## Unreleased

### Added

- EXP-001 pilot execution, artifact-capture, freeze, and operator guidance.
- Pilot preparation and execution-attestation schemas and tooling.
- Raven / evidence-gated executable-configuration research notes.
- Dogfooding and EXP-001 execution/measurement guidance.
- Public contribution, support, research-proposal, and security-reporting paths.
- CodeQL, Dependabot, and OpenSSF Scorecard supply-chain checks.
- Git-tracked public repository policy and release discipline.
- Engineering Layer Diagnostics for Prompt / Context / Harness / Loop / Graph / Evaluation failure localization.
- Documentation navigation and document-role guidance under `docs/README.md`.

### Changed

- EXP-001 preparation provenance is separated from runtime execution attestation.
- Security reporting and coordinated-disclosure expectations are explicit.
- GitHub Actions use least-privilege permissions and immutable action SHAs.
- Current README/CITATION metadata no longer advertises an unpublished version; version metadata is added only with an immutable tag and GitHub Release.
- Brownfield adoption now documents an evidence-based complexity-promotion rule instead of treating additional agents, loops, or graph structure as default progress.
- Human-facing supervision is clarified as a coordination cost: experiments should control or disclose materially different human-facing concurrency, while `human_interventions` remains a count rather than a cognitive-load metric.
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
