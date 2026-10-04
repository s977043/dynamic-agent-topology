# Dynamic Agent Topology (DAT)

[日本語](README.md) | [English](README_en.md)

> **AIソフトウェア開発のための、適応的かつEvidence-drivenなAgent Topology。**  
> **どのAgent Topologyが、どの条件で、どれだけのコストに対して有効なのか？**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status: v0.2.1 Manual adoption-ready](https://img.shields.io/badge/Status-v0.2.1%20Manual%20adoption--ready-green.svg)](docs/NORTH_STAR.md)
[![CI](https://github.com/s977043/dynamic-agent-topology/actions/workflows/spec-lint.yml/badge.svg)](https://github.com/s977043/dynamic-agent-topology/actions/workflows/spec-lint.yml)
[![CodeQL](https://github.com/s977043/dynamic-agent-topology/actions/workflows/codeql.yml/badge.svg)](https://github.com/s977043/dynamic-agent-topology/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/s977043/dynamic-agent-topology/badge)](https://scorecard.dev/viewer/?uri=github.com/s977043/dynamic-agent-topology)

**Dynamic Agent Topology (DAT)** は、AI Agent Teamの構造を設計・選択・評価・改善するための、Provider非依存の仕様と実験基盤です。

DATは、次の原則から始めます。

> **タスクを確実に解ける、最も単純なTopologyを使う。**  
> **追加の協調コストを正当化できるEvidenceがあるときだけ、Topologyを複雑化する。**

## DATが目指すもの

DATは、単に「複数Agentをどう並べるか」を定義するものではありません。

```text
Knowledge & Benchmarks
        ↓
Hypothesis
        ↓
Topology Specification
        ↓
Runtime Mapping
        ↓
Execution
        ↓
Evidence & Trace
        ↓
Evaluation
        ↓
Ablation
        ↓
Adopt / Reject / Evolve
```

Topologyを経験則だけで採用せず、**仮説 → 実行 → 証拠 → 評価 → 改善**のループで検証します。

## DATではないもの

- **固定Topologyのカタログではありません。** Canonical Topologyはベストプラクティスではなく、比較・検証するための仮説とBaselineです。
- **新しいAgent Runtimeではありません。** Claude Code / Codex / Gemini CLI / Antigravityなど、既存Runtime上での利用を想定しています。
- **Multi-Agent至上主義ではありません。** Deterministic PipelineとSingle Agentを第一級のBaselineとして扱います。
- **Agentの自己評価をGround Truthとはみなしません。** 利用可能な場合は、deterministic / observableなEvidenceを優先します。

## Topologyの中核要素

DATではTopologyを単なるPrompt Graphとして扱いません。

1. **Role Contract** — Agentが担う責務と期待される成果物
2. **Permission Boundary** — Prompt上の役割と、実際に許可されたCapabilityを分離
3. **Context Boundary** — AgentごとのContextとArtifactをスコープ
4. **Explicit Dependencies** — Agent間のhandoffや依存関係を明示
5. **Evidence** — deterministic / observable / judgment evidence
6. **Routing & Escalation** — Topologyそのものと、Topology選択ポリシーを分離
7. **Topology Adherence** — 宣言した組織構造と、実際の実行結果の一致度を評価

## Baseline / Canonical Topology

| ID | 構成 | 目的 |
|---|---|---|
| P0 | Deterministic Pipeline | Agentを使わない最小Baseline |
| T0 | Single Agent | 低coordination-costの標準Baseline |
| T1 | Worker → Verifier | 独立Verificationの価値を検証 |
| T2 | Worker → Reviewer → Verifier | 独立Judgmentの価値を検証 |
| T3 | Specialized Team | 高複雑度タスクでの専門化を検証 |

Dynamic RoutingはTopologyではなく、`policies/` 配下のControl Planeとして別に定義します。

## Dynamicとは何か

DATにおけるDynamicは、単にAgent数を増やすことではありません。

```text
Select
→ Observe
→ Escalate / De-escalate
→ Recompose
→ Evaluate
```

現在は、まず **Topology SelectionとEscalation** を中心に扱います。  
将来的には、実行中のDe-escalationやRecompositionまで検証対象にします。

## 既存プロジェクトへの導入

DAT導入は、Multi-Agent化と同義ではありません。

```text
A0 Assess
→ A1 Bind Evidence
→ A2 Observe
→ A3 Recommend
→ A4 Canary
→ A5 Dynamic
```

| Stage | 内容 |
|---|---|
| A0 Assess | Repository / CI / Runtime / 既存Agent設定を確認 |
| A1 Bind | Test / Lint / Buildなど既存Evidenceを接続 |
| A2 Observe | 現行Workflowを変更せずBaselineを取得 |
| A3 Recommend | Topologyの推奨だけを行う |
| A4 Canary | 限定したTaskでTopologyを実行 |
| A5 Dynamic | Evidenceに基づく動的なTopology適応 |

**A5に到達すること自体が成功ではありません。**  
A2 / A3 / 固定T0・T1が最適なProjectも想定しています。

まず試す場合は [Quick Start](docs/QUICKSTART.md)、設計詳細は [Brownfield Adoption Protocol](docs/ADOPTION.md) を参照してください。

失敗の切り分けと複雑化判断には [Engineering Layer Diagnostics](docs/ENGINEERING_LAYERS.md) を使います。

## 対象Runtime

DATはRuntime / Model / Roleを分離して扱います。

初期対象：

- Claude Code
- Codex
- Gemini CLI
- Antigravity

Runtime固有の差分は `adapters/` に閉じ込め、Canonical Topologyを特定Runtimeの設定形式に依存させない方針です。

## リポジトリ構成

```text
docs/         North Star / Architecture / Glossary / Metrics / Adoption
knowledge/    研究・公式知見と採用した設計原則
schemas/      DATのMachine-readableな仕様
roles/        Canonical Role Contract
baselines/    Agentを使わないExecution Baseline
topologies/   Canonical Agent Topology
policies/     Routing / Escalation Policy
adapters/     Runtime Adapter
experiments/  実験定義・Scenario Set
fixtures/     再現可能な小規模Scenario fixture
harness/      Experiment Artifactの検証・集計Harness
examples/     Brownfield導入例
```

## Dogfooding

v0.2.1 Manual adoption kitは、外部Repository `s977043/notionnext-blog` にA2 Observe / Codex / T0固定で導入し、consumer PRとmerge後mainのDAT validationが成功しています。

詳細: [Dogfooding Evidence](docs/DOGFOODING.md)

## 最初の実験

[EXP-001: T0 vs T1](experiments/EXP-001-t0-vs-t1/README.md) では、Single Agentに独立Verifierを追加する価値を比較します。

同一Task / Runtime / Model / EffortでT0とT1を繰り返し実行し、Task SuccessだけでなくRegression、Human Intervention、Token、Latency、Topology Adherence、Verifier False Acceptを合わせて評価します。

Topology全体だけでなく、Role / Skill / Verifierなど**内部Capabilityの限界寄与**もpaired ablationで評価します。「呼ばれた」は効果の証拠ではありません。詳細は [Experiment Protocol — Capability-level ablation](docs/EXPERIMENTS.md#capability-level-ablation) と [Metrics — Capability contribution](docs/METRICS.md#capability-contributionderived-comparison) を参照してください。

## Current Focus

現在の最優先は **EXP-001の一次データ取得**です。

- Execution tracking: Issue #15
- Empirical runs: **live progress is tracked in Issue #15**
- Feature Freeze: **ACTIVE**
- `DECISION.md`: **NOT RUN**
- 新Topology / Routing拡張 / Research・Production Profile設計: **EXP-001完了まで延期**

Freeze policy: [EXP-001 Feature Freeze](experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md)

Execution handoff: [EXP-001 Execution Handoff](docs/EXP-001_EXECUTION.md)

Artifact capture: [EXP-001 Artifact Capture Guide](docs/EXP-001_ARTIFACT_CAPTURE.md)

DATはいま仕様追加フェーズではなく、**Evidence acquisitionフェーズ**にあります。

## Evidence Base

DATは既存研究・公式知見をそのまま流用せず、**Source ClaimとDAT側の採用判断を分離**して管理します。

初期Knowledge Baseには、以下を含めています。

- OpenCollab
- TeamBench
- AsynCodeBench
- Anthropic Multi-Agent Research

詳細は [knowledge/sources.yaml](knowledge/sources.yaml) を参照してください。

## 現在の状態

**v0.2.1 Manual adoption-ready**

現在は、以下の土台を整備しています。

- North Star / Architecture / Glossary
- Role / Topology / Runtime / Evaluation Schema
- P0 Execution Baseline / Canonical Topology T0〜T3
- Routing / Escalation Policy
- Brownfield Adoption Protocol
- External Project Validator
- Runtime Binding / DAT Lock
- GitHub Actions integration template
- Runtime Adapter Contract
- Knowledge Base
- Schema / Semantic Validation CI
- EXP-001: T0 vs T1
- ExecutionTrace / RunEvaluation Schema
- Run Evaluationの条件別集計

別リポジトリへの手動導入と検証は可能です。Runtime Adapterの自動compile/applyとAgent実行オーケストレーションはまだ実装しません。

## Guiding Principle

> **Do not assume a topology is better. Test it.**

Topologyは「良さそうだから採用する」のではなく、Evidenceで比較し、必要ならAblationし、採用・棄却・改善を判断します。

## Contributing / Security

コントリビューションは [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。Bug / Proposal / Research Proposal / Usage Question は用途別のIssue Formを利用してください。利用・導入相談は [SUPPORT.md](SUPPORT.md)、コミュニティ基準は [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) を参照してください。

セキュリティ上の問題は公開Issueへ詳細を書かず、[SECURITY.md](SECURITY.md) の手順で報告してください。

## License

MIT
