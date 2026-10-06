## Summary

<!-- What changes in this PR? Keep scope explicit. -->

## Why

<!-- Problem, hypothesis, evidence, or maintenance reason. -->

## Scope

- In scope:
- Out of scope:

## Validation

<!-- Exact commands, CI jobs, or manual checks performed. -->

```text
# paste concise results here
```

## Evidence / compatibility impact

<!-- Note schema compatibility, runtime impact, experiment impact, or why there is none. -->

## EXP-001 feature-freeze check

- [ ] This PR does not change frozen EXP-001 inputs or evaluation semantics.
- [ ] If it does, the blocking-defect process and freeze revision rules were followed.
- [ ] Not applicable.

## Security / privacy

- [ ] No secrets, private source code, confidential prompts, or unsanitized traces are included.
- [ ] GitHub Actions and other executable dependencies are least-privilege and pinned where practical.
- [ ] Not applicable.

## Checklist

- [ ] I kept the change as small as practical.
- [ ] I updated documentation when behavior or contracts changed.
- [ ] I added or updated deterministic validation where appropriate.
- [ ] I separated observed evidence from interpretation and judgment.


<details>
<summary>EXP-001 empirical Run PR — fill only when this PR adds or updates a canonical Run result</summary>

## EXP-001 Run acceptance review

Run ID: `<runId>`

### Run integrity

- [ ] This PR preserves the active Feature Freeze and does not change Prompt / Scenario / Fixture / Topology / Role / Model / Effort / evaluation semantics.
- [ ] The execution attestation records a fresh workspace/session boundary and no cross-run feedback, and the observable artifacts do not contradict it. This is attestation evidence, not independent proof.
- [ ] Preparation provenance is preserved; this PR does not silently replace a previous attempt.
- [ ] Failed / aborted / infrastructure attempts, if any, remain separately preserved and are not counted as complete Runs.

### Cross-artifact consistency review

Use `N/A` only when the corresponding optional observation was not recorded. The PR author records observable consistency results; the final reviewer conclusion is added only after review.

```text
- runId: <runId>
- execution-attestation ↔ trace session/freshness/cross-run fields: PASS | N/A | BLOCKED
- attested timestamps ↔ trace start/finish: PASS | N/A | BLOCKED
- trace token summary ↔ evaluation efficiency: PASS | N/A | BLOCKED
- prompt / frozen-condition drift: NONE | BLOCKED
- sensitive-data / hidden-reasoning scan: PASS | BLOCKED
- single-run validation: PASS | FAIL
```

### Reviewer judgment

The reviewer records the final judgment in a review comment after checking the evidence above.

```text
EXP-001 Run acceptance: ACCEPT | BLOCK
Reason: <concise evidence-based reason>
```

### Acceptance boundary

- [ ] A review comment records `ACCEPT`; this means only that this Run can be accepted as a complete EXP-001 empirical Run.
- [ ] No T0/T1 superiority or topology-quality judgment is made from this individual Run.
- [ ] The next matrix item will not start until this Run is accepted.

Reference: `docs/EXP-001_ARTIFACT_CAPTURE.md#manual-review-record`

</details>
