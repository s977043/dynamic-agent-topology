# 残タスクの実行計画

> Current checkpoint: 2026-10-14 JST（#187統合・#188 CI PASS確認後）。これは実行時点のスナップショット。**各Issue・PR・main HEAD・CI・Human承認記録を作業直前に再取得する**。過去の16/18や次Run指示は現行計画ではない。

## 現在地（一次ソースと承認境界）

- `main` 確認時SHA: `5c310945fcfef96004db8662bd9796e7d7243a22`（PR #187反映後。作業前に再取得）。
- Open Issues: 14（確認時）。Open PR: [#186 Release candidate（Draft）](https://github.com/s977043/dynamic-agent-topology/pull/186) と [#188 Provenance audit](https://github.com/s977043/dynamic-agent-topology/pull/188)（別branchの作業）。件数・最新headは都度再取得。
- [EXP-001 Issue #15](https://github.com/s977043/dynamic-agent-topology/issues/15): **18/18 empirical Runs ACCEPT、9/9 paired blocks**。18/16件版の集計再現と独立結果レビュー後、[DECISION.md](../experiments/EXP-001-t0-vs-t1/DECISION.md) は **PILOT COMPLETE — Keep T0**（PR #181 / #182 はmerge済み）。
- [Feature Freeze](../experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md): **COMPLETED revision 3**。[PR #183](https://github.com/s977043/dynamic-agent-topology/pull/183) はHuman承認・merge済み。mainで固定33 blobの原本監査、18/18 completeness、CIを再検証した記録は[#15](https://github.com/s977043/dynamic-agent-topology/issues/15)を参照。**COMPLETEDは旧RunやFrozen dataの改変許可ではない**。
- EXP-001の観測範囲はCodex / gpt-6.1-sol / high、3 ScenarioのPilot。T0/T1両側成功率100%、T1の平均Token量はT0の2.206倍。難しいTaskや他Runtimeへの一般化は禁止。
- `docs/AGENT_HARNESS.md` に基づき、Feature Freeze改訂・Frozen artifact変更・release/tag・force push・削除・secretはHuman専権。通常PRも必須CI・作成者と別セッションの独立レビュー・自律境界を満たしてからmerge。

## 優先順位・残条件

| 順序 | Issue / PR | 次の実行可能な最小作業 | 完了条件 |
| --- | --- | --- | --- |
| 0 | [#15](https://github.com/s977043/dynamic-agent-topology/issues/15) | EXP-001実験収集・判断・Freeze解除後の監査は記録済み。**HumanがIssue closeを判断**。通常AgentはRunを再実行せず監査記録を保持 | Frozen 33 blobs / 18 Run / Keep T0 / CIの既存記録を保全し、Human dispositionを待つ |
| 1 | [#57](https://github.com/s977043/dynamic-agent-topology/issues/57) | [#187](https://github.com/s977043/dynamic-agent-topology/pull/187) に負側Fixtureと設計案を統合済み。[#188](https://github.com/s977043/dynamic-agent-topology/pull/188) に独立・read-only監査を起案済み。最新headのCI PASS、**独立別セッションレビュー待ち** | 4 FAIL / 3 UNKNOWN / baseline PASS、旧18 Runを誤FAILにしないEvidence、独立Reviewer ACCEPTと通常merge後のmain検証。historical acceptanceは変更しない |
| 2 | [#93](https://github.com/s977043/dynamic-agent-topology/issues/93) / [#88](https://github.com/s977043/dynamic-agent-topology/issues/88) | T0をBaselineに、selectorのshadow判断とtreatmentのpaired効果を分離して設計 | 宣言済み母集団・安全な副作用隔離・独立Outcome・追加Costを満たす |
| 並行 | [#159](https://github.com/s977043/dynamic-agent-topology/issues/159) | Actionsからの自動draft PR作成が403で止まる理由を**管理者が設定とpolicyで確認** | 正規GITHUB_TOKEN経路でdraft成功、Observe/Promoteのno-op、必須CIの起動を実測。設定変更・権限拡張はここで行わない |
| 並行 | [#31](https://github.com/s977043/dynamic-agent-topology/issues/31) | Repository設定の残差を管理者が取得。[Draft #186](https://github.com/s977043/dynamic-agent-topology/pull/186) は0.3.0候補。公開日、版数、mergeとtag/ReleaseはHumanが決定・実行 | 独立レビューと最新head CI、正式な公開日とrelease commitのCI/Scorecard成功を照合。仮日付でmergeしない |
| 後続 | #21 / #42 / #59 / #63 / #82 / #150 / #162 / #166 | 個別研究の仮説・反証条件・最小実測を比較 | EXP-001解除を確認し、各Issueの個別GateでGO / NO-GO / INCONCLUSIVEを記録 |

上記の優先度は実行提案であり、実験着手・Policy適用・権限変更の許可ではない。Freeze解除は完了したが、#57以降の実装・新実験にはそれぞれの独立レビュー、再現Evidence、Runtime PermissionとHuman-owned境界の確認が必要。

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
