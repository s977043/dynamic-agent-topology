# DAT vNext — P0 Baseline / Contract Inventory

- Status: **PARTIAL P0 / STATIC INSPECTION ONLY**。実際の利用者作業時間・有料モデル・機能優位性は **NOT MEASURED**。
- Parent: [#268](https://github.com/s977043/dynamic-agent-topology/issues/268)
- Observed snapshot: `main` `4475b3004ecd07ae5da313121543067119a59479` (2026-10-29 00:28:47Z)
- Published distribution: [v0.4.1](https://github.com/s977043/dynamic-agent-topology/releases/tag/v0.4.1) (2026-10-29)
- Companion: [RFC](DAT_VNEXT_RFC.md) / [Independent review protocol](DAT_VNEXT_REVIEW_RUNBOOK.md)

## 1. Evidence confidence and source discipline

凡例：
- **STATIC VERIFIED** = 指定SHAのソースコード・公開メタデータの確認。実行成功や品質を意味しない。
- **REPORTED** = リポジトリ内の既存実験レポート／検証記録の記載。今回独立再実行した結果ではない。
- **NOT MEASURED** = 実測のデータなし。数値を推定で埋めない。
- **PROPOSED** = 調査すべき仮説であり採用済み判断ではない。

| Dimension | Current evidence | Status | Source |
| --- | --- | --- | --- |
| Purpose | Provider-agnosticなAgent Topology仕様・Experiment・Evaluation。Agent Runtimeではない | STATIC VERIFIED | [North Star](../NORTH_STAR.md), [Architecture](../ARCHITECTURE.md) |
| UX — selection | `dat-select`がRisk/Complexity/Evidence等のPolicy入力を評価。未確定で選択保留、実構成は変更しない | STATIC VERIFIED | [Skill](../../skills/dat-select/SKILL.md), [routing](../../policies/routing/R0_dynamic.yaml) |
| UX — observation | `dat-observe`がYAML作成、validator、Git外保存、集計を案内 | STATIC VERIFIED | [Skill](../../skills/dat-observe/SKILL.md), [CLI](../../scripts/run_observation.py) |
| Project adoption | `.dat/`にproject/runtimes/dat.lock、条件付きでevidence/policyを配置。Manual Adapter | STATIC VERIFIED | [Quickstart](../QUICKSTART.md), [Validator](../../scripts/validate_project.py) |
| Runtime capabilities | `adapters/*/capabilities.yaml`にstatus。未知は `unknown`、権限制御の実効性とは別 | STATIC VERIFIED | [Runtime schema](../../schemas/runtime-capability.schema.json) |
| Experiment | Experiment schema、RunEvaluation/ExecutionTrace、paired block、train/test/regression | STATIC VERIFIED | [Experiment Protocol](../EXPERIMENTS.md), [schema](../../schemas/experiment.schema.json) |
| Experiment summary | `summarize_experiment.py`は実験/条件別平均を作成し、混在するRuntime/Model/Effortを拒否 | STATIC VERIFIED | [Summarizer](../../scripts/summarize_experiment.py) |
| Daily observation counts | 構成別の観察件数は効果の証拠ではない。欠測をゼロにしない | STATIC VERIFIED | [Measurement](../OBSERVATION_MEASUREMENT.md) |
| EXP-001 | 18 Run / 9 paired blocks。対象3 Scenario内でT0/T1成功100%。平均Token 68,022/150,080.67、pilot限定Keep T0 | REPORTED | [DECISION.md](../../experiments/EXP-001-t0-vs-t1/DECISION.md) |
| External dogfood | `notionnext-blog`でA2/Codex/T0のManual導入記録あり | REPORTED | [DOGFOODING.md](../DOGFOODING.md) |
| DX time / interruptions | 現行操作時間、設定負担、認知負荷、保守作業時間 | NOT MEASURED | 次のP0作業 |
| Runtime permissions | このセッションでClaude/Codexの実効権限と認証・予算を独立検証したものではない | NOT MEASURED | Runtimeごとのpreflightが必要 |
| CI head | 現行mainの最新必須CIを本Baseline作成時に実行していない | NOT MEASURED | PR headについて別途検証 |

## 2. Public contract inventory (regression-sensitive)

出典：[Release Readiness — Compatibility Boundary](../RELEASE_READINESS.md)。以下は既存利用者が依存する可能性のある契約。**全ての利用箇所を確認したとの主張ではない**。

| Contract family | Sources | Compatibility review |
| --- | --- | --- |
| Machine-readable spec | `schemas/` | 以前受理した値の拒否、field変更、意味論変更がないか |
| Topology and role vocabulary | `topologies/`, `roles/`, `baselines/` | 同じID/Roleが別の意味にならないか |
| Selection / Escalation | `policies/` | 同じ入力に対する判定、未知時の保留の意味が変わらないか |
| CLI | `scripts/` including `run_observation.py`, `validate_project.py`, `summarize_experiment.py` | 入出力、exit code、error handling、依存変更 |
| RunObservation | `schemas/run-observation.schema.json`, `docs/RUN_OBSERVATION_DESIGN.md` | N/A/unknownと0、レビュー独立性、秘匿、保存先 |
| Skill | `skills/dat-select/SKILL.md`, `skills/dat-observe/SKILL.md` | スキル名・発火説明・Canonical正本への参照 |
| Distribution | `.claude-plugin/`, `.codex-plugin/` | Marketplace命名、Version、Plugin互換性 |
| External adoption | `examples/brownfield/.dat/`, `docs/QUICKSTART.md` | `dat.lock.yaml`、revision pin、Runtime Binding |
| Experiment integrity | `experiments/EXP-001-t0-vs-t1/`, freeze audit | Frozen 33 original blob SHA、履歴とRunの不変性 |

## 3. Current user journeys to reproduce BEFORE designing new APIs

### Journey A — Assess / Select

**Fixture:** 公開または使い捨てのTask description。low-complexity / unknown-input / medium-risk / high-risk を含める。

1. `dat-select`を現行Promptで起動する（Runtimeが使えない場合はPolicyを手動解釈し、その旨を記録）。
2. 入力Task、既知/未知、該当Rule、返答、必要なユーザー追加入力、提案の根拠を保存。
3. 観測: 所要時間、ユーザー操作数、正しい保留、余分な質問、Runtime変更や許可の有無。
4. **選択できたこと ≠ 構成の優位性**。効果の採否は別実験。

### Journey B — Observe / Store

1. サンプル作業の完了/失敗/中断という3ケースを用意。プロンプト・private情報・個人名を含めない。
2. `dat-observe`の指示でRunObservationを作成、既存validator、Git外store保存、集計を実行。
3. `unknown`や欠測を埋めていないか、パス・シークレットの検査、誤受理・拒否、手入力項目数を記録。
4. 作業時間・編集回数・保存エラー・再試行数を測定。**今回は未実施**。

### Journey C — Compare / Decide

1. 凍結済みのEXP-001資料は**参照のみ**。異なるTaskを新規Runと偽らない。
2. `scripts/summarize_experiment.py`等でcanonical Artifactを集計、実験条件・Run欠損・paired blockを照合。
3. T0/T1のOutcome、Cost、回帰、Limitationsを明記し、現行Decisionを記載どおり再現できるか確認する。
4. 比較に必要な手順やOutputの欠落を記録。独立Oracleのない合成fixtureでは有効性を結論しない。

### Journey D — Adopt new project (optional only if time permits)

1. `examples/brownfield/.dat/`を使い、使い捨てリポジトリにManual Adoption。必須Evidence commandは信頼されたRunnerだけで実行。
2. `validate_project.py --project ... --dat-root ... --require-pinned`で静的整合を検証。
3. 構成の提案、Runtime強制、導入の成功を混同しない。
4. Config編集数、所要時間、誤設定を記録。実consumerには触れない。

## 4. Measurement record for fair A/B UX comparison

同じ担当者が同じTaskを実施すると学習効果があるため、順序をcounterbalanceするか、結果の制限を明記する。初回はfeasibility-only。

| Field | A (current) | B (vNext spike) | Rule |
| --- | --- | --- | --- |
| Task ID / AC | 未実施 | 未実施 | 同一Task/検証基準 |
| Repo SHA / artifact SHA | `4475b300...`（参照元） | 未作成 | 実行時のSHAとFixtureを記録 |
| Runtime / Model / Effort | 未測定 | 未測定 | Runtime条件を揃える |
| Start/end and active work time | unknown | unknown | active作業と待機を分離 |
| Human operations / prompts | unknown | unknown | 操作定義を事前固定 |
| Files edited / config steps | unknown | unknown | 実変更数。ファイル数単独で優劣判定しない |
| Validation exit / negative cases | unknown | unknown | 同一testを実行 |
| Outcome / regressions | unknown | unknown | 独立ACで判定 |
| Token / model invocation / cost | unknown | unknown | 取得不能はunknown |
| Context / handoff / errors | unknown | unknown | 手戻りを記録 |
| Reviewer findings / time | unknown | unknown | 独立/同一セッションを識別 |

## 5. Known limitations / STOP conditions

- このInventoryはGitHubソースの**静的確認**。コマンド実行・利用者測定・最新PR CIは完了していない。
- EXP-001の成功率100%とToken比率は対象Pilotに限定。Hard-taskとfoldの有効性は#244/#248で別途研究。
- 旧releaseの互換性は静的表だけで保証しない。破壊的変更が必要になった場合は別途Human判断。
- 許可されていない有料モデル、追加課金、独立Reviewの捏造、本番Credential、Frozen Artifactへの書込みは禁止。

## 6. P0 Exit / Next smallest action

- [x] Source-of-truth paths・公開契約・既知結果・未知をInventory化。
- [ ] 実際のJourney A/B/Cを**実行**し、操作数・人時・エラーとRuntimeを計測。
- [ ] 顕在化した痛点を、利用価値に関連付けた優先順位表にする。
- [ ] 比較条件と候補Taskを事前登録してからBのoffline Spikeへ進む。
- [ ] 独立Reviewerに現行Aを改善するだけで十分ではないかを確認させる。

**P0 completion is NOT claimed.** 設計文書の作成は測定の代わりではない。
