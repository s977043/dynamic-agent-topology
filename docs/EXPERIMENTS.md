# Experiment Protocol

DATのExperimentは、Topologyを「良さそうだから採用する」のではなく比較可能な仮説として扱うための契約です。

## 最低限固定するもの

- Task / Scenario
- Runtime
- Model
- Effort
- Fresh workspace
- Evidence commands
- 最低Run数

比較条件間でこれらを揃え、Topology以外の差分をできるだけ減らします。

## train / test / regression

公開fixtureはプロトコル確認用です。本番の研究・評価ではtest setを調整に使わず、可能なら未観測の外部test setを用意してください。

## Run artifacts

各Runは以下を残します。

1. `ExecutionTrace`
2. `RunEvaluation`

Traceは「何が起きたか」、Evaluationは「どう評価したか」を分離します。
