# 反復採点と実行証跡のリハーサル

#293の保存済み成果物を2 block、T0→T1 / T1→T0の順で再採点した。各blockで初期コードを負の対照とし、計6 subprocessの結果・時刻・exit・hashを保存した。**6/6が既知期待値と一致**し、入力の前後hashは不変だった。これはP0による保存成果物の再現性確認で、新しいT0/T1エージェント比較ではない。

事前の[PLAN.md](PLAN.md) SHA256は `0b7a1cb28dc1720a6a8ab9c4309262211ec9f7167dd5764f0f00d22502e7bac5`。実行前に親へ通知したが、独立timestamp証明ではない。実行時の完全commit・plan/script hashは[manifest](results/manifest.json)に保存した。

| block | 採点順 | 結果 |
|---|---|---|
| b01 | 初期→T0→T1 | 6/18→18/18→18/18 |
| b02 | 初期→T1→T0 | 6/18→18/18→18/18 |

[summary](results/summary.json)、[別置対応表](results/mapping.json)、各opaque labelのJSONに原本を保存する。採点器にはarm名を渡さないが、公開ソース・hashと共有FSから対応は分かり得るため、盲検を実証したとは扱わない。既知の結果を再生しているのでheld-out testや独立のモデル試行数は増えない。順序反転は採点順のみであり、モデルの順序・cache交絡を解消しない。

| 計測 | 今回のoffline | 次回liveで必要な根拠 |
|---|---|---|
| 時間 | monotonicの採点subprocess時間 | 各legの開始/完了イベント、親観測遅れの区別 |
| model / effort | null（model呼出しなし、非該当） | 実効値。設定・継承の推測は不可 |
| tokens / USD | null（取得対象のmodel呼出しなし） | 全legのusageと価格根拠。欠測を0にしない |
| 人間注意時間 | null（人間計時なし） | 実参加者によるactive attention計時 |
| 隔離 / blinding | 未実証 | workspace/権限境界と対応表開示の実測 |
| Verifier要求・返答 | 非該当 | [証跡テンプレート](VERIFIER_TEMPLATE.md)の本文/hash/返答要約 |

## 再現コマンド

```sh
PYTHONDONTWRITEBYTECODE=1 python docs/runtime-canary/repetition/replay.py --out /tmp/dat-replay-unique
```

既存directoryはexit 2で上書きを拒否する。新規directoryを指定すること。信頼済みの自作fixture専用で、oracleはPython importを実行する。未信頼コードのsandboxとして使用しない。外部依存・network/model呼出し・CI変更はない。

[validation.json](validation.json)にはPython3.12での負側検査を保存した。既存directoryへの再実行はexit 2、全既存ファイルhash不変。source欠落はexit 1、6件すべてのFileNotFoundErrorとsummaryを保持し、成功扱いにしない。実行結果の時刻はこの環境固有であり、再実行時の一致対象は採点・hash・順序・欠測状態である。

## 判断

採点経路の再現性と失敗保持は確認できた。既存のT0維持判断を変更する新しい効果証拠はない。live比較の反復、model/effort固定、権限隔離、モデル費用・人間注意時間は未実施。次は実行時の取得可能性を確認し、取得不能ならcontrolled比較を保留する。#244/#248/#295の実験やHuman専権の承認を置き換えない。
