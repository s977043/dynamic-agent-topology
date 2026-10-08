# EXP-001 T1 r01 one-time infrastructure retry — #97

## Scope

This is a one-time reviewed exception for:

`EXP-001-train-normalize-name-r01-T1`

Original incomplete session:

`01a1132a-1de0-70d2-b810-c500b79430c9`

The original attempt is preserved under:

`experiments/EXP-001-t0-vs-t1/runs/infrastructure-failures/EXP-001-train-normalize-name-r01-T1/01a1132a-1de0-70d2-b810-c500b79430c9/`

This exception does not generalize to other Runs.

## Classification

The retained attempt shows:

- Worker changed `app.py` from `.strip().upper()` to `.strip().lower()`.
- The frozen deterministic Evidence command `python -m unittest discover -s tests` was attempted twice.
- Both attempts exited 127 with `zsh: command not found: python`.
- No successful deterministic Evidence was observed.
- The retained event stream ends while collaboration was in progress.
- A completed independent Verifier handoff is not evidenced.
- No execution attestation or RunEvaluation was fabricated.
- Runtime model / effort / timing are not independently verified by the retained archive and must not be inferred from the incomplete attempt.
- The canonical T1 Run therefore remains incomplete and not accepted.

This is not accepted as a task fail because the required deterministic Evidence could not start and the T1 topology did not complete. It is also not discarded: the attempt remains part of attempt accounting and infrastructure-failure reporting.

The retry decision is made **before seeing any retry result**. The justification is not that the observed code change looked promising; it is that the frozen Evidence command could not execute and the required T1 Verifier phase never completed.

## Preserve the original attempt

Before any retry, verify the archived files remain byte-identical to the reviewed archive:

| File | SHA-256 |
| --- | --- |
| `STOP-REPORT.md` | `622130cffc631295f97033b858c46bc7b206011f3aa1ad81a6c728a989e10cbd` |
| `evidence.txt` | `3fc80c177276d9d5fe9874f3856326b629fc9ad1954348335d86617ed6ed6a71` |
| `event-summary.json` | `b6f542d3f9bbcc7a6e0ffae99b919cb0429764380f1cb20b60fdebcad32b0fbf` |
| `patch.diff` | `a204da931aaf8dc68627a9b29dd74eaf2e0335c4f63830016d37378727f71c00` |
| `prompt.md` | `d98fdfb3c56ecc5659466d8b4ba607bb94e77c2a7d74360175b9657b6b93bf86` |
| `run-meta.yaml` | `2621205e473c0cd1f3eb6c75aa023be70e02053ba6532cceb03e6e50a9fc5ca6` |

Do not edit these archived files to reflect the retry.

## Read-only static preflight support

The reviewed archive bytes, the committed SHA256SUMS ledger, canonical T1 preparation,
active Freeze revision 3, and accepted T0 single-run artifact can be checked without
starting a model:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/audit_exp001_t1_retry.py
```

After the approved reset/reprepare, require a workspace ID that is distinct from
the archived attempt:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/audit_exp001_t1_retry.py --require-new-workspace-id
```

**This is a static audit, not an execution attestation or permission to consume
the retry allowance.** It does not establish a fresh external workspace, fixture
byte integrity immediately before startup, native `python` availability in the
normal experimental sandbox, write allow/deny controls, or fresh Codex/Verifier
behavior. The Operator must still perform all gates below on the actual host.

## Retry entry gate

The retry is allowed only after this procedure is reviewed and merged.

Before model invocation:

1. Feature Freeze revision 3 must pass unchanged.
2. The accepted T0 r01 Run must still pass single-run validation.
3. The original T1 infrastructure archive hashes above must match.
4. Use a clean isolated checkout and a nonexistent external workspace.
5. Preserve the currently prepared canonical T1 `run-meta.yaml` / `prompt.md` before reset.
6. Reprepare the same matrix slot with the unchanged frozen `prepare_pilot_run.py`, a new unique workspaceId, and a fresh fixture.
7. The new prompt must be byte-identical to both the canonical prepared prompt and archived failed-attempt prompt. Expected SHA-256: `d98fdfb3c56ecc5659466d8b4ba607bb94e77c2a7d74360175b9657b6b93bf86`.
8. Parsed preparation metadata must be identical to the archived preparation except for `spec.workspaceId`; the new workspaceId must be unique.
9. The fresh workspace file set and bytes must match the frozen fixture.
10. In the normal experimental sandbox, without invoking the model, prove that the frozen command `python -m unittest discover -s tests` can start. Do not make it pass by adding an alias, shim, symlink, wrapper, PATH mutation, or by substituting `python3`; the literal frozen command must be natively resolvable in the Run environment.
11. On the untouched fixture, the same command must produce the expected initial Evidence FAIL.
12. Prevent incidental Python bytecode writes during preflight, then recheck the fresh workspace file set and bytes against the frozen fixture immediately before model startup.
13. No prior T1 messages, patch, archive, failure explanation, or outcome may be exposed to the retry session.

If any gate fails, stop. Do not consume the retry allowance.

Gate 10 の実行環境判定基準と非model確認手順: [EXP-001_RETRY_T1_R01_PYTHON_ENV.md](EXP-001_RETRY_T1_R01_PYTHON_ENV.md)（Reviewer判断待ち）。

## Single permitted retry

Start exactly one fresh Codex session with:

- the unchanged T1 prompt only;
- the unchanged fixture;
- Runtime `codex`;
- Model `gpt-6.1-sol`;
- Effort `high`;
- the normal experimental sandbox;
- no session resume/fork;
- no cross-run feedback.

The retry allowance is consumed when the model invocation starts.

No second retry is authorized by this document regardless of outcome.

A valid T1 retry must complete the frozen topology contract: Worker implementation → independent Verifier handoff/review → deterministic Evidence-based final assessment. Worker-only completion is insufficient even if tests pass.

## Result handling

### Complete pass / fail / inconclusive

If the retry produces a complete Artifact set:

- preserve actual observed Evidence;
- preserve observable Worker → Verifier handoff/review events;
- confirm the Verifier did not directly edit implementation files;
- run single-run validation;
- perform the documented manual cross-artifact consistency review;
- require Reviewer Judgment `EXP-001 Run acceptance: ACCEPT` before progressing.

A task fail or inconclusive result is retained as the result for this matrix slot. It is not retried again under this infrastructure exception.

### Another infrastructure abort

If the retry cannot complete for infrastructure reasons:

- preserve the attempt separately;
- do not fabricate missing Artifacts;
- do not retry automatically;
- stop EXP-001 and require a new reviewed disposition.

## Selection-bias guard

This exception is intentionally narrower than a general retry policy.

- The original incomplete attempt remains visible permanently.
- Retry eligibility is determined from the inability to execute the frozen Evidence command and incomplete T1 topology, not from whether the observed patch looked correct.
- The retry uses the same matrix slot; it does not add a new repetition.
- The retry cannot be repeated until success.
- A complete fail or inconclusive result is retained as the slot result.
- A second infrastructure abort causes STOP and a new reviewed disposition; it does not automatically grant another retry.
- The eventual EXP-001 summary must disclose attempted-session counts and infrastructure/incomplete attempts separately from the 18 complete matrix Runs, including counts by condition so one condition's operational instability is not hidden by pass/fail-only reporting.

## Counting

Before retry:

- complete matrix Runs: **1 / 18**
- total Codex attempts: **3**
- retained infrastructure/incomplete attempts: **2**

After the retry starts, total attempts become 4.

A successful complete retry may raise complete matrix Runs to **2 / 18**. The original incomplete T1 attempt remains separately disclosed and is never counted as pass/fail.

## Next gate

Do not prepare or invoke the next matrix slot until the T1 retry:

1. produces a complete Artifact set,
2. passes single-run validation,
3. passes manual cross-artifact consistency review, and
4. receives Reviewer Judgment:

`EXP-001 Run acceptance: ACCEPT`

This exception does not change Prompt, Fixture, Topology, Role Contract, Runtime, Model, Effort, Evaluation semantics, Run Matrix, Feature Freeze revision, or the 18 / 18 completion requirement.
