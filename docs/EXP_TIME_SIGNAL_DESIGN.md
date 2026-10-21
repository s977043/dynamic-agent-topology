# 経過時間シグナル評価の設計案（#201）

状態: **非規範的な設計案（未採用・独立レビュー前）**。実験開始・model 起動・予算消費・Runtime 変更・worker 増強の許可ではありません。本設計に基づく model 起動（予備検証を含む）は Operator が行い、Agent は代行しません。`experiments/`、`schemas/`、`topologies/`、`roles/`、`adapters/`、EXP-001 の Frozen file は変更しません。現時点の効果は **INCONCLUSIVE**（実測 0 件）です。

- 起案日: 2026-10-19 / 基準: origin/main `3504a78`
- 関連: [Issue #201](https://github.com/s977043/dynamic-agent-topology/issues/201)、[Issue #166](https://github.com/s977043/dynamic-agent-topology/issues/166)、[Issue #42](https://github.com/s977043/dynamic-agent-topology/issues/42)（closed / not planned）、[Issue #93](https://github.com/s977043/dynamic-agent-topology/issues/93)
- 一次ソース: Issue 本文、[EXPERIMENTS.md](EXPERIMENTS.md)、[METRICS.md](METRICS.md)、[ARCHITECTURE.md](ARCHITECTURE.md)、[AGENT_HARNESS.md](AGENT_HARNESS.md)
- 外部 Source（参照のみ・効果の根拠にしない）: [Prompting Claude Opus 5.5 — Time signals for multiagent harnesses](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5)

## 0. Evidence・解釈・推奨の区別

| 区分 | 内容 |
|---|---|
| Source claim | 外部ガイドは、multiagent harness でメッセージに `elapsed` や `elapsed / budget` を付けると協調が改善し得ると述べる。これは提供者の主張であり DAT での観測ではない |
| 観測済み DAT Evidence | なし。EXP-001 は time signal を操作しておらず、何も示さない |
| DAT 側の解釈 | time signal は Runtime Mapping（Harness / `adapters/`）側の入力であり、Topology・Role・Routing Policy の変更ではない |
| 推奨案（未採用） | §1 以降。しきい値・具体 task・Runtime の組は未確定（§11） |

## 1. 結論（推奨案）

**2 arm（A: シグナルなし / C: `elapsed Ns / budget Ns`）の paired 比較から始め、B（elapsed のみ）は後続 ablation に回す（実施の判断基準は U6）。** 同一 Topology・Worker 数・Runtime・Model・Effort の下で、Harness がメッセージ末尾に付ける 1 行だけを変える。

### 2 arm に絞る根拠（判断基準: 要件適合性 → 安全性 → 保守性 → コスト → 拡張性）

- **要件適合性**: 最初に答えるべき問いは「何らかの time signal に効果があるか」。C は情報量が最大の treatment なので、最初の比較に置く。ただし budget 情報が elapsed 単独の効果を弱める可能性もあり、A/C で差が出なくても B に効果がないとは言えない。B を実施するかは A/C の結果だけで決めず、U6 の判断材料として扱う。
- **コスト**: 3 arm は同じ paired block 数で Run 数が 1.5 倍。小標本の feasibility 段階では arm を増やすと 1 arm あたり件数が減り INCONCLUSIVE になりやすい。
- **安全性**: C は「予算」を見せるため、検証を省略して早く終える方向に働く危険が最も高い。最初に C を検証対象にすると、この危険（§6 H-S）を早期に検出できる。
- **限界**: A/C 差が出ても「elapsed 単独で十分か」は答えられない。この結論は B を実施するまで出さない。

## 2. 既存 Issue との scope review

| Issue | 独立変数 / 対象 | 本設計との関係 | 重複回避 |
|---|---|---|---|
| #166 | Worker 数 W=1/2/4 × 協調有無 × 予算方式（総額固定 / 1 体あたり固定） | 予算を「Harness が強制する資源量」として扱う | 本設計は Worker 数・協調方式・予算強制値を**固定**し、予算を「モデルに見せる助言」としてだけ扱う。#166 の arm と同じ Run を共有しない |
| #42（closed / not planned） | generic Loop / Graph 契約（retry・停止・budget exhaustion）の必要性 | hard timeout・停止は既存 Harness / run-kit で扱う、という判断 | 本設計は新しい Loop 契約を作らない。hard timeout は既存 Harness の強制条件として全 arm 共通に置く。budget 枯渇時の挙動を契約化しない |
| #93 | 実行 strategy（cascade・critique・stronger model）比較 | model / capability binding を変える | 本設計は model binding を固定する。#93 系の実験（EXP-002 案）と arm を混ぜない |

**結論**: 3 Issue はいずれも「資源・構造・model を変える」。本設計は「同じ資源・構造・model に対し、モデルが受け取る時間情報だけを変える」。同一 Run を兼用すると独立変数が重なるため、別実験とする。

## 3. 因果交絡の列挙と制御

| # | 交絡 | 内容 | 制御 |
|---|---|---|---|
| K1 | prompt 長・内容差 | signal 行の追加自体がトークン数・指示を変える | A には同じ位置に固定の中立行（例: 空行または固定文字列）を置くか、差分が signal 行だけであることを Run 前に diff で確認。signal 以外の文言を足さない |
| K2 | 予算の強制と助言の混同 | budget を見せると同時に hard timeout を変えると効果が分離できない | hard timeout・token 上限・permission は全 arm で同一値。budget は助言値で、強制値とは別に事前登録 |
| K3 | budget 値の後知恵 | 結果を見て budget を調整 | task ごとの budget 値と選び方（例: 予備 A run の wall clock の固定倍率）を開始前に固定し hash で記録 |
| K4 | elapsed 値の出所 | モデルの自己申告や不正確な値 | Harness が単調時計で実測した値のみ。表示値と実測値の対応を Trace で照合 |
| K5 | activation 未確認 | signal が実際には届いていない | 各 Run で「signal が提示された」ことを Trace で別途確認（§7 activation）。未確認 Run は効果解釈から除外し欠測として計上 |
| K6 | 実行順序・キャッシュ | 先行 arm の prompt cache・外部状態・学習 | paired block 内で順序を counterbalance、fresh workspace / session、cache 状態と順序を記録 |
| K7 | Worker 数・協調の差 | #166 の変数が混入 | Worker 数・Topology・handoff 方式を全 arm で固定 |
| K8 | model / effort / tool 版の差 | 時期による Runtime 更新 | block 内で Runtime・Model・Effort・tool 版を固定し記録。異なる block は descriptive-only |
| K9 | 検証省略による見かけの高速化 | 早く終わったが verification を飛ばした | 独立 AC で判定。verification skip・未完了 Run を「高速化」に数えない（§8） |
| K10 | 終了宣言の誤認 | `end_turn` や progress summary を完了とみなす | 完了は AC + Evidence のみで判定 |
| K11 | 難度の床／天井効果 | 全 arm 全成功・全失敗では差が出ない | 正 case（多 worker / 探索が意味を持つ）と負 case（単純で時間圧が無関係）を両方登録 |
| K12 | Operator の介入差 | arm を知った Operator の介入 | 介入規則を事前固定し、介入回数を arm 別に記録。可能な範囲で Evaluator を blind にする |

## 4. 事前登録 task 案

要件: 使い捨て・秘密なし・公開可能な repo revision、#166 / #93 の task と重複しない、決定的な Verification command がある。具体 task は未確定（U1）。

| 区分 | 案 | 期待 |
|---|---|---|
| 正 case | 小さな修正タスク。前半に複数ファイルにまたがる read-only 調査があり、その調査を複数 worker で分担する意味がある（例: 小規模 repo の関数使用箇所を調べ、仕様に合わせて一括修正しテストを通す） | time signal が協調・打ち切り判断に影響し得る |
| 負 case | 単一ファイル・短時間で終わる修正（例: EXP-001 系と同程度の単純関数修正。ただし EXP-001 fixture は使わず別に用意） | 効果なし（差が出たら交絡を疑う） |

各 task の登録項目: repo revision、AC、Verification command、想定難度（結果で書き換えない）、副作用範囲、助言 budget 値と算出方法、hard timeout、Worker 数。

## 5. Arms・budget・hard timeout

| arm | Harness がメッセージ末尾に付ける内容 | 実施 |
|---|---|---|
| A | なし（または K1 の固定中立行） | 必須 |
| C | `elapsed <seconds>s / <preregistered_budget>s` | 必須 |
| B | `elapsed <seconds>s` | 後続（実施の判断基準は U6） |

A の形（シグナルなし / 固定中立行）は U5 で未確定だが、事前登録の確定時にどちらか一方へ固定し、予備検証の trace で A と C のメッセージ差分がシグナル行だけであることを確認してから本実行に進む。

- **助言 budget**: task ごとに事前固定。算出方法の候補は「Operator が実施する予備 A run の wall clock の固定倍率」。予備 run は効果推定に使わない。
- **hard timeout**: 全 arm 同一値で助言 budget より十分大きく（例: budget の固定倍率）、Harness が強制する。超過は timeout として記録し成功扱いしない。
- **token / spend 上限・permission boundary**: 全 arm 同一の強制条件。
- 未完了・stuck の自動継続は有限回で停止し、エスカレーションとして記録する。
- signal 付与は Runtime Mapping（Harness / adapter 設定）の関心事として扱い、Topology・Role 定義に書かない。

## 6. 仮説と AC

- **H-E（effectiveness）**: 正 case において、C は A に対し verified success を非劣化に保ったまま wall clock または total tokens を事前宣言の最小幅以上に改善する。
- **H-S（safety）**: C は A より verification skip・timeout・boundary violation を増やさない。
- **H-N（負 case）**: 負 case では A/C に事前宣言幅を超える差がない（差があれば交絡を疑い解釈を保留）。

Task の AC: 各 task の Verification command が exit 0 かつ独立 Evaluator による AC 照合が一致。

## 7. 記録する指標と missingness

| 指標 | 定義・出所 |
|---|---|
| task_success | 独立 AC 判定（生成 Agent の自己申告を使わない） |
| wall_clock_ms | Harness の単調時計 |
| total_tokens | provider usage（cached 含む定義を明示） |
| agent_invocations / handoffs | Trace |
| human_interventions | 回数（注意負荷の代理にしない） |
| timeout / abort | Harness の停止理由 |
| boundary_violations | Trace と permission log |
| verification_skipped | AC に必要な検証が実行されたかを Trace で確認 |
| signal_presented（activation） | 各メッセージに signal が実際に付いたか、表示値と実測 elapsed の差 |

- **activation と effectiveness を分離**: signal_presented が確認できない Run は effectiveness の解釈に使わない。
- **missingness**: 取得できない値は 0 で埋めず欠測として記録し、arm 別に欠測率を報告する。失敗・中断・timeout Run は除外せず、成功 Run と区別して保持する。
- 指標の意味は [METRICS.md](METRICS.md) に合わせ、新しい canonical metric を追加しない。

## 8. 判定規則（PASS / FAIL / INCONCLUSIVE）

しきい値（最小改善幅、非劣化幅、最小 paired block 数、欠測率上限）の数値は本案で決めない（U2）。

| 判定 | 条件 |
|---|---|
| PASS | activation 確認済み block が最小件数以上、H-E を満たし、H-S の違反なし、負 case で交絡兆候なし。PASS でも既定化はせず、独立評価と Human の adopt / defer / reject 判断を経る |
| FAIL | success が非劣化幅を超えて低下、verification skip・timeout・boundary violation が C で増加、またはコスト改善が最小幅未満 |
| INCONCLUSIVE | 件数不足、欠測率上限超過、activation 未確認 Run の比率超過、負 case で説明できない差、block 内の Runtime 等の不一致 |

- 厳しい予算で検証を省略して速くなった場合は FAIL または INCONCLUSIVE とし、PASS にしない。
- task_success 単独では採用判断しない。
- 小標本の feasibility 判断と効果推定を分けて報告する。

## 9. 予備検証（disposable、Operator 実施）

結果は Evidence として採用判断に使わず、repo に Run Artifact を残さない。後から追えるよう、実施日時・Runtime / Model / Effort・下記 1〜4 の確認結果（PASS / FAIL）だけを #201 のコメントに記録する（trace 本文や秘密値は載せない）。

1. Harness が単調時計の elapsed を signal 行として付与し、Trace に残せるか（activation 計測の成立）。
2. A/C の prompt 差分が signal 行だけであることを機械的に確認できるか。
3. hard timeout・token 上限が全 arm 同一に強制されるか。
4. 正・負 case 候補を A で 1 回ずつ実行し、助言 budget の算出に必要な wall clock を得る。

1〜3 のいずれかが確認できなければ本実験を設計し直す。

## 10. Human-owned 境界

- task 母集団・しきい値・model 呼び出し予算の確定は Human 判断。
- model 起動は Operator が行う。Agent 起動の例外（EXP-001 の一回限り retry）は本実験に適用されない。
- 外部 SDK / OSS / MCP は追加しない。Runtime Permission の拡張、新しい credential は扱わない。
- 新しい schema・Policy・adapter 設定の追加は独立レビューと通常 PR 手順を経る。Freeze 改訂・release / tag・削除は Human 専権。
- 外部ガイドを `knowledge/sources.yaml` で adopted にしない。

## 11. 未確定事項

- **U1** 具体 task（正・負 case）と公開可能な repo revision。
- **U2** しきい値の数値と paired block 数。
- **U3** Runtime / Model / Effort / Worker 数の組と、同一 Harness で signal 行を付与できるか。
- **U4** 助言 budget の算出倍率と hard timeout の倍率。
- **U5** A に固定中立行を置くか、完全になしにするか（K1）。
- **U6** B を後続で実施する判断基準。
