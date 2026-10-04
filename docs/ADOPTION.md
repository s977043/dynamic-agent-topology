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

## Complexity Promotion Rule

DATでは、Agent数、Topology edge、Routing rule、Loop、state、retry、branch/joinなどの協調機構を、便利そうという理由だけで追加しません。

より複雑な仕組みへ進む前に、少なくとも次を確認します。

1. **Need is evidenced** — 同種の失敗や制約が複数Run / Taskで再現している、またはSecurity / Permission / data integrityなどのhigh-severity invariant breachが観測されている。重大な境界違反を再発待ちにしない。
2. **Smaller intervention is insufficient** — Prompt、Context、Harnessなど、より小さいWork Unitへの修正では十分に解決できない。Engineering Layer自体に成熟度順や上下関係があるとはみなさない。
3. **Benefit justifies coordination cost** — Task success、安全性、品質、Human Interventionなどの改善が、Token、Latency、運用負荷、handoff failureなどの追加コストを正当化できる見込みがある。Security / correctness上のcritical risk低減は単純なcost増より優先される場合がある。
4. **Workflow is stable enough to encode** — まだ頻繁に変化している手順を早期に固定化しない。重大リスクへの暫定guardrailは例外として導入できるが、恒久設計とは分離する。
5. **The change is falsifiable** — 何を測れば採用・棄却・単純化できるかを事前に定義できる。

条件を満たさない場合の既定動作は、**現状維持または単純化**です。複雑化しないことも正しい設計判断として扱います。

診断には [Engineering Layer Diagnostics](ENGINEERING_LAYERS.md) を使い、最小のBroken Work UnitとExpected Invariantを特定してからPromotionを検討します。

Promotion後も、Evidenceが追加コストを正当化しない場合はde-escalate / simplifyします。A5やMulti-Agent化は成熟度のゴールではありません。

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
