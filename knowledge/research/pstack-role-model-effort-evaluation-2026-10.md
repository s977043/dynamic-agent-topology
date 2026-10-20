# pstackのRole × Model × Effort配分：DATでの評価候補（2026-10-18）

## Status / scope

**Research-only / NOT ADOPTED / no runtime activation.** pstackはDATにインストールしない。外部Plugin/SDK/MCP/Skillのコード、設定、権限、モデル既定値を取り込まず、設計上の仮説だけを記録する。

- 対象の正本: [#93](https://github.com/s977043/dynamic-agent-topology/issues/93)（選択的multi-model orchestration）、[#88](https://github.com/s977043/dynamic-agent-topology/issues/88)（model escalation / handoff）、[#82](https://github.com/s977043/dynamic-agent-topology/issues/82)（独立した反証的判断）。
- 現在の設計作業: [Draft PR #194](https://github.com/s977043/dynamic-agent-topology/pull/194)。同PRのCascade/Critique設計を複製せず、その前提・評価に不足する論点をIssue側へ返す。
- Release hold（2026-10-20再確認）: [PR #218](https://github.com/s977043/dynamic-agent-topology/pull/218)がHuman判断によりmergeされ、mainの`CITATION.cff`と`CHANGELOG.md`は**0.3.0の公開予定日2026-10-20**に更新された。ただし`v0.3.0`のimmutable tagとGitHub Releaseは**未公開**（Release API一覧は空）。metadataの予定日・PRのmergeと、実際の公開証跡は別。公開操作/タグと最終確定はHuman-ownedであり、release gate完了まで本研究PRはDraftでmergeしない。
- EXP-001は18/18 Run、9/9ペアのPilotで**Keep T0**。この結果は別モデル・別タスク・pstackへの効果証明ではない。Frozen 33 blobsおよび既存Decisionを変更しない。

## Provenance / 確認した事実

調査日: 2026-10-18。参照先のupstream `cursor/plugins` main headは`0b8e952052d482ee6de06deebf14d590d77b1b34`（調査時点のsnapshot）。

- Discovery（投稿者の紹介。実装の証拠ではない）: [@sora_bizのX投稿](https://x.com/sora_biz/status/2110356303340322854)。
- Primary: [pstack README](https://github.com/cursor/plugins/blob/0b8e952052d482ee6de06deebf14d590d77b1b34/pstack/README.md)、[setup-pstack skill](https://github.com/cursor/plugins/blob/0b8e952052d482ee6de06deebf14d590d77b1b34/pstack/skills/setup-pstack/SKILL.md)、[Claude Code adapter](https://github.com/cursor/plugins/blob/0b8e952052d482ee6de06deebf14d590d77b1b34/pstack/docs/harness/claude-code.md)。
- pstackはCursor向けPluginで、`/poteto-mode`がタスクからplaybookを選び、`/setup-pstack`がrole別モデルとreasoning budgetを設定する。複数モデルによる`arena`、`interrogate`、`swarm`などのワークフローを説明している。
- upstream READMEには**Claude CodeでのPlugin導入**と、Cursor固有機能をskipするadapterの説明がある。つまり「Cursor専用で他には一切対応しない」とは言えない。
- upstream READMEが説明する初期の例は**実装系Grok、判断・文章系Opus 5.5**であり、`setup-pstack`でモデル選択を変更できる。このupstreamで**OpenAI Codexへのネイティブ移植・feature parity・提示モデル設定の動作保証**は確認していない。投稿で示された具体的なAstra/Sol推論段階は、DAT標準値でもupstreamの普遍的defaultでもない。
- Claude Code adapterは別の実行環境へmodel指定を写像し、対応できないprovider slugのモデル指定を省略する。**宣言されたmodelと実効modelが一致しないfallback**を考慮し、実験ではeffective model/effortと実行contextを観測する。静的なRole指定だけでは**選んだモデルの実行・最小権限・独立性**を証明しない。
- upstreamの技法と開発者の目的は、DATでの比較実験の参考であって、task success・cost改善・defect reductionのDAT測定値ではない。

## 既存DATとの重複 / 差分

| pstackから読み取れる考え方 | DATの既存責務 | 追加の価値 / 最小対応 |
|---|---|---|
| task-to-playbook selection | #93、docs/ENGINEERING_LAYERS.md、Routing/Strategy | playbook分類の観測可能性と誤分類を研究候補として追加。実Routerは作らない |
| per-role model + effort + budget | #88、#162、adapters、docs/METRICS.md | Role、Model、Effort、Topology、予算を混同しない評価計画の補助 |
| parallel arena / swarm / panel | #93、#166、docs/EXPERIMENTS.md | fan-out、各legのtoken/latency/human supervisionを完全計上 |
| isolated / cross-model judgment | #82、#93（Critique） | objective、Context、Role分離、Modelの限界寄与を分ける |
| verification-first / shipping playbooks | 既存Verifier、Evidence、#159 | verified outcomeとモデルの「完了」報告を分離。自動mergeは許可しない |

## Hypotheses / 反証条件

**H1（Task-conditioned model allocation）**: 同一の既存T0、同じ対象タスク母集団、Runtime・tool/permission・verification・hard budgetを固定したとき、事前登録したtask classから開始model/effortを選ぶ方針は、固定選択と比較して、品質下限を守った**verified successあたり総コスト**を改善できるか。Routingが実際に発動したというTraceがなければ`INCONCLUSIVE`。固定強モデルとの比較や混合タスク母集団のselector検証は#194 / #93の設計を先行し、本ノートでは新たなEXP番号を割り当てない。

**H2（Effect attribution）**: model、effort、parallelism、judge、検証工程を一度に変えた「pstack風パッケージ vs T0」では、改善原因は識別できない。まずrouting policyを一つの**bundle treatment**として比較し、利益が確認される場合に限り、その後にmodel-only / effort-only / orchestration-onlyの限定的ablationを事前登録する。異なるmodel間で同名effortの能力やtoken budgetが等価だと仮定しない。

**H3（Independent review）**: 既存Reviewerやdeterministic Verifierが取り逃した**再現欠陥**を前提に、same-context review、独立context・同model review、独立context・別model reviewの差を#82 / #93の既存Critique armsへマッピングする。Reviewerの読み取り専用宣言と、Runtimeの実際の書込/外部実行権限は区別する。新Reviewer roleは仮説が反証されたら作らない。

## Cheapest useful verification / 実行前ゲート

1. **先に#194の未確定U2〜U8**（母集団、gate、予算、runtime/model、判定基準）をレビューし、同じ実験を別PRで作らない。モデル・effort変更は、使用可能性/モデル識別子/実効的な適用をTraceで確認する。**negative control:** 利用不可のprovider/model slugを宣言したテストでは、Claude Code adapterが指定を省略してparent session modelへfallbackし得るため、`declaredModel != effectiveModel`を観測したrunを意図したtreatmentの成功例に算入せず停止・除外理由を記録する。
2. 正/負の小さな匿名化タスクを混在させ、独立ACと再現fixtureを用意する。既存EXP-001の簡単な3シナリオだけから品質向上を主張しない。
3. Paired blocks、fresh context、順序counterbalance、repeated runs、一定のpermission boundary / runtime/tool version / hard resource ceilingを宣言。各legのtoken・wall-clock・cache read/write・fan-out・retry・abortを**実測**し、観測usage × 適用時点の料金表による**推定費用**と取得可能な実請求額を区別する。未計測legを無料とみなさない。
4. policy選択のshadow結果は、未実行treatmentのOutcomeを知った後で変更できないよう事前commit/hashし、selectorの精度・treatmentの有効性・runtime enforcementを別々に評価する。単純な後知恵でのroute最適化を成功としない。
5. Outcomeはindependent AC、regressions、critical defect、false accept、human interventions、token、wall-clock、handoffs、aborts/missingness、boundary violationsで判断する。Reviewer modelを変えた場合はcontext/objective/予算差も記録する。Claude Code adapterの`Explore`指定はBash能力を残すため、read-onlyの**実効強制**はPromptやAgent名ではなく、隔離fixture上のnegative/positive permission testで別途確認する。
6. 小標本のfeasibilityとpolicy優越性を分離。success=0のarmではcost / verified successをゼロや有限値に補完せず、成功率と総費用を別々に報告する。必要条件を満たさない、未activate、scope外副作用、独立確認不足なら`INCONCLUSIVE`。品質下限違反・境界違反は`FAIL`。効果があってもHuman-owned judgmentなしに既定化しない。

## Decision / 非採用境界

**今取り込む:** 出典と相違点、反証可能な研究課題、既存#93/#88/#82へつなぐpre-run controlの記録。

**今取り込まない:** pstackのPlugin/Skill/SDK/MCP依存、Playbook runtime、Routing Policy、canonical Topology / Role、schema、実モデル配分、実験実行、permission変更、独立Reviewerの自動承認、PRの自動merge。

追加Runtimeを先に作らず、#194で設計される最小比較が成立しなければ**Defer / Reject**する。Source Claim != DAT Evidence; declared model/permission != observed execution/enforcement; AI review != human approval.
