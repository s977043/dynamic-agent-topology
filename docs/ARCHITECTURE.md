# Architecture

DATは、混同しやすい責務を5つのPlaneに分離します。

```text
Desired Organization
  topology + role contracts + constraints
            │
            ▼
Control Plane
  routing + escalation policy
            │
            ▼
Runtime Mapping
  adapter + capability resolution
            │
            ▼
Observed Execution
  trace + handoffs + violations
            │
            ▼
Evaluation
  evidence + metrics + decision
```

## 分離ルール

- Topology ≠ Routing Policy
- Role ≠ Permission
- Role ≠ Model
- Runtime ≠ Model Provider
- Reviewer ≠ Verifier
- Verifier ≠ Evidence
- Declared Topology ≠ Observed Execution
- Execution Baseline ≠ Agent Topology

## Topology

Agent Topologyは、Agent/RoleのNode、関係を表すEdge、Dependency、構造上のConstraintを定義します。Runtime固有のModel・Command・設定形式は含めません。

## Execution Baseline

P0 Deterministic PipelineはAgent Topologyではありません。Agentを使わない比較対象として、`baselines/` 配下の独立したExecutionBaselineとして定義します。

## Routing / Escalation

RoutingはTopologyを選択し、Escalationは許容する複雑度の上限を定めます。どちらもTopology定義とは別のControl Planeです。

## Runtime Adapter

AdapterはDATの抽象CapabilityとRoleをRuntime固有の設定へ写像します。v0.1ではClaude Code / Codex / Gemini CLI / AntigravityのCapability Manifestを持ち、未確認事項は`unknown`として明示します。

## Execution Trace

実際に何が起きたかを記録し、Declared Topologyとの乖離をAdherenceとして評価できるようにします。

## Evaluation

Task Outcomeだけでなく、Topology Adherence、Boundary Violation、Evidence Quality、Collaboration Costを合わせて評価します。

## Engineering Layer Diagnostics

上記のArchitecture Planeは責務分離のための構造です。障害解析では、これとは別軸の **Prompt / Context / Harness / Loop / Graph / Evaluation** を診断レンズとして使います。Planeを置き換えたり、新しいHarness Planeを追加したりはしません。

診断契約とCrosswalkは [Engineering Layer Diagnostics](ENGINEERING_LAYERS.md) を参照してください。
