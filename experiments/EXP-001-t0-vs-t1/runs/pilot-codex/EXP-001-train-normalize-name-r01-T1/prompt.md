<!-- runId: EXP-001-train-normalize-name-r01-T1 -->
<!-- blockId: EXP-001-train-normalize-name-r01 -->
<!-- executionOrder: 2 -->

# EXP-001 Pilot Prompt

You are executing exactly one controlled EXP-001 run.

## Universal Constraints

- Complete only the assigned scenario task.
- Do not inspect artifacts or results from any other EXP-001 run.
- Do not change the task, runtime, model, effort, or deterministic evidence command.
- Preserve the existing public API unless the scenario explicitly says otherwise.
- Deterministic evidence is authoritative; agent self-assessment is not ground truth.

## Topology Contract

- Operate as a Worker → independent Verifier topology.
- The Worker implements the change.
- After implementation, hand off to a Verifier in a separate role/context.
- The Verifier uses the same pilot model and effort as the Worker.
- The Verifier inspects the implementation and deterministic evidence but must not edit implementation files.
- If the Verifier finds a defect, it returns findings to the Worker; only the Worker may modify the implementation.
- A Verifier PASS is not ground truth; deterministic evidence remains authoritative.

## Task

normalize_nameが前後空白を除去し、小文字へ正規化するように修正する。既存APIを変更しないこと。

## Acceptance Criteria

- 前後空白が除去される
- 英字が小文字へ正規化される
- 既存テストを含む全テストが成功する

## Deterministic Evidence

- `python -m unittest discover -s tests`
