# 次回live比較用Verifier証跡テンプレート（未実行）

これは入力項目の例であり、起動・課金・権限変更を承認しない。今回の保存成果物リプレイではVerifierは呼ばれない。

## 実行前

- blockId / scenario / arm opaque ID / attempt ID:
- 同一input・task・oracle・worker promptのhash、固定commit:
- runtime/version、実効model/effort（設定値と分離）、権限・workspace隔離の確認根拠:
- worker/verifierそれぞれの予算上限、timeout、最大修正回数:
- worker開始/完了・handoff・verifier開始/完了の時計と取得方法:
- evaluatorにarm対応を開示する時点、対応表保管者、漏洩可能性:
- 新規課金等があればOperator承認の根拠:

## 公開可能な依頼文

合成taskとcandidateのhash固定ファイルだけを渡す。Verifierは別セッションとし、他arm・正解oracle・workerの自己評価を渡さない。正常・異常・境界とinput非破壊性を独立して確認し、PASS/FAIL/INCONCLUSIVE、必須指摘、実施コマンド・結果、未検証範囲を返す。candidateは編集しない。依頼文の正確な本文とhashを保存する。

## 返答要約と照合

- runtimeのsession識別子（取得不能ならnull。task名と混同しない）:
- 入力candidate hash、要求hash、返答取得時刻:
- 判定、必須指摘、根拠・再現コマンド、未検証範囲:
- 修正があれば元candidateと修正後hash、再検証記録:
- worker/verifier/evaluator各legのtokens/USD、取得元、欠測理由:
- 人間active attentionは実参加者による計時の有無。wall timeから推定しない:

実効model/effort・権限・同等input等を揃えられなければcontrolled efficacy比較は開始しない。通常subagentで限定feasibilityを行う場合も別計画として範囲を固定し、不明値をnullにして優劣を主張しない。秘匿情報・private内容・raw reasoningは保存しない。
