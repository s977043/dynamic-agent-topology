<!-- runId: EXP-001-regression-safe-divide-r02-T1 -->
<!-- blockId: EXP-001-regression-safe-divide-r02 -->
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

- Operate as a Worker → independent Verifier topology.
- The Worker implements the change.
- After implementation, hand off to a Verifier in a separate role/context.
- The Verifier uses the same pilot model and effort as the Worker.
- The Verifier inspects the implementation and deterministic evidence but must not edit implementation files.
- If the Verifier finds a defect, it returns findings to the Worker; only the Worker may modify the implementation.
- A Verifier PASS is not ground truth; deterministic evidence remains authoritative.

## Task

safe_divide(a, b)はbが0のとき0.0を返し、それ以外では通常の除算結果を返すように修正する。

## Acceptance Criteria

- ゼロ除算時に0.0を返す
- 通常除算の結果を壊さない
- 全テストが成功する

## Deterministic Evidence

- `python -m unittest discover -s tests`
