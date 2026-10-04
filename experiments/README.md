# Experiments

DATではExperimentを第一級Artifactとして扱います。

各Experimentは最低限、以下を持ちます。

- 問いと仮説
- 比較条件（Topology）
- Runtime / Model / EffortのControl
- train / test / regressionのScenario Set
- Primary / Secondary Metrics
- 最低Run数
- 採否基準
- RunごとのExecutionTrace / Evaluation

## データ分離

TopologyやPromptの改善に使えるのは原則`train`です。`test`は最終比較、`regression`は採用後の品質維持に使います。

最初のExperimentは [EXP-001: T0 vs T1](EXP-001-t0-vs-t1/README.md) です。
