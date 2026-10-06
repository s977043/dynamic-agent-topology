# EXP-001 Artifact Capture Guide

この文書は、実Codex Run終了後の結果をDAT Repositoryへ取り込むための**記録ガイド**です。

> この文書はArtifact Schemaや評価意味論のSource of Truthではありません。

正本は次です。

- `schemas/execution-trace.schema.json`
- `schemas/evaluation.schema.json`
- `schemas/pilot-run-meta.schema.json`
- `schemas/pilot-execution-attestation.schema.json`
- `scripts/validate_pilot.py`
- `experiments/EXP-001-t0-vs-t1/pilot/RUNBOOK.md`

内容が矛盾する場合は正本を優先します。Schemaはfield contract、Runbookは実行順序、この文書は実Run後の記録判断を補助する役割です。

## Capture boundary

DATへ保存するのは、実Runから観測・再構成できる**外部化されたEvidence**です。

保存するもの:

- 実行条件とprovenance
- observableなagent action / handoff / verify / evidence event
- deterministic Evidence結果
- patch
- Run outcome / metrics
- 実行時間・token数など、Runtimeから取得できた計測値

保存しないもの:

- chain-of-thought / hidden reasoning
- API key / token / credential
- private environment dump
- unrelated repository/user data
- 推測したtoken数・latency・agent action
- 取得できなかった値を0で埋めた値

## Per-run directory

各Runは既存のArtifact contractに従います。

```text
experiments/EXP-001-t0-vs-t1/runs/pilot-codex/<runId>/
├── run-meta.yaml
├── prompt.md
├── execution-attestation.yaml
├── trace.yaml
├── evaluation.yaml
├── patch.diff
└── evidence.txt
```

`run-meta.yaml` と `prompt.md` はprepare時に生成済みです。prepare時点ではfresh sessionやcross-run feedbackを確定事実として記録しません。実Codex終了後に `execution-attestation.yaml` と結果Artifactを追加します。

## 0. execution-attestation.yaml

実Codex session終了後に、実行者/Runtime側で観測した実行事実をattestします。

**Attestation != Verification.** このArtifactは「実行条件について何が観測・申告されたか」を外部化するもので、fresh sessionやcross-run isolationを独立に証明するGround Truthではありません。validatorはSchema・Pilot条件・他Artifactとの整合を検査しますが、申告内容そのものの真実性を生成しません。

- `sessionId` — 実際のsessionへ割り当てた非秘密opaque ID
- `freshSession` — 実際にfreshだったか
- `crossRunFeedbackUsed` — 他Run情報を使用したか
- `runtime / model / effort` — 実際に使った値
- `startedAt / finishedAt` — timezone付き実測時刻

期待値と異なっていてもPilot値へ書き換えません。実際の値を保存し、validatorがpolicy違反を判定します。

## 1. trace.yaml

`trace.yaml` は**観測された実行イベント**を時系列で記録します。

### metadata

run-matrixと一致する値を使用します。

- `runId`
- `experiment`
- `scenario`
- `condition`
- `blockId`

### executionSubject

conditionに対応する既存Experiment定義を使用します。

- T0: `AgentTopology / T0-single-agent`
- T1: `AgentTopology / T1-worker-verifier`

### runtime / model

実際に使用したRuntime / Model / Effortのみ記録します。

Pilot固定値と異なった場合は値をPilotへ合わせて書き換えず、Runをinvalidとして扱います。

### events

eventは、外部から確認できる出来事だけを記録します。

例:

- start
- action
- handoff
- review
- verify
- evidence
- violation
- finish

`sequence` はRun内で一意かつ単調増加にします。

`details` にhidden reasoningを書きません。必要なのは「何が起きたか」であり、「モデル内部でどう考えたか」ではありません。

### summary

- `agentInvocations`
- `coordinationTransitions`
- `humanInterventions`
- `inputTokens` / `outputTokens` — Runtimeから取得できた場合のみ
- `wallClockMs` — complete Runでは必須。Run開始/終了から実測する

取得できないoptional metricは省略します。**0は「観測値0」の場合だけ使用**します。

`RunEvaluation.efficiency.wallClockMs` は `evaluation.schema.json` で必須です。`ExecutionTrace.summary.wallClockMs` はSchema上optionalですが、このEXP-001記録ガイドではcomplete RunのTrace/Evaluation整合のため記録対象とします。どちらも推測値ではなく実測値を使用します。

## 2. evaluation.yaml

`evaluation.yaml` はRun結果の評価記録です。

### executionContext

traceと同じRuntime / Model / Effortを記録します。

### outcome

- `taskSuccess`
- `regressionDetected`
- `acceptanceCriteriaPassed`
- `acceptanceCriteriaTotal`

deterministic EvidenceとAcceptance Criteriaに基づいて記録します。Agentの自己評価を根拠にtask successをPASSへしません。

### collaboration

- `topologyAdherence`
- `boundaryViolations`
- `handoffFailures`
- `humanInterventions`

T0/T1の実行契約に対する観測結果として記録します。

### evidence

- `requiredGates`
- `passedGates`
- `completeness`
- `verifierFalseAccept`

T1でVerifierがPASSした後にdeterministic EvidenceがFAILした場合、既存契約に従って `verifierFalseAccept: true` とします。

T0など、該当しない場合はSchemaが許す範囲で `null` を使います。意味のないfalse/0へ変換しません。

### efficiency

trace summaryと一致する値を記録します。

- token metrics — 観測できた場合のみ
- `wallClockMs` — complete Runでは必須
- `agentInvocations`
- `coordinationTransitions`

### verdict

既存Schemaの値のみ使用します。

- `pass`
- `fail`
- `inconclusive`

不明確なRunを無理にpass/failへ寄せません。

## 3. patch.diff

Runで行われた実装変更をdiffとして保存します。

- fixture開始状態からRun終了状態までの差分
- empty fileは不可
- credential / unrelated fileを含めない
- 後から「理想的なpatch」へ編集しない

Runが実装変更前に失敗した場合は、空patchを作ってcomplete扱いしません。Failure handlingに従います。

## 4. evidence.txt

実際に実行したdeterministic Evidenceの外部化された結果を保存します。

最低限:

- 実行したcommand
- exit status
- PASS / FAIL
- 必要な範囲のstdout/stderr

保存前にsecretやprivate pathが含まれていないことを確認します。

Evidenceの全文が不要な場合でも、結果を再確認できる情報は残します。

## Capture sequence

1. Codex Runを終了する
2. `execution-attestation.yaml` を実際の実行事実から作成する
3. deterministic Evidenceを実行・記録する
4. patch.diffを保存する
5. trace.yamlを観測事実から作成する
6. evaluation.yamlをEvidenceに基づいて作成する
7. secret / private data / hidden reasoningがないことを確認する
8. single-run validationを実行する

```bash
python scripts/validate_pilot.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml \
  --run-id <runId>
```

PASSしたRunだけ、paired blockの次のRunへ進めます。

## Missing measurements

値を取得できなかった場合:

- optional fieldなら省略する
- required fieldならRunをcomplete扱いしない
- 0や平均値で補完しない
- 後から推定値を「実測」として書かない

Missing measurement自体がPilot frictionのEvidenceです。

## Validation is not measurement

`validate_pilot.py` がPASSすることは、Artifact contractが整合していることを意味します。

それだけで、

- Topologyが有効だった
- T1がT0より優れていた
- 測定値が正確だった
- 実行手順にhidden contaminationがなかった

ことまでは証明しません。

最終判断は18 / 18 Run完了後の集計とレビューで行います。


## Failed / aborted / inconclusive runs

失敗Runを「なかったこと」にしません。

### fail

実Codex Runが完了し、Artifact contractも満たしているが、deterministic EvidenceやAcceptance Criteriaを満たさなかった場合です。

- `evaluation.yaml verdict: fail`
- `taskSuccess: false`
- 実際のEvidenceをそのまま保存
- patchが存在するなら実際のpatchを保存
- single-run validationを通せるArtifactを残す

これは**有効な実測Run**です。成功Runだけを残すことは禁止します。

### inconclusive

Run自体は実行され、Artifactを記録できるが、結果からpass/failを確定できない場合です。

- `evaluation.yaml verdict: inconclusive`
- 不明確な理由を `notes` に簡潔に記録
- 取得できたEvidenceは保存
- 欠測値を推定しない

inconclusiveをpass/failへ丸めません。

### aborted / infrastructure failure

Runtime障害、Operator mistake、session contamination、workspace問題などで、既存Artifact contractを満たせないRunです。

これは**complete empirical runとして数えません**。

- 空の `patch.diff` / `evidence.txt` を作ってvalidatorを通さない
- 不足Artifactを捏造しない
- そのRunを成功/失敗の集計へ入れない
- Issue #15にrunId・停止理由・観測できた範囲を記録する
- paired blockの次Runへ進まない

原因がBlocking defectならFeature Freeze手続きに従います。

原因が単なる外部Runtime/Operator failureでも、同じrunIdを勝手にやり直して「良い方だけ残す」ことはしません。再実行が必要な場合は、#15で扱いを明示し、既存Operator/Freeze contractと整合する方法をレビューしてから進めます。

### Why this matters

失敗Runの除外はsurvivorship biasを作ります。

EXP-001では、

> successful runsだけを比較する

のではなく、

> 事前に固定した18 Runがどうなったか

をEvidenceとして扱います。

Runを除外する場合、その理由も結果の一部です。


## Paired block integrity

T0/T1はpaired comparisonです。

片方のRunがArtifact contractを満たさない場合、もう片方だけを使ってpaired deltaを解釈しません。

- 先行Runがsingle-run validationを通らない → 次Runを開始しない
- 後続Runがaborted → blockはpaired comparison未成立
- 片側だけ成功 → 「T0/T1差」として一般化しない

18 Run完了後の集計でも、paired comparisonが成立しているかをレビューします。


## Privacy and sanitization checklist

Artifactをcommitする前に、次を確認します。

### Do not commit

- API key / OAuth token / cookie / credential
- home directoryやprivate mountを含む不要なabsolute path
- unrelated environment variables
- private repository content
- user/account identifiers
- chain-of-thought / hidden reasoning
- Runtime内部の非公開prompt
- 他RunのArtifact

### Keep when needed for reproducibility

- public command nameと引数
- exit status
- test/build結果
- public Runtime / Model / Effort identifier
- opaque sessionId / workspaceId
- wall-clock / token metrics（Runtimeから取得できた場合）
- patch対象のfixture file

### Redaction rule

Evidenceにsecret/private dataが混じった場合、値だけをredactし、結果の意味は残します。

例:

```text
COMMAND: python -m unittest discover -s tests -v
EXIT: 1
STDERR:
... /home/<redacted>/workspace/tests/test_app.py ...
```

RedactionによってPASS/FAILや再現に必要な情報まで消さないようにします。

Redactionした事実は `evaluation.yaml notes` など既存の自由記述欄で簡潔に明示できます。

## Cross-artifact consistency review

Feature Freeze revision 3では `scripts/validate_pilot.py` 自体が凍結されています。実Run開始後にvalidator semanticsを変更しないため、次のcross-artifact関係はEXP-001中は**レビュー項目として手動確認**します。自動化候補はIssue #57でpost-EXP-001へ延期しています。

- Trace start eventに `sessionId` / `freshSession` / `crossRunFeedbackUsed` がある場合、`execution-attestation.yaml` と一致する
- 単一のtimestamp付きstart / finish eventがある場合、attested `startedAt` / `finishedAt` と一致する
- Trace summaryとRunEvaluation efficiencyの双方に `inputTokens` / `outputTokens` がある場合、一致する
- 不一致を「意味は同じ」として丸めず、Runを受理する前に原因をレビューする

これは新しい測定条件や評価意味論ではありません。既に記録した同一実行事実がArtifact間で矛盾していないことを確認するための整合レビューです。

## Manual review record

Feature Freeze revision 3の間は、上記cross-artifact consistency reviewの自動validator追加を行いません。そのため、各complete RunをRepositoryへ取り込むPRでは、**手動レビューを実施したEvidenceをPR本文またはreview commentへ残します**。

新しいRun ArtifactやSchema fieldは追加しません。次の最小記録で十分です。

```text
Cross-artifact consistency review
- runId: <runId>
- execution-attestation ↔ trace session/freshness/cross-run fields: PASS | N/A | BLOCKED
- attested timestamps ↔ trace start/finish: PASS | N/A | BLOCKED
- trace token summary ↔ evaluation efficiency: PASS | N/A | BLOCKED
- prompt / frozen-condition drift: NONE | BLOCKED
- sensitive-data / hidden-reasoning scan: PASS | BLOCKED
- single-run validation: PASS | FAIL
- reviewer conclusion: ACCEPT | BLOCK
```

`N/A` は該当するoptional observationが存在しない場合だけ使用します。値があるのに一致確認できない場合は `BLOCKED` とし、次のmatrix itemへ進みません。

`ACCEPT` はTopologyやConditionの優劣判断ではありません。**そのRunをEXP-001のcomplete empirical Runとして受理できるか**だけを意味します。

この記録はIssue #57でpost-EXP-001 automationを検討するまでの暫定的なreview Evidenceです。

## Reproducibility checklist

結果Artifactを作成した後、まずsingle-run validation前に次を確認します。validation結果そのものを含むManual review recordは、single-run validation後に完成させます。

- runId / blockId / scenario / conditionがmatrixと一致
- Runtime / Model / EffortがPilot固定値
- prompt hashがrun-metaと一致
- evidence.txtにcommand / exit status / observable resultがある
- patch.diffが実際のRun差分
- optional metricsは実測できた値だけ
- trace/evaluationの共通metricsが一致
- Cross-artifact consistency reviewのうち、validation結果を必要としないArtifact間整合を確認
- secret / private data / hidden reasoningがない
- 他Run結果を混入していない

single-run validationがPASSした後、Manual review recordへvalidation結果を記入し、残りのcross-artifact reviewを完了して `reviewer conclusion: ACCEPT` を確認します。`BLOCK` の場合は次のmatrix itemへ進みません。

Schema validationが通っても、このチェックを省略しません。
