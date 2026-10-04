# Glossary

DATで意味を固定して使う主要用語をまとめます。実装上の識別子は英語表記を維持し、説明は日本語で記述します。

## Organization and execution

| Term | Definition |
|---|---|
| **Agent** | Runtime上で実行されるAI participant。Role、Model、Runtimeそのものとは区別する。 |
| **Role** | Model / Runtimeから独立した責務契約。何を判断し、何を出力し、何をしてはいけないかを表す。 |
| **Topology** | Role/Node、関係、依存、構造上のConstraintからなる宣言上の組織構造。 |
| **Execution Baseline** | Agent Topologyではない比較対象。例: P0 Deterministic Pipeline。 |
| **Runtime** | Claude Code、Codex、Gemini CLI、Antigravityなど、Agent実行を担う環境。 |
| **Model** | Runtimeが利用する推論モデル。RoleやRuntimeとは独立に扱う。 |
| **Adapter** | DATの抽象Role / CapabilityをRuntime-nativeな構成へ対応付ける層。 |
| **Manual Adapter** | DATがbindingを検証する一方、Runtime-native設定を自動生成・上書きしない統合方式。 |

## Control plane

| Term | Definition |
|---|---|
| **Routing Policy** | Task条件から利用するTopologyを選択するRule。 |
| **Escalation / De-escalation** | より複雑 / より単純なTopologyへ移行すること。 |
| **Recomposition** | 実行条件に応じてRole/構造の組み合わせを再構成すること。 |
| **Capability** | Runtime、Role、Skill、Verifierなどが提供する個別能力。存在・利用・効果を分けて評価する。 |
| **Activation** | 対象Capabilityが実際のRunで選択・実行されたこと。ActivationはEffectivenessの証拠ではない。 |

## Evidence and evaluation

| Term | Definition |
|---|---|
| **Evidence** | 実行や結果を判断するために外部化された観測情報。deterministic / observable / judgment由来を区別して扱う。 |
| **Verifier** | Evidenceを用いて独立Verificationを担うRole。Verifier自身の判断はGround Truthではない。 |
| **Reviewer** | 仕様・設計・差分などを独立に評価するRole。Verifierとは責務を分離できる。 |
| **Ground Truth** | 対象判断に対して利用可能な、より強く外部検証可能な基準。AgentやVerifierの自己申告を自動的にGround Truthとはみなさない。 |
| **ExecutionTrace** | 観測されたAction / Handoff / Review / Verification / Evidence eventなどを時系列で記録するArtifact。 |
| **RunEvaluation** | 1 RunのOutcome、Collaboration、Evidence、Efficiency、Verdictを記録するArtifact。 |
| **Attestation** | 実行条件について観測・申告された事実を外部化するArtifact。独立VerificationやGround Truthとは異なる。 |
| **Adherence** | Observed ExecutionがDeclared Topologyへどの程度沿っていたか。 |
| **Ablation** | Role / Edge / Capabilityなどを除去・差し替えし、限界寄与を比較する方法。 |

## Adoption

| Term | Definition |
|---|---|
| **Project Binding** | `.dat/project.yaml` に置くProject固有のTopology / Runtime binding。 |
| **Project Policy** | `.dat/policy.yaml` に置くrollout stage、Routing / Escalation参照などのProject固有Policy。 |
| **Evidence Profile** | `.dat/evidence.yaml` に置く既存Test / Lint / Build等のEvidence gate宣言。 |
| **Runtime Binding** | `.dat/runtimes.yaml` に置くDAT Runtime名と既存Runtime設定ファイルの対応。 |
| **DAT Lock** | `.dat/dat.lock.yaml` に置くDAT version/source/revision binding。導入先がどのDAT契約へ依存するかを明示する。 |

## Experiment

| Term | Definition |
|---|---|
| **Paired comparison** | 同じScenarioとControl条件でbaseline/candidateを対にして比較する方法。 |
| **Block** | 同じScenarioの比較条件を束ねる単位。DATでは`blockId`で識別する。 |
| **Inconclusive** | 非activation、欠測、control破れ、paired case不足などにより、有効/無効を確定できない状態。FAILや「効果なし」と同義ではない。 |
