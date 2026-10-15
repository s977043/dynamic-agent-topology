# Cloudでの知識整合性検証（#63）

2026-10-16 JST、Python 3.12.14 / Linux x86_64、基準main `3b760ffc56bd724d6378abaff1a46e7036365fab`。[事前計画](CLOUD_VERIFICATION_PLAN.md)に従った合成資料の限定検証です。新しい知識基盤・本番admission gate・Schemaは採用しません。

## 実行とレビュー

計画とoracleを測定前に独立レビューしました。実装レビューでは、欠測をFAILにする問題と、抽出結果を検証対象と同じ関数で正解扱いする問題を修正。欠測はUNKNOWN、明示された矛盾はFAILとし、実抽出の正解ラベルをPENDING_REVIEWにして初回測定を委託しました。測定後、別セッションが4 PDFの描画・実テキスト・全23件の出力を原文と照合し、独立した正解ラベルで集計しました。

- 実行担当: `/root/knowledge63_execute`。初回1回、再測定・結果の除外なし。
- 独立Reviewer: `/root/knowledge63_resume_review`。実runtime model ID不明。PDFのimage tableは目視でA=-12 / B=7を確認。
- rootも画像・出力を確認。既存出力先への再実行は拒否され、初回の全bytes不変を確認。
- 実行時依存: ReportLab 4.4.9、Pillow 12.3.0、pypdf 6.10.0、PyMuPDF 1.26.6、pdftotext 25.03.0。導入・ネットワーク・model呼出しなし。

## 結果

`process`は抽出exit0だけ、`link`はprocess成功とsource hashの存在・synthesis接続だけを見る比較です。hashの正しさはlink baselineでは確認しません。候補は事前宣言したsource facts、矛盾、hash/provenance、revision、接続を別々に検査します。既知のoracleを受け取る方式であり、一般の事実検証器ではありません。

| 層 | 件数 | 独立内容判定 correct / incorrect / UNKNOWN | process・linkが通したincorrect | 候補が通したincorrect |
|---|---|---|---|---|
| 実PDF抽出 | 12 | 10 / 0 / 2 | incorrect母数0、比較不可 | 同左 |
| 抽出後の故障注入 | 8 | 2 / 6 / 0 | 各6/6 | 0/6 |
| 合成の鮮度context | 3 | 2 / 1 / 0 | 各1/1 | 0/1 |

実PDFでは両engineの符号付きtext・2 columnの宣言factsが一致しました。**実際の非空抽出に誤りは観測されていません**。画像のみの2件は抽出テキストが空白で、内容判定と候補はUNKNOWN。process/linkはこれも通しており、「抽出成功」と「検証済み」を区別する必要があります。OCRは実行しておらず、OCRの精度は判断しません。2 columnも宣言factsの有無だけを調べ、一般的な読順を評価していません。

故障注入の符号欠落・必要section削除・別文献の連結は、**抽出後に意図的に加えたもの**で、抽出器の自然発生バグではありません。符号/外来markerはFAIL、必要sectionの欠測はUNKNOWNです。ここでのincorrectは宣言済みの完全性・source帰属に対する破損/欠落を含み、すべてが単独の虚偽命題という意味ではありません。

### 正しい内容の保留とorphan

内容判定はcorrect14件をすべてPASSにしました。一方、全体admissionはそのうち9件を接続・provenance・鮮度の理由で保留しました。これを内容の誤検出と混同しません。

| 層 | correct母数 | 全体admissionのFAIL保留 | UNKNOWN保留 | 理由 |
|---|---|---|---|---|
| 実PDF抽出 | 10 | 2 | 4 | orphan、provenance欠測、revision欠測 |
| 注入 | 2 | 2 | 0 | stale source hash（textは正しい） |
| 鮮度context | 2 | 0 | 1 | revision欠測 |

orphanの正しいtextは内容PASS/接続FAIL、接続済みの破損textは内容FAILまたはUNKNOWN/接続PASSとなりました。リンクの有無と内容の正しさは別の観測です。全体admissionは23件中PASS5 / FAIL9 / UNKNOWN9でした。

## 再現方法と証跡

任意の新しい空output先を指定します。probeはdefault CIには追加していません。上記optional依存を備える環境が必要です。

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/probes/knowledge_integrity_probe.py \
  --output-dir /tmp/dat-knowledge63-new-run
```

`oracle.json`、readonly PDF、render PNG、engine別text、source hashの前後、commands/versions、23件のJSON/CSV、初期summaryを生成します。**初期summaryのPENDING_REVIEWは未確定で、最終結果ではありません。** Reviewerが画像と出力を比較して別のannotationを作る必要があります。今回、実抽出の非空10件をcorrect、空の画像2件をUNKNOWNと独立判定しました。残りの注入/合成textも全件レビューしました。summaryを上書きせず、独立annotationは別保存です。

初回のローカル証跡は `/workspace/dat-readiness/knowledge63-firstrun/`、独立annotationは `/workspace/dat-readiness/knowledge63-independent-review.json`。これらは公開GitHub添付ではありません。scriptと計画、固定oracle・判定表をrepoに残し、第三者は新規生成物から独立に再判定できます。以下のSHA256は初回との同一性確認用で、一般的な真正性保証ではありません。

| 証跡 | SHA256 |
|---|---|
| 実行script | `c61ccde3c7e9d7ea8b492b81ceaf2881e14f4aef74754b564b953be1ee6d568e` |
| 事前計画 | `31b56a92b51f6f76d7fd36dfd416169c8fef76dec7458a3dcd79af561b347e63` |
| raw observations.json | `1bc33d356d37284bbb6bc31b3a798f4d6ee1e71875b6cdf61ea47bf695e63d32` |
| signed PDF | `c95827587173754ab88b6a1bdefeb2df4260da976784997375a7a93df01e69c1` |
| image PDF | `91634a034045408c41292858158b1bd932798d36c889146dee0776fafa1a7545` |
| columns PDF | `a3f7f1e8c025d5da3d77c89a0271e8511a9b5b7219a28aed52d7b9d05a3d90ca` |
| foreign PDF | `d29216e62aa126b857f6ed8a792a9d16a0a90d2c0e13f16a068c45202ca44660` |

4 PDFは測定前後のhash一致。実行時間1.0053秒、summary保存前93,619 bytes。Python起動後の生成/抽出/記録を含み、独立レビュー時間・CI待ち・model/金銭コストを含みません。反復測定や環境間比較ではありません。

## 既存仕様のCloud検証

別の隔離worktreeでmain3b760ffのspec-lintにある39 run stepのうち、既存依存のinstallだけを実行せず、残り38 shell stepはすべてexit0でした。active Freeze専用のone-time監査はshell内の条件でSKIPされており、その監査の実行成功とは数えません。completed snapshotの33 blob監査はPASS、別途`validate_pilot.py --require-complete`も期待18件PASS。probeの測定やPR headのCIとは別のbaselineです。

## 判断と残る範囲

既知sourceとcritical factsを持つ小さいcorpusで、process成功・接続だけでは破損/未確認を受理し得ること、原文照合で保留できることを確認しました。oracleとgateはこの用途向けに設計されており、代表文献での抽出精度・未知の矛盾検出・コスト改善のbenchmarkではありません。人手工数・実世界の誤受理率・一般H1/H2/H3効果はINCONCLUSIVEです。

次は独立した新規corpus/held-out facts、実際のextractor故障、OCRを含むimage/table/layout、source改版とsynthesis更新、作業者の判定負荷を別に評価します。現時点でKnowledge Plane・graph・常用gateを採用せず、#63はopen維持。EXP-001の受理/DECISION/Frozen dataとRelease公開権限は変更していません。
