# Claude Code OpusPlan / Scout / Critic: 多モデル役割分担の検証候補

> Status: **Research-only / NOT ADOPTED**。観測・整理日: 2026-10-18 JST。
> Ownership: [#93](https://github.com/s977043/dynamic-agent-topology/issues/93)（compound / routing）・[#82](https://github.com/s977043/dynamic-agent-topology/issues/82)（Critic / adversarial objective）・[#88](https://github.com/s977043/dynamic-agent-topology/issues/88)（escalation / handoff）。
> 既存の [Advisor × read-only Researcher](claude-code-advisor-readonly-researcher-2026-10.md) の研究を置き換えない。実運用設定・新Role・新Topology・新Schemaの採用ではない。

## Input and evidence boundary

検討対象は「Opusで計画/Advisor、Sonnetで実装、Haikuで探索、Opus Criticで完了前に反証する」という利用者提供の設定例。**ベンダーによる成果保証やDATの比較実測ではない**。

一次資料（2026-10-18閲覧）:

- [Claude Code model configuration](https://code.claude.com/docs/en/model-config): `opusplan` はPlan ModeでOpus、実行でSonnetを選ぶ特別な設定。全タスクに強制的なOpus計画ステップを追加するものではない。`modelSettings` のeffortはモデル別。エイリアスの実モデルはprovider/CLI版と組織制限で変わる。
- [Claude Code subagents](https://code.claude.com/docs/en/sub-agents): `model`・`effort`・`tools`・`permissionMode` を定義可能。subagent modelは呼び出し時指定→frontmatter→`CLAUDE_CODE_SUBAGENT_MODEL`→親モデルの順（現在の仕様）。global変数は探索専用ではなく、モデル指定のないgeneral-purposeにも作用する。強制用の別変数 `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` とは区別する。
- [Claude Code advisor](https://code.claude.com/docs/en/advisor): `advisorModel` は助言モデルの指定であり、実際の呼び出しは主モデル判断・互換性等に依存。独立したPR Reviewerや必須Gateではない。subagentにもAdvisor構成が継承され得る。
- [Settings and precedence](https://code.claude.com/docs/en/settings): project/user/managed設定、環境変数、実行時選択が競合する。effective permissionとmodelの観測なしに、宣言値を実効制御と扱わない。

## Current DAT baseline / duplication check

- DATは **Role ≠ Model ≠ Permission ≠ Runtime**、Review Judgment ≠ Verification Evidence、Trigger ≠ Permission を既に分離（[AGENTS.md](../../AGENTS.md)、[Experiment principles](../../docs/EXPERIMENTS.md)）。
- EXP-001は18/18 ACCEPT、9/9 paired blocks、Pilot限定で **Keep T0**。Feature Freezeはcompleted revision 3。既存の凍結Artifact、評価条件、過去Evidenceは変更しない。
- [#82](https://github.com/s977043/dynamic-agent-topology/issues/82) は独立Adversaryの必要性が未実証。[#93](https://github.com/s977043/dynamic-agent-topology/issues/93) のcompound treatment / selective routingと重複するため新Issue・新runtime機構は不要。
- [#193](https://github.com/s977043/dynamic-agent-topology/pull/193) は既存の `.claude/settings.json` permissionルールを修正中。[#186](https://github.com/s977043/dynamic-agent-topology/pull/186) はHuman判断待ちRelease Draft。これらを巻き込んで設定を直接変更しない。
- このRepositoryの `.claude/agents/` は既存Agile Coach / Scrum Masterのみ。新しい `scout.md` / `critic.md` が実行された事実はない。

## Architecture and security review

| Candidate | Possible benefit | Main failure/confound | DAT boundary |
| --- | --- | --- | --- |
| `model: opusplan` | 計画と実装のモデル分担 | Plan Modeの起動率、切替・キャッシュ・総費用を無視 | Claude Code adapter / runtime mapping |
| `scout` with Haiku | 探索Context分離、短い参照結果 | 本当に起動したか不明、探索品質低下、余分なhandoff | Optional Explorer / Read-only intent |
| `CLAUDE_CODE_SUBAGENT_MODEL=haiku` | 未指定subagentの既定費用を下げ得る | general-purpose implementationにも及ぶため採用しない | Provider-local default; global設定は非推奨 |
| `advisorModel: opus` | 曖昧な判断で助言 | Model判断で未起動、subagentへ継承、full-transcriptコスト/情報露出 | Advisor != independent review |
| `critic` with Opus | 欠陥発見の可能性 | Roleだけで実行も必須化もされず、同一sessionの自己承認になり得る | Reviewer Judgment; verifier/CI/human gateを代替しない |

Reviewerを「壊す」指示にしても、欠陥の存在を自動証明しない。Findingには `severity / file:line / reproduced evidence / counterexample / recommended correction / unknown` を求める。差分は呼び出し側で生成し、Read/Grep/GlobのみのReviewerへ入力する手法を優先。Bashを許す場合は、非破壊コマンドのallowlistと実Runtime negative testが必要。`permissionMode: plan` だけでは、親の `bypassPermissions`・`acceptEdits` 等のモードを上書きできないケースがある。

権限を変更する提案は `AGENTS.md` / `docs/AGENT_HARNESS.md` のHuman-owned merge境界に従う。read-only tool list ≠ 機密ファイルの読み取り制限。実契約を検証しないまま本番secretが見えるcheckoutへ投入しない。

## Falsifiable questions and staged minimal comparison

まず **既存Reviewerが見逃した再現可能な欠陥**、または **探索負荷による測定可能な非効率** を1つ選ぶ。なければ新Roleを作らず `DEFER`。

| Arm | Treatment (constant unless specified) | Contrast |
| --- | --- | --- |
| A | Sonnet T0（Advisor off）、既存Verifier/CI | baseline |
| B | A + Haiku Scout（only Read/Grep/Glob） | B−A: delegation package |
| C | B + same-model Reviewerに反証的objectiveを与える（optional gate） | C−B: adversarial review package |
| D | CのReviewerをOpusへ変更（同じobjective、入力、権限、budget） | D−C: model-strength increment |
| E | Dで `opusplan` を使用し、Plan Mode発火を観測（それ以外を可能な限り固定） | E−D: plan/execution model split package |

比較は**順次実施する候補**であり、一斉5-arm実験の事前承認ではない。大きいArmへ進む条件を先に定義する。Advisorは既存の[4-arm研究](claude-code-advisor-readonly-researcher-2026-10.md)で別Treatmentとし、必要になるまでEへ同時追加しない。正確な因果帰属が難しい場合は交絡と記録する。

### Preregister and measure

1. Task class（探索集中/通常/高リスク）、実欠陥fixture、AC、negative/positive oracle、独立Evaluator、practical improvement、許容false positiveとToken/Latency/Human時間上限を開始前に固定。
2. 同じrevision/input/予算/verification commandsを使い、fresh checkout/session、実行順序のcounterbalance、前armの診断の持ち込み禁止を守る。モデル別effort・provider・CLI版を記録。
3. **宣言 vs 実測**を分離: effective model ID、subagent spawn、Advisor invoked/declined/unavailable、Plan Mode発火、tool attempts/denials、permission mode、検出欠陥の再現、CI/Verifier結果。
4. Costはmain/Scout/Critic/Advisor別のcached・uncached token、全leg latency、retries、Human correction/review、total verified-success costまで測る。未知の値を0にしない。
5. quality regression、secret境界違反、未承認操作、必須Gate欠落ならNO_GO。観測不足・効果が出ない場合はINCONCLUSIVE/REJECTを許す。cheap baselineが十分ならA/T0を維持する。

### First safe probe (no model launch in this change)

- Disposableでsecret-freeなfixture上で、実Claude Code版、provider、`/model`・`/tasks`、構成ファイルの読み込みを確認。
- ScoutにRead/Grep/Globは可能、Write/Edit/Bash/MCP/ネットワーク経路は拒否、Criticに禁止されたwriteがないことを確認する（**現時点では未実測**）。
- 既存PR #193の変更・Humanレビューを先に解決し、実効権限を再確認。設定の修正・CLI起動・実Experiment開始は別タスク/権限ゲートとする。

## Decision and non-goals

**Decision: research intake only; runtime adoption = NO_GO until observed advantage and enforcement tests.** 最新公式文書から「設定可能」と確認しただけで「効果がある」や「強制された」と結論しない。既存の#82/#88/#93で候補を追跡し、独立ReviewerとHuman-owned decisionを維持。

本変更では `.claude/`、`CLAUDE.md`、`AGENTS.md`、Adapter、Schema、Topology、Routing、凍結Artifact、依存、CIを変更しない。Release #186のHuman判断、PR #193のHuman merge、既存Issueの未達taskも勝手に完了扱いしない。
