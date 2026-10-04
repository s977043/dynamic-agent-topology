# Release readiness

Use this checklist to decide whether a DAT revision is ready to become a published release.

A release is a **distribution boundary**, not evidence that an experiment succeeded. EXP-001 results and release readiness are reviewed independently.

## Source of truth

This document is the operational release checklist. `CHANGELOG.md` records user-visible change history, `CITATION.cff` records citation metadata, and Git tags / GitHub Releases define the published immutable boundary.

If these sources disagree, stop publication and reconcile them before creating or moving any release reference.

## Candidate selection

Before opening a release PR:

- identify the exact candidate commit on `main`;
- compare it with the previous published release, or with the documented historical content point when no release exists yet;
- choose the version from the user-visible compatibility/change boundary, not from commit count;
- confirm `CHANGELOG.md` accurately describes the candidate;
- confirm no frozen experiment input or evaluation semantic was changed unintentionally.

### Current post-0.2.1 line

`0.3.0` is a **working candidate**, not a default or published version. The current line contains material additive changes beyond the historical unpublished `0.2.1` content point, including experiment-execution / attestation tooling and public-repository capabilities. The final version must still be decided in the release PR from the actual candidate diff and the project's evolving compatibility policy.

Do not publish `v0.2.1` from current `main`. If the historical `0.2.1` release is ever published, its tag must point to the historical content point documented in `CHANGELOG.md`.

## Evidence gate

The exact candidate commit must have successful:

- `spec-lint / validate`;
- `codeql / Analyze Python`.

Review OpenSSF Scorecard as supply-chain evidence. If the candidate changes workflows, dependencies, permissions, or other supply-chain posture, require a successful Scorecard run for that candidate commit. Otherwise, a recent successful scheduled/main result may be used when its revision and freshness are recorded in the release review.

A reviewer must verify that failed, cancelled, skipped, stale, or superseded workflow runs are not being treated as successful evidence.

## Metadata gate

The release PR should:

- move relevant entries from `Unreleased` into the chosen version section;
- keep README status/version wording consistent with the release; version-neutral README wording may remain version-neutral;
- add matching `version` and `date-released` to `CITATION.cff` when publication is being prepared;
- keep adoption status separate from experiment conclusions;
- record the intended release commit and version in the PR description.

`date-released` must represent the actual publication date. Do not leave release metadata on `main` indefinitely if the corresponding tag and GitHub Release are not published.

## Publication gate

After the release PR is merged, treat the repository as **publication pending** until the tag and GitHub Release exist:

1. verify the merged commit is exactly the intended release commit;
2. verify required CI/security evidence for that commit according to the Evidence gate;
3. create immutable tag `vX.Y.Z` at that commit;
4. publish the matching GitHub Release from that tag;
5. verify README, `CHANGELOG.md`, `CITATION.cff`, tag, and GitHub Release describe the same version boundary.

Never move an existing published version tag to a different commit. Publish a new version instead.

## Publication failure

Keep the publication-pending interval short. If tag or GitHub Release publication cannot be completed:

- do not retarget an existing tag;
- do not claim the release is published;
- fix the publication blocker or revert/correct versioned metadata on `main`;
- document the interruption in the release PR or follow-up issue when it affects the public release boundary.

## EXP-001 boundary

EXP-001 is currently evidence acquisition under feature freeze. Publishing DAT does not imply that T1, a Verifier, or any other Topology/Capability has been proven effective.

Do not delay a repository release solely to manufacture a positive experiment result. Conversely, do not use a release to imply experimental validation that has not occurred.
