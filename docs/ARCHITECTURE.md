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

### R0 の入力と現行の当てはめ方

この節は、[`policies/routing/R0_dynamic.yaml`](../policies/routing/R0_dynamic.yaml) と `skills/dat-select` の現行の挙動を説明するものです。すべての RoutingPolicy に適用する新しい規範ではなく、R0・schema・validator の挙動も変えません（#277）。

R0 の分岐が参照する入力は次の 4 つです。R0 と schema は値の列挙も判定基準も定めていません。下の表は、値の意味の欄も含めて全体が任意の読み取り例であり、定義・閾値ではなく、既存の判定を上書きしません。最終的な読み取りは記録者が行い、分からない入力は「分からない」とします。R0 が参照しない値（例: `complexity: medium`）の意味は、ここでは定めません。

| 入力 | R0 が参照する値 | 読み取り例（意味） | 判定例 |
| --- | --- | --- | --- |
| `complexity` | `low` | Task を解くのに要る作業の込み入り具合が小さい | 例: 1 ファイルの誤字修正、手順の決まった定型の変更 |
| `ambiguity` | `low` | 何をすれば完了かが Task から読み取れる | 例: 完了条件や期待する出力が依頼文に書かれている |
| `risk` | `medium`、`high` | 誤ったときの影響の大きさ | 例: `high` は認可・secret・本番操作・データ削除に関わる変更、`medium` は影響範囲が限られるが誤りが利用者に届きうる変更 |
| `existingEvidence` | `strong` | Task の正しさを十分に確かめられる既存の手段・証拠がある | 例: 対象の変更を検証できる既存のテスト・再現手順・過去の観測がある。証拠が存在するだけでは `strong` と判定しない |

現行の挙動として、次の点を明記します。

- 現行の `dat-select` の手順では、R0 の分岐を上から当てはめ、最初に合った分岐の構成を使います。この順序は R0 と `schemas/routing-policy.schema.json` には書かれておらず、他の RoutingPolicy に一般化するものではありません。
- R0 には既定（fallback）の分岐がありません。どの分岐にも合わないとき、`dat-select` は構成を推測せず選択保留にします。これは Project Binding を扱わない単独の `dat-select` 手順の説明です。Project Binding を使う場合の「Routing Rule が一致しなければ `defaultTopology` へ fallback する」規則は [ADOPTION の Policy rules](ADOPTION.md#policy-rules) にあり、この節はその規則とどちらが優先するかを定めず、変更もしません。
- 分岐 (1) `{complexity: low, ambiguity: low}` は `risk` を参照しません。そのため `risk: high` の Task でも complexity・ambiguity が low なら (1) で T0 になり、(3) `{risk: high}` には届きません。これが意図した設計かどうかは不明です（G-A2、[P0 記録](rfc/DAT_VNEXT_P0_JOURNEYS.md)）。

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
