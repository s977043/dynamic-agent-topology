# Metrics

DATはTask Outcomeだけでなく、組織構造が正しく機能したかと、そのために払ったコストを同時に評価します。

## Primary metrics

| Metric ID | 意味 |
|---|---|
| `task_success_rate` | Acceptance Criteriaと必須Evidenceを満たしたRunの割合 |
| `regression_rate` | 既存動作を壊したRunの割合 |
| `human_interventions` | Run完了までに必要だった人間介入回数 |

## Secondary metrics

| Metric ID | 意味 |
|---|---|
| `total_tokens` | input + output token。Runtimeが取得可能な場合に記録 |
| `wall_clock_ms` | Run全体の経過時間 |
| `topology_adherence` | 宣言Topologyに沿って実行された割合（0〜1）。P0など非Agent BaselineではN/A (`null`) |
| `boundary_violations` | Role/Permission境界違反件数 |
| `handoff_failures` | Handoff失敗件数 |
| `evidence_completeness` | 必須Evidenceの収集率（0〜1） |
| `verifier_false_accept_rate` | Deterministic Evidenceが失敗しているのにVerifierが承認した割合 |
| `agent_invocations` | Agent起動回数 |
| `coordination_transitions` | Agent間のhandoff/review/verify遷移数 |

## 原則

単一Metricだけを最適化しません。特にTask Successだけを見て、Token、Latency、Human Intervention、Role Violationを無視しないことをDATの評価原則とします。


## Capability contribution（derived comparison）

Capability contributionは単一RunのMetricではなく、paired blockのbaseline / candidateから導出する**比較結果**です。既存の `RunEvaluation` を正本とし、互換性のない `capability_score` を追加しません。

代表的なdelta:

| Derived delta | 解釈 |
|---|---|
| `Δ task_success_rate` | Capability追加/変更によるTask成功率の変化 |
| `Δ regression_rate` | 回帰リスクの増減 |
| `Δ human_interventions` | 人間介入負荷の増減 |
| `Δ total_tokens` | Token costの増減 |
| `Δ wall_clock_ms` | Latencyの増減 |
| `Δ boundary_violations` | Role/Permission境界違反の増減 |
| `Δ verifier_false_accept_rate` | 独立Verificationの誤受理率の増減 |
| `Δ topology_adherence` | 宣言Topologyへの準拠度の変化 |

符号だけで自動採用しません。例えばTask Successが同等でもToken / Latency / coordination transitionが大きく増えるなら、追加Capabilityの正当化は弱くなります。一方、安全性に関わるcritical regression低減は単純なcost増より優先される場合があります。

Capabilityがcandidate側で実際にactivationしていない、paired blockが成立していない、sampleが不足している場合は比較を `INCONCLUSIVE` とし、0 deltaとして補完しません。
