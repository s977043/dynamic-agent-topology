# ウェーブ観察記録の設計案（#223）

状態: **非規範的な設計案（未採用・独立レビュー前）**。採用には [Issue #223](https://github.com/s977043/dynamic-agent-topology/issues/223) の段階 2 以降について Human の判断が必要です。本書は schema・validator・adapter の追加を許可しません。`schemas/`、`scripts/`、`adapters/`、`topologies/`、EXP-001 の Frozen file は変更しません。観察記録の有効性は **INCONCLUSIVE**（DAT 仕様としての実測 0 件）です。

- 起案日: 2026-10-21 / 基準: origin/main `560e512`
- 関連: [Issue #223](https://github.com/s977043/dynamic-agent-topology/issues/223)
- 一次ソース: Issue 本文、[ARCHITECTURE.md](ARCHITECTURE.md)、[GLOSSARY.md](GLOSSARY.md)、[METRICS.md](METRICS.md)、[DOGFOODING.md](DOGFOODING.md)、[AGENT_HARNESS.md](AGENT_HARNESS.md)、`schemas/execution-trace.schema.json`、`schemas/evaluation.schema.json`、`schemas/project-binding.schema.json`、`schemas/dat-lock.schema.json`、`topologies/canonical/T0〜T3`、`experiments/EXP-001-t0-vs-t1/pilot/freeze.yaml`
- 先行試作: DAT の外にある個人環境の試作（記録項目 23 個、既存台帳 27 件での取得率棚卸し、記録・集計スクリプト）。特定ツールの作業台帳を前提にしたもので、本書はそれを写さず一般化する

## 0. Evidence・解釈・推奨の区別

| 区分 | 内容 |
|---|---|
| 観測値（Issue #223 より） | 既存の作業台帳 27 件を記録の型に当てはめると、件数・PR 数・構成・人の介入回数は 8 割以上取れた。結果は 11%、レビュー指摘数は 25%、手戻りは 14〜22%。ランタイム・モデル・終了時刻・所要時間・起動回数は 0%。試作スキルで 2 件を記録でき、「委託なし＋別モデルの独立レビュー」の構成分類が曖昧になった |
| 観測値の限界 | 27 件は特定ツールの台帳 3 リポジトリ分で、取得率は試作者 1 名の手作業判定。DAT の仕様に基づく記録ではない |
| DAT 側の解釈 | 取得率が低い項目はすべて「完了時にしか分からない値」。台帳が着手時に書かれ完了時の結果を残さないという構造が原因と解釈する（Issue の原因記述と一致するが、因果は未検証） |
| 推奨案（未採用） | §3 の (B) 新しい `RunObservation` artifact。§4 以降はこれを前提にする |

## 1. 問題

DAT を他リポジトリの日常開発で使うとき、Organizer・Worker・独立 Reviewer で進める 1 回の作業単位（以下「ウェーブ」）を記録する DAT 側の仕様がない。

- `ExecutionTrace` / `RunEvaluation` は事前登録した実験の Run を前提にしている。`metadata` は `experiment`・`scenario`・`condition`・`blockId` を必須とし、`additionalProperties: false`。日常のウェーブにはこれらの値がない
- 両 schema は EXP-001 の Frozen file（`freeze.yaml`）に含まれ、現時点では変更できない
- 現行の試作は個人環境と特定ツールの台帳に依存し、ランタイムを変えると使えない

## 2. 反証可能な仮説

**H1（取得率）**: ウェーブ完了時に `RunObservation` を 1 件書く手順にすると、試作の棚卸しで取得率が低かった項目（`outcome`、`endedAt`、`reviews` の指摘数、`rework`、`runtime`、`model`）の取得率が、既存台帳の値（11%・0%・25%・14〜22%・0%・0%）を上回り、各項目 80% 以上になる。

- 判定対象: 段階 4 の dogfooding で、2 リポジトリ以上・合計 20 件以上の記録
- 「取得」の定義: 値が `unknown` でないこと。`0` や空配列 `[]` は明示値として取得に数える
- **棄却条件**: 20 件以上集めても上記 6 項目のいずれかの取得率が 50% 未満なら H1 を棄却し、記録の時点・手順の設計を見直す。20 件に届かない場合は INCONCLUSIVE とし、採否の根拠にしない

**H2（構成分類の再現性）**: §5.2 の判定基準を使えば、同じ記録から 2 つの独立セッションが付ける `topologyEquivalent` が一致する。

- **棄却条件**: 20 件以上で一致率が 80% 未満なら、判定基準を見直すまで集計に `topologyEquivalent` を使わない
- 限界: 一致は分類規則の明確さを示すだけで、構成の効果を示さない

## 3. 選択肢の比較

| 案 | 内容 | 利点 | 欠点 | plane 分離への影響 |
|---|---|---|---|---|
| (A) 既存 schema を拡張 | `ExecutionTrace` の `metadata` を任意化し、ウェーブ項目を足す。結果系は `RunEvaluation` に足す | 型が増えない。既存 summarizer を流用できる可能性 | 両 schema が Frozen で EXP-001 中は変更不可。実験用の必須項目を緩めると EXP-001 の検証が弱くなる。結果を `RunEvaluation` に入れると、日常記録が評価（`verdict`）の形をとり、観察と効果判定が混ざる | Observed と Evaluation の両方を触り、境界が曖昧になる |
| (B) 新 artifact `RunObservation` | `schemas/run-observation.schema.json` を新設し、Observed Execution plane の記録として扱う。`verdict` を持たない | Frozen と衝突しない。実験 Run と日常ウェーブを型で区別できる。ランタイム非依存の項目だけを持てる | schema と validator が 1 組増える（保守コスト）。`ExecutionTrace` と `runtime` / `model` / `summary` 系の項目が重複する | Observed Execution にだけ置く。Evaluation は事前登録実験の `RunEvaluation` に限定したまま |
| (C) 仕様化しない | 記録手順を `adapters/` の文書だけに置き、形式は各導入先に任せる | 追加コストが最小 | ランタイムごとに形式がずれ、複数リポジトリの集計ができない。Issue の目的（ランタイム非依存）を満たさない | Runtime Mapping に観察の定義が入り込む |

**推奨: (B)**。要件適合性（ランタイム非依存・Evaluation と分離）と安全性（Frozen と衝突しない）で (A)(C) に勝る。保守コストの増加は、`ExecutionTrace` と同名・同義の項目（`runtime`、`model`、`agentInvocations`、`humanInterventions`、`wallClockMs`）を同じ形で持たせ、将来の統合を可能にすることで抑える。Freeze 解除後に (A) へ寄せるかは段階 5 以降の Human 判断とする。

## 4. 位置づけ

- `RunObservation` は Observed Execution plane の記録。「宣言上どう動くはずだったか」ではなく、ウェーブ完了時に観測できた事実を記録する
- 効果判定（`verdict`、`taskSuccess` の解釈、構成間比較）は持たない。比較の結論は `experiments/` の事前登録実験だけで扱う
- `topologyEquivalent` は「観測された構成が DAT canonical のどれに相当するか」の分類で、宣言した Topology（Desired Organization）とは別。宣言との差は将来 `topologyAdherence` 相当の評価対象になり得るが、本設計では扱わない

## 5. 記録の項目案

### 5.1 項目

試作の 23 項目から、特定ツールの台帳に依存する項目（台帳ファイルの状態、元ファイルのパス、対象リポジトリの固定 enum）を除き、ランタイム非依存に一般化した。

| 項目 | 意味 | 型 | `ExecutionTrace` / `RunEvaluation` との対応 |
|---|---|---|---|
| `metadata.observationId` | 記録の識別子 | string | trace `metadata.runId` に相当（同名にはしない） |
| `metadata.project` | 導入先の識別名 | string | `.dat/project.yaml` の `metadata.name` |
| `metadata.datVersion` | 使った DAT の版 | string | `.dat/dat.lock.yaml` |
| `startedAt` / `endedAt` | 開始・終了時刻 | date-time または `unknown` | trace `events[start/finish].timestamp` |
| `wallClockMs` | 所要時間 | integer または `unknown` | trace `summary.wallClockMs` |
| `goalRecorded` | 目的を事前に書いたか | boolean | なし |
| `outcome` | 結果 | `completed` / `interrupted` / `failed` / `unknown` | `verdict` とは別物（効果判定ではない） |
| `outcomeReason` | 中断・失敗の理由（1 行、本文を含めない） | string | なし |
| `runtime` / `model` | Organizer と Worker ごとのランタイム・モデル・effort | trace と同形の object の配列 | trace `runtime` / `model` |
| `topologyEquivalent` | 観測された構成の相当 | `P0` / `T0` / `T1` / `T2` / `T3` / `other` / `unknown` | trace `executionSubject.name` の観測版 |
| `topologyBasis` | 判定根拠（委託・独立レビュー・専門役割の有無） | object | なし |
| `tasks.total` / `tasks.delegated` | タスク数・委託したタスク数 | integer または `unknown` | なし |
| `agentInvocations` | 委託・再委託を含む起動総数 | integer または `unknown` | trace `summary.agentInvocations` |
| `artifacts` | 作成・merge した PR 等の参照 | `{ref, state}` の配列 | trace `events[].artifact` |
| `reviews` | 独立レビューの記録 | `{target, reviewerKind, findings{blocking, nonBlocking}, decision}` の配列 | trace `events[type=review]` |
| `rework.count` | 修正のための再委託・再レビューの回数 | integer または `unknown` | `handoffFailures` とは同義でない |
| `humanInterventions` | 人の介入の種別ごとの件数 | `{kind, count}` の配列 | trace `summary.humanInterventions`（合計） |

`reviewerKind` は `same-session` / `separate-session` / `separate-model` / `human` の enum。モデル名は `runtime` / `model` に置き、レビュー本文は書かない。

### 5.2 `topologyEquivalent` の判定基準

ウェーブに書かれた事実だけで判定する。計画にあるが実施の記録がない役割は数えない。

| 判定 | 条件 |
|---|---|
| P0 | エージェントが関与せず、決定的な処理だけで完了した |
| T0 | 委託も独立レビューもなく、1 主体が実装と検証を行った |
| T1 | (a) 委託があり、Organizer が一次ソースで照合した（Organizer を Verifier とみなす）が、それ以外の独立レビューがない。または (b) 委託がなく、別セッション・別モデルの独立レビューが Verifier を担った（Organizer を Worker とみなす） |
| T2 | 委託があり、Organizer の照合に加えて別主体の独立レビューの記録がある |
| T3 | T2 に加え、Worker・Reviewer・Verifier 以外の専門役割が別タスクとして実施された。同じ役割の並列は T3 に数えない |
| other | Worker がいない（例: 他者の PR のレビューだけ） |
| unknown | 委託やレビューの有無が読み取れない |

**境界ケース「委託なし＋別モデルの独立レビュー」**: T1 (b) とする。根拠は、T1 の canonical 定義が「生成する主体と検証する主体の分離」であり、委託の有無ではないこと。ただし Reviewer ≠ Verifier（ARCHITECTURE）なので、そのレビューが merge 判断を担った場合だけ Verifier とみなし、助言だけなら T0 とする。どちらだったかを `topologyBasis.reviewGatedMerge`（boolean）に残し、集計時に再分類できるようにする。

### 5.3 `unknown` と 0 の区別

- 分からない値は文字列 `unknown`。0・空配列・`false` で補わない（METRICS の欠測値方針と同じ）
- レビューをしなかったときは `reviews: []`、手戻りがなかったときは `rework.count: 0` を明記する。これが H1 の「取得」に数えられる
- 時刻が分単位以上で両方分かるときだけ `wallClockMs` を出す
- 集計は `unknown` を分母から除き、除いた件数を併記する

## 6. 保存先と秘匿

- **保存先（推奨）**: 導入先の `.dat/state/observations/` に 1 ウェーブ 1 ファイルで置く。`.dat/state/` は `examples/brownfield/.gitignore` で既に除外されている場所で、既定ではコミットしない
- 集計や DOGFOODING への転記は、サニタイズ済みの集計値だけを人が選んで DAT 側に載せる
- 含めないもの: 秘密情報、private source、未サニタイズのプロンプト・会話本文、レビュー本文、個人環境の絶対パス。`humanInterventions` は種別と件数だけ、`outcomeReason` は 1 行の要約だけ
- validator（段階 2）で、自由記述欄の長さ上限と、絶対パス・トークン形式の文字列の検出を行うことを検討する

## 7. adapter の責務

| 置き場所 | 内容 |
|---|---|
| 仕様側（`schemas/`、`scripts/`、本書） | 項目と型、判定基準、`unknown` の規則、秘匿規則、validator と集計 |
| `adapters/claude-code/` | ウェーブ完了時に記録する手順（いつ・どの情報源から値を取るか）、Claude Code のサブエージェント起動数・モデル ID の取り方 |
| `adapters/codex/` | 同上を Codex の実行形態に合わせたもの |

adapter は値の取り方だけを持ち、項目や判定基準を追加・変更しない。特定ツール（例: 作業台帳を持つオーケストレーション用スキル）との連携は、adapter の例として書くに留める。

## 8. 段階 2〜5

| 段階 | 作業 | 完了条件 | Human 判断 |
|---|---|---|---|
| 2 | `run-observation.schema.json`、semantic check、validator、テスト、`spec-lint.yml` への組み込み、正例・負例 fixture | CI が通り、`unknown` と 0 の区別・秘匿規則の負例が落ちる。Frozen file に差分がない | 本書の採否と (B) の選択。新 artifact kind の追加 |
| 3 | `adapters/claude-code/`・`adapters/codex/` に記録手順 | 各ランタイムで 1 件ずつ、validator を通る記録を作れる | なし（通常 PR） |
| 4 | 2 リポジトリ以上で dogfooding、`DOGFOODING.md` と Learning ledger に記録 | 20 件以上で H1・H2 を判定し、棄却・INCONCLUSIVE を含めて記録する | 対象リポジトリと期間の選定 |
| 5 | 次の版の候補として公開 | `RELEASE_READINESS.md` のゲートを通る | release / tag は Human のみ |

## 9. やらないこと

- 観察記録から構成の優劣を結論づけない。比較は事前登録した実験（`experiments/`）だけで行う
- `RunObservation` に `verdict` や効果判定の項目を持たせない
- EXP-001 の Frozen file（`execution-trace` / `evaluation` schema を含む）を変更しない
- 記録を自動で取る runtime 連携や hook を DAT 側に実装しない（adapter は手順の記述に留める）
- 先行試作の台帳固有の項目や個人環境のパスを仕様に持ち込まない

## 10. 未決事項

- U1: `outcome` に `handed-off`（別ウェーブへ引き継ぎ）を独立値として持たせるか
- U2: `.dat/state/` 以外に、集計用の共有先（例: サニタイズ済み JSONL）を DAT 側で定義するか
- U3: T1 (b) の `reviewGatedMerge: false` を T0 とする規則で H2 の一致率が下がるかは、段階 4 で確認する
