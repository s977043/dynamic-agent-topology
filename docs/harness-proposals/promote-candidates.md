# Learning ledger: Guard検討起案

この文書は起案材料です。ledger state・規則・Guard・codeを変更しません。採用と実装はHuman承認の別PRで判断します。

既存の `review_package.py` はL-009・L-010の対策です。既存対策の効果を先に確認し、新規Guardが必要とは断定しません。

## L-009

- 観測: 独立 Reviewer の判断が判断材料不足で誤判定・無効化した（基準文書の取得がネットワークで失敗したまま ACCEPT を出した、Issue コメント未提供で前提を確認できず NO&#45;GO、指定外参照の禁止と Reviewer 起動時の作業ディレクトリ確認が衝突して判定無効）
- 回数: 3
- Evidence: PR &#35;130 の Run acceptance レビュー（Issue &#35;15 comment 6106366753 に至る 4 回）
- <https://github.com/s977043/dynamic-agent-topology/issues/15#issuecomment-6106366753>
- <https://github.com/s977043/dynamic-agent-topology/pull/130>
- 対策検討候補: 判断材料（基準文書・関連 Issue コメント・PR 本文と diff・Artifact）を 1 ディレクトリにまとめ依頼書と共に渡す。作業ディレクトリの確認は許可し、禁止範囲はその外とする

- [ ] 既存対策と再発Evidenceを照合
- [ ] 必要性・反証可能な仮説・変更先を確定
- [ ] 誤検知/取り逃しの検証とrollbackを定義
- [ ] 独立レビューとHuman承認を別PRで取得

## L-010

- 観測: 『指摘ゼロ』を完了の定義にした机上レビューの往復が収束せず（15 回以上）、Run が進まなかった
- 回数: 2
- Evidence: PR &#35;110・&#35;116・&#35;121・&#35;122 のレビュー往復、本番スクリプトの NO&#45;GO 3 回
- <https://github.com/s977043/dynamic-agent-topology/pull/110>
- <https://github.com/s977043/dynamic-agent-topology/pull/116>
- <https://github.com/s977043/dynamic-agent-topology/pull/121>
- <https://github.com/s977043/dynamic-agent-topology/pull/122>
- 対策検討候補: 必須を安全・秘密値・プロトコル違反・回収不能の 4 分類に絞り、推奨は事後改善に回す。同箇所の指摘が続く場合はドライランやリハーサルで実際に動かして確かめる

- [ ] 既存対策と再発Evidenceを照合
- [ ] 必要性・反証可能な仮説・変更先を確定
- [ ] 誤検知/取り逃しの検証とrollbackを定義
- [ ] 独立レビューとHuman承認を別PRで取得

