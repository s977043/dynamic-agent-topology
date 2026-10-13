# Promoteの定期起案

Issue #159④。`harness-promote.yml`は月曜07:13 UTCと手動実行で、trusted mainのledgerからcount 2以上・candidate・同Repository Evidenceが揃う項目のGuard検討文書draft PRを作ります。採用・ledger state変更・規則・Guard・codeの自動変更は行いません。既存対策（L-009/L-010のreview_package.py等）の効果を先に確認します。

自身のworkflowファイルがmainで変更されたpushも、反映後の実運用確認として起動します。jobは非fork repositoryかつdefault branchがmainの場合だけ実行します。forkにrunが作られないことまでは保証せずjobを停止します。生成文書・ledger・他branchのpushは起動条件に入りません。push時はevent SHA、週次/手動時はmainをcheckoutし、そのSHAをログに記録します。APIで取得したpublisher baseは起案commitのparentから確認し、event headと混同しません。

path条件は変更ファイルのいずれかが一致すれば成立し、workflowとledger/docの同時変更も対象です。生成文書/ledgerだけの変更は対象外です。両harness workflowを同時変更したmain pushでは各workflowが一回ずつ実行対象になります。他branch/path非一致のrun非起動と、fork/default変更のjob skipを区別します。

run SUCCESSだけではdraft作成の証明になりません。`DRAFT_PR_N`、GitHub上のdraft状態、一文書限定の差分を照合します。OPEN_PROPOSAL/PROPOSAL_UNCHANGED等のno-opを初回起案成功として扱いません。初回のPR作成拒否も停止条件の実測として保存します。

生成先は`docs/harness-proposals/promote-candidates.md`一件のみです。文書内容のdigestで専用branchを決め、生成時刻/main SHAを文書に含めないため同じ候補は再起案しません。open自動PRがある間は停止し、人が変えたbranch、過去PR、残存branchを再利用・更新・削除しません。候補が消えた場合も文書やPRを自動削除しません。原因確認・採否・更新はHumanが判断します。

GITHUB_TOKENが作成したPRは通常PR CIを自動起動しません。schema/入力検査とPR CIを区別してください。Humanによるclose/reopenまたは別認証の操作でCIを起動し、必須CIと独立レビューを確認します。これらのlive操作経路は未実測です。実運用受理にはworkflow実行、draftのみ作成、同一入力no-op、CI起動をGitHubで確認してIssue #159に証跡を記録します。起案対象Guardの実装・採用はHuman承認の別PRです。

## 停止・回収

初回の実測結果、403停止時の確認順序、受理条件は[初回運用検証と復旧](HARNESS_LIVE_OPERATIONS.md)を参照してください。

`MAIN_MOVED_RETRY`は次回mainで再検討します。`PROPOSAL_REF_EXISTS`は同名refの由来を確認し、上書きしません。`PROPOSAL_HISTORY_EXISTS`は過去起案を確認します。API失敗後はdraft/ref/commitの有無を確認し、残存refを自動削除しません。workflowを無効化する場合もHumanがGitHub設定で実施します。tokenやrawログを公開しません。

## 検証

Python 3.12で`python scripts/test_harness_promote.py`、既存Observe tests、ledger、guidance、Freeze検証を実行します。API helperはObserveと共有し、redirect・size・pagination制限を維持します。
