# First T0 infrastructure retry — #51

## Scope and entry gate

This is a one-time exception to same-run reprepare/replay prohibition for
`EXP-001-train-normalize-name-r01-T0`, following independent review and merge of
this procedure and explicit recording in #15. It supersedes #51's initial stop
instruction only for the verified stopped invocation below. It does not use or
extend the pre-execution #48 exception.

Original session: `01a1095b-9caf-7691-a255-c0b434a5539a`.
Original observation commit: `d6d864e53ba149f36dc3efef97ac3e36583e6a78` (#52).

The source observation shows three sandbox-startup failures, exit 8, before any
inspection or test command executed. The fixture stayed unchanged and no patch
or RunEvaluation was created. Effective runtime/model/effort was Codex 0.160.0 /
gpt-6.1-sol / high. This is an infrastructure-failed session, not observed task
failure. If contrary evidence of executed commands, edits or task outcomes is
found, stop: this exception is inapplicable.

The CLI process and model were actually invoked; the original session must not
be relabeled as preparation-only or erased. Complete empirical runs are 0/18.

## Preserve before retry

1. In a clean isolated checkout, preserve all six original files, byte-for-byte,
   under `experiments/EXP-001-t0-vs-t1/runs/infrastructure-failures/EXP-001-train-normalize-name-r01-T0/01a1095b-9caf-7691-a255-c0b434a5539a/`.
   Keep the archive Git-tracked, record SHA-256 for each file, and verify against
   commit #52. Include metadata, original prompt, attestation, trace, evidence and
   STOP-REPORT. Never replace the failed attestation with new session facts.
2. Document old/new workspace identities and subsequent session identity in a
   recovery record. Matrix runId identifies the experimental slot; sessionId
   identifies this distinct invocation. Check identities against both canonical
   and archived attempts, not only the canonical validator's file set.
3. Preserve the original STOP-REPORT's no-replay instruction as historical
   evidence; reference this reviewed exception rather than editing history.

## Fresh preparation and preflight

After archival, use the unchanged frozen `prepare_pilot_run.py` to prepare the
same matrix slot with a new unique workspaceId and a nonexistent workspace
outside every DAT checkout. Do not modify frozen prompts, fixtures, matrix,
model/effort, role contracts, validators or evaluation semantics.

Require prompt byte equality against the archived prompt. Parsed preparation
metadata must match except `spec.workspaceId`. Require fresh workspace file set
and bytes to match the frozen fixture, and Feature Freeze validation to pass.
Independently review the archive and preparation diff before model invocation.
On preparation failure, preserve partial outputs, restore the original six-file
canonical run directory (including attestation, trace, evidence and STOP-REPORT),
and stop instead of automatically trying again.

Verify sandbox operation without a model in a separate diagnostic workspace:
allowed writes must succeed and forbidden writes must be denied. Do not reuse
the diagnostic wide-read profile as experimental permissions. Confirm the
declared Python evidence command can start in a sandbox, then confirm expected
initial Evidence FAIL on the new untouched experiment fixture.
Disable Python bytecode writes during preflight and recheck the workspace file
set and bytes immediately before model startup.

## Single permitted retry

Start one fresh Codex session with only the unchanged run prompt and fresh
fixture. Keep Codex 0.160.0, gpt-6.1-sol and high fixed. Use the normal experimental
workspace sandbox. Do not supply original messages, recovery notes, archived
artifacts or results to the Worker. No session resume/fork or cross-run feedback.

Save new attestation and result artifacts from observed facts. Verify actual
model/effort and unique sessionId. There is at most one retry authorized by this
exception, regardless of success, failure or infrastructure outcome. Any further
failure stops execution for a separately reviewed decision; never keep retrying
until pass. Task fail/inconclusive results are retained normally, not retried
under this infrastructure exception.

## Counting and next gate

The original stopped invocation remains reported as one infrastructure failure,
including its measured duration and usage. Report total attempted sessions and
complete matrix runs separately. A successful retry produces two attempted
sessions for this slot and at most one complete matrix run; it does not become
two repetitions. Do not include the infrastructure attempt as pass/fail in
`summarize_experiment.py`, consistent with the existing Artifact Capture Guide,
but always disclose it alongside the eventual 18-run summary and DECISION.

Archive preservation, attempt accounting and single-run result validation are
required before preparing T1. No T0/T1 superiority judgment before 18 valid
matrix runs. This procedure does not declare the pilot complete or unfreeze it.
