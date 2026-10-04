# Release readiness

Use this checklist to decide whether the current `main` revision is ready to become a published DAT release.

A release is a **distribution boundary**, not evidence that an experiment succeeded. EXP-001 results and release readiness are reviewed independently.

## Candidate selection

Before opening a release PR:

- identify the exact candidate commit on `main`;
- choose the version from the user-visible compatibility/change boundary, not from commit count;
- confirm `CHANGELOG.md` accurately describes the candidate;
- confirm no frozen experiment input or evaluation semantic was changed unintentionally.

For the current post-0.2.1 line, evaluate `0.3.0` as the default candidate because the repository has gained material experiment-execution, attestation, documentation, and public-repository capabilities. This is a candidate, not a published version.

## Evidence gate

The candidate commit must have successful:

- `spec-lint / validate`;
- `codeql / Analyze Python`;
- `Scorecard supply-chain security / Scorecard analysis`.

A reviewer should also verify that failed, cancelled, or stale workflow runs are not being treated as successful evidence.

## Metadata gate

The release PR should:

- move relevant entries from `Unreleased` into the chosen version section;
- add the chosen version to `README.md` and `README_en.md` only when the release is actually being prepared;
- add matching `version` and `date-released` to `CITATION.cff`;
- keep adoption status separate from experiment conclusions.

Do not advertise a version on current `main` merely because a historical content point used that version.

## Publication gate

After the release PR is merged:

1. verify the merged commit is the intended release commit;
2. verify required CI/security workflows on that commit;
3. create immutable tag `vX.Y.Z` at that commit;
4. publish the matching GitHub Release;
5. verify README, changelog, citation metadata, tag, and GitHub Release agree.

If publication cannot be completed, revert or correct release metadata rather than leaving `main` claiming a release that does not exist.

## EXP-001 boundary

EXP-001 is currently evidence acquisition under feature freeze. Publishing DAT does not imply that T1, a verifier, or any other topology/capability has been proven effective.

Do not delay a repository release solely to manufacture a positive experiment result. Conversely, do not use a release to imply experimental validation that has not occurred.
