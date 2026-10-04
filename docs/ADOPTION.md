# Brownfield Adoption Protocol

DATは、既存プロジェクトをいきなりMulti-Agent化するための仕組みではありません。

## Adoption Stages

| Stage | Name | 目的 |
|---|---|---|
| A0 | Assess | Repository / CI / Runtime / 既存Agent設定を把握する |
| A1 | Bind | Test / Lint / Buildなど既存Evidenceを接続する |
| A2 | Observe | 現行Workflowを変更せずBaselineを取得する |
| A3 | Recommend | Topology recommendationだけを行う |
| A4 | Canary | 限定TaskでTopology executionを試す |
| A5 | Dynamic | Evidenceに基づく適応を有効化する |

**A5に到達することは成功条件ではありません。** A2 / A3 / 固定T0/T1が最適なProjectもあります。

## Reference Layout

```text
.dat/
├── project.yaml
├── evidence.yaml
├── policy.yaml
├── runtimes.yaml
├── dat.lock.yaml
├── generated/
└── state/
```

### Source of Truth

- `project.yaml`: Project Binding
- `evidence.yaml`: Evidence Profile
- `policy.yaml`: Project Policy
- `runtimes.yaml`: Runtime Binding
- `dat.lock.yaml`: DAT spec/version binding
- `generated/`: Runtime向け生成物。原則Git管理しない
- `state/`: Trace/Evaluationなどのlocal state。原則Git管理しない

## Stageごとの必須Artifact

- A0: `project.yaml`, `runtimes.yaml`, `dat.lock.yaml`
- A1〜A2: 上記 + `evidence.yaml`
- A3: 上記 + `policy.yaml` + Routing Policy
- A4〜A5: 上記 + Escalation Policy

## Policy rule

- A0〜A2ではRouting Policyは必須ではありません
- A3〜A5ではRouting Policyを必須とします
- A4〜A5ではEscalation Policyを必須とします
- Project側の明示的overrideを共通Policyより優先します
- Routing Ruleが一致しない場合はProject Bindingの`defaultTopology`へfallbackします

## Runtime Adapter rule

v0.2.1では**Manual Adapter**を標準とします。

DATは既存の `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` 等を自動上書きしません。`.dat/` がDesired Stateであり、Runtime固有設定との差分は導入者が明示的に管理します。

## Validation

DAT本体のexampleだけでなく、外部リポジトリを次のCLIで検証できます。

```bash
python scripts/validate_project.py --project /path/to/project --dat-root /path/to/dat
```

詳細は [QUICKSTART.md](QUICKSTART.md) を参照してください。


## Validation Boundary

External Project Validatorが保証するのは、DAT ArtifactのSchema・参照・Version・Runtime capability contractの整合です。

**Manual AdapterのRuntime設定が、宣言したRole / Permission / Topologyを実際に守って動くことまでは保証しません。** A4以降では実RuntimeのTrace / Evidenceを取得し、Topology Adherenceとして別途検証してください。

`overrides/` の自動merge semanticsはv0.2.1では未実装です。Project固有差分は各Artifactへ明示的に記述してください。
