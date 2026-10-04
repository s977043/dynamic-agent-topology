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
