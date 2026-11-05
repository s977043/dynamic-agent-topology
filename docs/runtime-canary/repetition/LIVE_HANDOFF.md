# 保存candidateへのlive Verifier handoff（2026-11-04）

これは既存成果物を新しいVerifierへ渡した運用確認1件。新worker run、T0/T1反復比較、offline replayの追加標本ではない。独立採点oracleの18ケースとも別の確認である。

## 入力と依頼

main `541a4bedad068af4e0f5951ad1cc075af3308ac6` の `docs/runtime-canary/t0-final.py` を `candidate.py` にコピー。taskは同じ `task.md`。Verifierにarm名や前回結果を伝えず、fork_turns=noneで起動。親は由来を知っており、共有FSへのアクセス制限は強制していないので、盲検保証ではない。

- candidate SHA256: `c7cefb20433a3266be9b44e25d59a111da3810be943e9fc53a2386122d4c0e5c`
- task SHA256: `59209283ab188ad164febe0ca0adcef27bf101e8359194dc5d22d54317bad01d`
- 公開可能な依頼全文（`<scratch>`のみ実際の作業用pathを置換）:

```text
Verify a public synthetic Python candidate against its task. Read only <scratch>/task.md and <scratch>/candidate.py. Use independent in-memory tests; no editing, network, delegation, or model CLI. You are not told its source arm. Report PASS/FAIL/INCONCLUSIVE, test method and counts, required findings, limitations. This is a live verification handoff check on an existing saved candidate, not a new worker run or topology comparison. Finish within five minutes.
```

## 応答要約と証拠限界

host collaboration task `/root/blind_verifier` は **PASS、必須指摘0** と返答。Verifier自己申告では19種類の入力から長さ0〜3の7,240列、固定乱数の10,000列、計17,240件を独自oracleで確認した。最大revision、tie、順序、無効値、入力identityと値の維持を確認したという結果。テストコードそのものを保存していないため、この件数は再現可能な測定値ではなく、Verifierの応答要約としてのみ扱う。最終ソースhashは元のcandidateと一致し、修正なし。

初回依頼直前の親観測UTC `2026-11-04T03:27:35Z`、完了応答受領後の親観測 `2026-11-04T03:28:23Z`。この48秒は親の記録・tool・待ちを含む観測窓で、推論時間や人間の注意時間ではない。推論tokens、USD、実効model/effort、platform session ID、人間active attentionは取得できずnull。task labelをsession IDや別モデル証拠へ転用しない。

通常Pythonオブジェクトの有限検査で、悪意あるsubclass・並行変更は未検証。読み取り範囲遵守は自己申告であり監査ログによる実証ではない。保存コードを隠した名称で渡してPASSを受け取れることは確認したが、Verifierの品質向上効果やfalse accept率はこの1件から推定しない。
