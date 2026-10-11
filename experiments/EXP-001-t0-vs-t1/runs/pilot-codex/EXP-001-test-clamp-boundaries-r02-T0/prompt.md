<!-- runId: EXP-001-test-clamp-boundaries-r02-T0 -->
<!-- blockId: EXP-001-test-clamp-boundaries-r02 -->
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

clamp(value, low, high)がlow未満をlow、high超過をhighへ丸め、範囲内の値はそのまま返すように修正する。

## Acceptance Criteria

- 下限未満はlowになる
- 上限超過はhighになる
- 範囲内の値は変更されない
- 全テストが成功する

## Deterministic Evidence

- `python -m unittest discover -s tests`
