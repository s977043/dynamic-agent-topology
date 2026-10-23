# 難度の高い Task での T0 / T1 比較の事前登録（確定版）

状態: **U1〜U7 の確定版（事前登録は未成立）**。本書は実験開始・model 起動（較正 Run を含む）・予算消費・experiment Artifact や Task / fixture の追加の許可ではありません。予算の承認と、課金が発生する model 起動は Human（Operator）専権で、Agent は代行しません（[AGENT_HARNESS.md](AGENT_HARNESS.md) の自律境界）。現時点の効果は **INCONCLUSIVE**（実測 0 件）です。

- 確定日: 2026-10-23 / 基準: origin/main `5b9e715`
- 経緯: 下書き（#241、`HARD_TASK_T0_T1_PREREGISTRATION_DRAFT.md`、独立レビュー MERGE_OK）を本書に改名して確定版にした。HOTL の規則（#242）により、実験の設計判断は Agent が独立レビュー付きで決める
- 対象: [HARD_TASK_T0_T1_DESIGN.md](HARD_TASK_T0_T1_DESIGN.md)（以下「設計案」）§9 の U1〜U7
- 一次ソース: 設計案、[EXP-001 DECISION.md](../experiments/EXP-001-t0-vs-t1/DECISION.md)、[experiment.yaml](../experiments/EXP-001-t0-vs-t1/experiment.yaml)、[POST_EXP001_EVALUATION_DESIGN.md](POST_EXP001_EVALUATION_DESIGN.md) §10、[MODEL_ROLE_SPLIT_DESIGN.md](MODEL_ROLE_SPLIT_DESIGN.md)、[Issue #93](https://github.com/s977043/dynamic-agent-topology/issues/93) の 2026-10-23 Human 判断記録、[AGENT_HARNESS.md](AGENT_HARNESS.md)、AGENTS.md

**事前登録の成立条件**: 本書（確定版）を固定し、その blob hash を対応 Issue に記録した時点で事前登録が成立する。hash の記録は本書を含む PR の merge 後にオーガナイザー（Agent）が行う。これは記録の操作で、予算の承認や model 起動を伴わないため Human 専権ではなく、[AGENT_HARNESS.md](AGENT_HARNESS.md) の HOTL の自律境界の範囲で Agent が実行できる。成立前は較正 Run も含めて model を起動しない。成立後に結果を見て本書を書き換えない。変更が必要になったら、新しい版として理由を記録し、hash を記録し直す。

## 0. Source claim・Evidence・解釈・Judgment の区別

| 区分 | 内容 |
|---|---|
| Source claim | paired 二値比較の必要件数の近似式（McNemar 検定の標準的な近似）は統計の一般知識であり、DAT の観測ではない |
| 観測済み DAT Evidence | EXP-001 の 18 Run（Codex / gpt-6.1-sol / high、3 Scenario × T0/T1 × 3 rep）。meanTotalTokens は T0 68,022.0、T1 150,080.67、T1/T0 = 2.206。全件成功で品質指標は同値。Keep T0（DECISION.md） |
| DAT 側の解釈 | EXP-001 の Task は T0 で解ける難度だった（床効果）。hard Task での T0 成功率、T1 の改善幅、hard Task の token 消費、候補中の hard の割合はいずれも **UNKNOWN** |
| Judgment（設計判断） | U1〜U7 を本書の値で確定する（HOTL、Agent が独立レビュー付きで決定）。実験結果についての Judgment はなし |

以下の表で「根拠の種類」は、**Evidence**（DAT の観測値から導く）、**規則**（既存の DAT 基準・文書に揃える）、**推測**（観測なし。設計判断として固定した値）のいずれかを示す。推測の値は観測で正しさが示されたものではなく、結果の解釈ではその前提を併記する。

## 1. 確定値の要約

| # | 確定値 | 根拠の種類 |
|---|---|---|
| U1 | Codex / gpt-6.1-sol / high に固定。実効値は較正前に Trace で再確認 | 規則 + Evidence |
| U2 | 公開ライセンスの OSS repo の過去 revision から、実在の修正 commit を逆適用した Task を集める手順（§3）。候補 40〜50 件。候補の実体（repo の一覧）は本書では作らない | 推測（件数） |
| U3 | p_max = 2/5（0/5 は主集合から除外し別記録）、Δ = 0.30、K = 1.5、regression 上限 +0.10、r_max = 0.20、p_ceiling = 0.60 | K は規則、他は推測 |
| U4 | n_cal = 5、rep = 3、評価集合 13 Task 以上（39 paired block 以上。独立性を仮定した概算で、検出力の保証ではない） | 計算（前提は推測） |
| U5 | 総額 ≒ (5 × C × 68,022 + N × 3 × 218,102.67) × m。C=44、N=13、m=1 で約 23.5M tokens。予算の上限と承認は Operator が決める | Evidence + 推測（m、C） |
| U6 | 本書の範囲外。Task / fixture / experiment Artifact は事前登録成立後の別 PR | 規則 |
| U7 | 記録する（共変量。主判定には使わない） | 規則 |

## 2. U1: Runtime / Model / Effort

- **確定**: EXP-001 と同じ **Codex / gpt-6.1-sol / high** に固定する。較正 Run の前に、Operator の環境で実効値（Runtime 版、Model、Effort）を Trace から確認し、EXP-001 の `executionContext` と照合して記録する。不一致は control deviation として扱い、較正を始めない。
- **根拠**:
  - EXP-001 との比較可能性。床効果の解消（難度だけを変える）を問うには、難度以外の条件を EXP-001 に揃えるのが最も交絡が少ない（設計案 §1）。
  - EXP-001 の token 実績（U5 の見積もり）をそのまま使える。
  - #220（[MODEL_ROLE_SPLIT_DESIGN.md](MODEL_ROLE_SPLIT_DESIGN.md)）は Model を変える比較で、#93 の EXP-002 / EXP-003 も model / gate を変える。本設計で同時期に Model を変えると、難度の効果と model 差を分離できない。
- **採らなかった案**: (a) #220 の結果が出た後の既定 model に揃える（EXP-001 との比較可能性を失う）。(b) Claude Code 系 Runtime（EXP-001 との比較可能性を失い、token 実績も使えない）。
- **未確認**: gpt-6.1-sol / high が較正時点でも提供・同一挙動か（**UNKNOWN**）。提供終了していれば U1 から再判断して新しい版にし、難度は再較正する（設計案 §4）。

## 3. U2: hard 候補の母集団（手順）

候補の実体（repo・revision の一覧）は本書では作らない。以下の手順で収集し、候補一覧を較正前に固定する（§9）。

1. **出所**: OSI 承認ライセンスで公開されている repo の、公開済み commit だけを使う。特定の private code・社内 repo・秘密を含む repo は使わない。[POST_EXP001_EVALUATION_DESIGN.md](POST_EXP001_EVALUATION_DESIGN.md) §10 の U2 と同じ候補表を共有してよい（共有する場合は両設計の事前登録に同じ候補表 hash を記録する。共有するかは EXP-002 の事前登録と同時に決める）。
2. **Task の作り方**: バグ修正 commit を 1 つ選び、その親 revision を Task の起点にする。AC はその commit で追加・変更されたテスト（修正前に失敗し、修正後に通る）。Worker / Verifier には修正 commit とテストを渡さない。
3. **候補の条件**（すべて満たす）:
   - 修正前にテストが決定的に失敗し、修正後に決定的に通る（各 3 回実行で確認。model は起動しない）。
   - オフラインで build / test が完了する。
   - 修正が 2 ファイル以上または 30 行以上にまたがる（難度の床を避けるための推測による目安）。
   - negative oracle（テスト削除・skip・期待値書き換えの検出）を 1 つ以上書ける。
4. **除外条件**（結果以外の理由に限る）: ネットワーク・外部サービス・GPU が必要、テストが flaky、ライセンス不明、秘密や個人情報を含む、EXP-001 / #93 / #201 / #166 / #220 の Task と同じ repo revision、AC が修正の意図を表していない。
5. **ライセンス記録**: 候補ごとに repo、revision、repo のライセンス、対象ファイルのライセンス、由来、再配布条件、AC、negative oracle、除外理由を候補表に記録する。ライセンス・由来・再配布条件のどれかを確認できない、または再配布を認めない候補は除外する。
6. **件数**: 候補 C = 40〜50 件。N = 13 と、候補中に hard（U3 の帯）が入る割合 q = 0.3 から C = N / q ≒ 44。これは **期待値ベースの計画数** で、hard が 13 件以上になる保証はない。q は **推測**（観測なし）。
7. **追加規則**（hard が 13 件に届かないとき）: 同じ出所・同じ条件で候補を **1 回だけ** 追加する。追加件数の上限は **初回の候補数 C と同数** に固定する。初回の実測 q が 0 より大きければ、追加件数は min(「不足件数 ÷ 初回の実測 q」（切り上げ）, C) とし、q = 0 なら上限 C を使う。上限を C にする根拠: 較正の総費用を初回の 2 倍までに抑えられ、Operator が追加予算の上限を較正前に知れる。2 倍を超える規模は、Δ = 0.20 を見送ったのと同じ理由（最初の比較としては過大）で採らない。追加分の較正予算は初回と同じ単価で Operator が承認する。上限まで追加しても 13 件に届かなければ feasibility-only とする（設計案 §7）。結果を見てから追加規則を変えない。
- **採らなかった案**: (a) 既存の公開ベンチマーク（SWE-bench 系など）から抽出（学習データ混入の懸念とライセンス確認が要る）。(b) 合成 Task（外的妥当性が低い）。
- **未確認**: q、候補 1 件の準備工数、学習データ混入の程度（すべて **UNKNOWN**）。

## 4. U3: 閾値

| 値 | 確定値 | 根拠 | 根拠の種類 |
|---|---|---|---|
| p_max | n_cal = 5 のうち verified success 2 回以下（≤ 0.4）。0/5 は主集合から除外し別集合として記録 | 設計案 §4: 0 の Task は T1 でも解けない可能性が高く、差が出る余地は一部成功の帯にある。上限 2/5 は T0 が過半で失敗する帯 | 推測 |
| Δ | T1 − T0 の verified success rate 差 ≥ 0.30 | 下記「Δ の判断」 | 推測（予算との釣り合い） |
| K | verified success 1 件あたり total tokens の T1/T0 ≤ 1.5 | EXP-001 基準 3 の「token 増加 50% 以内」を成功 1 件あたりに置き換えたもの | 規則 |
| regression 上限 | T1 の regression rate − T0 の regression rate ≤ 0.10 | 39 block で 1 件あたり約 0.026。4 件差までを許容幅とした値で、根拠となる観測はない | 推測 |
| critical boundary violation | T1 に 1 件でもあれば標準採用しない | EXP-001 基準 4 | 規則 |
| r_max | 評価時 T0 成功率 − 較正時 T0 成功率 ≤ 0.20 | 平均への回帰の許容幅。観測なし | 推測 |
| p_ceiling | 評価時 T0 成功率 ≥ 0.60 で INCONCLUSIVE | 運用上の保守的な除外閾値で、p_max・r_max からは導出しない。評価時 T0 成功率が 0.60 のとき、Δ = 0.30 を満たすには T1 成功率 0.90 以上が要る。天井付近では差が出る余地が小さいので、この帯の結果は難度の操作化に失敗したものとして扱う | 推測 |

**Δ の判断（オーガナイザー、2026-10-23）**: Δ = 0.30 を採用する。Δ = 0.20 では必要件数と予算が約 2 倍（78 block、26 Task、C ≒ 87）になり、最初の比較としては過大なため。0.30 で H1 が不支持なら「この条件で Δ = 0.30 以上の効果は確認できない」と報告し、「効果がない」とは言わない。0.30 未満の小さい効果の検出は、別の事前登録による追加実験で扱う。

- **採らなかった案**: Δ = 0.20（上記）。0/5 を主集合に含める（両 arm 0 の block が増え検出力が下がる）。
- **未確認**: hard Task での T0 / T1 の成功率（**UNKNOWN**）。

## 5. U4: n_cal・評価 Task 数・rep 数

- **確定**: n_cal = 5、rep = 3、評価集合 N ≥ 13 Task（39 paired block 以上）。下限未満なら feasibility-only（設計案 §7）。
- **計算（前提は推測）**: paired 二値比較（McNemar）の近似必要 block 数

  n = (z_α + z_β)² × (p₁₀ + p₀₁) / (p₁₀ − p₀₁)²

  - p₁₀ = T1 成功・T0 失敗の割合、p₀₁ = その逆。前提: 片側 α = 0.05（z = 1.645）、検出力 0.8（z = 0.842）、(z_α + z_β)² ≒ 6.19。
  - T0 = 0.3、T1 = 0.6（Δ = 0.30）、block 内で独立と仮定: p₁₀ = 0.6 × 0.7 = 0.42、p₀₁ = 0.3 × 0.4 = 0.12 → n ≒ 6.19 × 0.54 / 0.09 ≒ 37.1 → **38 block**。rep = 3 で 13 Task。
  - 同じ前提で Δ = 0.20（T1 = 0.5）: p₁₀ = 0.35、p₀₁ = 0.15 → n ≒ 77.4 → 78 block、26 Task。
  - これは **独立性を仮定した概算** で、discordance（p₁₀、p₀₁）を実測したものではない。T0 = 0.3 は p_max = 0.4 の帯の中ほどとした **推測**。
  - 同じ Task の rep どうしは相関するので、実効件数は 38 より少ない。Task 内相関を踏まえた実効検出力は **UNKNOWN** のまま。
  - **判定での扱い**: 39 block 以上は feasibility-only を外すための件数の下限にすぎず、検出力の保証とは解釈しない。H1 が不支持でも「効果がない」とは言わず、検出力未確認として報告する。
- **n_cal = 5**: 帯の判定（≤ 2/5）に最低限の解像度を持たせる値。n_cal = 3 では帯の誤分類が増える。較正が予算の支配項になるため、これ以上は増やさない。推測。
- **rep = 3**: EXP-001 と同じ。
- **採らなかった案**: N を固定せず逐次に追加する（停止規則の事前宣言が必要になり複雑化する）。

## 6. U5: 予算の見積もりと承認者

- **見積もり式**:

  総 tokens ≒ (n_cal × C × t_T0 + N × rep × (t_T0 + t_T1)) × m

  - t_T0 = 68,022、t_T1 = 150,080.67（EXP-001 meanTotalTokens。cached input を含む `total_token_usage`、T1 は 2 session 合計）。**Evidence**。
  - m = hard Task での token 消費の EXP-001 比。**UNKNOWN**。
  - C = 候補数（U2）、N = 評価 Task 数（U4）。
- **概算**（n_cal = 5、C = 44、N = 13、rep = 3）:
  - 較正: 5 × 44 × 68,022 = 14,964,840
  - 評価: 13 × 3 × (68,022 + 150,080.67) = 8,506,004.13
  - 合計 = 23,470,844.13 ≒ **23.5M tokens × m**
- **運用**: 較正と評価を別予算にする。較正は C 候補 × n_cal 回（式の 5 × C 項。最初の 25 Run を含む）。最初の 5 候補（25 Run）で m を実測して見積もりを更新し、更新後の較正見積もりが承認済みの較正予算に収まれば、残りの C − 5 候補を同じ手順で較正する。収まらなければ較正を止め、Operator が較正予算を再承認するまで再開しない。評価予算は較正の完了後に承認を受ける。上限到達で停止し、停止した Run は中止として残す（設計案 §6）。
- **承認者**: **予算の上限と承認は Operator（Human）が決める**。本書は金額・上限の数値を定めない。Agent は予算を承認・消費しない。
- **未確認**: m、q、利用枠・課金の境界（**UNKNOWN / NOT_TESTED**）。

## 7. U6: Artifact の置き場所

本書の範囲外。事前登録の成立後、新しい experiment Artifact・Task 定義・fixture を別 PR で起案し、既存 schema への適合と semantic check の要否をその PR で判断する（AGENTS.md: 新 artifact kind は schema・semantic check・spec-lint 配線を伴う）。EXP-001 の Frozen file は流用も変更もしない。

## 8. U7: #205 の task nature を共変量にするか

- **確定**: **記録する**。各候補 Task に task nature（探索 / 複製 / 既知解）を、較正 Run の前に、結果を見ない担当者が付ける。主判定（H1〜H3）は難度層だけで行い、task nature 別の集計は探索的な報告にとどめる。
- **根拠**: 較正前に記録すれば追加の model 起動は不要。後から付けると結果に引きずられる。#205 は研究ノートで未採用（`knowledge/sources.yaml` 未登録）のため、判定基準には使わない。
- **採らなかった案**: 記録しない（#205 の H1 との接続が失われる）。task nature で層別して主判定する（U4 の件数では層ごとの検出力がない）。
- **未確認**: 分類の評定者間一致（**NOT_TESTED**）。

## 9. 実験開始前に残る手順

順番に行う。各段階の結果は対応 Issue に記録する。

1. **事前登録の成立**: 本書を含む PR の merge 後、オーガナイザーが本書の blob hash を対応 Issue に記録する（Agent。HOTL の範囲の記録操作で、Human 専権ではない）。
2. **候補の収集と記録**: §3 の手順で候補を集め、候補表（ライセンス記録と task nature を含む）を作る。テストの決定性確認は model を起動せずに行う（Agent、別 PR）。
3. **候補一覧の固定**: 選定規則と候補一覧を commit し、その blob hash を Issue に記録する。#194 と共有する場合は両方に同じ hash を記録する（Agent、独立レビュー付き）。
4. **予算の承認**: Operator が較正予算の上限を決めて承認する（Human 専権）。
5. **実効値の確認**: Operator が環境の Runtime / Model / Effort を確認し、U1 と一致することを記録する。不一致なら較正を始めない。
6. **較正 Run**: Operator が較正を実行する（Human 専権）。最初の 5 候補（25 Run）で m を実測して見積もりを更新し、承認済みの較正予算に収まれば残りの C − 5 候補を較正する。収まらなければ止めて、Operator が再承認する（§6）。
7. **評価集合の確定**: 較正結果から U3 の帯で評価集合を選ぶ。13 件に届かなければ §3 の追加規則を 1 回だけ適用し、それでも届かなければ feasibility-only とする。
8. **Artifact の起案**: experiment Artifact・Task 定義・fixture を別 PR で起案する（U6）。
9. **評価予算の承認**: 更新した見積もりを基に Operator が評価予算を承認する（Human 専権）。
10. **評価 Run**: Operator が評価を実行する（Human 専権）。結果は独立 Reviewer の結果レビューを経て Judgment を記録する（設計案 §7）。
