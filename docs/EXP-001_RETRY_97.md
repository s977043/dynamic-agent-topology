# T1 r01 infrastructure-aborted retry — #97

## Decision

`EXP-001-train-normalize-name-r01-T1` may receive **one fresh retry** only after this procedure is independently reviewed, merged, and recorded in Issue #15.

This is a narrow exception to the normal same-run replay prohibition. It does not change the EXP-001 Feature Freeze, matrix, Prompt, Fixture, Topology, Role, Runtime, Model, Effort, Evidence command, Metric, or evaluation semantics.

Original observed session: `01a1132a-1de0-70d2-b810-c500b79430c9`.

Archived attempt: `experiments/EXP-001-t0-vs-t1/runs/infrastructure-failures/EXP-001-train-normalize-name-r01-T1/01a1132a-1de0-70d2-b810-c500b79430c9/`.

## Why this attempt is not a task result

The preserved archive records that:

- the Worker inspected the fixture and changed `app.py` from `.strip().upper()` to `.strip().lower()`;
- the frozen deterministic Evidence command `python -m unittest discover -s tests` was attempted twice;
- both attempts exited `127` with `zsh: command not found: python`;
- no successful deterministic Evidence was obtained;
- the independent Verifier handoff did not complete;
- no execution attestation or RunEvaluation was created;
- model / effort / timing were not independently verified from the retained archive.

The implementation edit means this is **not** equivalent to the first T0 sandbox-startup stop in #51. However, exit 127 means the required Evidence command did not execute, so the attempt cannot be classified as an observed task pass or task fail under the frozen contract.

The observed patch must not be used as success Evidence. Retry eligibility is based only on command unavailability and incomplete Run evidence, not on whether the archived patch appears correct.

## Bias control

This exception is defined after observing an incomplete attempt, so it must not become a general keep-retrying-until-pass rule.

To limit selection and survivorship bias:

1. preserve the original attempt permanently and disclose it in final attempt accounting;
2. authorize exactly one new invocation for this matrix slot;
3. use a fresh workspace and fresh session with no resume, fork, or cross-run feedback;
4. do not provide the archived patch, messages, event summary, retry rationale, or prior outcome to the Worker or Verifier;
5. do not manually edit the fresh fixture or provide task-specific human guidance;
6. accept the retry's observed task outcome even if it is FAIL or INCONCLUSIVE, provided the Run contract is complete and reviewer acceptance determines it is a valid empirical Run;
7. if the retry is again infrastructure-aborted or cannot satisfy the Run contract, do not retry automatically; stop for a new reviewed completion/disposition decision.

The retry is therefore not conditional on obtaining a better task result.

## Preserve before retry

Before any new preparation or model invocation:

1. verify the archived `SHA256SUMS` against all six archived files;
2. verify archived `prompt.md` and `run-meta.yaml` remain the originally reviewed preparation record;
3. keep the archived `patch.diff`, Evidence failure, STOP report, and event summary unchanged;
4. record that the raw source event log is not Git-tracked and that reviewers cannot independently recompute every event fact from the sanitized archive alone;
5. keep the canonical complete empirical count at **1 / 18**.

Do not rewrite the archive to match the retry.

## Fresh preparation

After this procedure is merged, prepare the same matrix slot with the unchanged frozen `prepare_pilot_run.py` using:

- a new unique opaque `workspaceId`;
- a nonexistent external workspace path;
- the same runId / blockId / scenario / condition / repetition / executionOrder;
- a Prompt byte-identical to the archived and canonical Prompt;
- a fresh workspace byte-identical to the frozen fixture before preflight.

The existing canonical preparation may be replaced only as part of this reviewed retry exception. Preserve the old preparation in the existing infrastructure-failure archive first. If preparation fails, preserve partial outputs and stop; do not automatically try again.

## Non-model preflight

Before consuming the retry allowance, use the **normal experimental execution environment** without a model to verify that the frozen Evidence command is actually runnable.

Required preflight:

1. Feature Freeze validation PASS;
2. fresh fixture file set/content matches the frozen fixture;
3. `python` resolves in the environment used for the experimental session;
4. the exact frozen command `python -m unittest discover -s tests` starts and reaches the tests;
5. on the untouched fixture, the command produces the expected initial test failure caused by the known fixture defect, not exit 127, sandbox startup failure, or another environment failure;
6. preflight does not modify implementation files; suppress incidental Python bytecode writes and recheck fixture bytes afterwards.

If any preflight item fails, do not start the model and do not consume the retry allowance. Record the environment problem in Issue #15.

Do not replace the frozen command with `python3` or another command merely because it is available.

## Single permitted retry

The retry allowance is consumed when the fresh Codex model invocation starts.

Run exactly the frozen T1 contract:

- Runtime: Codex;
- Model: GPT-6.1 Sol;
- Effort: High;
- Worker → independent Verifier topology;
- original T1 Prompt only;
- fresh session;
- cross-run feedback disabled.

After execution, capture only observed facts. Verify actual runtime/model/effort/session identity in the execution attestation. Preserve Trace, Evaluation, patch, and deterministic Evidence according to the existing Artifact Capture procedure.

No second retry is authorized by this exception.

## Acceptance and progression

A retry does not become a complete empirical Run merely because the command can execute.

Before advancing to the next matrix item:

1. the retry must have the complete required Artifact set;
2. single-run `validate_pilot.py --run-id EXP-001-train-normalize-name-r01-T1` must PASS;
3. manual cross-artifact review must be completed;
4. a reviewer must record `EXP-001 Run acceptance: ACCEPT`.

If the retry produces a valid observed task failure or inconclusive result with complete artifacts, retain that result; do not retry to seek a PASS.

If the retry is infrastructure-aborted or incomplete, it does not count as a complete Run and execution pauses for a separately reviewed decision because the frozen 18 / 18 completion condition would remain unsatisfied.

## Attempt accounting

Keep these quantities separate:

- attempted model sessions;
- infrastructure-aborted / incomplete attempts;
- accepted complete empirical Runs.

The original T1 attempt remains visible regardless of retry outcome. A successful retry would make this matrix slot have two attempted sessions but at most one accepted complete empirical Run.

Final EXP-001 reporting must disclose the extra T1 attempt and the fact that this retry exception was introduced after an infrastructure-aborted attempt. Do not present the eventual 18 accepted Runs as if exactly 18 model invocations occurred.

## Non-goals

This procedure does not:

- accept the archived T1 attempt as a task result;
- change the frozen Evidence command;
- change the Feature Freeze revision;
- weaken the 18 / 18 completion gate;
- authorize retries for any other matrix slot;
- authorize repeated infrastructure retries;
- permit use of the previous T1 patch or messages as Worker/Verifier context;
- make any T0/T1 superiority judgment.
