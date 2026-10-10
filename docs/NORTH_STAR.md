# North Star

## Core question

> **Which agent topology works, under what conditions, and at what cost?**

> **Do not assume a topology is better. Test it.**

DATの中心課題は、Agent数やTopologyの複雑さを増やすことではありません。**タスクを十分な品質で解ける最小構成を見つけ、追加の協調コストをEvidenceで正当化すること**です。

DAT**自体をどう育てるか**については、[Practice Evolution](PRACTICE_EVOLUTION.md)でアジャイルの価値観・外部知識の評価・小さな検証・人間の承認境界を整理します。これはTopology実験のControlや本書のNorth Starを変更するものではありません。

## Ten engineering principles

1. **Minimal Team First** — P0またはT0を起点にし、追加coordinationは測定された価値で正当化する。
2. **Dynamic means Select, Escalate, De-escalate, Recompose** — DynamicはAgent数の増加ではなく、状況に応じたTopologyの選択と再構成を意味する。現在の実装・評価は主にSelection / Escalationを扱い、De-escalation / Recompositionは将来の検証対象とする。
3. **Role ≠ Model ≠ Runtime** — 責務、モデル選択、実行環境を独立に扱う。
4. **Role Contract ≠ Permission Enforcement** — Prompt上の責務と、Runtimeが実際に強制できる権限境界を分離する。
5. **Builder ≠ Judge** — 非自明な変更では、作成と独立判断を必要に応じて分離する。
6. **Verifier ≠ Ground Truth** — Verifierの判断を真実そのものとみなさず、利用可能な場合はより強いdeterministic / observable Evidenceを優先する。
7. **Context Isolation by Default** — Contextを必要範囲に限定し、Agent間の情報共有は明示Artifactを優先する。
8. **Explicit Dependency Modeling** — Handoffと依存関係を明示し、後から追跡できるようにする。
9. **Observable Collaboration** — Adherence、Violation、Handoff、Cost、Outcomeを観測可能にする。
10. **Ablation Before Adoption** — RoleやCapabilityは「良さそう」ではなく、限界寄与を比較して標準採用を判断する。

## Non-goals

DATは次を目的としません。

- 汎用Agent Runtimeを新規実装すること
- Prompt libraryを網羅すること
- Model単体の性能ランキングを作ること
- Multi-Agentを常にSingle Agentより優先すること
- Agent自身の自己評価をGround Truthとして扱うこと

## Current implementation boundary

現在のDATは、**仕様・導入契約・Runtime capability mapping・Trace / Evaluation・比較実験基盤**を中心に提供します。

- Canonical Topologyはベストプラクティス集ではなく、比較・検証するための仮説です。
- Runtime Adapterは現時点ではManual Adapterが標準で、Runtime-native設定の自動compile/applyは行いません。
- Dynamic adaptationの全機能を実装済みとは扱いません。
- 実行可能であることと、Topologyが有効であることを別々に検証します。

## Version scopes

### v0.1

Vocabulary、Schema、Baseline Topology、Evidence source、Brownfield adoption stage、Runtime Adapter contractの基礎を定義しました。

### v0.2

再現可能なExperiment定義、train / test / regressionの分離、`ExecutionTrace` / `RunEvaluation` 契約、EXP-001（T0 vs T1）、Artifact validation / summary harnessを追加しました。

### v0.2.1 historical content point (unpublished)

外部RepositoryへのManual Brownfield Adoptionを追加したhistorical content pointです。完全な`.dat/` Reference Layout、Runtime Binding、DAT Lock、External Project Validator、CI integration template、Manual Adapterの保証境界を含みます。

`v0.2.1` は現在の`main`全体を表す公開Releaseではありません。Release境界はRepository rootの`CHANGELOG.md`とimmutable Git tag / GitHub Releaseを優先します。
