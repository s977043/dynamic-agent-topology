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

## 集計時のControl

`summarize_experiment.py` は、同じExperimentに複数のRuntime / Model / Effortが混在する入力を拒否します。Execution Contextごとに分けて集計し、Runtime差とTopology差を混同しないことを優先します。


## Pilot completeness validation

EXP-001 Pilotは `scripts/validate_pilot.py` でplan/matrixをCI検証します。

実Run完了時は `--require-complete` を付け、18 RunすべてのTrace / Evaluation / patch / Evidenceが揃い、Pilot固定Runtime / Model / Effortと一致することを確認します。


## Operator support

`scripts/prepare_pilot_run.py` は単一Pilot Runのfresh workspaceとpre-run Artifactだけを生成します。`scripts/pilot_status.py` は進捗を表示しますが、`artifacts-present` をsemantic completionとは扱いません。

最終完了判定のSSoTは引き続き `validate_pilot.py --require-complete` です。

status表示はcanonical Artifactの有無だけを読みます。外部保存されたincomplete / aborted attemptのdispositionや再試行可否は [Issue #15](https://github.com/s977043/dynamic-agent-topology/issues/15) を確認してください。`prepared` は実行許可ではありません。進行判断と最終completenessの区別は [Execution Handoff](../docs/EXP-001_EXECUTION.md) にあります。
