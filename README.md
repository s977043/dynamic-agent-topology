# Dynamic Agent Topology (DAT)

[日本語](README.md) | [English](README_en.md)

> **AIソフトウェア開発のための、適応的かつEvidence-drivenなAgent Topology。**  
> **どのAgent Topologyが、どの条件で、どれだけのコストに対して有効なのか？**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status: v0.1 Foundation](https://img.shields.io/badge/Status-v0.1%20Foundation-orange.svg)](docs/NORTH_STAR.md)

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

v0.1では、まず **Topology SelectionとEscalation** を中心に扱います。  
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

詳しくは [docs/ADOPTION.md](docs/ADOPTION.md) を参照してください。

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
experiments/  実験プロトコル
harness/      将来のExecution / Evaluation Harness
examples/     Brownfield導入例
```

## Evidence Base

DATは既存研究・公式知見をそのまま流用せず、**Source ClaimとDAT側の採用判断を分離**して管理します。

初期Knowledge Baseには、以下を含めています。

- OpenCollab
- TeamBench
- AsynCodeBench
- Anthropic Multi-Agent Research

詳細は [knowledge/sources.yaml](knowledge/sources.yaml) を参照してください。

## 現在の状態

**v0.1 Foundation**

現在は、以下の土台を整備しています。

- North Star / Architecture / Glossary
- Role / Topology / Runtime / Evaluation Schema
- Canonical Topology P0〜T3
- Routing / Escalation Policy
- Brownfield Adoption Protocol
- Runtime Adapter Contract
- Knowledge Base
- Schema Validation CI

Runtime Adapter本体とExecution/Evaluation Harnessは、仕様と評価プロトコルが安定するまで段階的に実装します。

## Guiding Principle

> **Do not assume a topology is better. Test it.**

Topologyは「良さそうだから採用する」のではなく、Evidenceで比較し、必要ならAblationし、採用・棄却・改善を判断します。

## License

MIT
