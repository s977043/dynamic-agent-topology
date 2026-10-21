---
name: dat-select
description: 作業に着手する前に、タスクを確実に解ける最も単純なエージェント構成（P0/T0/T1/T2/T3）を根拠付きで 1 つ選ぶ。「DAT で構成を選んで」「どのトポロジーで進める？」「dat-select」で使う。構成の自動適用はしない。
---

# dat-select

着手前に、このタスクに足りる最も単純な構成を 1 つ選び、短い判断として示す。ランタイムの設定・エージェント起動・ファイル書き換えはしない。

## 正本

定義は次のファイルにある。ここに写さず、必要な箇所だけ読む（パスはこの SKILL.md からの相対パス）。

- P0: [baselines/P0_deterministic_pipeline.yaml](../../baselines/P0_deterministic_pipeline.yaml)
- T0〜T3: [topologies/canonical/](../../topologies/canonical/)
- 選び方の既定: [policies/routing/R0_dynamic.yaml](../../policies/routing/R0_dynamic.yaml)、上限: [policies/escalation/E0_default.yaml](../../policies/escalation/E0_default.yaml)
- 用語（Reviewer と Verifier の違いなど）: [docs/GLOSSARY.md](../../docs/GLOSSARY.md)

## 手順

1. タスクから次を読み取る。分からない項目は `unknown` とし、推測で埋めない。
   - 決定的な処理（スクリプト・既存ツール）だけで終わるか
   - complexity / ambiguity / risk（low・medium・high）
   - 既存の Evidence（テスト・CI・再現手順）が受け入れ判断に使えるか
2. 単純な側から順に当てはめ、最初に足りたものを選ぶ。
   - **P0**: エージェントなしで決定的に終わる
   - **T0**: complexity・ambiguity とも low。1 エージェントで実装と確認ができる
   - **T1**: 生成物を受け入れる前に、別の主体（別セッション・別モデル・人・CI）による検証が要る
   - **T2**: risk が high で、検証に加えて受け入れ判断を持たない助言レビューが要る
   - **T3**: 専門役割を別タスクに分ける必要が、具体的な理由で示せる。既定にしない
3. E0 の上限（T2・3 エージェント）を超える案は、超える理由を書いたうえで人に確認する。
4. 複雑な構成を選ぶ理由は、そのタスクの具体的なリスクで書く。「念のため」「一般に良いとされる」は理由にしない。

## 出力

次の形で 10 行程度にまとめる。

```text
構成: T1（worker → verifier）
理由: <タスク固有の根拠 1〜3 行>
単純な案を選ばない理由: <T0 では足りない点。P0/T0 を選んだときは省略>
unknown: <判断に使えなかった項目。なければ「なし」>
検証: <誰が・何で受け入れを判断するか>
```

- 構成を選んだことは効果の証拠ではない。優劣の結論は書かない。
- 実行後の記録は `dat-observe` で行う。
