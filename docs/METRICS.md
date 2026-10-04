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
| `topology_adherence` | 宣言Topologyに沿って実行された割合（0〜1） |
| `boundary_violations` | Role/Permission境界違反件数 |
| `handoff_failures` | Handoff失敗件数 |
| `evidence_completeness` | 必須Evidenceの収集率（0〜1） |
| `verifier_false_accept_rate` | Deterministic Evidenceが失敗しているのにVerifierが承認した割合 |
| `agent_invocations` | Agent起動回数 |
| `coordination_transitions` | Agent間のhandoff/review/verify遷移数 |

## 原則

単一Metricだけを最適化しません。特にTask Successだけを見て、Token、Latency、Human Intervention、Role Violationを無視しないことをDATの評価原則とします。
