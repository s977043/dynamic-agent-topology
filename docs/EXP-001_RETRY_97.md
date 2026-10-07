# EXP-001 T1 r01 infrastructure retry — #97

## Status

This document authorizes **one fresh retry** for the matrix slot
`EXP-001-train-normalize-name-r01-T1` after the archived incomplete attempt
from session `01a1132a-1de0-70d2-b810-c500b79430c9`.

It is a slot-specific exception to the normal same-run replay prohibition. It
does not establish a general retry policy for EXP-001.

The retry is authorized only after this procedure is independently reviewed,
merged, and linked from Issue #15 / Issue #97.

## Classification

The archived attempt is classified as **infrastructure-aborted / incomplete**,
not as a task fail and not as a complete empirical Run.

Observed facts:

- the Worker started and changed `app.py`;
- the frozen deterministic Evidence command
  `python -m unittest discover -s tests` exited 127 twice;
- stderr reported `zsh: command not found: python`;
- no successful deterministic Evidence exists;
- the independent Verifier handoff did not complete;
- no execution attestation or RunEvaluation was created;
- PR #86 preserved the attempt separately and explicitly did not accept the Run
  or authorize retry.

The apparent quality of the partial patch is **not** evidence for retry
authorization and must not be used to decide whether to retry.

## Why a one-time retry is acceptable

Permanently dropping this slot would cap the fixed 18-slot matrix below the
existing 18 / 18 completion gate and break the paired r01 comparison.

Retrying until success would create survivorship / selection bias.

The narrow recovery is therefore:

1. preserve the original attempt permanently;
2. verify the frozen Evidence command is natively executable before model start;
3. use a fresh workspace and fresh Codex session;
4. keep every experimental treatment input unchanged;
5. allow exactly one new invocation for this slot;
6. consume the allowance when that Codex invocation starts, regardless of its
   outcome.

This decision is based on the environment-level exit 127 and incomplete
Artifact contract, not on whether the observed code edit appears correct.

## Immutable source record

The original attempt remains under:

`experiments/EXP-001-t0-vs-t1/runs/infrastructure-failures/EXP-001-train-normalize-name-r01-T1/01a1132a-1de0-70d2-b810-c500b79430c9/`

Its `SHA256SUMS` remains the preservation ledger. Do not edit or replace the
archived files as part of retry execution.

The canonical prepared `prompt.md` and archived `prompt.md` are byte-equivalent,
and the canonical / archived `run-meta.yaml` describe the same original
preparation. The retry must not expose the archive, partial patch, messages,
failure notes, or prior result to the new model session.

## Pre-invocation gates

Before the retry invocation:

1. Run Feature Freeze validation and stop on any drift.
2. Create a **new external fresh workspace** from the frozen fixture. Do not
   reuse the modified workspace from the aborted attempt.
3. Assign a new unique, non-secret workspaceId for the recovery workspace.
   Preserve the old workspaceId in the attempt record; do not overwrite history.
4. Reuse the exact canonical T1 prompt bytes. No prompt, task, topology, role,
   model, effort, fixture, scenario, metric, or Evidence-command change is
   permitted.
5. In the same normal experimental sandbox / command environment intended for
   the Run, confirm the literal command name `python` is natively resolvable.
   Do **not** add an alias, shim, symlink, PATH mutation, wrapper, or substitute
   `python3`.
6. On the untouched fresh fixture, execute the frozen deterministic Evidence
   command and require it to **start successfully and fail for the expected
   fixture behavior**. Exit 127, sandbox startup failure, or another
   environment-level failure is not the expected initial FAIL.
7. Reconfirm the fresh fixture file set / bytes immediately before model start.

If any pre-invocation gate fails, do not start Codex and do not consume the
single retry allowance. Record the stop in Issue #97.

## Single permitted retry

After all pre-invocation gates pass:

- start one fresh Codex session/context;
- use only the unchanged canonical T1 prompt as model input;
- keep Runtime / Model / Effort fixed to the Pilot contract;
- do not resume or fork the aborted session;
- do not provide prior attempt artifacts, patch, messages, review notes, or
  outcome information;
- preserve Worker / independent Verifier role boundaries;
- use the frozen deterministic Evidence command unchanged.

The retry allowance is consumed at the moment the new Codex invocation starts.

No automatic second retry is allowed.

## Outcome handling

If the retry produces a complete task fail or inconclusive result with the
required Artifact contract, preserve it as the empirical result for this slot.
Do not retry it because of the outcome.

If the retry hits another infrastructure abort or cannot complete the required
Artifact contract:

- preserve the new attempt separately;
- do not fabricate missing values;
- do not advance to the next matrix item automatically;
- stop for a new independently reviewed disposition.

If the retry completes:

1. capture execution attestation / trace / evaluation / patch / evidence from
   observed facts;
2. run single-run validation;
3. perform the manual cross-artifact consistency review;
4. require a reviewer comment
   `EXP-001 Run acceptance: ACCEPT` before advancing to the next matrix item.

## Accounting

The original aborted T1 invocation remains an attempted session and
infrastructure failure. It never becomes a pass/fail matrix result.

The retry is another attempted session for the **same matrix slot**, not another
repetition.

Continue reporting separately:

- attempted Codex sessions;
- infrastructure-aborted attempts;
- complete empirical Runs.

A completed retry can increase complete empirical Runs from 1 / 18 to 2 / 18,
but cannot erase the original aborted attempt.

## Freeze boundary

This procedure does not change any frozen EXP-001 Artifact or treatment
semantics. In particular it does not change:

- run matrix or order;
- Prompt / Scenario / Fixture;
- T0 / T1 Topology or Role Contracts;
- Runtime / Model / Effort;
- deterministic Evidence command;
- Schema / validator;
- Metric / evaluation semantics;
- Feature Freeze revision.

If executing this procedure would require any such change, stop and use the
Feature Freeze blocking-defect process instead.

## Next gate

This document authorizes only the one-time fresh retry for
`EXP-001-train-normalize-name-r01-T1`.

It does not authorize the following matrix slot. After retry execution, the
normal validation + Reviewer ACCEPT gate controls progression.
