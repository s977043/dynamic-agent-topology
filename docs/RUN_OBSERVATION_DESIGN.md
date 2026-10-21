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

- 判定対象: 段階 4 の dogfooding で集めた記録
- 「取得」の定義: 値が `unknown` でないこと。`0` や空配列 `[]` は明示値として取得に数える
- 取得率の分母: 判定対象の全記録で固定する。`unknown` は分母に残し、未取得として数える（§5.3 の一般集計で `unknown` を分母から除く規則とは別で、H1 には適用しない）
- 判定は次の順に適用し、結果は 1 つだけになる
  1. **INCONCLUSIVE（前提不足）**: 記録が 20 件未満、または 2 リポジトリ未満。取得率は見ない
  2. **棄却**: 6 項目のいずれかの取得率が 50% 未満。記録の時点・手順の設計を見直す
  3. **支持**: 6 項目すべての取得率が 80% 以上
  4. **INCONCLUSIVE（中間）**: 上のどれにも当たらない（いずれかが 50% 以上 80% 未満）
- INCONCLUSIVE は採否の根拠にしない

**H2（構成分類の再現性）**: §5.2 の判定基準を使えば、同じ記録から 2 つの独立セッションが付ける `topologyEquivalent` が一致する。

- 対象の選び方: H1 の判定対象と同じ記録の全件を使う（抜き取りや選別をしない）。判定する 2 セッションは、記録を書いたセッションとは別にし、互いの判定を見ない
- 一致率の分母: 全件。片方または両方が `unknown` の記録も分母に含め、両方 `unknown` は一致、片方だけ `unknown` は不一致として数える。`unknown` の件数も併記する
- 判定（相互排他）: 20 件未満は INCONCLUSIVE、20 件以上で一致率 80% 以上は支持、80% 未満は棄却。棄却したら判定基準を見直すまで集計に `topologyEquivalent` を使わない
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
| `topologyBasis` | 判定根拠（§5.2 の 5 項目） | object | なし |
| `tasks.total` / `tasks.delegated` | タスク数・委託したタスク数 | integer または `unknown` | なし |
| `agentInvocations` | 委託・再委託を含む起動総数 | integer または `unknown` | trace `summary.agentInvocations` |
| `artifacts` | 作成・merge した PR 等の参照 | `{ref, state}` の配列 | trace `events[].artifact` |
| `reviews` | 独立レビューの記録 | `{target, reviewerKind, role, findings{blocking, nonBlocking}, decision}` の配列 | trace `events[type=review]` |
| `rework.count` | 修正のための再委託・再レビューの回数 | integer または `unknown` | `handoffFailures` とは同義でない |
| `humanInterventions` | 人の介入の種別ごとの件数 | `{kind, count}` の配列 | trace `summary.humanInterventions`（合計） |

`reviewerKind` は `same-session` / `separate-session` / `separate-model` / `human` の enum。モデル名は `runtime` / `model` に置き、レビュー本文は書かない。

### 5.2 `topologyEquivalent` の判定基準

ウェーブに書かれた事実だけで判定する。計画にあるが実施の記録がない役割は数えない。

`topologyBasis` には次を記録する。各値は `yes` / `no` / `unknown`。

- `agentInvolved`: エージェントが実装または検証に関与したか
- `delegated`: Worker への委託があったか
- `verification`: 生成物を受け入れる前の検証の記録があるか。あれば `verifierKind`（`organizer` / `separate-session` / `separate-model` / `human`）も残す
- `independentReview`: 実装者と別の主体による助言のレビュー（受け入れ判断を持たない）があったか。`reviews[]` に `role: advisory` が 1 件以上あれば `yes`
- `specialistRole`: Worker・Reviewer・Verifier 以外の専門役割が別タスクで実施されたか

各 `reviews[]` には `role`（`advisory`: 助言のみ / `verifier`: 受け入れ・merge の判断を持つ）を必須で持たせ、助言と検証を記録上で区別する。`role: verifier` のレビューは `verification`（と `verifierKind`）の根拠にだけ使い、`independentReview` には数えない。`role: advisory` は `independentReview` の根拠にだけ使い、`verification` には数えない。1 件のレビューが両方に数えられることはない（Reviewer ≠ Verifier）。

判定は上から順に適用し、最初に当たったものに決める（相互排他）。

| 順 | 判定 | 条件 |
|---|---|---|
| 1 | unknown | `agentInvolved`・`delegated`・`verification` のいずれかが `unknown` |
| 2 | P0 | `agentInvolved: no` で、決定的な処理だけで完了した |
| 3 | other | `agentInvolved: no` で、人だけで実施・検証した。または Worker がいない（例: 他者の PR のレビューだけ） |
| 4 | T0 | `verification: no`（検証の記録がない）。または委託がなく、検証が実装と同じ主体だけで行われた。助言のレビューだけがあっても T0 |
| 5 | T3 | 委託があり、検証の記録があり、`independentReview: yes`、`specialistRole: yes`。同じ役割の並列は専門役割に数えない |
| 6 | T2 | 委託があり、検証の記録があり、`independentReview: yes` |
| 7 | T1 | (a) 委託があり、検証の記録がある（`verifierKind` を問わない）。または (b) 委託がなく、別セッション・別モデル・人が `role: verifier` として検証した（Organizer を Worker とみなす） |
| 8 | unknown | 1〜7 のどれにも当たらない（全件が必ずどれか 1 つに分類される。該当した記録は判定基準の見直し候補として件数を併記する） |

**境界ケース「委託なし＋別モデルの独立レビュー」**: そのレビューの `role` で決める。`verifier` なら T1 (b)、`advisory` だけなら T0。根拠は、T1 の canonical 定義が「生成する主体と検証する主体の分離」であり委託の有無ではないこと、かつ Reviewer ≠ Verifier（ARCHITECTURE）であること。`role` が記録されていなければ `verification: unknown` となり unknown に落ちる。

### 5.3 `unknown` と 0 の区別

- 分からない値は文字列 `unknown`。0・空配列・`false` で補わない（METRICS の欠測値方針と同じ）
- レビューをしなかったときは `reviews: []`、手戻りがなかったときは `rework.count: 0` を明記する。これが H1 の「取得」に数えられる
- 時刻が分単位以上で両方分かるときだけ `wallClockMs` を出す
- 集計は `unknown` を分母から除き、除いた件数を併記する

## 6. 保存先と秘匿

- **保存先（推奨）**: 導入先の `.dat/state/observations/` に 1 ウェーブ 1 ファイルで置く。`.dat/state/` は `examples/brownfield/.gitignore` で既に除外されている場所で、既定ではコミットしない
- 含めないもの: 秘密情報、private source、未サニタイズのプロンプト・会話本文、レビュー本文、個人環境の絶対パス。`humanInterventions` は種別と件数だけ、`outcomeReason` は 1 行の要約だけ
- **秘匿規則は記録の全項目に適用する**。列挙した項目に限らない。対象は `metadata.*`、`runtime` / `model` の識別（名前・版・モデル ID・effort）、`reviews[].target`・`decision`、`artifacts[].ref`・`state`、`outcomeReason`、`topologyBasis`、`humanInterventions[].kind`、将来追加する項目を含む、すべての文字列値
- 参考: `schemas/execution-trace.schema.json` でも `runtime.name`、`model.id`、`events[].actor`・`target`・`artifact` は制約のない自由文字列で、識別情報が入り得る。`RunObservation` の同形の項目も同じく自由文字列として扱う
- 識別情報（PR URL・ブランチ名・private リポジトリ名・導入先名・個人名など）は、private な導入先では DAT 側へ転記するときに仮名（例: `project-a`、`pr-1`）へ置き換える
- **サニタイズ済み**の定義: (1) 上の「含めないもの」を含まない、(2) 識別情報が公開済みのもの（public リポジトリ名・公開 PR 番号）か仮名だけである、(3) 段階 2 の validator を通る、の 3 つをすべて満たすこと
- **保存前**（`.dat/state/observations/` への書き込み時）: 記録者が validator を実行し、通らない記録は保存しない
- **転記前**（集計値や DOGFOODING へ載せるとき）: 識別情報を仮名に置き換え、validator を再実行し、人が差分を確認してから載せる。転記するのは集計値と仮名化した記録だけ
- **段階 2 の必須の負例**: 記録内のすべての文字列値（enum 以外）の長さ上限超過、絶対パス（`/Users/`・`/home/`・`C:\` 形式）、トークン形式の文字列（例: `ghp_`・`sk-` で始まる文字列、長い高エントロピー文字列）を含む記録を validator が拒否すること

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
- U3: 委託なしで `role: advisory` のレビューだけを T0 とする規則で H2 の一致率が下がるかは、段階 4 で確認する
