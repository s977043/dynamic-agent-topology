# 提示資料 B

**計測練習用の教材です。実PRを操作しないでください。** PR #289の変更を題材にし、独立レビュー未到着という判断時点を仮定しています。実際のPRはその後レビュー・merge済みです。この教材は現在のPR状態や、過去の画面そのものを再現した原本ではありません。

同じ判断材料を並べ替えた資料です。計測中はもう一方の提示資料・採点基準を開かず、下の5問へ回答してください。これは資料から判断を抽出する練習であり、コード全体の再監査ではありません。

## 次の判断に必要な条件

この教材の判断時点では、作成者以外のセッションによる独立レビューはまだ届いていません。これは固定した教材の仮定であり、現在のPR状態の主張ではありません。[教材前提]

通常PRのAgent mergeには、必須CI成功と別セッションの独立レビューで未解決必須指摘0などの条件が必要です。作成者の自己レビューは独立承認ではありません。独立レビュー担当が対象head・差分・Evidenceを確認し、その後に最新head/base/CIと他のmerge条件を再確認します。[S3]

## 変更と互換性

対象headは`107ff8d8b823ce6483472797867b531ca79023b1`、baseは`7eae35b2f29bb0903aab21f3637d587c48c2c7ea`です。変更は比較helper、既存テスト、METRICS、手動計測proposalの4ファイルです。元のsummarizer、Schema、Runtime、権限、依存は変更していません。[S1][S3][S4]

片側欠測を含む平均比は、両条件の値が揃うペアだけから計算します。T0=[100,200]、T1=[欠測,400]なら2.666…ではなく2.0です。条件別の記述平均`conditionMeans`は維持し、JSONへ`pairedMetricSummary`を追加します。[S1]

Scenarioを跨いで重複するblockIdの除外指定は、従来の複数除外からexit 2の拒否へ変わります。欠測のない一意な入力の数値は維持しますが、すべての入力で後方互換という意味ではありません。[S1][S4]

## 確認できたこと・未実行の範囲

対象headの`validate` / `Analyze Python` / `CodeQL`は成功しています。spec-lintはCPython 3.12.15で実行し、既存18 Run・9ペアのtoken比2.206354806778、16 Run・8ペアの2.219870243384を確認しました。CIの合成merge refはmainへのmerge完了を表しません。[S2]

EXP-001原本33 blobの維持をCIで確認しています。一方、active-freeze限定preflightとUbuntuにないmacOS専用sandbox probeはSKIPです。これらを実行済みとは扱いません。[S2]

## まだ証明していないこと

Human Attentionの実測は、この教材の材料には含まれません。合成テストや既存Runの数値一致は、人の注意時間が短縮したEvidenceではありません。手動計測proposalは新しい実験起動・課金・承認・mergeを許可するものではありません。[S4]

## 回答する5問

1. この教材の時点でmerge条件は充足していますか。未充足なら何ですか。
2. 次に誰が何を確認しますか。作成者の自己レビューで置き換えられますか。
3. 利用者に伝えるべき挙動・出力の変更を挙げてください。
4. 検証Evidenceの場所と、その実行環境・未実行の範囲を挙げてください。
5. Human Attentionが改善したと判断できますか。その理由は何ですか。

## 共通のEvidence参照

- [S1] 比較処理と回帰テスト: [compare_paired_blocks.py](https://github.com/s977043/dynamic-agent-topology/blob/107ff8d8b823ce6483472797867b531ca79023b1/scripts/compare_paired_blocks.py)、[test_compare_paired_blocks.py](https://github.com/s977043/dynamic-agent-topology/blob/107ff8d8b823ce6483472797867b531ca79023b1/scripts/test_compare_paired_blocks.py)。
- [S2] 対象headのCI: [spec-lint job](https://github.com/s977043/dynamic-agent-topology/actions/runs/41474916271/job/125377816757)、[CodeQL workflow](https://github.com/s977043/dynamic-agent-topology/actions/runs/41474916299)。
- [S3] 当該revisionの権限・独立レビュー条件: [AGENTS.md](https://github.com/s977043/dynamic-agent-topology/blob/40d7b94e027373b659d1860db7e1309535e81d3f/AGENTS.md)。
- [S4] 互換性と計測範囲: [METRICS.md](https://github.com/s977043/dynamic-agent-topology/blob/40d7b94e027373b659d1860db7e1309535e81d3f/docs/METRICS.md)、[HUMAN_ATTENTION_PILOT.md](https://github.com/s977043/dynamic-agent-topology/blob/40d7b94e027373b659d1860db7e1309535e81d3f/docs/HUMAN_ATTENTION_PILOT.md)。
