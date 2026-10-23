# 難度の高い Task での T0 / T1 比較の事前登録の下書き

状態: **非規範的な下書き（未採用・独立レビュー前）**。本書は事前登録そのものではありません。実験開始・model 起動（較正 Run を含む）・予算消費・experiment Artifact や Task / fixture の追加の許可でもありません。model 起動は Operator が行い、Agent は代行しません。現時点の効果は **INCONCLUSIVE**（実測 0 件）です。

- 起案日: 2026-10-23 / 基準: origin/main `4ae90bd`
- 対象: [HARD_TASK_T0_T1_DESIGN.md](HARD_TASK_T0_T1_DESIGN.md)（以下「設計案」）§9 の U1〜U7
- 一次ソース: 設計案、[EXP-001 DECISION.md](../experiments/EXP-001-t0-vs-t1/DECISION.md)、[experiment.yaml](../experiments/EXP-001-t0-vs-t1/experiment.yaml)、[POST_EXP001_EVALUATION_DESIGN.md](POST_EXP001_EVALUATION_DESIGN.md) §10、[MODEL_ROLE_SPLIT_DESIGN.md](MODEL_ROLE_SPLIT_DESIGN.md)、[Issue #93](https://github.com/s977043/dynamic-agent-topology/issues/93) の 2026-10-23 Human 判断記録、AGENTS.md
- 形式の先例: [MODEL_ROLE_SPLIT_DESIGN.md](MODEL_ROLE_SPLIT_DESIGN.md)

**事前登録の成立条件**: 本書の U1〜U7 を Human と独立 Reviewer が確定し、確定版を 1 ファイルに固定して、その blob hash を対応 Issue に記録した時点で事前登録が成立する。それまでは較正 Run も含めて model を起動しない。確定後に結果を見て書き換えない。

## 0. Source claim・Evidence・解釈・Judgment の区別

| 区分 | 内容 |
|---|---|
| Source claim | paired 二値比較の必要件数の近似式（McNemar 検定の標準的な近似）は統計の一般知識であり、DAT の観測ではない |
| 観測済み DAT Evidence | EXP-001 の 18 Run（Codex / gpt-6.1-sol / high、3 Scenario × T0/T1 × 3 rep）。meanTotalTokens は T0 68,022.0、T1 150,080.67、T1/T0 = 2.206。全件成功で品質指標は同値。Keep T0（DECISION.md） |
| DAT 側の解釈 | EXP-001 の Task は T0 で解ける難度だった（床効果）。hard Task での T0 成功率、T1 の改善幅、hard Task の token 消費、候補中の hard の割合はいずれも **UNKNOWN** |
| Judgment | なし。以下の推奨値はすべて未採用の案 |

以下の表で「根拠の種類」は、**Evidence**（DAT の観測値から導く）、**規則**（既存の DAT 基準・文書に揃える）、**推測**（観測なし。Human が確定する）のいずれかを示す。

## 1. 推奨値の要約

| # | 推奨 | 根拠の種類 |
|---|---|---|
| U1 | EXP-001 と同じ Codex / gpt-6.1-sol / high に固定。実効値は較正前に Trace で再確認 | 規則 + Evidence |
| U2 | 公開ライセンスの OSS repo の過去 revision から、実在の修正 commit を逆適用した Task を集める。候補 40〜50 件 | 推測（件数） |
| U3 | p_max = 2/5（0/5 は主集合から除外し別記録）、Δ = 0.30、K = 1.5、regression 上限 +0.10、r_max = 0.20、p_ceiling = 0.60 | K は規則、他は推測 |
| U4 | n_cal = 5、rep = 3、評価集合 13 Task 以上（39 paired block 以上） | 計算（前提は推測） |
| U5 | 総額 ≒ (5 × C × 68,022 + N × 3 × 218,103) × m。C=44、N=13、m=1 で約 23.5M tokens。承認者は Human（Operator） | Evidence + 推測（m、C） |
| U6 | 本書の範囲外。Task / fixture / experiment Artifact は事前登録確定後の別 PR | 規則 |
| U7 | 記録する（共変量。主判定には使わない） | 規則 |

## 2. U1: Runtime / Model / Effort

- **推奨**: EXP-001 と同じ **Codex / gpt-6.1-sol / high** に固定する。較正 Run の前に、Operator の環境で実効値（Runtime 版、Model、Effort）を Trace から確認し、EXP-001 の `executionContext` と照合して記録する。不一致は control deviation として扱い、較正を始めない。
- **根拠**:
  - EXP-001 との比較可能性。床効果の解消（難度だけを変える）を問うには、難度以外の条件を EXP-001 に揃えるのが最も交絡が少ない（設計案 §1）。
  - EXP-001 の token 実績（U5 の見積もり）をそのまま使える。
  - #220（[MODEL_ROLE_SPLIT_DESIGN.md](MODEL_ROLE_SPLIT_DESIGN.md)）は Model を変える比較で、#93 の EXP-002 / EXP-003 も model / gate を変える。本設計で同時期に Model を変えると、難度の効果と model 差を分離できず、どの実験の結果が何の差によるのかを後から説明できない。
- **代替案**: (a) #220 の結果が出た後の既定 model に揃える（比較可能性は #220 側と取れるが EXP-001 と取れない）。(b) Claude Code 系 Runtime（EXP-001 との比較可能性を失い、token 実績も使えない）。
- **未確認**: gpt-6.1-sol / high が較正時点でも提供・同一挙動か（**UNKNOWN**）。提供終了していれば U1 から再判断し、難度は再較正する（設計案 §4）。

## 3. U2: hard 候補の母集団

- **推奨手順**:
  1. **出所**: OSI 承認ライセンスで公開されている repo の、公開済み commit だけを使う。特定の private code・社内 repo・秘密を含む repo は使わない。[POST_EXP001_EVALUATION_DESIGN.md](POST_EXP001_EVALUATION_DESIGN.md) §10 の U2 と同じ候補表を共有してよい（共有する場合は両設計の事前登録に同じ候補表 hash を記録する）。
  2. **Task の作り方**: バグ修正 commit を 1 つ選び、その親 revision を Task の起点にする。AC はその commit で追加・変更されたテスト（修正前に失敗し、修正後に通る）。Worker / Verifier には修正 commit とテストを渡さない。
  3. **候補の条件**: 修正前にテストが決定的に失敗し、修正後に決定的に通る（各 3 回実行で確認）。オフラインで build / test が完了する。修正が 2 ファイル以上または 30 行以上にまたがる（難度の床を避けるための推測による目安）。negative oracle（テスト削除・skip・期待値書き換えの検出）を 1 つ以上書ける。
  4. **除外条件**（結果以外の理由に限る）: ネットワーク・外部サービス・GPU が必要、テストが flaky、ライセンス不明、秘密や個人情報を含む、EXP-001 / #93 / #201 / #166 / #220 の Task と同じ repo revision、AC が修正の意図を表していない。
  5. **件数の目安**: 候補 C = 40〜50 件。U4 の必要評価数 N = 13 と、候補中に hard（U3 の帯）が入る割合 q を 0.3 と置いた場合の C = N / q ≒ 44 から。q は **推測**（観測なし）。
  6. 候補表（repo、revision、AC、negative oracle、除外理由）を較正前に commit し、hash を記録する。
- **代替案**: (a) 既存の公開ベンチマーク（SWE-bench 系など）から抽出（手間は減るが、学習データ混入の懸念とライセンス確認が要る。採るなら Source として `knowledge/sources.yaml` の手続きを経る）。(b) 合成 Task（難度を制御しやすいが外的妥当性が低い）。
- **未確認**: q、候補 1 件の準備工数、学習データ混入の程度（すべて **UNKNOWN**）。

## 4. U3: 閾値

| 値 | 推奨 | 根拠 | 根拠の種類 |
|---|---|---|---|
| p_max | n_cal = 5 のうち verified success 2 回以下（≤ 0.4）。0/5 は主集合から除外し別集合として記録 | 設計案 §4: 0 の Task は T1 でも解けない可能性が高く、差が出る余地は一部成功の帯にある。上限 2/5 は T0 が過半で失敗する帯 | 推測 |
| Δ | T1 − T0 の verified success rate 差 ≥ 0.30 | U4 の件数を予算内に収めるための最小検出幅。Δ = 0.20 では必要件数がほぼ倍になる（U4） | 推測（予算との釣り合い） |
| K | verified success 1 件あたり total tokens の T1/T0 ≤ 1.5 | EXP-001 基準 3 の「token 増加 50% 以内」を成功 1 件あたりに置き換えたもの | 規則 |
| regression 上限 | T1 の regression rate − T0 の regression rate ≤ 0.10 | 39 block で 1 件あたり約 0.026。4 件差までを許容幅とした値で、根拠となる観測はない | 推測 |
| critical boundary violation | T1 に 1 件でもあれば標準採用しない | EXP-001 基準 4 | 規則 |
| r_max | 評価時 T0 成功率 − 較正時 T0 成功率 ≤ 0.20 | 平均への回帰の許容幅。観測なし | 推測 |
| p_ceiling | 評価時 T0 成功率 ≥ 0.60 で INCONCLUSIVE | p_max 0.4 + r_max 0.2。これを超えると Δ = 0.30 の上乗せが 0.9 以上を要し、天井に近づく | 推測（他の推測値から導出） |

- **代替案**: Δ = 0.20（検出力は上がるが U4 の件数・U5 の予算が約 2 倍）。0/5 を主集合に含める（hard の候補は増えるが、両 arm 0 の block が増え検出力が下がる）。
- **未確認**: hard Task での T0 / T1 の成功率（**UNKNOWN**）。

## 5. U4: n_cal・評価 Task 数・rep 数

- **推奨**: n_cal = 5、rep = 3、評価集合 N ≥ 13 Task（39 paired block 以上）。下限未満なら feasibility-only（設計案 §7）。
- **計算（前提は推測）**: paired 二値比較（McNemar）の近似必要 block 数

  n = (z_α + z_β)² × (p₁₀ + p₀₁) / (p₁₀ − p₀₁)²

  - p₁₀ = T1 成功・T0 失敗の割合、p₀₁ = その逆。前提: 片側 α = 0.05（z = 1.645）、検出力 0.8（z = 0.842）、(z_α + z_β)² ≒ 6.19。
  - T0 = 0.3、T1 = 0.6（Δ = 0.30）、block 内で独立と仮定: p₁₀ = 0.6 × 0.7 = 0.42、p₀₁ = 0.3 × 0.4 = 0.12 → n ≒ 6.19 × 0.54 / 0.09 ≒ 37.1 → **38 block**。rep = 3 で 13 Task。
  - 同じ前提で Δ = 0.20（T1 = 0.5）: p₁₀ = 0.35、p₀₁ = 0.15 → n ≒ 6.19 × 0.50 / 0.04 ≒ 77.4 → 78 block、26 Task。
  - T0 = 0.3 は p_max = 0.4 の帯の中ほどとした **推測**。同一 Task の rep は相関するため実効件数は 38 より少なく、この値は下限の目安にとどまる。
- **n_cal = 5 の根拠**: 帯の判定（≤ 2/5）に最低限の解像度を持たせる値。n_cal = 3 では 1/3 と 2/3 の 2 段階しかなく、帯の誤分類が増える。予算（U5）で較正が支配項になるため、これ以上は増やさない。推測。
- **rep = 3**: EXP-001 と同じ（設計案 U4 の下限候補）。
- **代替案**: N を固定せず逐次に追加する（停止規則の事前宣言が必要になり複雑化するため推奨しない）。

## 6. U5: 予算と承認者

- **見積もり式**:

  総 tokens ≒ (n_cal × C × t_T0 + N × rep × (t_T0 + t_T1)) × m

  - t_T0 = 68,022、t_T1 = 150,080.67（EXP-001 meanTotalTokens。cached input を含む `total_token_usage`、T1 は 2 session 合計）。**Evidence**。
  - m = hard Task での token 消費の EXP-001 比。**UNKNOWN**（hard Task は長くなる可能性が高いが観測なし）。
  - C = 候補数（U2）、N = 評価 Task 数（U4）。
- **概算**（n_cal = 5、C = 44、N = 13、rep = 3）:
  - 較正: 5 × 44 × 68,022 = 14,964,840
  - 評価: 13 × 3 × 218,103 = 8,506,017
  - 合計 ≒ **23.5M tokens × m**（m = 2 なら約 47M）。Δ = 0.20 を採る場合は N = 26、C ≒ 87 で約 2 倍。
- **推奨する運用**: 較正と評価を別予算にし、それぞれ上限を事前宣言する。較正の最初の 5 候補（25 Run）で m を実測し、見積もりを更新して Human が評価予算を再承認する。上限到達で停止し、停止した Run は中止として残す（設計案 §6）。
- **承認者**: Human（Operator）。Agent は予算を承認・消費しない。
- **未確認**: m、q、利用枠・課金の境界（**UNKNOWN / NOT_TESTED**）。

## 7. U6: Artifact の置き場所

本書の範囲外。事前登録が確定した後、新しい experiment Artifact・Task 定義・fixture を別 PR で起案し、既存 schema への適合と semantic check の要否をその PR で判断する（AGENTS.md: 新 artifact kind は schema・semantic check・spec-lint 配線を伴う）。EXP-001 の Frozen file は流用も変更もしない。

## 8. U7: #205 の task nature を共変量にするか

- **推奨**: **記録する**。各候補 Task に task nature（探索 / 複製 / 既知解）を、較正 Run の前に、結果を見ない担当者が付ける。主判定（H1〜H3）は難度層だけで行い、task nature 別の集計は探索的な報告にとどめる。
- **根拠**: 較正前に記録すれば追加の model 起動は不要でコストがほぼない。後から付けると結果に引きずられる。#205 は研究ノートで未採用（`knowledge/sources.yaml` 未登録）のため、判定基準には使わない。
- **代替案**: 記録しない（#205 の H1 との接続が失われる）。task nature で層別して主判定する（件数が層ごとに不足し、U4 の件数では検出力がない）。
- **未確認**: 分類の評定者間一致（**NOT_TESTED**）。

## 9. 確定前に残る判断

- U3 の推測値（p_max、Δ、regression 上限、r_max、p_ceiling）と U2 の q は、Human と独立 Reviewer の確定が要る。
- U2 を #194 と共有するかは、EXP-002 → EXP-003 の順序（#93、2026-10-23 Human 判断）を踏まえ、EXP-002 の事前登録と同時に決める。
