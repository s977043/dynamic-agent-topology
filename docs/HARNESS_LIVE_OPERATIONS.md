# 開発ハーネスの初回運用検証と復旧

Issue [#159](https://github.com/s977043/dynamic-agent-topology/issues/159) の実運用受理は、コードの統合と分けて管理します。以下は2026-10-14 JSTのチェックポイントです。最新状態はIssueの証跡を参照してください。

## 初回の実測

[#174](https://github.com/s977043/dynamic-agent-topology/pull/174) の統合SHA `d67f2d5c2e48fe10dd0d2008e717c9cc60da245f` で、両workflowがpush起動しました。ログのcheckout SHAと生成commitのparentはこのSHAに一致しました。

| 処理 | 実行 | 生成commit | 結果 |
|---|---|---|---|
| Observe | [run 38481873935 / attempt 1](https://github.com/s977043/dynamic-agent-topology/actions/runs/38481873935/attempts/1) | [da2cbf2c](https://github.com/s977043/dynamic-agent-topology/commit/da2cbf2c71259768806e3dfc1705b7c0e49bdae7) | ledgerと生成表を作成、PR作成段階で `API_HTTP_403`・exit 1 |
| Promote | [run 38481873976 / attempt 1](https://github.com/s977043/dynamic-agent-topology/actions/runs/38481873976/attempts/1) | [0b312a04](https://github.com/s977043/dynamic-agent-topology/commit/0b312a048a2427f2a4cbc204ff7b9750b7b79a87) | 検討文書一件を作成、PR作成段階で `API_HTTP_403`・exit 1 |

PR作成段階という判断は、残存ref/commitと、ref作成後の次のAPIがPOST pullsである実行コードを照合したものです。ログのContents/PullRequests writeだけではPR作成許可の成立を証明できません。403の具体的な設定・policy原因は未確定です。

生成元commitを保持し、接続GitHub actor `s977043` が別途診断用draft [#175](https://github.com/s977043/dynamic-agent-topology/pull/175)・[#176](https://github.com/s977043/dynamic-agent-topology/pull/176) を作成しました。各3ループの独立レビューと必須CI成功後に統合しました。#176は最新mainとの同期後も再レビュー・再CIを実施しました。この手動経路の成功をGITHUB_TOKENによる自動起案成功とは扱いません。

Observeの取り込みは旧11件を保持した未分類candidate3件、Promoteは既存L-009/L-010の検討文書のみです。規則・Guard・stateの採用、EXP-001のRun acceptanceを意味しません。

## Promoteの同入力no-op実測

[run 38481873976 / attempt 2](https://github.com/s977043/dynamic-agent-topology/actions/runs/38481873976/attempts/2) は2026-10-14 JSTに失敗jobだけを正規Actions経路で再実行し、SUCCESSになりました。[job 115590890603](https://github.com/s977043/dynamic-agent-topology/actions/runs/38481873976/job/115590890603) のログはcheckout `d67f2d5c2e48fe10dd0d2008e717c9cc60da245f` と `PROPOSAL_UNCHANGED` を記録しています。

再実行前後のAPI mainは `0b41084f528423db552cc7569f22e6ec840839fe` でした。スクリプトはcheckout内のledgerではなくAPI mainのSHAに固定したledgerと文書を読みます。対象L-009/L-010の生成内容が統合済み文書に一致し、publish呼出し前に戻る経路です。新しい生成commitのparentを示す証跡ではありません。これはPromoteだけのno-op実測で、Observeのlive no-op、自動draft生成成功、403原因の解消は証明しません。attempt 1の失敗は別に保持します。

## 403停止時の確認順序

1. run ID・attempt・event head・ログのcheckout SHAを記録し、成功/失敗を区別する。ログの秘密値や原文を公開文書へ転載しない。
2. ref・commit・PRを読み取り確認する。生成commitのparentと差分を確認し、存在するrefを削除・reset・上書きして再試行しない。
3. RepositoryのSettings → Actions → GeneralにあるPR作成許可と、適用される組織/enterprise policyを管理権限で確認する。未取得の設定を403だけで無効と断定しない。
4. 必要な設定変更は管理者の正規操作として記録する。cloudのHTTP制限、GitHub connector actor、ActionsのGITHUB_TOKENは別の認可経路なので、一方の成功から他方の許可を推定しない。別credentialで拒否された自動処理を継続しない。
5. 残存refまたは過去PRがある同入力のpublisherは停止する。許可を直しても単純な再実行では初回起案成功を証明できない。refを消して成功させるのではなく、履歴を保持し、正当に発生した新しい提案対象と独立レビューで次の検証を計画する。

診断用手動draftを作る場合は別作業と明記し、元runの失敗、生成元SHA、作成actor、branch同期の有無を本文に残します。自動処理のリトライや設定拒否の迂回として扱いません。

## 受理条件と残タスク

| 確認項目 | このチェックポイントの状態 |
|---|---|
| workflow起動・checkout・生成物の範囲 | 実測済み |
| 403時の停止・生成commit保持 | 実測済み |
| 手動診断draftの必須CI・独立レビュー・統合 | 実測済み |
| 正規GITHUB_TOKEN経路の `DRAFT_PR_N` と `draft=true` | 未達 |
| 同入力のlive no-op | Promote実測済み、Observe未検証 |
| GITHUB_TOKEN生成PRからの必須CI起動手順 | 未検証 |

GITHUB_TOKEN作成PRは通常のpull_request CIを起動しません。Humanのclose/reopen等の承認済み手順で、最新headの必須CIと独立レビューを確認します。手動診断draftでCIが動いたことはこの経路の検証を代替しません。no-opのSUCCESSも初回draft生成成功の代替になりません。

現在のCodex cloudは `api.github.com` がHTTP許可対象外で、接続コネクターもActions permissionsの取得/更新に非対応です。設定の確認・変更は未実施です。APIアクセス設定の変更は環境の正規設定フローで行い、proxyを迂回しません。

EXP-001の実行はOperatorの担当です。この運用検証をRun起動・Freeze解除・#165の正式ACCEPTへ流用しません。端末接続、実験原本、公開設定・Release判断の残タスクはそれぞれ既存Issueで管理します。
