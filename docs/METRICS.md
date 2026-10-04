# Metrics

DATはTask Outcomeだけでなく、**組織構造が意図どおり機能したか**と、**そのために払ったコスト**を同時に評価します。

Metricは単一Runの観測値と、複数Runから導出する集計値を区別します。欠測値やN/Aを0へ変換しません。

## Primary metrics

| Metric ID | 意味 | 集計上の注意 |
|---|---|---|
| `task_success_rate` | Acceptance Criteriaと必須Evidenceを満たしたRunの割合 | 現行summarizerでは入力された`RunEvaluation`の`taskSuccess`を平均する |
| `regression_rate` | 既存動作を壊したRunの割合 | 現行summarizerでは入力された`RunEvaluation`の`regressionDetected`を平均する |
| `human_interventions` | Run完了までに必要だった人間介入回数 | 単一Runではcount。現行summarizerはconditionごとの平均を出す |

aborted / infrastructure failureなど、completeな`RunEvaluation`を持たないRunをどう扱うかはExperiment固有のRunbookに従います。集計対象から外れたRunの存在を解釈上隠してはいけません。

## Secondary metrics

| Metric ID | 意味 | Missing / N/A |
|---|---|---|
| `total_tokens` | input + output token | 両方取得できるRunだけで集計。推定値で補完しない |
| `wall_clock_ms` | Run全体の実測経過時間 | complete Runでは実測値を記録する |
| `topology_adherence` | 宣言Topologyに沿って実行された度合い（0〜1） | P0など非Agent BaselineではN/A (`null`) |
| `boundary_violations` | Role / Permission境界違反件数 | 観測された0と未観測を混同しない |
| `handoff_failures` | Handoff失敗件数 | 観測された0と未観測を混同しない |
| `evidence_completeness` | 必須Evidenceの収集率（0〜1） | 必須Gateの定義に依存する |
| `verifier_false_accept_rate` | Deterministic Evidenceが失敗しているのにVerifierが承認した割合 | `verifierFalseAccept`がN/AでないRunのみを分母にする |
| `agent_invocations` | Agent起動回数 | Runtimeから観測可能な範囲を記録する |
| `coordination_transitions` | Agent間のhandoff / review / verify遷移数 | Topologyが複雑になるほど増えうるcoordination cost |

## Current aggregation semantics

`scripts/summarize_experiment.py` は、同じExperimentについてRuntime / Model / Effortが複数混在している場合に集計を拒否します。Condition単位で、入力された`RunEvaluation`から次を集計します。

- `taskSuccessRate`: `taskSuccess` booleanの平均
- `regressionRate`: `regressionDetected` booleanの平均
- `meanHumanInterventions`: `humanInterventions`の平均
- `meanTopologyAdherence`: `null`を除いた平均
- `meanEvidenceCompleteness`: `completeness`の平均
- `meanTotalTokens`: input/output tokenの両方があるRunだけの平均
- `meanWallClockMs`: `wallClockMs`の平均
- `verifierFalseAcceptRate`: `verifierFalseAccept`が`null`でないRunだけのboolean平均

この集計処理は欠測値を0に置換しません。一方、**入力されなかったRunの存在までは自動的に説明しない**ため、Pilot completeness validationやRunbook上の進捗確認と合わせて解釈します。

## Evaluation principles

- 単一Metricだけを最適化しません。
- Task Successだけを見てToken、Latency、Human Intervention、Boundary Violationを無視しません。
- N/Aと0を区別します。
- Observed metricと推定値を混在させません。
- 小さい差を自動的に「改善」と断定せず、ExperimentのDecision Policyとsample sizeを確認します。

## Capability contribution

Capability contributionは単一RunのMetricではなく、paired blockのbaseline / candidateから導出する**比較結果**です。既存の`RunEvaluation`を正本とし、互換性のない`capability_score`を追加しません。

代表的なdelta:

| Derived delta | 解釈 |
|---|---|
| `Δ task_success_rate` | Capability追加/変更によるTask成功率の変化 |
| `Δ regression_rate` | 回帰リスクの増減 |
| `Δ human_interventions` | 人間介入負荷の増減 |
| `Δ total_tokens` | Token costの増減 |
| `Δ wall_clock_ms` | Latencyの増減 |
| `Δ boundary_violations` | Role / Permission境界違反の増減 |
| `Δ verifier_false_accept_rate` | 独立Verificationの誤受理率の増減 |
| `Δ topology_adherence` | 宣言Topologyへの準拠度の変化 |

符号だけで自動採用しません。例えばTask Successが同等でもToken / Latency / coordination transitionが大きく増えるなら、追加Capabilityの正当化は弱くなります。一方、安全性に関わるcritical regression低減は単純なcost増より優先される場合があります。

Capabilityがcandidate側で実際にactivationしていない、paired blockが成立していない、sampleが不足している場合は比較を`INCONCLUSIVE`とし、0 deltaとして補完しません。
