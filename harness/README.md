# Harness

v0.2のHarnessは**Runtime実行器ではなく、Experiment Artifactの検証・集計を行う最小Harness**です。

## 現在できること

- JSON SchemaによるExperiment / Scenario / Trace / Evaluation検証
- Semantic validationによるTopology / Runtime / Scenario参照整合性チェック
- `scripts/summarize_experiment.py` によるRun Evaluationの条件別集計

## まだしないこと

- Claude Code / Codex / Gemini CLI / Antigravityの自動起動
- Canonical TopologyからRuntime設定への自動compile/apply
- Agent lifecycleの自動trace capture
- 統計的有意差検定

これらはExperiment Artifactの契約を実Runで検証してから段階的に追加します。
