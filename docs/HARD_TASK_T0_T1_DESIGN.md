# 難度の高い Task での T0 / T1 比較の評価設計案

状態: **非規範的な設計案（未採用・独立レビュー前）**。実験開始・model 起動・予算消費・experiment Artifact や fixture / scenario の追加の許可ではありません。本設計に基づく model 起動（予備 Run を含む）は Operator が行い、Agent は代行しません。`experiments/`、`fixtures/`、`schemas/`、`topologies/`、`roles/`、`scripts/`、EXP-001 の Frozen file は変更・流用しません。現時点の効果は **INCONCLUSIVE**（実測 0 件）です。

- 起案日: 2026-10-23 / 基準: origin/main `5ed2d2e`
- 動機: [EXP-001 DECISION.md](../experiments/EXP-001-t0-vs-t1/DECISION.md) の Judgment（Keep T0）と Limitation 13（床効果）、[EXPERIMENTS.md](EXPERIMENTS.md) の Re-evaluation triggers（対象 Task distribution の変化）
- 一次ソース: EXP-001 DECISION.md、[experiment.yaml](../experiments/EXP-001-t0-vs-t1/experiment.yaml) の `decisionPolicy`、[EXPERIMENTS.md](EXPERIMENTS.md)、[METRICS.md](METRICS.md)、[AGENT_HARNESS.md](AGENT_HARNESS.md)、AGENTS.md
- 形式の先例: [MODEL_ROLE_SPLIT_DESIGN.md](MODEL_ROLE_SPLIT_DESIGN.md)（#220）、[EXP_TIME_SIGNAL_DESIGN.md](EXP_TIME_SIGNAL_DESIGN.md)（#201）

## 0. Source claim・Evidence・解釈・Judgment の区別

| 区分 | 内容 |
|---|---|
| Source claim | 「Worker と独立 Verifier を分けると難しい Task で品質が上がる」は一般的な主張であり、DAT の観測ではない |
| 観測済み DAT Evidence | EXP-001 の 18 Run（3 Scenario × T0/T1 × 3 rep、Codex / gpt-6.1-sol / high）は全件成功。品質指標は T0/T1 とも上限値で、token 比 T1/T0 は 2.206（18 件）。基準 2・3 が FAIL で Keep T0 |
| DAT 側の解釈 | EXP-001 の 3 Scenario は T0 で既に解ける難度で、T1 の品質上の寄与を測る余地がなかった（床効果）。これは T1 一般の否定でも肯定でもない |
| Judgment | なし。本文の推奨・仮説・閾値は未採用の案で、採用は独立 Reviewer と Human の判断を経る |

## 1. 結論（推奨案）

**Runtime・Model・Effort を固定し、Topology（T0 / T1）だけを変える paired 比較を、「事前に T0 の成功率が低いと確認した Task 集合」で行う。Task の選定（較正）と評価を別の Run 集合に分け、評価集合は較正の後・評価 Run の前に凍結する。**

- 変更因子は Topology の 1 つだけ。モデル差は #220（[MODEL_ROLE_SPLIT_DESIGN.md](MODEL_ROLE_SPLIT_DESIGN.md)）、escalation / stronger model は #93 / #88（[POST_EXP001_EVALUATION_DESIGN.md](POST_EXP001_EVALUATION_DESIGN.md)）の対象で、本設計とは交絡させない。
- 少数 Run の結果は feasibility-only とし、T1 の採用根拠にしない。

## 2. 重複照合

| 対象 | 読んだ範囲 | 扱う問い | 本設計との関係 |
|---|---|---|---|
| [POST_EXP001_EVALUATION_DESIGN.md](POST_EXP001_EVALUATION_DESIGN.md)（#194） | 全文 | 混合母集団での T0 vs stronger model（F）と shadow gate（EXP-002）、失敗後の model 昇格（EXP-003） | 変える因子が model / gate で、Topology は変えない。「T0 が失敗し得る task の母集団」（U2）という部品は共通。本設計は Topology の比較で、問いは重複しない。母集団の調達は同書 §10 の U2 と共有し得る |
| [Issue #93](https://github.com/s977043/dynamic-agent-topology/issues/93) | 本文・全コメント | compound strategy、Critique A–D、Cascade E–G、multi-model、司令官型（PR #219） | T1（Worker→Verifier、同一 model）の難度別比較を正面から扱う arm・設計はない |
| [Issue #88](https://github.com/s977043/dynamic-agent-topology/issues/88) | 本文・全コメント | baseline 失敗後の fresh session / handoff / model 昇格（A–E） | 対象は eligible failure 上の recovery。Topology は変えない。「EXP-001 の成功 Run を失敗として流用しない」は本設計も守る |
| [Issue #82](https://github.com/s977043/dynamic-agent-topology/issues/82) | 本文・全コメント | 反証 objective / 独立 Adversary Role の段階 ablation | 独立 Role 化（C）は近いが、対象は Reviewer / Adversary の判断。本設計は既存 T1 の Verifier を変えずに使う。#82 の carryover・事前宣言・評価者独立の統制は本設計でも採る |
| [Issue #166](https://github.com/s977043/dynamic-agent-topology/issues/166) | 本文・全コメント | Worker 数と規模の数理モデル（EXP-POP / EXP-ECO） | 問いが異なる。重複なし |
| [PR #205](https://github.com/s977043/dynamic-agent-topology/pull/205)（2026-10-23 merge。研究ノートとして追加され、`knowledge/sources.yaml` では未採用） | 本文・diff 全体 | task nature（探索 / 複製 / 既知解）で層別した treatment と selector | H1 が「探索的 Task で独立 Verifier が T0 より良いか」で近いが、層の軸が task nature で selector 評価を含む。本設計の軸は「T0 の実測成功率で定義する難度」で selector を扱わない。#205 は研究ノートとして merge されたため、難度層と task nature を事前記録の共変量として両方残すことができる（残すかは U7） |

判断: 「T0 / T1 を固定 model で難度条件付きに比べる」問いを主題にした既存 issue・文書はないため、新規文書とした。

## 3. 仮説（反証可能）

**H1（主）**: 事前に T0 の成功率が低いと確認し凍結した評価 Task 集合で、Runtime・Model・Effort を固定したとき、T1 の verified success rate が T0 より事前宣言の最小改善幅 Δ 以上高い。

**H2（コスト）**: H1 が成り立つとき、T1 の token 増加は EXP-001 基準 3 の考え方（「品質改善がその増加を明示的に正当化できる」）で正当化できる。具体的には、verified success 1 件あたりの total tokens（失敗 Run の消費を含む）が T0 を事前宣言の倍率 K 以上上回らない。T0 の評価集合での verified success が 0 件のときは、1 件あたりの値が定義できないため H2 は評価不能とし、全体の判定は H1 を満たしても INCONCLUSIVE とする（T1 の成功 1 件あたり total tokens と T0 の総 token は報告する）。

**H3（安全）**: T1 の regression rate が T0 を事前宣言の regression 上限を超えて上回らない（判定単位は評価集合全体の Run 単位の割合）。critical boundary violation は別の規則とし、EXP-001 基準 4 と同じく T1 に 1 件でもあれば、H1・H2 の結果にかかわらず T1 を標準採用しない（判定単位は Run 単位の件数。T0 側の件数は比較に使わず報告する）。

反証条件:

- 評価集合で T1 − T0 の verified success 差が Δ 未満 → H1 は不支持（Keep T0 を維持）。
- T0 の評価集合での verified success rate が、較正時の値から事前宣言の上昇幅 r_max を超えて上がる、または事前宣言の上限 p_ceiling 以上になる（判定単位は評価集合全体の Run 単位の割合）→ 難度の操作化に失敗。H1 は INCONCLUSIVE。r_max と p_ceiling は U3 で評価 Run 前に固定する。
- Verifier が false accept で成功を水増ししている（独立 AC で不合格のものを T1 が成功と申告）→ その Run は失敗として数え、verifier false accept rate を別に報告する。

Δ、K、regression の上限は推測で決めない（§9 U3）。

## 4. 「T0 で解けない難度」の操作的定義

- **定義**: 固定した Runtime / Model / Effort / T0 で、較正 Run を n_cal 回（U4）実行したとき、独立 AC による verified success が p_max 以下（U3）の Task を「hard」とする。主観的な「難しそう」は使わない。
- **上限と下限**: 成功率 0 の Task は T1 でも解けない可能性が高く、差が出る余地は「T0 が一部成功する」帯の方が大きい。0 を含めるかは事前に宣言する（U3）。含める場合も、評価で T0・T1 とも全 Task が 0 なら、どちらも解けない難度だったとして INCONCLUSIVE とする。
- **難度は Task の性質ではなく「この Runtime / Model / Effort での T0 の性能」で定義する**。条件を変えたら再較正が要る。

## 5. 選定の事前固定と選択バイアスへの対処

予備 Run で T0 を測ってから選ぶと、偶然失敗した Task を選ぶ（平均への回帰）ため、評価集合での T0 成功率が見かけより上がり、T1 の効果が過大または過小に見える。対処:

1. **較正と評価を分ける**: 較正 Run（T0 のみ）は選定にだけ使い、評価の集計に入れない。評価では T0 / T1 の両方を新しい Run で取り直す。
2. **選定規則を較正前に固定する**: 候補 Task の一覧、p_max、n_cal、除外規則（環境不備・AC 不明確など結果以外の理由に限る）を、較正 Run の前に commit / Issue コメントで記録する。
3. **評価集合を評価 Run 前に凍結する**: 選定結果（Task ID・revision・AC・oracle）を評価 Run 前に記録し、評価結果を見て Task を入れ替えない。
4. **T1 は較正に使わない**: 選定に T1 の結果を使うと選定自体が treatment に依存する。
5. **回帰の程度を報告する**: 較正時と評価時の T0 成功率を並べて報告する。評価時に大きく上がった場合は §3 の反証条件で扱う。
6. **候補の母集団も記録する**: hard に入らなかった Task も一覧と較正結果を残し、選定の射程（どの母集団の、どの帯か）を明示する。結論はこの選定集合に条件付きで、Task 分布一般へ外挿しない。

## 6. 事前登録項目

評価 Run の前に、次をすべて記録する。未記録の項目がある場合は評価 Run を始めない。

| 項目 | 内容 |
|---|---|
| Task の選び方 | 候補母集団の出所（公開・許可済み repo revision のみ。private code 不可）、§4・§5 の規則、除外規則 |
| 独立 AC | Task ごとに、Worker・Verifier に渡す情報とは別に保持する決定的な Verification command / 期待結果。T1 の Verifier の判断は成功判定に使わない |
| negative oracle | 誤った修正・テスト削除・AC の回避などを不合格にする負側チェック。Task ごとに少なくとも 1 つ |
| 指標 | 主: verified success rate。副: regression rate、human interventions、total tokens（T1 は全 session 合計）、wall clock、verifier false accept rate、boundary violations、verified success 1 件あたり total tokens。定義は [METRICS.md](METRICS.md) と EXP-001 の集計に揃える |
| 閾値 | Δ、K、regression 上限、INCONCLUSIVE 条件（欠損率、paired 不成立、T0 成功率の上昇幅 r_max と上限 p_ceiling、T0 の評価成功 0 件） |
| budget と停止条件 | 較正・評価それぞれの token / Run 上限と承認者。予算到達、infrastructure failure の連続、boundary violation、quarantine などで停止し、停止した Run は失敗・中止として区別して残す |
| counterbalance | Task × rep を block とし、block 内の T0 / T1 順序を交互または事前乱数で決める。fresh workspace / fresh session、arm 間で patch・診断・Verifier 所見を持ち越さない |
| 固定条件 | Runtime・Model・Effort・prompt 方針・tool 権限。実効値を Trace から確認し、宣言と異なる Run は control deviation として記録する |

EXP-001 の Frozen file（scenarios、prompts、fixtures、T0/T1 topology、roles、schemas、pilot scripts）は流用も変更もしない。新しい Task / fixture / experiment Artifact が必要になった時点で、別 PR・別の事前登録として扱う。

## 7. 判断の射程

- **少数 Run は feasibility-only**: 評価集合や rep 数が事前宣言の下限（U4）に届かない場合、結果は手順の実行可能性と指標の取得可否の確認にとどめ、H1〜H3 の判断に使わない。
- Judgment は Adopt T1 / Keep T0 / Continue / Reject design のいずれかを、独立 Reviewer の結果レビューを経て記録する。結論は「この Runtime / Model / Effort、この選定集合」に条件付き。
- 未確認の値・取得できない指標は推測で埋めず **NOT_TESTED / UNKNOWN** と書く。

## 8. 境界（Human-owned）

- model 起動（較正・評価とも）は Operator が fresh workspace / fresh session で行う。Agent は代行しない。
- 予算の承認と、課金が発生する model 起動は Human（Operator）専権。閾値などの設計判断と、新しい experiment / fixture の追加と採否は、[AGENT_HARNESS.md](AGENT_HARNESS.md) の HOTL の自律境界に従い Agent が独立レビュー付きで判断する。
- Topology ≠ Routing Policy、Role ≠ Model。本設計は T0 / T1 の既存定義を変えず、runtime 固有の手順は `adapters/` 側に置く。

## 9. 未確定事項

U1〜U7 は [HARD_TASK_T0_T1_PREREGISTRATION.md](HARD_TASK_T0_T1_PREREGISTRATION.md) で確定した（2026-10-23）。事前登録は同書の blob hash を Issue に記録した時点で成立する。

| # | 事項 | 現状 |
|---|---|---|
| U1 | 固定する Runtime / Model / Effort | 確定: Codex / gpt-6.1-sol / high |
| U2 | hard 候補の母集団の出所と件数 | 手順を確定（候補 40〜50 件、追加は 1 回まで）。候補一覧は未作成 |
| U3 | p_max（0 を含めるか）、Δ、K、regression 上限、r_max、p_ceiling | 確定: p_max = 2/5（0/5 除外）、Δ = 0.30、K = 1.5、+0.10、0.20、0.60 |
| U4 | n_cal、評価集合の最小 Task 数、rep 数 | 確定: n_cal = 5、13 Task 以上、rep = 3 |
| U5 | 較正・評価の budget と承認者 | 見積もり式と概算を確定。予算の上限と承認は Operator が決める |
| U6 | 新しい Task / fixture / experiment Artifact の置き場所と schema 適合 | 事前登録成立後の別 PR で扱う |
| U7 | #205 の task nature を共変量として記録するか | 確定: 記録する（主判定には使わない） |
