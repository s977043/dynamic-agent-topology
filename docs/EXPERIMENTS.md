# Experiment Protocol

DATのExperimentは、TopologyやCapabilityを「良さそうだから採用する」のではなく、**比較可能な仮説**として扱うための契約です。

## Control what changes

比較条件間では、評価対象以外の差分をできるだけ減らします。最低限、次を固定・記録します。

- Task / Scenario
- Runtime
- Model
- Effort
- Fresh workspace policy
- Evidence commands
- Run count / repetition policy

Experiment固有の固定条件は、各`experiment.yaml`やPilot ArtifactをSource of Truthとします。

## Train / test / regression

公開fixtureはProtocolやHarnessの確認にも使われます。本番の研究・評価では、test setを調整用Feedbackとして使わず、可能なら未観測の外部test setを用意してください。

- **train** — Prompt / Workflow / Capability改善に利用できる開発用Scenario
- **test** — 採用判断のため、調整から分離して評価するScenario
- **regression** — 既存能力や安全性が悪化していないことを確認するScenario

Split名だけで独立性が保証されるわけではありません。実際の運用でcross-run feedbackやcontaminationを防ぐ必要があります。また、個別ExperimentがFeature Freezeやcross-run feedback禁止を定めている場合は、`train` splitであってもそのRun結果を途中改善へ使用しません。

## Run artifacts

各Runは原則として次を分離して残します。

1. `ExecutionTrace` — 何が起きたか
2. `RunEvaluation` — 観測結果をどう評価したか

TraceとEvaluationを分離することで、後から評価ロジックを確認しやすくし、Observed ExecutionとJudgmentを混同しにくくします。

## Paired comparison block

同じScenarioの比較条件は`blockId`で束ねます。同一block内ではExperimentのControl設定に従い、Runtime / Model / Effortなどを一致させます。

```text
same scenario + same controls
  ├─ baseline condition
  └─ candidate condition
       ↓
paired comparison
```

これにより、Topology差とRuntime / Model差を混同しにくくします。順序効果が問題になる場合はcounterbalancingも明示します。

### Human-facing concurrency

TopologyやCapabilityの変更が、Humanへ同時に提示されるAgent状態、承認要求、レビュー要求、例外処理の数を変える場合、その差を無視しません。

- Humanが担当する判断の種類とEscalation条件は、比較可能な範囲で既存のExperiment / Runbook条件に従って揃えます。これは新しい必須ArtifactやSchema fieldを意味しません。
- candidateの構造上、human-facing concurrency自体が変化する場合は、その差を「単なる実装詳細」ではなくcoordination / operational costとして記録します。
- `human_interventions`の回数だけから認知負荷やcontext-switch costを推定しません。
- 観測方法が未定義な負荷を0として扱わず、必要ならconfounder / limitationとして残します。

この原則は、新規Experiment設計またはFreeze前のcontrol定義で使います。現行Experiment Schemaへ新しいfieldを追加することを意味せず、既にFeature Freeze中のExperimentへ新しい必須controlを遡及適用しません。

EXP-001 Feature Freeze中は、この観点を理由に既存Control、必須Metric、RunEvaluation field、受理条件を変更しません。human-facing concurrencyの差が観測された場合は、既存contract違反でない限りRunを後付けでinvalid化せず、confounder / limitation / operational costとして記録します。正式な測定契約が必要なら、実測上の不足をEvidenceとしてpost-freezeで別途提案します。

## Execution subject

Experiment conditionは`AgentTopology`だけでなく`ExecutionBaseline`も参照できます。これによりP0 vs T0のような比較を同じExperiment Contractで表現できます。

P0のような非Agent baselineでは`topologyAdherence`は`null`とし、0として扱いません。N/Aと「準拠度0」は意味が異なります。

## Capability-level ablation

Topology全体の比較だけでは、「追加したRole / Agent / Skill / Verifierが本当に寄与したか」は分かりません。DATではTopology内部のCapabilityも、必要に応じてpaired ablationで評価します。

```text
same Scenario / Runtime / Model / Effort / workspace policy
  ├─ baseline: capability absent or previous version
  └─ candidate: capability present or changed
       ↓
paired delta
```

### Control rule

比較条件間で変えてよい主因は、評価対象のCapabilityだけです。Runtime / Model / Effort / Scenario / Evidence command / budget policyを同一block内で固定し、別の変更を混ぜません。

対象例:

- WorkerにVerifierを追加する
- Reviewer Roleを追加・削除する
- Skillを有効化・無効化する
- Routing Policyを差し替える
- Verifierの旧版と新版を比較する

### 複数の変更要因を分解する

新しいRole / Agent / Model / Permission Boundary / Routing ruleを同時に必要とするように見えるCandidateでも、より小さいablationが可能なら、それらを1つの不可分な介入として扱いません。

可能な場合は、原因候補を段階的に分けて比較します。例:

```text
A: 既存Capability
B: 既存Capability + 新しいobjective / instruction
C: Bを独立Role / Agent化し、model / effort / input Evidenceを可能な限り一致
D: C + より強いmodel / capability binding
```

この分解により、次を区別しやすくします。

- objective / Promptの効果
- 独立Role / Context Boundaryの効果とcoordination cost
- model / Runtime Mappingの効果

より小さいArmで改善を説明できるなら、別のInvariantが複雑な構造を要求しない限り、小さい介入を優先します。

実際のArmはCandidateに依存します。処置をきれいに分離できない場合、このTemplateへ無理に合わせず、confoundとして明示します。

これは新規またはpost-freeze Experiment向けの設計原則です。active Feature Freeze、既存Experiment control、RunEvaluation field、acceptance criterionを遡及的に変更しません。

### Activation before effectiveness

Capabilityが宣言・登録されているだけでは評価しません。candidate側で対象Capabilityが実際に選択・実行されたことをTraceで確認してから、Outcome差を解釈します。

> **Usage != Effectiveness.**

「呼ばれた」「Agent数が増えた」「Reviewが1段増えた」はactivation evidenceであり、改善Evidenceではありません。

### Decision semantics

paired comparisonの結果は次の3値で扱います。

- `PASS`: 事前定義したacceptanceを満たし、critical regressionがない
- `FAIL`: 事前定義したreject条件に達した
- `INCONCLUSIVE`: 非activation、paired case不足、sample不足、control破れなどで寄与を判定できない

`INCONCLUSIVE`を「効果なし」と同一視しません。また単一の総合Scoreに潰さず、Outcome / Regression / Human Intervention / Token / Latency / Boundary Violation / Adherenceを別々に確認します。

## Missing, aborted, and small samples

- 取得できないMetricを0で補完しません。
- aborted / infrastructure failureを成功・失敗Runへ無理に変換しません。
- paired conditionの片側が成立しない場合、そのblockだけからpaired deltaを解釈しません。
- 少数RunでProtocolが成立したことと、広いTask分布へ一般化できることは別です。

具体的な除外・再実行ルールは各Experiment / PilotのRunbookを優先します。

## Re-evaluation triggers

次の変更では、以前の採用判断を永久の事実として扱わず再評価します。

- Modelのmajor update
- Runtime / orchestration semanticsの変更
- Capabilityの責務・Prompt・Permission・Routingのmaterial change
- Cost / Latency budgetの変更
- 対象Task distributionの変化

強い基盤Modelが、以前は追加Capabilityで補っていた能力を吸収する場合があります。その場合、品質を維持したままcoordination costを減らせるなら、de-escalate / simplifyも成功です。

## Source of truth

この文書はExperiment設計原則の説明です。個別実験のQuestion、Hypothesis、Control、Decision Policy、Run順序は、対象`experiments/`配下のMachine-readable ArtifactとRunbookを優先します。
