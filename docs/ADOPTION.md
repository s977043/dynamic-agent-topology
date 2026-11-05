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

## A0: 任意のWorkflow Brief（業務課題から始める）

Agentの役割や人数を決める前に、導入対象の業務を短く確認します。これは初回相談用の**任意の問い**であり、新しい必須Artifact、承認Gate、Topology推薦規則ではありません。会話や既存Issueに残すだけでも構いません。

1. **Outcome / Bottleneck**: 誰のどの作業が滞り、何が改善すれば成功か。処理件数だけでなく、成果や待ち時間を明確にする。
2. **Task / Delegation**: 定型処理、判断の要る作業、人間が保持する最終判断を分ける。まずAgentを使わないP0やSingle AgentのT0で足りるか確認する。
3. **Capabilities / Trust**: 現在接続されているRuntime、Tool、データ、実効Permissionを確認する。Promptに「使える」と書くだけでToolや権限が生まれるわけではない。秘密情報・外部書き込み・不可逆操作の境界を明示する。
4. **Evidence / Cost**: 成功条件、既存の検査方法、失敗・回帰・人間介入・時間・Tokenなどの比較可能な観測項目を決める。未取得は未知として扱い、効果を推測しない。
5. **Smallest safe test**: 現行Workflowを変更せず取得できる最初のSignalと、停止・差し戻し条件を決める。実測で不足が確認されるまでエージェントやHandoffを増やさない。

例えばPRレビュー待ちが課題なら、最初に既存CIとレビュー待ち時間を観測し（A1〜A2）、成功条件と既存の承認・merge権限、Humanへのエスカレーション条件を整理します。Reviewer Agentを増やすことは解決策の**候補**であり、最初から3〜5体のチームを組む必要はありません。追加する場合は[Complexity Promotion Rule](#complexity-promotion-rule)に従い、品質・安全性と協調コストのEvidenceで判断します。

このWorkflow BriefはDATの仕様そのものではなく、A0の会話を助ける入口です。Role Contract、Handoff、Evaluationの定義は既存の[Architecture](ARCHITECTURE.md)と該当Artifactを参照し、実効PermissionはRuntime-native設定と実行時Evidenceで別途確認します。EXP-001のFeature Freeze中は、ここで得たアイデアを凍結実験のPrompt・条件へ反映しません。

### タスク単位で選定・分担・観測をつなぐ例

上の問いを具体的な作業に使うときは、既存Issueや計画に次のメモを残せます。**任意の記入例**であり、新しいArtifact・必須Gate・Routing入力ではありません。種類・規模・依存関係は作業を理解する材料で、ファイル数やタスク数からAgent数を決める閾値ではありません。

| 確認すること | 記入する内容 |
|---|---|
| 何を解くか | 種類（調査・実装・検証など）、変更範囲と規模、完了条件、失敗時の影響。分からない点は未確定とする |
| 分ける意味があるか | 先行成果物、共有するファイル・契約、独立して受入可能な成果物。分割しない理由や、引継ぎ・統合で増える負担も記す |
| 誰が何を完了するか | 作業単位ごとの編集責任者、入力のrevision、出力、受入検査、依存先。独立レビューが必要なら対象と観点も指定する |
| どの構成を選ぶか | 作業単位ごとの既存Policy入力と根拠、`dat-select`の構成・該当分岐・不明入力。利用可能なRuntimeと権限、全体の上限も確認する |
| 何を観測するか | 品質検査の結果、実際の分担とレビュー、失敗・中断・手戻り、取得できた消費と欠測理由。計画時の見積もりと実測を分ける |

例えば「既存機能の説明を、実装と一致するよう更新する」なら、同じ文書を編集する作業は一人にまとめられます。既存仕様の調査を分けるのは、その結果を独立して確認でき、編集者と調査範囲が重複せず、引継ぎの負担に見合う場合です。調査結果が編集の前提なら、その編集は結果を待ちます。文書が確定した後の独立レビューは、同じrevisionの差分・完了条件・検証結果を渡して行います。調査役・編集役・レビュー役を常に三人配置する例ではありません。

各作業の選定には [dat-select](../skills/dat-select/SKILL.md) を使い、[R0の現行挙動](ARCHITECTURE.md#r0-の入力と現行の当てはめ方)をそのまま適用します。上の文書編集を `complexity: low` / `ambiguity: low` と読み取れた場合は、最初の分岐でT0です。R0はこの分岐でriskを見ないため、high riskでもT0になり得ますが、実行権限や必要な独立検査を省略する許可にはなりません。入力が不明で分岐を決められない場合や、どの分岐にも一致しない場合は、単独の`dat-select`では選択保留です。Project Bindingのfallbackは下の[Policy rules](#policy-rules)の別の文脈であり、ここでは優先順位を新設しません。

分担後も各作業に上限を配り直すだけで全体予算を増やさず、既存の[Escalation Policy](../policies/escalation/E0_default.yaml)と導入先の承認・実行制約を確認します。1つの既存サブスクリプション内・追加課金なしを条件にする場合も、利用経路と利用枠を確認し、枠内だからToken・待ち時間・人の確認負担がゼロとは扱いません。外部モデル・別契約・A2A通信基盤はこの手順の前提ではありません。

計画、実装、PR前のレビューで同じ根拠を使える場合は、対象revision・範囲・観点・独立性が一致する既存結果を参照できます。差分や完了条件が変われば影響する確認を更新します。PlanGate等で作る計画やRiver Review等のレビュー結果を参照する場合も、発見しただけ・読み込んだ・適用した・実行して結果を得た、を区別し、利用不能なPluginを実行済みにしません。これらの利用はDATの自動接続や承認の代行を意味しません。

実行後は [dat-observe](../skills/dat-observe/SKILL.md) で実際のウェーブを記録します。推奨構成をそのまま`topologyEquivalent`に写さず、[判定規則](RUN_OBSERVATION_DESIGN.md#52-topologyequivalent-の判定基準)で実態から決めます。助言と検証を同じレビューで二重計上せず、親子の集計Tokenも重複加算しません。調査・引継ぎ・統合・レビュー・失敗やretryを含む全体の消費を確認し、取得できない値は`unknown`にします。人のactive attentionはwall timeと分け、必要なら既存の[手動計測手順](HUMAN_ATTENTION_PILOT.md)を参照します。このメモの項目をRunObservationの新しいfieldとして追加する必要はありません。

品質未達、共有編集の競合、引継ぎ負担や利用枠の超過があれば、次の作業単位で分割・構成・範囲を見直す候補にします。観察だけから「人数を増やす／減らすと改善する」と結論づけず、構成の優劣は[比較実験](EXPERIMENTS.md)で検証します。現在の構成を保つ判断も含め、未測定の自動最適化を完成済みとは扱いません。

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

人間の負荷を評価するとき、`human_interventions`の回数だけで低コストとは判断しません。同じ介入回数でも、複数Agentへの同時監督、頻繁なcontext switch、判断待ちのfan-outが増える可能性があります。比較可能な範囲ではHumanが担当する判断とEscalation条件を揃え、揃えられない差分はExperiment上のconfounder / operational costとして明示します。

## Runtime Adapter rules

現行の標準は**Manual Adapter**です。

DATは既存の`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`等を自動上書きしません。`.dat/` はDAT側のDesired State / bindingであり、Runtime-native設定との差分は導入者が明示的に管理します。

Manual AdapterでDATが確認できるのは、宣言されたRuntime / Capability / Artifact参照の整合までです。Runtimeが実際にRole / Permission / Topologyを守って動いたかは、実行時Evidenceで別途確認します。

Runtime固有のpermission enforcement、event interception、audit、UI guardrailなどは、必要に応じてManual Adapterと併用する**runtime-native implementation detail**として扱います。DATはそれらを自動適用・保証しません。DAT coreへ取り込む前に、観測されたRuntime gapとExpected Invariantを明示し、native controlやより小さい介入で不足することを確認します。Provider固有機構の存在だけを理由に採用せず、実行時Evidenceで効果と副作用を評価します。

この種の候補は [Engineering Layer Diagnostics](ENGINEERING_LAYERS.md#runtime-specific-guardrail-candidates) から追跡します。Claude Code Modsは現在Research candidateであり、EXP-001 Feature Freeze中のRuntime behaviorには使用しません。

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
