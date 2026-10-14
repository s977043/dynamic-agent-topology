<!-- runId: EXP-001-regression-safe-divide-r03-T0 -->
<!-- blockId: EXP-001-regression-safe-divide-r03 -->
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

safe_divide(a, b)はbが0のとき0.0を返し、それ以外では通常の除算結果を返すように修正する。

## Acceptance Criteria

- ゼロ除算時に0.0を返す
- 通常除算の結果を壊さない
- 全テストが成功する

## Deterministic Evidence

- `python -m unittest discover -s tests`
