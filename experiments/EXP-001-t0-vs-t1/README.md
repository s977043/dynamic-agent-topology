# EXP-001: T0 vs T1

## 問い

**Single Agentに独立Verifierを追加する価値は、coordination costを上回るか？**

DATの最初の実験では、T0とT1だけを比較します。最初からT2/T3を持ち込まず、Verifierという1つのRoleの限界効用をAblationとして確認します。

## 条件

- **T0**: Single Agent
- **T1**: Worker → Verifier

Runtime / Model / Effort / Taskは条件間で揃え、Topologyだけを主変数にします。

## データ分離

- `train`: splitの一般目的は実験手順やPrompt/Role Contractの調整。ただし現在のEXP-001 PilotはFeature Freeze中のため、18 Run完了までは途中のtrain結果を使ってPrompt / Role / Topology / Scenario / Evaluation semanticsを変更しない
- `test`: Topology選択の最終比較に利用。調整の材料にはしない
- `regression`: 採用後のTopology変更で既知品質を壊していないか確認

このリポジトリに含むfixtureは**プロトコルの動作確認用であり、外部Benchmarkとしての統計的妥当性を主張しません**。本評価では、非公開または未観測のtest setを追加することを推奨します。

## 実行単位

各scenarioを比較blockとして扱い、同じ`blockId`のT0/T1はRuntime / Model / Effortを揃えたfresh workspaceで実行します。RunごとにExecutionTraceとRunEvaluationを保存します。

最低実行回数は `experiment.yaml` の `minimumRunsPerScenarioPerCondition` に従います。

## 採否

T1は「Verifierがいるから良い」とは判断しません。Task Success、Regression、Human Intervention、Token/Latency、Topology Adherence、Verifier False Acceptを合わせて判断します。

## Fixture実行規約

`evidenceCommands` は各Scenarioの `fixturePath` をcurrent working directoryとして実行します。

Repository内のfixtureは、修正前に最低1つの必須Evidenceが失敗する状態をCIで確認します。これにより、fixtureが誤って「最初から成功するTask」へ変質することを防ぎます。

## Decision status

PR #54（merge commit `a718293`）時点ではPilot実行中で、最初のT0 Runがsingle-run validationを通り、complete empirical runsは **1 / 18** です。これはT0/T1比較の結論ではありません。18 / 18とcompleteness validationが揃うまで優劣は主張せず、採否記録は [DECISION.md](DECISION.md) を `NOT RUN` のまま維持します。Live progressと次RunはIssue #15を正本とします。


## Pilot

最初の実Runtime Pilotは [pilot/RUNBOOK.md](pilot/RUNBOOK.md) に固定します。

- Codex
- GPT-6.1 Sol
- High effort
- T0 / T1
- 3 scenarios
- N=3
- 18 runs
- fresh session/context per run
- counterbalanced paired order

Pilot Artifactが18 Run揃うまでは `DECISION.md` を `NOT RUN` のまま維持します。最初のcomplete Runだけを見てPrompt / Topology / Scenario / Evaluation semanticsを変更しません。


## Feature Freeze

EXP-001は実測フェーズに入ったため、18 Run完了まで実験条件を凍結します。

- Freeze policy: [pilot/FREEZE.md](pilot/FREEZE.md)
- Freeze manifest: [pilot/freeze.yaml](pilot/freeze.yaml)
- Execution tracking: Issue #15

Prompt / Topology / Scenario / Fixture / Evaluation semanticsは途中結果を見て変更しません。Blocking defect時は実行を停止し、Freeze policyの例外手続きに従います。
