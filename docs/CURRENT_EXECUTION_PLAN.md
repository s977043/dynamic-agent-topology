# 残タスクの実行計画

> Current checkpoint: 2026-10-14 JST。これは実行時点のスナップショット。**各Issue・PR・main HEAD・CI・Human承認記録を作業直前に再取得する**。過去の16/18や次Run指示は現行計画ではない。

## 現在地（一次ソースと承認境界）

- `main` 確認時SHA: `55c47011116cf3e792df808135039ce21e05fd34`（PR #182反映後）。
- Open Issues: 14 / Open PRs: 1（確認時）。PR一覧・Issue一覧は都度再確認。
- [EXP-001 Issue #15](https://github.com/s977043/dynamic-agent-topology/issues/15): **18/18 empirical Runs ACCEPT、9/9 paired blocks**。18/16件版の集計再現と独立結果レビュー後、[DECISION.md](../experiments/EXP-001-t0-vs-t1/DECISION.md) は **PILOT COMPLETE — Keep T0**（PR #181 / #182 はmerge済み）。
- [Feature Freeze](../experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md): **ACTIVE revision 3**。解除提案は[Draft PR #183](https://github.com/s977043/dynamic-agent-topology/pull/183)。最終head `11db1df588b7664b801a8693409ff62fdf2b0d52` のCI SUCCESSは確認記録があるが、**別セッション独立レビューとHuman明示承認・Human mergeは未達**。この計画を承認の代わりに使わない。
- EXP-001の観測範囲はCodex / gpt-6.1-sol / high、3 ScenarioのPilot。T0/T1両側成功率100%、T1の平均Token量はT0の2.206倍。難しいTaskや他Runtimeへの一般化は禁止。
- `docs/AGENT_HARNESS.md` に基づき、Feature Freeze改訂・Frozen artifact変更・release/tag・force push・削除・secretはHuman専権。通常PRも必須CI・作成者と別セッションの独立レビュー・自律境界を満たしてからmerge。

## 優先順位・残条件

| 順序 | Issue / PR | 次の実行可能な最小作業 | 完了条件 |
| --- | --- | --- | --- |
| 0 | [#183](https://github.com/s977043/dynamic-agent-topology/pull/183) / [#15](https://github.com/s977043/dynamic-agent-topology/issues/15) | 最新headで別セッション独立レビューとCIを照合し、**Humanが明示承認してHuman自身がmerge**。Agentは自己承認・mergeしない | `main` でfreeze status / 33 frozen blobs / 18 Run / DECISION / CIを再確認し、#15へ監査結果を記録 |
| 1 | [#57](https://github.com/s977043/dynamic-agent-topology/issues/57) | 既存のattestation ↔ trace ↔ evaluation間のprovenance不整合を負側fixtureで再現し、独立auditの最小案を比較 | 不明をUNKNOWNに保持し、観測外の違反ゼロを推定しない。旧Experimentの評価意味論は書換えない |
| 2 | [#93](https://github.com/s977043/dynamic-agent-topology/issues/93) / [#88](https://github.com/s977043/dynamic-agent-topology/issues/88) | T0をBaselineに、selectorのshadow判断とtreatmentのpaired効果を分離して設計 | 宣言済み母集団・安全な副作用隔離・独立Outcome・追加Costを満たす |
| 並行 | [#159](https://github.com/s977043/dynamic-agent-topology/issues/159) | Actionsからの自動draft PR作成が403で止まる理由を**管理者が設定とpolicyで確認** | 正規GITHUB_TOKEN経路でdraft成功、Observe/Promoteのno-op、必須CIの起動を実測。設定変更・権限拡張はここで行わない |
| 並行 | [#31](https://github.com/s977043/dynamic-agent-topology/issues/31) | Repository設定・保護ルール・Release readinessの未確認値を権限ある担当が取得 | 現在値の根拠を照合。Release/tagはHuman判断 |
| 後続 | #21 / #42 / #59 / #63 / #82 / #150 / #162 / #166 | 個別研究の仮説・反証条件・最小実測を比較 | EXP-001解除を確認し、各Issueの個別GateでGO / NO-GO / INCONCLUSIVEを記録 |

上記の優先度は実行提案であり、実験着手・Policy適用・権限変更の許可ではない。特に#57以降の実装変更はFreeze解除の正本を確認するまで開始しない。

## 検討 → レビュー → 対応 → レビュー（繰り返し）

1. **Inspect**: 最新のIssue・PR・branch head・変更対象契約とHuman-owned境界を再取得。過去チェックポイント・セッションmemoryを最新事実と誤認しない。
2. **Plan & challenge**: 最小のreversibleな修正、期待する観測、負側テスト、rollback、交絡要因を確認。Agile Coach / Scrum Masterは必要時のみ相談し、独立Reviewerに代えない。
3. **Change & verify**: 小さなbranch/PRを作り、対象テスト・Freeze監査・必要CIを実測。失敗と未観測をPASSに置換しない。
4. **Independent review & disposition**: 作成者とは別セッションのReviewerがhead固定で差分とEvidenceを検査。必須指摘を修正し、CI・差分・headが変われば再レビュー。
5. **Merge or block**: Human専権変更はHuman自身による承認・merge待ち。その他のPRでも既存の自律境界を満たす場合だけmergeする。未達はIssueに証跡・阻害要因・解除条件を残す。

## 過去状態と再確認

- **16/18 Run**、safe-divide r03を次に実行、#165待ち、`DECISION NOT RUN`などは過去のチェックポイントであり、**再実行指示ではない**。履歴は[#15](https://github.com/s977043/dynamic-agent-topology/issues/15)と過去commitを参照。
- #159のObserve/Promoteの自動PR作成403は未解決。手動作成した診断PRのmergeやPromote no-op成功を、正規自動draft成功と混同しない。[Live operations](HARNESS_LIVE_OPERATIONS.md)を参照。
- Mac / ThinkPad / Claude Code cloudの接続・環境値は未実測が残る。[Environment usage](ENVIRONMENT_USAGE.md)の履歴値を承認済みRun条件に転用しない。
