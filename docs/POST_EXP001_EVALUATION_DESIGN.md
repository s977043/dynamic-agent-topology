# post-EXP-001 評価の設計案（#93 / #88）

状態: **非規範的な設計案（未採用・独立レビュー前）**。[CURRENT_EXECUTION_PLAN.md](CURRENT_EXECUTION_PLAN.md) 順序 2 の設計案です。実験開始・Policy 適用・experiment Artifact 追加の許可ではありません。`experiments/`、`schemas/`、EXP-001 の Frozen file は変更しません。EXP-001 の受理判断と [DECISION.md](../experiments/EXP-001-t0-vs-t1/DECISION.md) は、この文書によって変わりません。

- 起案日: 2026-10-15 / 基準: origin/main `3b760ff`
- 関連: [Issue #93](https://github.com/s977043/dynamic-agent-topology/issues/93)、[Issue #88](https://github.com/s977043/dynamic-agent-topology/issues/88)
- 一次ソース: Issue #93 / #88 本文とコメント、[CURRENT_EXECUTION_PLAN.md](CURRENT_EXECUTION_PLAN.md)、[EXPERIMENTS.md](EXPERIMENTS.md)（Capability-level ablation 節）、[EXP-001 DECISION.md](../experiments/EXP-001-t0-vs-t1/DECISION.md)、[experiment.schema.json](../schemas/experiment.schema.json)
- 研究ノート（候補であり採用済みの契約ではない。参照のみ）: [hydrafusion-adaptive-execution-strategy.md](../knowledge/research/hydrafusion-adaptive-execution-strategy.md)、[evidence-driven-model-escalation-handoff.md](../knowledge/research/evidence-driven-model-escalation-handoff.md)、[claude-code-advisor-readonly-researcher-2026-10.md](../knowledge/research/claude-code-advisor-readonly-researcher-2026-10.md)

## 0. Evidence・解釈・推奨の区別

| 区分 | 内容 |
|---|---|
| 観測済み Evidence | EXP-001 の 18 Run は全成功で、T0 が失敗した Run はない（DECISION.md）。#88 には再現可能な baseline 失敗が 1 件も登録されていない（#88 2026-10-15 判定）。`experiment.schema.json` の condition は `executionRef` のみで、condition ごとの model binding を表現する field はない |
| DAT 側の解釈 | EXP-001 の結果は難度の床効果（Limitation 13）の下での観測であり、stronger model や escalation の効果について何も示さない。本設計はその結論を一般化しない |
| 推奨案（未採用） | U1: model binding は `adapters/` 側に置き、experiment から参照する（§10）。schema は拡張しない |
| 未確定（本文の提案） | §1 以降の推奨案・仮説・指標・U2〜U8。開始前に Human と独立 Reviewer が宣言する |

## 1. 結論（推奨案）

**別々の実験にして順序を付ける。共通部品は「宣言済み母集団（task registry）」と「T0 baseline Run」だけを共有する。**

1. **EXP-002（先行）: #93 Cascade 系の最小版 = 混合母集団上の T0 vs always-stronger（F）paired 比較 + shadow gate 記録**
   - 全 task で T0（= #93 の E）と F（最初から強い capability、fresh session）を paired で実行する。
   - gate（selector）は T0 の Run 終了時点の観測（Verification 結果など）だけを入力に **shadow で判断を記録**し、F の Outcome を見る前に凍結・記録する。F-first blockではFのOutcome・usage・診断をgate担当から隔離して封印し、gate判断のhash固定後に開示する。gate は「どの比較 evidence を集めるか」を決めない（全 task で両 arm を実行）。
   - これで 1 回の収集から次の 2 つを分離して得る:
     - treatment 効果: F − T0 の paired delta（全体、および T0 失敗層／成功層の層別）
     - selector 品質: shadow 判断 × matched outcome から作る benefit label の 4 分類（correctly selected / missed beneficial / unnecessary / correctly avoided）
   - 副産物: T0 が再現可能に失敗した task が #88 の eligible 候補になる。
2. **EXP-003（後続）: #88 recovery の最小版 = eligible failure 上の C vs D（compact handoff 固定で model だけを変える）**
   - EXP-002 で得た T0 失敗のうち、小さい Prompt/Context/Harness 修正で解消しないものを対象とする。予算と Runtime が許せば B / E を追加する（payload 効果）。A（current session 継続）は最後に回す。
   - 結論は conditional-on-eligibility に限定する。
3. **Critique（#93 A/B/C/D）と Advisor 4-arm は後回し**。Critique は isolated critic の権限・隔離の attestation が Stage 0 で確立してから着手する。

### 推奨理由（判断基準: 要件適合性 → 安全性 → 保守性 → コスト → 拡張性）

- **要件適合性**: 順序 2 の完了条件「selector の shadow 判断と treatment の paired 効果を分離」を、EXP-002 の 1 本の収集で両方満たせる。matched counterfactual が全 task にあるので、nonselected task の扱いを推定で埋めずに済む（#93 H2 の INCONCLUSIVE 条件を回避）。
- **母集団の問題を先に解く**: #88 は「再現可能な baseline 失敗」が 1 件も登録されておらず、単独では開始できない（#88 2026-10-15 判定）。EXP-001 の 18 Run は全成功で転用不可。EXP-002 の T0 Run が eligible 候補の発見手段を兼ねる。
- **Issue 計画との順序の違い**: #93 は selector study を eligibility-conditioned treatment evaluation の後に置き、#88 は baseline 失敗の登録と小さい介入の診断を次の作業としている。本案はこの順序を意図的に入れ替える提案である。理由は、eligible failure が 0 件のままでは treatment 評価を始められず、EXP-002 の T0 Run がその登録作業を兼ねるため。EXP-002 の selector 品質は matched outcome に基づく shadow 評価に限り、eligibility-conditioned な recovery 効果の結論は EXP-003 まで出さない。#88 の「失敗候補の登録と小さい介入の診断」は EXP-003 の開始条件として残す。採否は両 Issue で Human と独立 Reviewer が判断する。
- **交絡の分離**: #88 の treatment は「失敗後の fresh session + handoff + model」、#93 Cascade は「gate + model 昇格」。1 本にまとめると handoff payload と gate と model の効果が同じ contrast に混ざる。#93 本文・#88 コメントとも「比較 arm を混同しない」と明記している。
- **安全性・保守性**: 各実験の arm 数を 2 にとどめ、Decision 3 値（PASS/FAIL/INCONCLUSIVE）を素直に適用できる。
- **コスト**: F を全 task で回すのは高いが、全taskでmatched outcomeを取得するための費用を伴う。G（cascade 実行）を別途回さず、G のコストは「T0 + gate + F（選択 task のみ）」として**合成値**で示す。これはcold-restart方策のoffline simulationであり、実際のGの効果・経済性は未実行としてINCONCLUSIVEに残す。合成時はFを同一repo初期状態・同一入力で起動し、T0のpatch/診断/handoffを渡さず、選択時はFだけ、非選択時はT0だけを最終出力とする。timeout/cancel/fallbackと成功判定、全破棄leg/再検証費を開始前に固定する。この同一性または必要な費用を確認できないtaskは合成評価もINCONCLUSIVEとする。

## 2. 比較した代替案

| 案 | 内容 | 長所 | 短所 | 判定 |
|---|---|---|---|---|
| **R（推奨）** | EXP-002 = T0 vs F 混合母集団 + shadow gate → EXP-003 = #88 C vs D | selector と treatment を 1 収集で分離。#88 の母集団を供給 | F 全件実行のコスト。G は合成値 | 推奨（未採用） |
| X1 | #93 と #88 を 1 本に統合（E/F/G + A–E を同一 task で） | 収集の重複が少ない | arm 数 8 前後、handoff / gate / model の交絡、eligible 条件と混合母集団が同居して結論の射程が曖昧 | 不採用 |
| X2 | #88 を先行（A–E recovery） | Issue の手順に沿う | eligible failure が 0 件で開始不能。selector 分離の条件を満たさない | 不採用（順序 2 の条件不足） |
| X3 | #93 Critique A/B/C/D を先行 | HydraFusion の主張に直接対応 | isolated critic の隔離 attestation が未確立。arm 4 つ。selector 評価にならない | 後回し |
| X4 | Cascade E/F/G を実際に 3 arm 実行 | G の観測コストが得られる | 独立fresh stateで全taskのE/F/Gを収集しshadow判断をoutcome開示前に固定すれば両立できるが、arm追加の費用と状態隔離が必要 | EXP-002 の結果が PASS 方向なら後続で検討 |
| X5 | shadow なしで T0 失敗 task のみ収集 | 安い | eligibility-conditioned になり selector 品質を測れない（EXPERIMENTS.md 禁止事項） | 不採用 |

## 3. 仮説と反証条件

### EXP-002

- **H-T（treatment）**: 宣言済み混合母集団において、F は T0 に対し verified success を事前宣言した最小実務改善幅以上に改善する。ただし改善は T0 失敗層に集中し、T0 成功層では品質同値・コストのみ増加する。
  - 反証: T0 失敗層でも F の success 改善が最小幅未満、または regression が F 側で増える → FAIL。T0 失敗層が事前宣言の最小件数に満たない → INCONCLUSIVE。
- **H-S（selectorのoffline simulation限定）**: T0 Run の観測だけを入力にした凍結 gate の shadow 判断の合成結果は、always-T0 と always-F の両 policy に対し、事前定義の「verified success あたり総コスト（gate コスト含む）」で優る。
  - 反証: missed beneficial または unnecessary の件数が事前宣言の上限を超える、または合成 policy コストが always-T0 / always-F のどちらかに劣る → FAIL。benefit label が付かない task（片側欠損）が事前宣言の割合を超える → INCONCLUSIVE。PASS/FAILは宣言したoffline simulationだけの判断とし、実Gのオンライン効果・latency・経済性の優越はINCONCLUSIVE。実policyの主張には独立したG armの実測が必要。
- **前提（activation）**: F が実際に強い capability で実行されたことを trace で確認できない Run は効果解釈に使わない。

### EXP-003

- **H-R（recovery, conditional）**: eligible failure において、D（強い model + compact handoff）は C（同 model + 同 handoff）より verified success あたりコストが良い。
  - 反証: D の success が C と同値以下、または D のコスト増を success 改善で正当化できない → FAIL。小さい修正で解消した task は母集団から除外し、除外件数を記録。eligible 件数不足 → INCONCLUSIVE。
- 結論は「eligible failure に到達した task での回復効果」に限定し、gate 精度や全 workload の routing 優劣は主張しない。

**しきい値（最小改善幅・regression 上限・最小件数・欠損率上限）は数値を本案で決めない。開始前に Human と独立 Reviewer の合意で宣言する（未確定事項 U3）。**

## 4. Arms と母集団

### EXP-002 arms

| arm | 内容 | 由来 |
|---|---|---|
| T0 | baseline model / capability、単一 Agent、bounded attempts、fresh workspace・session | EXP-001 Keep T0、#93 E |
| F | stronger capability を最初から使う単一 Agent。他条件は T0 と同一 | #93 F |
| shadow gate | 実行 arm ではない。T0 Run 終了時の観測から escalate / do-not-escalate を記録 | #93 G の gate 部分、#88 shadow-gate |

- topology は T0/F とも同じ（単一 Agent）。変えるのは model/capability binding だけ。Role ≠ Model の分離を保つ。

### 母集団（開始前に宣言・凍結）

- **混合**であること: T0 で解けると見込まれる task と、T0 が失敗し得る難度の task を両方含む。どちらかの層が空なら H-S は INCONCLUSIVE。
- 各 task の登録項目: 公開／許可済み repo revision、Acceptance Criteria、決定的な Verification command、想定難度層（事前の見立て。結果で書き換えない）、副作用の範囲、予算。
- EXP-001 の 3 Scenario は「易しい層」の候補にはなり得るが、難しい層の根拠には使わない。EXP-001 の Frozen fixture は変更しない（参照のみ）。
- train / test / regression の split を宣言し、gate の閾値調整は train 層だけで行う。test 層の matched outcome で gate を調整しない。

### EXP-003 arms

| arm | 内容 | 優先 |
|---|---|---|
| C | baseline model、fresh session、compact handoff | 必須 |
| D | stronger model、fresh session、C と同一の compact handoff | 必須 |
| B / E | full-transfer（baseline / stronger） | 予算次第 |
| A | current session 継続 | 最後 |

- compact handoff は 1 task につき 1 回だけ生成し、C と D で同一 bytes を使う。生成は Outcome を知らない手順で行う。

## 5. Outcome と Cost の指標

### Outcome（独立 Evaluator が判定）

- verified task success（Verification command の exit と AC 照合）
- regression（既存テスト・regression split）
- human interventions（回数。注意負荷の代理にしない）
- boundary violation（critical があれば標準採用しない）
- EXP-003 のみ: handoff 後の missing-context failure
- Evaluator には arm 名・生成過程の推論を渡さない（可能な範囲で blind）。blind にできない場合は limitation に記録。

### Cost（追加 Cost を含めて全計上）

- leg 別: fresh input / cached input / cache write / output tokens、wall clock、provider 課金の再計算に足る usage 記録
- policy レベル: gate 実行コスト、handoff 生成コスト、Verification 追加コスト、破棄された leg
- 主指標: **verified success あたり総コスト**（policy 別: always-T0 / always-F / shadow gate 合成）
- 欠損値は 0 で埋めない。EXP-001 の token 定義（cached を含む total_token_usage）と比較する場合は定義を明示する。

### selector 評価の出力

- 小 sample では precision/recall を出さず、4 分類の件数と各 case の Evidence を保持する。
- benefit label は事前定義の Outcome / Regression / Cost ルールで付け、gate 自身の説明は使わない。

## 6. 交絡の制御

| 交絡 | 制御 |
|---|---|
| cross-arm contamination | 各 arm を同じ repo revision・同じ初期入力・fresh workspace / session から開始。前 arm の patch・診断を持ち越さない（EXP-003 の handoff は treatment として明示） |
| 実行順序 | block（task × rep）ごとに T0/F の順序を counterbalance し、順序を記録。F-firstはOutcome/usage/診断をgate担当から封印し、T0観測によるgateのhash固定後に開示。隔離できないblockはselector解析から除外し欠測として計上 |
| Runtime / Effort 差 | 同一 block で Runtime・Effort・tool 版を固定。model binding だけを変える |
| prompt 差 | T0/F で同一 prompt。model 固有の prompt 調整は禁止（必要なら別 arm） |
| gate の後知恵 | gate 入力・閾値・決定規則・fallback を gate担当へのFのOutcome/usage/診断開示前に凍結し、判断を先に記録 |
| 環境混在（EXP-001 Limitation 1/2 の再発） | Run kit と環境を開始前に固定し、block 内で環境が異なる Run は descriptive-only |
| 難度の床効果（EXP-001 Limitation 13） | 母集団に T0 が失敗し得る層を含めることを開始条件にする |
| 評価の自己参照 | Outcome 判定は生成 Agent と別の Evaluator。非決定的な判定は不一致を保持 |

## 7. Stage 0（disposable な最小検証）

目的: 本実験の収集が成立するかだけを確かめる。**結果は Evidence として採用判断に使わない**。repo に Run Artifact を残さない（scratch / 外部 workspace のみ）。

1. **副作用隔離の negative test**: 使い捨て workspace で、Agent が workspace 外・remote・secret に書けないことを実測（書き込み試行が失敗することを確認）。試行先は使い捨ての canary パス・mock remote・ダミー secret に限り、実在の外部リソースや本物の credential は使わない。自然言語の「読み取り専用」指定や静的設定だけを attestation とみなさない。
2. **model binding の activation 確認**: F 相当の設定で、実際に使われた model/effort を trace / usage から取得できるか。取得できなければ F は unavailable 扱い。
3. **cost 取得の完全性**: leg 別 usage（cached 含む）と wall clock を 1 Run ずつ取得し、再計算できるか。
4. **shadow gate の凍結手順**: T0 Run の観測から gate 判断を記録し、FのOutcome/usage/診断の開示前にhash付きで固定できるか。T0-firstとF-first双方をドライランし、F-firstでは別保存先/別担当による封印と開示時刻を記録する。単なる「見なかった」という自己申告は隔離証跡にしない。
5. **難しい層の候補探索**: 候補 task を 2〜3 件、T0 で 1 回ずつ実行して失敗が再現しそうかを見る（探索であり母集団の採否判断には使わない旨を記録）。
6. EXP-003 用: compact handoff を 1 件生成し、C/D で同一 bytes を渡せるかを確認。

Stage 0 の Go 条件: 1〜4 がすべて機械的に確認できる。いずれか不可なら本実験を設計し直す（arm を unavailable にして黙って代替しない）。

## 8. Human-owned 境界

- 母集団の宣言・しきい値の確定・model 呼び出し予算の承認は Human 判断（費用・Permission を伴うため）。
- Runtime Permission の拡張、新しい credential、管理者設定の変更は行わない。
- 新しい schema・semantic check・Policy の追加は独立レビューと通常 PR 手順を経る。Freeze 改訂・release/tag・削除は Human 専権（AGENTS.md / AGENT_HARNESS.md）。
- EXP-001 の Frozen artifact（fixtures、T0/T1 topology、schemas 等）は変更しない。参照のみ。
- 本実験（Stage 0 を含む）の model 起動は Operator が行う。Agent は代行しない（AGENTS.md / AGENT_HARNESS.md の Agent 起動例外は EXP-001 の一回限りの retry に限られ、本実験には適用されない）。Agent 起動が必要になった場合は、Human 承認による自律境界の変更として別 PR で扱う。
- 研究ノート（hydrafusion / escalation / advisor）は候補であり、本設計の採用は `knowledge/sources.yaml` の adopted を変えない。

## 9. 将来の artifact 案（パスのみ。YAML は書かない）

- `experiments/EXP-002-t0-vs-stronger-shadow-gate/experiment.yaml`（`schemas/experiment.schema.json` 準拠）
- `experiments/EXP-002-t0-vs-stronger-shadow-gate/population.md`（母集団・層・split の宣言）
- `experiments/EXP-002-t0-vs-stronger-shadow-gate/gate.md`（shadow gate の入力・閾値・決定規則・凍結手順）
- `experiments/EXP-002-t0-vs-stronger-shadow-gate/DECISION.md`
- `experiments/EXP-003-escalation-recovery-compact-handoff/experiment.yaml`
- `experiments/EXP-003-escalation-recovery-compact-handoff/handoff-template.md`（候補。canonical 化しない）
- 必要なら `fixtures/exp-002/...`（EXP-001 の `fixtures/exp-001/` とは別ディレクトリ）

## 10. 推奨案と未確定事項

### 推奨案: U1 condition ごとの model binding

- 背景（Evidence）: `experiment.schema.json` の condition は `executionRef`（AgentTopology / ExecutionBaseline）のみで、condition ごとの model binding を表現できない。`controls.sameModel: false` は書けるが、どの arm がどの model かは machine-readable にならない。
- 比較した案: (a) model binding を `adapters/<runtime>/` 側の Runtime Mapping に書き、experiment から参照する。(b) schema を拡張する（新 artifact kind 扱いなら semantic check と spec-lint 配線が必要）。
- **推奨: (a)。schema の拡張はしない。**
- 理由: ARCHITECTURE.md の Plane 分離（Topology ≠ Model、Runtime ≠ Model Provider）を保つため。T0 と F は同じ topology で model binding だけが異なるので、binding を Runtime Mapping に置けば topology / experiment に model 固有の記述を持ち込まずに済む。(b) は schema・semantic check・spec-lint の追加を伴い、境界を experiment 側へ寄せる。
- 範囲: これは表現場所の推奨であり、具体的な Runtime・model・effort（U4）や adapter ファイルの作成は含まない。参照の具体的な書式は experiment Artifact を起案する PR で独立レビューを経て決める。

### 未確定事項（開始前に Human と独立 Reviewer が宣言する）

- **U2 母集団の出所**: 「T0 が失敗し得る難度」の task を、公開可能な repo revision から何件用意できるか不明。private code は使えない。
- **U3 しきい値**: 最小実務改善幅、regression 上限、層別最小件数、欠損率上限、rep 数は未定。EXP-001 の `minimumRunsPerScenarioPerCondition: 3` を下限候補とする。
- **U4 Runtime / model の組**: baseline と stronger の具体的な Runtime・model・effort、および同一 Runtime 内で両方を呼べるかは未確認。EXP-001 の Codex / gpt-6.1-sol / high は baseline 候補の 1 つにすぎず、結論は一般化しない。
- **U5 gate の入力**: T0 の Verification 失敗以外（自己申告、turn 数など）を入力に含めるか。固定 turn 数は仮説扱い（#88）。
- **U6 予算**: F 全件実行の費用見積もりと承認者。
- **U7 G の合成値の妥当性**: cold-restart offline simulationの同一初期状態・入力・非引継ぎ・fallback・成功判定・費用範囲を事前宣言し検証できるか。Reviewerの許容だけでは同一性を証明しない。未達なら合成評価はINCONCLUSIVE、実policyの主張にはX4のG実測へ切り替える。
- **U8 Critique / Advisor の順番**: EXP-003 の後か、並行か。現案では EXP-002 の結果を見て決める。
