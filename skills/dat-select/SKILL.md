---
name: dat-select
description: 作業に着手する前に、DAT の routing policy に沿って、タスクを確実に解ける最も単純なエージェント構成（P0/T0/T1/T2/T3）を根拠付きで 1 つ選ぶ。「DAT で構成を選んで」「どのトポロジーで進める？」「dat-select」で使う。構成の自動適用はしない。
---

# dat-select

着手前に構成を 1 つ選び、短い判断として示す。ランタイムの設定・エージェント起動・ファイル書き換えはしない。選択条件はこの Skill に持たず、正本の policy を読んで当てはめる（パスはこの SKILL.md からの相対パス）。

- 選び方: [policies/routing/R0_dynamic.yaml](../../policies/routing/R0_dynamic.yaml)
- 上限: [policies/escalation/E0_default.yaml](../../policies/escalation/E0_default.yaml)
- 各構成の意味: [baselines/](../../baselines/)、[topologies/canonical/](../../topologies/canonical/)

## 手順

1. routing policy を読み、その分岐が使う入力（`risk`・`existingEvidence` など）をタスクから読み取る。分からない入力は「分からない」とし、推測で埋めない。
2. routing policy の分岐を上から当てはめ、該当した分岐の構成を選ぶ。どの分岐にも当てはまらないとき、または入力が分からず分岐を決められないときは、構成を推測で選ばず「選択保留」とし、足りない入力を挙げて人（または呼び出し元）に確認する。
3. escalation policy の上限を超える構成になるときは、理由を書いて人に確認する。

## 出力

```text
構成: <topology 名、または「選択保留」>
該当した分岐: <policy の when の内容。保留なら「なし」>
分からない入力: <なければ「なし」。保留なら確認したい入力>
```

- 構成を選んだことは効果の証拠ではない。優劣の結論は書かない。
- 実行後の記録は `dat-observe` で行う。
