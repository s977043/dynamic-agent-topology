# Human Attention pilot proposal

**Status: proposal / manual worksheet。実測・効果判定は未実施。** Tracking: [#287](https://github.com/s977043/dynamic-agent-topology/issues/287)。

既存の[Metrics](METRICS.md)・[Experiment protocol](EXPERIMENTS.md)を使い、人間の注意時間を小さく観測するための任意の手順です。正式なArtifact kind、Metric Schema、新しいGate、Runtime、Software Factory、Routingの追加ではありません。既存の権限・独立レビュー・Operator条件を変更しません。

## 既存契約との接続

DATの`human_interventions`は回数であり、時間や認知負荷ではありません。共通語彙はPlanGateの[Human Attention Metrics（参照revision固定）](https://github.com/s977043/PlanGate/blob/0d8d9468b815ed7068b31b1a5742667d745ad202/docs/working/discussions/2026-09-23-human-attention-metrics.md)と照合します。これは語彙の参考であり、別Repositoryの権限をDATへ移すものではありません。V2のevent所有者はPlanGate #1285、横断評価は#1343 / #1349であり、DATに同じ実装を複製しません。

この提案の起点はユーザー提供の「My New Agentic Workflow」調査メモです。記事中の実績値をDATでの改善Evidenceにはしません。既存#64の「介入回数から認知負荷を推定しない」という境界を維持します。

## 最初の検証を小さくする

まず1つのpaired taskで、時間・判断・Evidenceを欠測なく記録できるかを確認します。これは**計測の実行可能性の確認**であり、効果の一般化や採用判断ではありません。新しい課金model sessionや実験を本書だけで開始しません。

最初のcandidateは同じ成果・同じEvidenceを提示するhandoff presentationの変更だけにします。Topology、model、effort、Runtime、tools、権限、承認点は固定し、Routingや並列度の変更を混ぜません。既存の固定された実験・評価対象を途中で変更しません。

効果評価へ進む前に、対象Issueに次を記録します。

| 固定する項目 | 最低限の内容 |
|---|---|
| 仮説・介入 | どの提示方法が、何の読解・調整を減らすか。baseline / candidateのrevision |
| 対象集合 | task profile、eligibility、Scenario / blockId、予定ペア数、失敗・中断・除外の扱い |
| 測定方法 | active intervalの開始・終了、measurement mode、欠測規則、測定overhead |
| 品質条件 | 同一のAC、独立したmaterial-item oracle、重大情報・provenance・未検証の可視性 |
| 判断条件 | 最小の実用的改善幅、許容回帰、費用上限、観察期間、停止条件 |
| 評価者・順序 | 評価者数、順序の反転/ランダム化、経験差・再読学習の扱い |

未設定なら結果を見て後付けで閾値を作らず、計測確認の結果に留めます。同一人物が同じtaskを続けて読む場合は記憶効果を記録します。fresh model contextだけでは人間の学習は消えません。効果評価では複数の対応fixtureと順序の釣り合わせを検討します。

## 手動worksheet

既存Issue / 実験記録から参照できる場所に、必要な値とEvidence参照だけを保存します。以下は記入欄の例であり、新しいSchemaや必須Artifactではありません。未取得欄を推測で埋めません。

| 欄 | 記録する内容 |
|---|---|
| Identity | task/run/PR、repository head、Scenario / blockId、baseline/candidateの対応 |
| Observation | `explicit` / `bounded_approximation` / `unavailable`、観測区間、欠測理由 |
| Active time | 実際に読む・判断する・応答する秒数。近似なら下限・上限 |
| Coordination | 状況確認・再説明・競合調整に使ったactive timeの内訳。Active timeへ再加算しない |
| Measurement overhead | timer操作・記録に使った時間。task attentionとは分離 |
| Interventions | 独立した判断要求episodeのIDと回数。同じ要求への複数click/commentは重複計上しない |
| Outcome / guards | 受入・失敗・中断・不明、AC/Evidence参照、重大情報の欠落、未検証事項 |
| Resources / limitations | token/費用の観測方法、待ち時間、順序・習熟・欠測等の交絡 |

同じ人の重複intervalは時間の和集合で数えます。例えば`[0,60]`と`[40,100]`は100秒で、120秒ではありません。分類が重なる場合は内訳を解消するか重複を明記し、内訳をそのまま合計しません。複数人の負担を合算するときはperson-secondsと明記し、wall-clockと区別します。

Agentの実行時間、PR作成からmergeまでの経過時間、通知後のqueue待ちをactive timeへ混ぜません。観測が完全で本当に人間が関与しない場合だけ0を記録します。計測していなければ`unavailable`、判断要求が存在しない場合の判断待ち時間など概念が適用されない場合は`not_applicable`です。凍結済みRunの`humanInterventions`や過去の未観測時間をこの定義で書き換えません。

## 比較と欠測

比較キーはExperiment / Scenario / blockIdです。両条件で測定方法・区間・品質条件を揃えます。Metricごとに両側の観測が揃うペアを示し、対象件数と欠測理由を併記します。異なる母集団の平均を割ってpaired比とは呼びません。観測済みの部分集合で差があっても、欠測が結果依存なら全対象への一般化はできません。

上下限のある近似を一点の実測に丸めません。baselineが`[120,180]`秒、candidateが`[90,150]`秒なら差の範囲は`[-90,30]`秒で、減少したとは断定できません。

`compare_paired_blocks.py`の#286対応は既存`RunEvaluation`のtokens / wall-clock比較の修正です。**この手動worksheetやHuman Attention時間を読み込む機能ではありません。** 未知の欄を既存Schemaへ追加して通そうとせず、最初は記録と算術を別途照合します。

完了・受入済みtaskだけを抽出して失敗や中断を隠しません。全eligible taskのoutcome分布と欠測を報告し、受入成果当たりの負担を出す場合は失敗・再試行分も同じ事前定義の対象集合に含めます。

## 補助指標を使う場合

最初の1ペアでは必要な指標だけ測ります。回復率・流出不具合率・費用を使う場合は分母と観測範囲を先に固定します。

- 自動回復率: 自動修復対象として事前定義した失敗episodeのうち、人間の修正なしで独立検証を通過した割合。retry回数を成功件数にしません。対象失敗が0件ならN/A、観測不能ならunavailableです。
- 完了後の不具合: 観察期間と検出方法を揃えます。観察期間未了・検査未実施を「不具合0」と扱いません。
- 受入成果当たりの費用: 同じ対象集合の失敗・retryを含む総費用 / 受入件数。0件ならN/A、費用未取得ならunavailableです。定額料金の配賦は実消費と分け、人件費への換算率も明示します。

## 判断・停止・残作業

注意時間が減っても、重大情報が消える、provenanceが失われる、必須検証を省く、権限を越える場合はcandidateを採用しません。安全上の違反は欠測によるINCONCLUSIVEに隠さず、違反として扱います。主要な観測や品質Evidenceが不足する場合は改善を宣言しません。

採用・継続・修正・見送りの判断は既存の評価/権限境界へ返します。時間差から自動でApprovalを出しません。試行数や儀式を増やすこと自体を目的にせず、計測が重すぎれば項目や介入を縮小します。

個人の査定には使いません。同意・保存期間・アクセス範囲を実施前に確認し、氏名・個人別行動ログ・秘密・生の会話全文を公開Repositoryへ保存しません。集計と匿名のtask/Evidence参照で目的を満たせる場合はそれに限定します。

未完了は#287で追跡します。文書がmergeされても、Operatorによる実測、独立した品質確認、効果判定は完了しません。実測なしの合成例やテストPASSをHuman Attention改善のEvidenceに転用しません。
