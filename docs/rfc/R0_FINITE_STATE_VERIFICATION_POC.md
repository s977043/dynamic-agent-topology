# R0 routing: 有限状態探索PoC（2026-11-24）

> **Status: PoC / SHADOW-ONLY / NOT ADOPTED**
> Tracker: [#335](https://github.com/s977043/dynamic-agent-topology/issues/335)
> 既存の仕様判断: [#277](https://github.com/s977043/dynamic-agent-topology/issues/277)（分岐順と尺度は既知の論点）
>
> この文書と診断スクリプトは**現行仕様を変更しない**。候補不変条件の違反を発見しても、Routing Policyの欠陥・高リスクタスクでの品質低下・新たなマージ条件が確定したとは扱わない。

## 目的・出典

Zenn記事「[なぜ今形式検証なのか](https://zenn.dev/ncdc/articles/dcec80b0c067b0)」（2026-11-19）は、既存テストに加え、仕様化した安全性の性質を証明・探索する考え方を紹介する。本PoCではまず**新しいTLA+ / Lean 4依存を導入せず**、現行R0の静的ルーティング判定を有限集合に抽象化して全列挙する。状態遷移・並行実行を扱うTLA+モデルそのものではない。

- 正本: [`policies/routing/R0_dynamic.yaml`](../../policies/routing/R0_dynamic.yaml)
- 現行の手順: [`skills/dat-select/SKILL.md`](../../skills/dat-select/SKILL.md)（上から最初の一致分岐を選ぶ）
- 説明と制約: [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md)（未知値では保留、R0にはfallbackなし、Project Bindingとは別）
- 先行する手動の発見と採否候補: [#277](https://github.com/s977043/dynamic-agent-topology/issues/277)

**今回新しく提供するのは再現可能な診断とそのテスト**であり、「high riskがT0になる」現象の発見自体は#277で既出である。

## 対象・抽象化

`scripts/audit_routing_states.py` は実際のR0 YAMLを `yaml.safe_load` で読み、各 `when` のキーで使われる値と「既知だがどのルールの値とも一致しない代表値（`__OTHER_KNOWN_VALUE__`）」を組み合わせ、**入力がすべて既知である**場合の first-match を再現する。

| 入力軸 | 抽象値 | 個数 |
| --- | --- | ---: |
| `complexity` | `low`、OTHER | 2 |
| `ambiguity` | `low`、OTHER | 2 |
| `existingEvidence` | `strong`、OTHER | 2 |
| `risk` | `high`、`medium`、OTHER | 3 |

`2 × 2 × 2 × 3 = 24` 状態。OTHER は実際の入力値や新しいenumではなく、現在の「文字列の完全一致」だけを前提にした同値類の代表である。`unknown` / 欠測 / 値の推定、Project Bindingの `defaultTopology`、Escalation上限、Runtime固有挙動、異なるRoutingPolicyへの一般化は対象外。モデルが実際のAI Skill実行と一致するかは別途E2Eで確認する必要がある。

## 候補不変条件（未承認）

**H1（候補のみ）**: `risk=high` なら、`when: {risk: high}` だけを条件とするルールが指定するTopologyを選ぶ。

これは`#277`で比較候補となった「高リスク分岐優先」を検査できる形にしたもので、**DATが採用した不変条件ではない**。R0の分岐順を変えたり、これを必須CIにして既存動作をFAIL扱いすることはしない。候補ルールが無い、または複数ある場合、判定結果は `NOT_EVALUATED` であってPASSではない。

## 観測と再現（2026-11-24）

実行環境: Python 3.13.5 / PyYAML 6.0.3（ローカルの独立再構成したR0とPoCファイルで実行。**Python 3.12のCIでの確認はPR作成時点で未実施**）。

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/audit_routing_states.py
PYTHONDONTWRITEBYTECODE=1 python scripts/test_audit_routing_states.py -v
```

| 観測（対象R0の上記抽象） | 件数 |
| --- | ---: |
| 全状態 | 24 |
| T0選択 | 6 |
| T1選択 | 3 |
| T2選択 | 6 |
| 分岐一致なし | 9 |
| H1に対する反例 | **2** |
| 合成ルールに対するテスト | **6件 PASS**（Python 3.13.5） |

H1反例は、`complexity=low`・`ambiguity=low`・`risk=high` で、`existingEvidence=strong` と OTHER の2分類。いずれも先頭分岐がT0を返す。これは **構文上の分岐順の再現**であり、「実際の高リスク作業におけるT0の安全性」や「T2の優位性」の測定結果ではない。

`test_audit_routing_states.py` は次を検査する。
1. 最初の一致分岐が優先されること。
2. 衝突する合成ルールに対して反例が検出されること（negative）。
3. 高リスクの分岐を先頭に置いた合成ルールでは、同じ候補に対する反例が無いこと（positive）。
4. 検査対象となる明示ルールが無い場合、`NOT_EVALUATED` になること。
5. 実際のR0 YAMLを読み込み探索できること（分岐の結果自体は固定しない）。
6. 不正な空条件のポリシーが拒否されること。

この診断コマンドの終了コード0は「探索が正常終了した」だけであり、H1の承認や検証PASSを意味しない。入力ファイルの欠損・不正では終了コード2。新規スクリプトは**既存必須CIへ未配線**であり、PRのCI成功は本PoCテストの自動実行を意味しない。

## 複数視点レビューと対応

| 観点 | 懸念 | 本PoCの処置 |
| --- | --- | --- |
| Architecture | ルーティングと権限・実行を混同する | 読み取り専用のPolicy探索に限定し、新Schema・Runtime変更なし |
| QA / 検出力 | 自明なPASSを「検証済み」と誤解する | 違反有り・無し・未定義を分離し合成ルールを検証 |
| Security / Safety | H1を無承認で安全ルールに格上げする | 候補を明記、CI・Guard・Merge Gateを変更しない |
| Compatibility | R0分岐変更は既存consumerにbreakingな可能性 | Policy・Skill・README・Schemaを一切編集しない |
| Maintenance / Cost | 形式検証用の新スタックと重複エンジンが増える | 既存PyYAML、追加依存なし、24状態だけを探索 |

以上は**同一セッション内の観点別レビュー**。DATの自律境界が求める、PR作成セッションとは別の独立Reviewerの検査ではない。

## 横断導入への接続・停止条件

- **PlanGate**: [#1640](https://github.com/s977043/PlanGate/issues/1640)の「入力軸 × 期待状態 × 再開可否」を、まず既存テストの不足として評価する。承認・再開をまたぐ状態遷移に固有の盲点が残る場合にTLA+/TLCの比較PoCを検討。C-3/C-4などの承認契約は変更しない。
- **River Review**: [PR #2881](https://github.com/s977043/river-review/pull/2881)のVerification-First評価と[PR #2900](https://github.com/s977043/river-review/pull/2900)の状態遷移レビューを正本候補として参照。反例を新しい独立の判定エンジンにせず、既存evaluation/fixtureへ取り込めるか先に確認する。
- **DAT**: H1を採用するかは#277の事前比較・人間の意思決定に従う。計算結果をPolicy・public contract・実モデル起動許可へ昇格させない。

**次のGate**: Python 3.12 CI、exact-head diff、別セッションの独立レビュー、凍結対象への変更ゼロ、Human-only操作の不実行を確認する。いずれか不明ならDraftのまま停止し、検証が成功したと主張しない。TLA+を追加する判断は、再試行・並行・状態遷移の反例が既存テストでは取りこぼされる実例を確認してから行う。
