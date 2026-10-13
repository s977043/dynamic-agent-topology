# Learning Observe の自動観測

Issue #159 施策③の実装です。`harness-observe.yml` は週次（月曜06:53 UTC）または手動で、default branch のスクリプトだけを実行します。EXP-001の実行条件、Guard、自律境界、promotionは変更しません。

## 採取と提案

直近7日の完了CI失敗と、PR review/commentの確定レビューサマリーを候補として収集します。CIはrun IDとattemptを区別し、最終jobの`completed_at`を用います。reviewは`submitted_at`、commentは`created_at`を用い、更新日時を発生日と解釈しません。日時欠測は採用しません。観測日付はUTCです。

CIのcancelled/skipped/neutralは失敗に含めません。任意本文の意味推定はせず、`review_package.py`と同じサマリー行および生成表のみを読みます。曖昧・重複・不正な表は欠測です。原文、ログ、秘密値、プロンプトは転載せず、ID・結論・日時・数値とcanonical GitHub URLだけを保存します。観測は原因未分類のcandidate（count=1）であり、原因分類・既存件数更新・promotionを行いません。

変更はledgerへの新規entry追記とAGENT_HARNESSの生成表だけです。既存entryと生成領域外は保持します。同じEvidence URLは再追記しません。Observe workflowと専用提案branchを採取対象から除外します。

## 実行と権限

```bash
GH_TOKEN=... python scripts/observe_learning.py --repo owner/repository
```

これはdry runです。ローカルのledgerを書き換えません。`--publish`はdefault branchのGitHub Actions refのみ許可します。単一jobの必要権限はcontents:write / pull-requests:write / actions:readです。API読み取り完了とschema検証後にのみdraft PRを作成します。API host以外へのLink/redirectは拒否し、エラーは安全なコードのみを出力します。

専用branchは`automation/harness-observe-<内容digest>`です。既存open提案・既存ref・main移動では上書きせず停止します。API失敗でpartial収集を投稿しません。publish途中の失敗で作成済みrefが残る場合も上書きや削除はせず、Operatorが状態を確認します。

RepositoryのActions設定でGitHub ActionsによるPR作成が許可されている必要があります。無効ならpublishは失敗します。**GITHUB_TOKENで作成したPRは通常のpull_request CIを起動しません。** Humanによるclose/reopenまたは別の承認済み認証でCIを起動し、最新headの必須CIと独立レビューを確認してから既存境界に従ってmergeします。自動mergeや自動承認は実装しません。

## 検証と制約

`python scripts/test_observe_learning.py`はネットワーク・書込みなしで、attempt/日時、本文非転載、候補の冪等性、既存状態保持、main移動、既存draft/ref保護、外部API拒否、paginationを検証します。通常CIにも追加しています。

各endpointは100ページ・1ページ100件、responseは8MB、request timeoutは20秒、job timeoutは15分に制限します。履歴増大やrate limitで全取得できないと提案を出しません。古いrunの再試行が直近で完了する場合を落とさないため、run作成日だけで早期打切りをしません。この制約下で取得成功した範囲の観測であり、GitHub外の失敗や自由形式レビューは対象外です。
