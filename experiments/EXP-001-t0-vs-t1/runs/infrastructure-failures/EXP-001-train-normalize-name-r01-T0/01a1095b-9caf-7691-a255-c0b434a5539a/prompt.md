<!-- runId: EXP-001-train-normalize-name-r01-T0 -->
<!-- blockId: EXP-001-train-normalize-name-r01 -->
<!-- executionOrder: 1 -->

# EXP-001 Pilot Prompt

You are executing exactly one controlled EXP-001 run.

## Universal Constraints

- Complete only the assigned scenario task.
- Do not inspect artifacts or results from any other EXP-001 run.
- Do not change the task, runtime, model, effort, or deterministic evidence command.
- Preserve the existing public API unless the scenario explicitly says otherwise.
- Deterministic evidence is authoritative; agent self-assessment is not ground truth.

## Topology Contract

- Operate as a single Worker agent.
- Do not delegate to another agent.
- Do not invoke a verifier or reviewer subagent.
- Implement the change, then run the declared deterministic evidence command.

## Task

normalize_nameが前後空白を除去し、小文字へ正規化するように修正する。既存APIを変更しないこと。

## Acceptance Criteria

- 前後空白が除去される
- 英字が小文字へ正規化される
- 既存テストを含む全テストが成功する

## Deterministic Evidence

- `python -m unittest discover -s tests`
