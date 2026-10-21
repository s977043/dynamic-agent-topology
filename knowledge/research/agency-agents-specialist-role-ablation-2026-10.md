# Agency Agents: 専門Roleの知識付加をT0で比較評価する（Research-only）

## 状態・非採用境界

- **Status:** research candidate / not adopted（2026-10-19確認、[Issue #211](https://github.com/s977043/dynamic-agent-topology/issues/211)）
- **一次資料:** [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents)、観測した `main` SHA [`652b2692f8d8ec2b1f1a38e559073e287dfdc469`](https://github.com/msitarzewski/agency-agents/commit/652b2692f8d8ec2b1f1a38e559073e287dfdc469)（2026-10-15 UTCのcommit。将来の最新版を意味しない）
- **License:** [MIT](https://github.com/msitarzewski/agency-agents/blob/652b2692f8d8ec2b1f1a38e559073e287dfdc469/LICENSE)。参照のみ。外部テキスト/コードの転載・コピー、依存追加、インストーラー実行、自動同期はしない。
- **DAT source ledger:** `knowledge/sources.yaml` の `msitarzewski-agency-agents-2026`、`adopted: []`。
- **Freeze:** EXP-001 revision 3の凍結Artifact、実行条件、schema、validator、Runtime mappingを変更しない。本書はpost-freezeに向けた設計候補のみ。

## 確認したsource claim（DATでの有効性の実測ではない）

1. READMEはMarkdownの専門Agent定義（責務・ワークフロー・成果物・成功指標）と `scripts/convert.sh` / `scripts/install.sh` を提供し、Claude Code / Codex / Hermesなどへの変換・導入を案内している。
2. [Multi-Agent Systems Architect](https://github.com/msitarzewski/agency-agents/blob/652b2692f8d8ec2b1f1a38e559073e287dfdc469/engineering/engineering-multi-agent-systems-architect.md) は責務境界、least privilege、failure recovery、structured trace、human gate、Evalを推奨する。
3. [Experiment Tracker](https://github.com/msitarzewski/agency-agents/blob/652b2692f8d8ec2b1f1a38e559073e287dfdc469/project-management/project-management-experiment-tracker.md) は仮説・primary KPI・control/variant・experiment learningを重視する。
4. [Agents Orchestrator](https://github.com/msitarzewski/agency-agents/blob/652b2692f8d8ec2b1f1a38e559073e287dfdc469/specialized/agents-orchestrator.md) はPM→開発↔QA→統合の自律パイプラインと再試行（最大3回）を記述する。
5. [Evidence Collector](https://github.com/msitarzewski/agency-agents/blob/652b2692f8d8ec2b1f1a38e559073e287dfdc469/testing/testing-evidence-collector.md) はスクリーンショットだけでは送信成功や永続化を証明できないと明示し、行動証拠と区別する。一方、サンプルの `qa-playwright-capture.sh` / `resources/views` は特定環境の前提。
6. READMEの `Production-Ready`、各role文書の「20 eval」「3 retry」「3秒」等の数値は**source内の推奨・表現**であり、DATのbenchmark値や採用基準ではない。

## DATの既存実装との照合

| Sourceから得る観点 | DAT/PlanGateで既にある境界 | 今回の判断 |
|---|---|---|
| Agentの個別責務・成果物 | DAT `roles/*.yaml`、`docs/ARCHITECTURE.md` | 既存Roleは置換せず、追加の判断基準のみablation候補にする |
| 少権限・Trace・回復 | DAT `docs/AGENT_HARNESS.md`、Role≠Permission | Promptに権限宣言を書いても強制にはならない。Runtime negative testが別途必要 |
| QA Evidence / 合否 | DAT VerifierとEvaluator分離、PlanGate独立レビュー・承認 | Agent自身のPASSや「ready」は証拠・Human承認にしない |
| 自律Orchestrator | PlanGateの既存WFとHuman-owned gate | 二重Orchestrator・自己承認・強制的な3 retryは**不採用** |
| 外部Tool変換・配布 | DATはRuntimeではなくmanual adapter | `install.sh`、`convert.sh`、desktop app、グローバル設定更新を**実行しない** |

重要: Agency AgentsのMarkdownはツールで処理されると実行指示になり得る**未信頼入力**。source記述は証拠として読むが、既存の権限・Approval・Policyを上書きしない。

## DAT側のInterpretation

Agent数を増やす研究ではなく、**T0のまま短い専門的判断基準を与える価値**を検証する。Skill追加、権限変更、Model変更、Topology追加、外部OSS取り込みを同時に行わない。「外部Roleが優秀」という結論を前提にしない。

- 評価対象の候補: 不明な前提の記録、最小変更、検証可能な受け入れ条件、Evidence gapを明示する短いRole guidance。
- 外部文書の人格・誇張・案件固有コマンドは使わず、既存Contractに適合する新規の短文を独自に作成する。
- 非採用の可能性: Prompt長や判断負荷、スコープ逸脱が増え、ベースラインより非効率になる。

## 反証可能な仮説と最小実験（**未実行**）

**H1:** 同一T0単一Agentへのbounded specialist guidance付加は、独立検証で測るTask Success/回帰/要件逸脱に正の影響を与えるか、品質を維持し総作業コストを減らす。

**H0/反証:** 品質が変わらずToken・Latencyが増える、scope creep増加、未検証claimの引用、または許可境界の逸脱が観測される。

| Arm | Topology | 変更点 | 固定するもの |
|---|---|---|---|
| A (control) | T0 | 現行Role guidance | Task/AC・Runtime・Model・Effort・Permission・評価コマンド |
| B (treatment) | T0 | 同じRoleに短い専門判断基準を追加 | 同上。Agent人数/Reviewer/Verifierは増やさない |

**Stage 0 (no model run):** 判断基準候補を出典依存しない形で別Artifactに設計し、既存Roleとの重複・Prompt token量・権限関係・独立評価契約・漏洩リスクを査読する。次段へ進む前に予算上限と実施許可を確認する。

**Stage 1 (post-freeze pilot candidate):** EXP-001の凍結Prompt/Fixture/Run artifactを流用・更新せず、別の非本番Fixtureとbaseline snapshotを新規に定義する。2種類のTask（専門的な判断が必要なTask／専門化が不要な単純Task）× 2 Arm × 2反復 = **最大8 Runの探索枠**を仮置き。必要Runs、事前停止基準、許容Regression、minimum practical improvement、実験コスト上限を**最初のRun前に**Operatorと確定する。各Armは同じRepository revision、同一Task/AC、fresh workspace/sessionを用い、実行順をcounterbalanceする。前Armの修正や学習情報を他Armに持ち越さない。実験が成立しなければ`INCONCLUSIVE`とする。

**Measure:** independent/deterministic Task Success、Regression、scope deviation、Human Intervention、total input/output/cached tokens（guidance overhead含む）、wall clock、boundary violation、必要時のhandoff、実際のguidance適用痕跡。Promptが読まれたことは効果の証拠ではない。Costは実測できる範囲だけ記録し、subscriptionの金額を推定しない。

**Evaluation:** Stage 1は探索的Pilotであり、8 Runだけでは一般的な有効性を主張しない。専門知識の意味的効果とPrompt長の効果が区別できない場合は、次の実験でtoken長を合わせた対照Armを追加する（Stage 1の途中でArmを増やさない）。各Arm共通のAC/検証コマンドを使い、可能ならArmを伏せた独立Evaluatorを使用。観測から後出しで閾値を変更しない。Agentの自己報告はGround Truthではない。実行失敗とタスク失敗を区別し、欠測を0にしない。

**Stop / reject:** 独立Judgment不在・Protocolに合わないRunは採用判断へ進めず保留する。frozen artifact変更、Secrets露出、権限逸脱、非独立評価、fresh-state破綻、予算超過、品質の重大な劣化があれば停止。優位性が再現できない場合は`DEFER`または`REJECT`し、Role増加は行わない。

**一般化の制限:** EXP-001はCodex・GPT-6.1 Sol・high・限定3 TaskのPilotで、T0/T1を比較したもの。そこでのT1のToken増加を、本比較A/Bの予測値やAgency Agentsの効果と混同しない。

## Adoption Gate / 追跡

- 本Noteとsource ledgerの記録は**採用ではない**。正式採用は将来の比較Evidence、独立Judgment、既存境界の遵守、canonical artifact+source ledgerの明示更新を要する。
- 次の判断: [Issue #211](https://github.com/s977043/dynamic-agent-topology/issues/211)。既存のpost-freeze研究 [#88](https://github.com/s977043/dynamic-agent-topology/issues/88) / [#93](https://github.com/s977043/dynamic-agent-topology/issues/93) はモデル・compound strategyの別テーマであり、本件の純粋なRole guidance効果と混ぜない。
- PlanGateの `AGENTS.md` / `CLAUDE.md` / `.claude/agents` 変更は今回の対象外。Human-owned承認を侵さない。
