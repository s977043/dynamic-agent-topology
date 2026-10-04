# Experiment Protocol

DATのExperimentは、Topologyを「良さそうだから採用する」のではなく比較可能な仮説として扱うための契約です。

## 最低限固定するもの

- Task / Scenario
- Runtime
- Model
- Effort
- Fresh workspace
- Evidence commands
- 最低Run数

比較条件間でこれらを揃え、Topology以外の差分をできるだけ減らします。

## train / test / regression

公開fixtureはプロトコル確認用です。本番の研究・評価ではtest setを調整に使わず、可能なら未観測の外部test setを用意してください。

## Run artifacts

各Runは以下を残します。

1. `ExecutionTrace`
2. `RunEvaluation`

Traceは「何が起きたか」、Evaluationは「どう評価したか」を分離します。

## Paired comparison block

同じScenarioの比較条件は `blockId` で束ねます。同一block内ではExperimentのControl設定に従い、Runtime / Model / Effortを一致させます。

これにより、Topology差とRuntime/Model差を混同しにくくします。

## Execution subject

Experiment conditionは `AgentTopology` だけでなく `ExecutionBaseline` も参照できます。これによりP0 vs T0のような比較を同じExperiment Contractで表現できます。

P0のような非Agent baselineでは `topologyAdherence` は `null` とし、0として扱いません。


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
- Reviewer roleを追加・削除する
- Skillを有効化・無効化する
- routing policyを差し替える
- Verifierの旧版と新版を比較する

### Activation before effectiveness

Capabilityが宣言・登録されているだけでは評価しません。candidate側で対象Capabilityが実際に選択・実行されたことをTraceで確認してから、outcome差を解釈します。

> **Usage != Effectiveness.**

「呼ばれた」「Agent数が増えた」「レビューが1段増えた」はactivation evidenceであり、改善Evidenceではありません。

### Decision semantics

paired comparisonの結果は次の3値で扱います。

- `PASS`: 事前定義したacceptanceを満たし、critical regressionがない
- `FAIL`: 事前定義したreject条件に達した
- `INCONCLUSIVE`: 非activation、paired case不足、sample不足、control破れなどで寄与を判定できない

`INCONCLUSIVE` を「効果なし」と同一視しません。また単一の総合Scoreに潰さず、outcome / regression / human intervention / token / latency / boundary violation / adherenceを別々に確認します。

### Re-evaluation triggers

次の変更では、以前の採用判断を永久の事実として扱わず再評価します。

- Modelのmajor update
- Runtime / orchestration semanticsの変更
- Capabilityの責務・prompt・permission・routingのmaterial change
- cost / latency budgetの変更
- 対象Task distributionの変化

強い基盤Modelが、以前は追加Capabilityで補っていた能力を吸収する場合があります。その場合、品質を維持したままcoordination costを減らせるなら、de-escalate / simplifyも成功です。
