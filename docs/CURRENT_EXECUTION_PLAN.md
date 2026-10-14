# 残タスクの実行計画

2026-10-14 UTCのチェックポイント。最新状態は各Issueを正本とし、実行前に更新・受理コメント・main SHA・CIを読み直します。確認時mainは `f39a3a50aa0c0bb0ee5ad1fc39f54bbcbac572d3`、Open Issue14件・Open PR0件、mainのspec-lint/CodeQL/ScorecardはSUCCESSでした。

## 進展と判断材料

[#165](https://github.com/s977043/dynamic-agent-topology/pull/165) は統合済みです。[Codex受理6157691664](https://github.com/s977043/dynamic-agent-topology/issues/15#issuecomment-6157691664) と [Antigravity受理6157693082](https://github.com/s977043/dynamic-agent-topology/issues/15#issuecomment-6157693082) が対象RunのACCEPTを記録しています。受理対象head `e8cb223` と統合前head `e5d04e2` のRun Artifact不変は [6157742024](https://github.com/s977043/dynamic-agent-topology/pull/165#issuecomment-6157742024) に記録されています。これは既存Reviewer判断の状態確認であり、このクラウドによる原本再監査ではありません。

EXP-001は16/18・8/9ペア。残りはregression safe-divide r03 T0→T1です。Feature FreezeはACTIVE/revision3。先行env-check STOP原本の未確認など、受理コメントの制約は最終分析でも保持します。train/normalize-name r01ペアの環境交絡を全r01へ拡張しません。

## 順序・担当・完了条件

| 優先 | 対象 | 次の対応 | 担当・依存 | 完了条件 |
|---|---|---|---|---|
| 1 | #15 状態同期 | 冒頭の16/18・次slot・履歴識別への更新を確認済み。以後も実行前に再読 | Agent、他セッション更新を保持 | 現状と履歴を明示。今回の同期は既存更新で達成 |
| 2 | #15 r03 T0 | 既存OPERATOR/run-kit-g手順でfresh環境・sessionの実測 | Operator、直前ACCEPT6157691664・既存Gate | 実7Artifact、必須CI、独立Run ACCEPT、merge |
| 3 | #15 r03 T1 | T0受理・merge後、既存counterbalanced matrixに従い実測 | Operator、r03 T0の受理 | 同上、18/18・9/9ペア |
| 4 | #15 完了分析 | completeness検証、再現集計、全18件と交絡ペア除外16件の比較、制約開示、DECISION.md | Agentが材料・分析PR、18/18受理が前提 | 独立レビュー・結果PR統合後、既存Freeze解除手続き |
| 並行 | #159 初回運用 | ActionsのPR作成許可と適用policyを確認し正規経路を検証 | 管理者の設定アクセスが必要 | GITHUB_TOKEN draft成功、Observe no-op、生成PRのCI起動経路を実測 |
| 並行 | #31 公開整備 | 未確認security設定の取得と照合、Release readinessを確認 | 設定アクセス、Release/tagはHuman判断 | 設定証跡・監査結果、Release可否の記録 |
| 後続 | post-freeze研究 | 下記Issueを仮説・対照・指標・必要環境で比較し採用候補を絞る | EXP-001完了・既存解除手続き | 各Issueの受理条件とDAT-side Evidenceを満たして判断 |

post-freeze対象は #21・#42・#57・#59・#63・#82・#88・#93・#150・#162・#166。文献追加や実験計画だけで実証完了・採用済み・Issue完了にしません。詳細の受理条件は各Issueを参照します。

## 開発ハーネスの残条件

#159の①〜⑤は統合済み。初回Observe/PromoteはPR作成で403停止し、別作業の手動診断draft #175/#176をレビュー後に統合しました。Promote attempt2は `PROPOSAL_UNCHANGED`・SUCCESSで、同入力no-opのみ実測済みです。[初回運用検証と復旧](HARNESS_LIVE_OPERATIONS.md) に失敗/成功と認可経路を分けて記録しています。

403の具体的設定・policy原因は未確定。現在のcloud APIアクセス制限とconnectorの設定endpoint非対応により管理設定の取得・変更は未実施です。残存ref/過去PRを削除・再利用して初回成功を作りません。Observeの再実行は新しいCI失敗等を採取し得るため、Promoteのno-op結果を転用せず入力と書込み経路を別途レビューします。

Mac・ThinkPad・Claude Code cloudの直接接続とmemory移行も未実測です。[環境比較](ENVIRONMENT_USAGE.md) の値は観測時点のものとして扱います。クラウド環境を承認済み実験環境の代わりに使いません。

## 計画更新と3ループ

調査中にIssue #15が他セッションから更新されたため、古い本文を使った変更案は破棄しました。更新直前に原文を再取得し、変更があれば計画を再レビューします。並行更新を上書きする全本文置換は行いません。

1. 検討→計画レビュー→対応→再レビュー：最新Issue・受理コメント・main/CIを確認し、依存・担当・完了条件を決める。矛盾があれば原文と履歴を保って状態を同期する。
2. 検討→レビュー→対応→再レビュー：実行可能な変更と検証を行い、別セッションが一次材料を照合する。失敗・未確認・アクセス不足を結果として残し、計画の依存を更新する。
3. 検討→レビュー→対応→再レビュー：最終head・最新mainとの差分・必須CI・独立指摘の解消を確認する。ユーザーのレビューOK後merge指示と既存自律境界に従い統合し、Issueと計画を更新する。

通常Runの起動・既存runIdの再prepareはAgentが代行しません。18/18以前の最終判断、Frozen条件変更、Freeze解除・Release/tagの権限をこの計画から推定しません。接続不足の項目は担当と解除条件を残してopenを維持し、未実測の成果を作りません。
