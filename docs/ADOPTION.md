# Brownfield Adoption Protocol

DATは、既存プロジェクトをいきなりMulti-Agent化するための仕組みではありません。既存のCI・Agent設定・開発フローを壊さず、**観測可能性と比較可能性を先に作る**ことを基本とします。

## Adoption stages

| Stage | Name | 目的 | 典型的な変更 |
|---|---|---|---|
| A0 | Assess | Repository / CI / Runtime / 既存Agent設定を把握する | DAT bindingの最小宣言 |
| A1 | Bind | Test / Lint / Buildなど既存Evidenceを接続する | Evidence Profile追加 |
| A2 | Observe | 現行Workflowを変更せずBaselineを取得する | 観測・検証のみ |
| A3 | Recommend | Topology recommendationだけを行う | Routing Policy追加 |
| A4 | Canary | 限定TaskでTopology executionを試す | Escalation Policyと実Runtime Trace |
| A5 | Dynamic | Evidenceに基づく適応を有効化する | Dynamic routing / adaptation |

**A5に到達することは成功条件ではありません。** A2 / A3 / 固定T0/T1が最適なProjectもあります。

## Reference layout

```text
.dat/
├── project.yaml
├── evidence.yaml      # A1以降
├── policy.yaml        # A3以降は必須。A0〜A2でも明示stage用に置ける
├── runtimes.yaml
├── dat.lock.yaml
├── generated/
└── state/
```

### Source of truth

- `project.yaml`: Project Binding
- `evidence.yaml`: Evidence Profile
- `policy.yaml`: Project Policy
- `runtimes.yaml`: Runtime Binding
- `dat.lock.yaml`: DAT spec/version/source/revision binding
- `generated/`: Runtime向け生成物。現行Manual Adapterでは原則Git管理しない
- `state/`: Trace/Evaluationなどのlocal state。原則Git管理しない

## Required artifacts by stage

| Stage | 必須Artifact |
|---|---|
| A0 | `project.yaml`, `runtimes.yaml`, `dat.lock.yaml` |
| A1–A2 | A0 + `evidence.yaml` |
| A3 | A1–A2 + `policy.yaml` + Routing Policy |
| A4–A5 | A3 + Escalation Policy |

`policy.yaml` をA0〜A2で置くこともできます。その場合、`spec.rolloutStage` が明示的なstageとして扱われます。

## Policy rules

- A0〜A2ではRouting Policyは必須ではありません。
- A3〜A5ではRouting Policyを必須とします。
- A4〜A5ではEscalation Policyを必須とします。
- Schemaで明示的に許可されるProject固有設定は、共有DefaultよりProject側を優先します。`overrides/` ディレクトリの自動mergeとは別概念です。
- Routing Ruleが一致しない場合はProject Bindingの`defaultTopology`へfallbackします。

## Complexity Promotion Rule

DATでは、Agent数、Topology edge、Routing rule、Loop、state、retry、branch/joinなどの協調機構を、便利そうという理由だけで追加しません。

より複雑な仕組みへ進む前に、少なくとも次を確認します。

1. **Need is evidenced** — 同種の失敗や制約が複数Run / Taskで再現している、またはSecurity / Permission / data integrityなどのhigh-severity invariant breachが観測されている。重大な境界違反を再発待ちにしない。
2. **Smaller intervention is insufficient** — Prompt、Context、Harnessなど、より小さいWork Unitへの修正では十分に解決できない。Engineering Layer自体に成熟度順や上下関係があるとはみなさない。
3. **Benefit justifies coordination cost** — Task success、安全性、品質、Human Interventionなどの改善が、Token、Latency、運用負荷、handoff failureなどの追加コストを正当化できる見込みがある。Agent数や並列度を増やすことで、人間が同時に監督・判断する対象や割り込みが増える場合、そのhuman-facing fan-outもcoordination costとして扱う。Security / correctness上のcritical risk低減は単純なcost増より優先される場合がある。
4. **Workflow is stable enough to encode** — まだ頻繁に変化している手順を早期に固定化しない。重大リスクへの暫定guardrailは例外として導入できるが、恒久設計とは分離する。
5. **The change is falsifiable** — 何を測れば採用・棄却・単純化できるかを事前に定義できる。

条件を満たさない場合の既定動作は、**現状維持または単純化**です。複雑化しないことも正しい設計判断として扱います。

診断には [Engineering Layer Diagnostics](ENGINEERING_LAYERS.md) を使い、最小のBroken Work UnitとExpected Invariantを特定してからPromotionを検討します。

Promotion後も、Evidenceが追加コストを正当化しない場合はde-escalate / simplifyします。A5やMulti-Agent化は成熟度のゴールではありません。

人間の負荷を評価するとき、`human_interventions`の回数だけで低コストとは判断しません。同じ介入回数でも、複数Agentへの同時監督、頻繁なcontext switch、判断待ちのfan-outが増える可能性があります。比較可能な範囲ではHuman supervision contractを固定し、固定できない差分はExperiment上のconfounder / operational costとして明示します。

## Runtime Adapter rules

現行の標準は**Manual Adapter**です。

DATは既存の`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`等を自動上書きしません。`.dat/` はDAT側のDesired State / bindingであり、Runtime-native設定との差分は導入者が明示的に管理します。

Manual AdapterでDATが確認できるのは、宣言されたRuntime / Capability / Artifact参照の整合までです。Runtimeが実際にRole / Permission / Topologyを守って動いたかは、実行時Evidenceで別途確認します。

## Validation

外部Repositoryは次のCLIで検証できます。

```bash
python scripts/validate_project.py --project /path/to/project --dat-root /path/to/dat
```

CIでは再現性のため`--require-pinned`を推奨します。

```bash
python scripts/validate_project.py \
  --project /path/to/project \
  --dat-root /path/to/dat \
  --require-pinned
```

詳細な導入手順は [QUICKSTART.md](QUICKSTART.md) を参照してください。

## Validation boundary

External Project Validatorが保証するのは、DAT ArtifactのSchema、参照、Version、Runtime capability contractなど**静的に検査可能な整合性**です。

次は保証しません。

- Manual AdapterのRuntime設定が宣言Role / Permission / Topologyを実際に強制すること
- Evidence commandそのものが安全・正しいこと
- 選択したTopologyがTaskに対して有効であること
- Runtime実行時にcross-run contaminationや未観測の逸脱がないこと

A4以降では実RuntimeのTrace / Evidenceを取得し、Topology AdherenceやBoundary Violationとして別途検証してください。

`overrides/` の自動merge semanticsは現時点では未実装です。Project固有差分は各Artifactへ明示的に記述してください。
