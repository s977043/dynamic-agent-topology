# DAT vNext — P0 Baseline / Contract Inventory

> **非規範的な設計案（未採用）。** 正本は既存文書（[RELEASE_READINESS.md](../RELEASE_READINESS.md)、[EXPERIMENTS.md](../EXPERIMENTS.md)、[METRICS.md](../METRICS.md)、[QUICKSTART.md](../QUICKSTART.md) など）で、矛盾する場合は正本が優先する。関係文書: [MAINTENANCE_COST_REVIEW.md](../MAINTENANCE_COST_REVIEW.md)、[POST_EXP001_EVALUATION_DESIGN.md](../POST_EXP001_EVALUATION_DESIGN.md)、[RESEARCH_AUTONOMOUS_CODING_LOOP_REFERENCES.md](../RESEARCH_AUTONOMOUS_CODING_LOOP_REFERENCES.md)、[CURRENT_EXECUTION_PLAN.md](../CURRENT_EXECUTION_PLAN.md)。

- 状態: **PARTIAL P0 / STATIC INSPECTION + AGENT OFFLINE JOURNEYS**。実際の利用者作業時間・有料モデル・機能優位性は **NOT MEASURED**。
- 親Issue: [#268](https://github.com/s977043/dynamic-agent-topology/issues/268)
- 観測したsnapshot: `main` `4475b3004ecd07ae5da313121543067119a59479`（2026-10-29 00:28:47Z）
- 公開済みの配布版: [v0.4.1](https://github.com/s977043/dynamic-agent-topology/releases/tag/v0.4.1)（2026-10-29。出典: [CHANGELOG.md](../../CHANGELOG.md)、[CITATION.cff](../../CITATION.cff)）
- 関連文書: [RFC](DAT_VNEXT_RFC.md) / [Independent review protocol](DAT_VNEXT_REVIEW_RUNBOOK.md) / [P0 Journey 実行記録](DAT_VNEXT_P0_JOURNEYS.md)（`main` `257f836`、agent による offline 実行。人の計測は未実施）

## 1. Evidenceの確度と出典の扱い

凡例：
- **STATIC VERIFIED** = 指定SHAのソースコード・公開メタデータの確認。実行成功や品質を意味しない。
- **REPORTED** = リポジトリ内の既存実験レポート／検証記録の記載。今回独立再実行した結果ではない。
- **NOT MEASURED** = 実測のデータなし。数値を推定で埋めない。
- **PROPOSED** = 調査すべき仮説であり採用済み判断ではない。
- **AGENT RUN** = agent がmodelを起動せずにコマンドを実行した計数（コマンド数・exit code・編集ファイル数・エラー）。人の操作時間や負荷ではない。

| 観点 | 現在のEvidence | 状態 | 出典 |
| --- | --- | --- | --- |
| 目的 | Provider-agnosticなAgent Topology仕様・Experiment・Evaluation。Agent Runtimeではない | STATIC VERIFIED | [North Star](../NORTH_STAR.md), [Architecture](../ARCHITECTURE.md) |
| UX — 選択 | `dat-select`がRisk/Complexity/Evidence等のPolicy入力を評価。未確定で選択保留、実構成は変更しない | STATIC VERIFIED | [Skill](../../skills/dat-select/SKILL.md), [routing](../../policies/routing/R0_dynamic.yaml) |
| UX — 観察 | `dat-observe`がYAML作成、validator、Git外保存、集計を案内 | STATIC VERIFIED | [Skill](../../skills/dat-observe/SKILL.md), [CLI](../../scripts/run_observation.py) |
| プロジェクト導入 | `.dat/`にproject/runtimes/dat.lock、条件付きでevidence/policyを配置。Manual Adapter | STATIC VERIFIED | [Quickstart](../QUICKSTART.md), [Validator](../../scripts/validate_project.py) |
| Runtime capabilities | `adapters/*/capabilities.yaml`にstatus。未知は `unknown`、権限制御の実効性とは別 | STATIC VERIFIED | [Runtime schema](../../schemas/runtime-capability.schema.json) |
| 実験 | Experiment schema、RunEvaluation/ExecutionTrace、paired block、train/test/regression | STATIC VERIFIED | [Experiment Protocol](../EXPERIMENTS.md), [schema](../../schemas/experiment.schema.json) |
| 実験の集計 | `summarize_experiment.py`は実験/条件別平均を作成し、混在するRuntime/Model/Effortを拒否 | STATIC VERIFIED | [Summarizer](../../scripts/summarize_experiment.py) |
| 日常観察の件数 | 構成別の観察件数は効果の証拠ではない。欠測をゼロにしない | STATIC VERIFIED | [Measurement](../OBSERVATION_MEASUREMENT.md) |
| EXP-001 | 18 Run / 9 paired blocks。対象3 Scenario内でT0/T1成功100%。平均Token 68,022/150,080.67、pilot限定Keep T0 | REPORTED | [DECISION.md](../../experiments/EXP-001-t0-vs-t1/DECISION.md) |
| 外部dogfood | `notionnext-blog`でA2/Codex/T0のManual導入記録あり | REPORTED | [DOGFOODING.md](../DOGFOODING.md) |
| Journey A〜D の offline 実行 | A: 手動解釈で4件中3件決定・1件保留。B: 3件保存、初回NG 6回（`verifierKind`）。C: DECISION.mdの数値と一致、paired blockは出力なし。D: floating+`--require-pinned` exit 1 → pinned exit 0 | AGENT RUN | [P0 Journey 実行記録](DAT_VNEXT_P0_JOURNEYS.md) |
| DX時間 / 中断 | 現行操作時間、設定負担、認知負荷、保守作業時間（人の計測） | NOT MEASURED | 次のP0作業 |
| Runtime権限 | このセッションでClaude/Codexの実効権限と認証・予算を独立検証したものではない | NOT MEASURED | Runtimeごとのpreflightが必要 |
| CI head | 現行mainの最新必須CIを本Baseline作成時に実行していない | NOT MEASURED | PR headについて別途検証 |

## 2. 公開契約の棚卸し（回帰に注意する箇所）

出典：[Release Readiness — Compatibility Boundary](../RELEASE_READINESS.md)。以下は既存利用者が依存する可能性のある契約。**全ての利用箇所を確認したとの主張ではない**。

| 契約の種類 | 対象 | 互換性の確認点 |
| --- | --- | --- |
| Machine-readable spec | `schemas/` | 以前受理した値の拒否、field変更、意味論変更がないか |
| Topology and role vocabulary | `topologies/`, `roles/`, `baselines/` | 同じID/Roleが別の意味にならないか |
| Selection / Escalation | `policies/` | 同じ入力に対する判定、未知時の保留の意味が変わらないか |
| CLI | `run_observation.py`、`validate_project.py`、`summarize_experiment.py` を含む `scripts/` | 入出力、exit code、error handling、依存変更 |
| RunObservation | `schemas/run-observation.schema.json`, `docs/RUN_OBSERVATION_DESIGN.md` | N/A/unknownと0、レビュー独立性、秘匿、保存先 |
| Skill | `skills/dat-select/SKILL.md`, `skills/dat-observe/SKILL.md` | スキル名・発火説明・Canonical正本への参照 |
| Distribution | `.claude-plugin/`, `.codex-plugin/` | Marketplace命名、Version、Plugin互換性 |
| External adoption | `examples/brownfield/.dat/`, `docs/QUICKSTART.md` | `dat.lock.yaml`、revision pin、Runtime Binding |
| Experiment integrity | `experiments/EXP-001-t0-vs-t1/`、`scripts/audit_exp001_completed_snapshot.py` | Frozen 33 original blob SHA、履歴とRunの不変性 |

## 3. 新しいAPIを設計する前に再現する現行の利用者Journey

実行記録: [DAT_VNEXT_P0_JOURNEYS.md](DAT_VNEXT_P0_JOURNEYS.md)（A〜Dを各1回、agentがoffline実行。人の計測は未実施）。

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

### Journey D — Adopt new project（時間がある場合のみ）

1. `examples/brownfield/.dat/`を使い捨てリポジトリへコピーし、Manual Adoptionする。必須Evidence commandは信頼されたRunnerだけで実行。
2. **前提手順:** 検証に使うDAT checkoutのrevision（SHAまたはtag）を確認する。lockの編集は手順3.2で行う（[QUICKSTART.md](../QUICKSTART.md)「5. DAT revisionを固定する」）。編集するのはコピー先の `.dat/dat.lock.yaml` だけで、既存の `examples/brownfield/` は変更しない。
3. `validate_project.py --project ... --dat-root ... --require-pinned`で静的整合を、次の順で2回検証し、両方の結果を記録する。
   1. コピー直後（`pinMode: floating` のまま）に1回実行する。期待結果: exit 1。
   2. コピー先のlockを pinned にし、手順2で確認したrevisionを指定してからもう1回実行する。期待結果: exit 0。
4. 構成の提案、Runtime強制、導入の成功を混同しない。
5. Config編集数、所要時間、誤設定を記録。実consumerには触れない。

## 4. A/BのUXを公平に比較するための計測記録

同じ担当者が同じTaskを実施すると学習効果があるため、順序をcounterbalanceするか、結果の制限を明記する。初回はfeasibility-only。

| 項目 | A（現行） | B（vNext spike） | 規則 |
| --- | --- | --- | --- |
| Task ID / AC | 未実施 | 未実施 | 同一Task/検証基準 |
| Repo SHA / artifact SHA | `4475b300...`（参照元）。Journey実行は `257f836d`（[実行記録](DAT_VNEXT_P0_JOURNEYS.md)） | 未作成 | 実行時のSHAとFixtureを記録 |
| Runtime / Model / Effort | Journey実行はmodel未使用（agentのoffline実行、Python 3.12.13）。Skill経由のRuntime条件は未測定 | 未測定 | Runtime条件を揃える |
| attempt ID / block ID | unknown | unknown | 開始したattemptはすべて1行ずつ残す。完了したattemptだけを比較に使わない |
| 完了 / 中断 / 環境障害 | unknown | unknown | attemptごとに区別して記録 |
| 再試行理由 | Journey B: 3記録とも1回再試行（`verifierKind: none` のschema NG）。他はunknown | unknown | 再試行したattemptごとに理由を記録 |
| 判明した消費（時間・Token・cost） | unknown | unknown | 中断・再試行分も含めて残す。取得不能はunknown |
| 開始/終了とactive作業時間 | unknown | unknown | active作業と待機を分離 |
| 人の操作 / prompt数 | unknown | unknown | 操作定義を事前固定 |
| 編集したファイル / 設定手順 | agent実行による計数: B 3ファイル×1行の修正、D 1ファイル（lock 2行）・4手順。人の値はunknown | unknown | 実変更数。ファイル数単独で優劣判定しない |
| Validation exit / negative cases | agent実行による計数: B 初回NG 6回→exit 0、負例2件（repo内store exit 2、重複ID exit 1）。C 5コマンドexit 0。D floating exit 1 → pinned exit 0 | unknown | 同一testを実行 |
| Outcome / 回帰 | unknown | unknown | 独立ACで判定 |
| Token / model起動 / cost | unknown | unknown | 取得不能はunknown |
| Context / handoff / errors | unknown | unknown | 手戻りを記録 |
| Reviewerの指摘 / 時間 | unknown | unknown | 独立/同一セッションを識別 |

## 5. 既知の限界とSTOP条件

- このInventoryはGitHubソースの**静的確認**。Journey A〜Dのagentによるoffline実行は[実行記録](DAT_VNEXT_P0_JOURNEYS.md)にあるが、利用者測定は完了していない。
- EXP-001の成功率100%とToken比率は対象Pilotに限定。Hard-taskとfoldの有効性は#244/#248で別途研究。
- 旧releaseの互換性は静的表だけで保証しない。破壊的変更が必要になった場合は別途Human判断。
- 許可されていない有料モデル、追加課金、独立Reviewの捏造、本番Credential、Frozen Artifactへの書込みは禁止。

## 6. P0の完了条件と次の最小行動

- [x] Source-of-truth paths・公開契約・既知結果・未知をInventory化。
- [x] Journey A〜Dをagentがmodelなしでoffline実行し、コマンド数・exit code・編集ファイル数・エラーを記録（[実行記録](DAT_VNEXT_P0_JOURNEYS.md)。Aは手動解釈）。
- [ ] 実際のJourney A/B/Cを人が**実行**し、操作数・人時・認知負荷とRuntimeを計測。
- [ ] 顕在化した痛点を、利用価値に関連付けた優先順位表にする。
- [ ] 比較条件と候補Taskを事前登録してからBのoffline Spikeへ進む。
- [ ] 独立Reviewerに現行Aを改善するだけで十分ではないかを確認させる。

**P0の完了は主張しない。** 設計文書の作成は測定の代わりではない。
