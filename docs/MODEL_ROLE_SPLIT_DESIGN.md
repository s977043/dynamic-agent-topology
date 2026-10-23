# モデル役割分担の評価設計案（#220）

状態: **非規範的な設計案（未採用・独立レビュー前）**。実験開始・model 起動・予算消費・Runtime 変更・`.claude/` 設定変更の許可ではありません。本設計に基づく model 起動（予備検証を含む）は Operator が行い、Agent は代行しません。`experiments/`、`schemas/`、`topologies/`、`roles/`、`adapters/`、EXP-001 の Frozen file は変更しません。現時点の効果は **INCONCLUSIVE**（実測 0 件）です。

- 起案日: 2026-10-23 / 基準: origin/main `48421fc`
- 対象: [Issue #220](https://github.com/s977043/dynamic-agent-topology/issues/220) の実行計画 G1（arm の最小化）と G2（事前登録）。G0・G3〜G5 は範囲外
- 一次ソース: Issue #220 の 2026-10-21 実行計画コメント、[ENVIRONMENT_USAGE.md](ENVIRONMENT_USAGE.md) の「2026-10-21: #220のモデル役割分担に向けた静的確認」節、[EXPERIMENTS.md](EXPERIMENTS.md)、[METRICS.md](METRICS.md)、[ARCHITECTURE.md](ARCHITECTURE.md)、[AGENT_HARNESS.md](AGENT_HARNESS.md)
- 関連（重複回避の対象）: [#162](https://github.com/s977043/dynamic-agent-topology/issues/162)、[#88](https://github.com/s977043/dynamic-agent-topology/issues/88)、[#93](https://github.com/s977043/dynamic-agent-topology/issues/93)、[PR #208](https://github.com/s977043/dynamic-agent-topology/pull/208)、[PR #206](https://github.com/s977043/dynamic-agent-topology/pull/206)、[POST_EXP001_EVALUATION_DESIGN.md](POST_EXP001_EVALUATION_DESIGN.md)、[EXP_TIME_SIGNAL_DESIGN.md](EXP_TIME_SIGNAL_DESIGN.md)

## 0. Source claim・Evidence・解釈・Judgment の区別

| 区分 | 内容 |
|---|---|
| Source claim | Claude Code 公式仕様では、subagent のモデルは呼出し指定→frontmatter→環境変数→親の順で決まり、`inherit` は親モデルを選ぶ（ENVIRONMENT_USAGE.md 2026-10-21 節の照合）。「Sonnet でも品質を保てる」「小さいモデルで費用が下がる」は一般的な主張であり DAT の観測ではない |
| 観測済み DAT Evidence | 静的確認のみ。既存 2 Agent は `model: inherit`、確認環境で `claude` CLI は未検出。実効モデル・追加課金の境界・利用枠・実効権限は **NOT_TESTED**。EXP-001 はモデルを操作しておらず、モデル差について何も示さない |
| DAT 側の解釈 | Role ≠ Model。モデル割当は Runtime Mapping（`adapters/` / Harness 設定）側の関心事であり、Topology・Role 定義の変更ではない。arm A/B は Topology を固定し model binding だけを変える |
| Judgment | なし。本文の推奨は未採用の案であり、採用・既定化は G4 の独立 Reviewer と Human の判断を経る |

## 1. 結論（推奨案）

**arm A（現行 T0）と arm B（同じ T0 でメインのモデルだけを Sonnet にする）の paired 比較を先行し、C（Haiku read-only 探索委任）と D（高リスク時のみ Opus escalation）は本設計の範囲外とする。** C/D は A/B の Evidence が出た後に、別の事前登録を持つ別比較として段階導入を検討する。

### 2 arm に絞る根拠（判断基準: 要件適合性 → 安全性 → 保守性 → コスト → 拡張性）

- **要件適合性**: 最初に答える問いは「同じ Topology のままメインモデルを Sonnet にして、事前宣言の品質下限を割らずにコストが下がるか」。変更因子を 1 つ（メインの model binding）に限定する。
- **安全性（交絡）**: C は委任という Topology 差（handoff・Agent 数）を、D は escalation という Routing Policy 差を持ち込む。A/B と同時に変えると効果を分離できない（Issue #220 の交絡点検 2）。
- **コスト**: arm を増やすと同じ予算で 1 arm あたりの件数が減り INCONCLUSIVE になりやすい。
- **限界**: A/B の結果から C/D の効果は言えない。B が FAIL でも C/D が無効とは言えない。

## 2. 既存 Issue / PR との scope review

| 対象 | 扱うもの | 本設計との関係 |
|---|---|---|
| #162 | モデル切替の workflow 品質・総コストの再検証 | 総コストの定義は #162 / METRICS.md を参照し、新しいコスト定義を作らない |
| #88 | Evidence に基づくモデル昇格とコンパクトな引き継ぎ | 昇格（arm D 相当）は #88 側。本設計は固定割当の比較だけを扱う |
| #93 | compound execution strategy・multi-model orchestration | Topology / strategy 差は #93 側。本設計は Topology を固定する |
| PR #208（merged） | Role×Model×Effort の研究ノート | 研究内容を再掲しない。Model と Effort の同時変更を避ける根拠として参照のみ |
| PR #206（merged） | Claude Code OpusPlan / Scout / Critic の採用前評価 | Claude Code 固有のモデル選択・権限確認の参照先。Scout（arm C 相当）の設定を先に導入しない |

## 3. 仮説（反証可能）

- **H-Q（品質非劣化）**: 事前登録した task 集合で、B の verified success 率は A に対し事前宣言の非劣化幅 δ_q 以内に留まる。B が δ_q を超えて低い場合に反証される。
- **H-C（コスト改善）**: 同じ task 集合で、B は A に対し事前宣言の課金換算コスト（#162 の定義に従う）を最小幅 δ_c 以上下げる。改善が δ_c 未満なら反証される。
- **H-S（安全性）**: B は A より false accept（AC 不合格を完了と申告）・boundary violation・negative oracle の不合格を増やさない。件数は種類ごとに paired block 単位で数え、同じ Run の同じ種類の違反は 1 件とする。B の件数が A を上回る種類が 1 つでもあれば H-S は反証され、判定は FAIL とする（§7）。違反の分類に迷う事例は独立 Reviewer が判定する。

δ_q・δ_c・最小 paired block 数は本案では決めない（U2）。

**本書は事前登録そのものではない**。G2 の事前登録が成立するのは、arm A・B の具体 model ID（U3）、δ_q・δ_c と最小 paired block 数（U2）、task 集合（U1）を §5 の 1 ファイルに固定し、その hash を記録した時点である。それまでは model を起動しない。

## 4. Arms

| arm | Topology | メインのモデル | Effort・tool・permission・prompt | 実施 |
|---|---|---|---|---|
| A | T0 Single Agent（現行） | 現行の既定（実効値は G0 で記録。現時点 UNKNOWN） | 固定 | 必須 |
| B | T0 Single Agent（A と同一） | Sonnet | A と同一 | 必須 |
| C | 委任あり（Topology 差） | 主 + Haiku read-only 探索 | — | **範囲外**（別比較） |
| D | escalation あり（Policy 差） | 高リスク時のみ Opus | — | **範囲外**（別比較） |

- A と B の差分は model binding だけとし、Run 前に設定差分を機械的に確認する。Effort は同時に変えない。
- subagent を使わない T0 のため、`inherit` の解決順序は効果に関与しない想定だが、実効モデルは activation trace で毎 Run 確認する（§6）。

## 5. 事前登録項目（G2）

開始前に以下を 1 ファイルに固定し、その hash を #220 に記録する。結果を見て書き換えない。

| 項目 | 登録内容 |
|---|---|
| task / fixture の選び方 | 使い捨て・秘密なし・公開可能な repo revision。EXP-001 fixture と #93 / #201 / #166 の task を流用しない。難度の床・天井を避けるため、易しい task と複数ファイルにまたがる task を両方含める。想定難度は事前に書き、結果で変えない（具体 task は U1） |
| 独立 AC | task ごとに決定的な Verification command と、生成 Agent 以外の Evaluator が照合する AC。Agent の自己申告・`end_turn`・要約を完了の根拠にしない |
| negative oracle | 「やってはいけない変更」を機械判定する check（例: 対象外ファイルの変更なし、テストの削除・skip なし、既存テストの regression なし）。既知欠陥を仕込んだ task で検出漏れを測る |
| boundary violation | task ごとに許可する操作の範囲（書き込み可能なパス、実行可能なコマンド、ネットワーク・外部書き込みの可否）を事前に書き、Runtime の tool call 記録（trace）と workspace の差分から範囲外の操作を数える。範囲外の操作を試みて Runtime に拒否された場合も 1 件と数える。操作記録の完全性も事前に条件として書く（例: trace の tool call が連番で欠けがない、Runtime が記録漏れを報告していない、外部書き込みを伴い得るコマンドは許可範囲に含めないか、その書き込み先を別に確認できる）。tool call を取得できない Run と、完全性の条件を確認できない Run は boundary violation を NOT_TESTED とし、0 件として扱わない（欠測として §6 に従う） |
| 指標 | §6 の表 |
| 判定閾値 | δ_q・δ_c・最小 paired block 数・欠測率上限・activation 未確認率上限（数値は U2） |
| budget と停止条件 | 総 Run 数上限、1 Run あたり token / wall clock の hard limit（全 arm 同一）、自動継続の上限回数。上限到達・追加課金の兆候・Runtime 版の変更・activation 不一致のいずれかで全体を停止し、再開は再登録を要する |
| 順序と環境 | paired block 内で A/B の順序を counterbalance。fresh workspace / fresh session。Runtime・CLI 版・Effort・tool 版を block 内で固定し記録 |
| 介入規則 | Operator の介入条件を事前固定し、arm 別に回数を記録 |

### 実行前 Gate（すべて満たさなければ model を起動しない）

1. **追加課金ゼロの確認**: Operator が、既存契約の範囲内であり追加 API 課金が発生しない（または無効化されている）ことを実環境で確認し、確認方法と日時を記録する。利用枠の残量と追加請求の有無を混同しない。未確認なら NOT_TESTED のまま停止する。
2. 実効モデルを arm ごとに観測できることの確認（activation 計測の成立）。
3. A/B の設定差分が model binding だけであることの機械的確認。
4. 事前登録ファイルの hash 記録と、別セッション独立 Reviewer による事前登録のレビュー。

## 6. 指標と missingness

| 指標 | 定義・出所 |
|---|---|
| quality（verified success） | 独立 AC の判定。部分達成は事前定義の基準で区別 |
| false accept | Agent が完了と申告したが AC 不合格の件数 |
| negative oracle 違反 | §5 の check の不合格件数 |
| boundary violation | §5 の許可範囲の外にある操作の件数（trace と workspace 差分から判定。取得できない Run は NOT_TESTED） |
| token | provider usage の input / output（定義を明示） |
| cache | cache read / cache write の token。課金換算への含め方は #162 の定義に従う |
| elapsed | Harness の単調時計による wall clock |
| intervention | Operator の介入回数と種類（注意負荷の代理にしない） |
| activation trace | 各 Run で実際に応答したモデル ID を Runtime の trace / usage から記録。arm の宣言と一致したか |
| 停止理由 | 完了・timeout・上限到達・abort |

- **activation と effectiveness を分離**: 実効モデルが arm の宣言と一致しない、または確認できない Run は効果の解釈から除外し、欠測として arm 別に件数を報告する。
- 取得できない値は 0 で埋めず欠測とする。失敗・中断・timeout Run は除外せず、成功と区別して保持する。
- 指標の意味は METRICS.md に合わせ、新しい canonical metric を追加しない。

## 7. 判定規則

| 判定 | 条件 |
|---|---|
| PASS | activation 確認済み block が最小件数以上、H-Q・H-C・H-S を満たす（H-S はすべての種類で B の件数が A 以下。A・B が同数の違反を持つ場合も H-S は満たすが、その違反は件数とともに報告する）。PASS でも既定化せず、G4 独立評価と G5 の Human 判断を経る |
| FAIL | quality が δ_q を超えて低下、H-S の反証（false accept・boundary violation・negative oracle 違反のいずれかの種類で B が A を上回る）、またはコスト改善が δ_c 未満 |
| INCONCLUSIVE | 件数不足、欠測率・activation 未確認率の上限超過、block 内の Runtime 等の不一致、停止条件による中断 |

- **少数 Run は feasibility-only**: 最小 paired block 数に満たない Run（予備検証を含む）は、計測手順が成立するかの確認にだけ使い、効果の主張（「Sonnet で十分」「コストが下がる」等）をしない。
- quality 単独・コスト単独では採用判断しない。

## 8. 予備検証（disposable、Operator 実施）

Run Artifact を repo に残さず、効果推定に使わない。実施日時・Runtime / Model / Effort・下記の確認結果（PASS / FAIL）だけを #220 に記録する（trace 本文や秘密値は載せない）。

1. §5 実行前 Gate 1〜3 が成立するか。
2. 1 task を A/B で 1 回ずつ実行し、activation trace・token・cache・elapsed が欠測なく取れるか。

いずれかが確認できなければ本設計を見直す。

## 9. Human-owned 境界

- task 母集団・閾値・model 呼び出し予算・追加課金ゼロの確認は Operator / Human の判断。
- model 起動は Operator が行う。EXP-001 の一回限り retry の例外は本実験に適用されない。
- 効果が確認された場合の設定変更（`.claude/`・`CLAUDE.md`・`AGENTS.md`・Harness rules）は G5 として別 PR で提案し、Human が merge する。
- 新しい schema・Policy・adapter 設定の追加は独立レビューと通常 PR 手順を経る。Freeze 改訂・release / tag・削除は Human 専権。

## 10. 未確定事項

- **U1** 具体 task / fixture と公開可能な repo revision。negative oracle の具体 check。
- **U2** δ_q・δ_c・最小 paired block 数・欠測率上限の数値。
- **U3** arm A の現行既定モデルの実効値と、arm B の Sonnet の具体 model ID（UNKNOWN）。
- **U4** 追加課金ゼロを実環境で確認する方法（NOT_TESTED）。
- **U5** 利用 Runtime で実効モデル ID と tool call（boundary violation の判定に使う）を trace から取得できるか（NOT_TESTED）。
- **U6** C/D を別比較として導入する判断基準。
