# Architecture

DATは、Topologyそのものと、Topologyを選ぶPolicy、Runtime固有設定、実行時の観測、評価結果を混同しないために、責務を5つのPlaneへ分離します。

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

## Responsibility boundaries

- **Desired Organization** — どのRole/Nodeを置き、どの関係・依存・制約を持たせるかを宣言する。
- **Control Plane** — Task条件やPolicyに基づいてTopologyを選択し、必要なら許容複雑度を制御する。
- **Runtime Mapping** — DATの抽象Role / CapabilityをRuntime-nativeな設定へ対応付ける。
- **Observed Execution** — 実際に起きたAction / Handoff / Review / Verification / Violationを記録する。
- **Evaluation** — Outcome、Evidence、Adherence、Violation、Costを使ってRunを評価する。

## Separation rules

- Topology ≠ Routing Policy
- Role ≠ Permission
- Role ≠ Model
- Runtime ≠ Model Provider
- Reviewer ≠ Verifier
- Verifier ≠ Evidence
- Attestation ≠ Verification
- Declared Topology ≠ Observed Execution
- Execution Baseline ≠ Agent Topology

## Topology

`AgentTopology` は、Agent/RoleのNode、関係を表すEdge、Dependency、構造上のConstraintを定義します。Runtime固有のModel、Command、設定ファイル形式はTopologyへ持ち込みません。

Canonical Topologyは「推奨構成」ではなく比較対象です。採用判断は、対象TaskとRuntimeで取得したEvidenceに基づいて行います。

## Execution Baseline

`P0 Deterministic Pipeline` はAgent Topologyではありません。Agentを使わない比較条件として、`baselines/` 配下の独立した `ExecutionBaseline` で定義します。

この分離により、P0 vs T0のような比較で「Agentを使うこと自体」の限界価値を評価できます。

## Routing and escalation

RoutingはTask条件に基づいてTopologyを選択します。Escalationは許容するTopology / Agent数 / coordination transitionなどの上限を制御します。

どちらもTopology定義とは別のControl Planeであり、Topologyの構造そのものへPolicy判断を埋め込みません。

## Runtime Adapter

Runtime AdapterはDATの抽象CapabilityとRoleを、Claude Code / Codex / Gemini CLI / AntigravityなどRuntime固有のCapabilityへ写像します。

現行のManual Adapterでは、DATはRuntime BindingとCapability整合を検証しますが、`AGENTS.md` / `CLAUDE.md` / `GEMINI.md` 等を自動生成・上書きしません。未確認Capabilityは`unknown`として扱い、存在を推測しません。

### Skillと配布パッケージ

`skills/`（`dat-select`・`dat-observe`）は、Claude Code・Codex で共通の `SKILL.md` 形式で書いた利用手順です。特定Runtimeの機能に依存する値の取り方は書かず、`adapters/<runtime>/` を参照します。`.claude-plugin/` と `.codex-plugin/` はこれらのSkillを各Runtimeへ届けるための配布パッケージで、Runtime Mappingではありません。どちらも構成の定義・判定規則を持たず、`topologies/`・`policies/`・`schemas/` を正本として参照します。

## Observed execution

`ExecutionTrace` は「宣言上どう動くはずだったか」ではなく、外部から観測できた実行イベントを記録します。

Declared TopologyとObserved Executionの差は `topologyAdherence` やBoundary Violationとして評価します。実行条件の自己申告やOperator観測を保存するAttestationは、独立Verificationと同義ではありません。

## Evaluation

`RunEvaluation` はTask Outcomeだけでなく、Topology Adherence、Boundary Violation、Evidence completeness、Verifier false accept、Human Intervention、Token / Latencyなどを組み合わせて評価します。

単一の総合Scoreへ過度に集約せず、品質・安全性・協調コスト・実行コストのトレードオフを残します。

## Engineering Layer Diagnostics

上記のArchitecture Planeは責務分離のための構造です。障害解析では、これとは別軸の **Prompt / Context / Harness / Loop / Graph / Evaluation** を診断レンズとして使います。

Engineering LayerはArchitecture Planeを置き換えるものではなく、成熟度順でもありません。失敗時に「どの最小Work Unitを直すべきか」を特定するための補助軸です。

診断契約とCrosswalkは [Engineering Layer Diagnostics](ENGINEERING_LAYERS.md) を参照してください。
## Source of truth

- 構造契約: `schemas/`
- Canonical Role: `roles/`
- Canonical Topology: `topologies/`
- Routing / Escalation Policy: `policies/`
- Runtime capability: `adapters/*/capabilities.yaml`
- Experiment contract: `experiments/`

この文書は責務境界の説明です。Machine-readable Artifactと矛盾した場合は、対象ArtifactとSchemaを優先します。
