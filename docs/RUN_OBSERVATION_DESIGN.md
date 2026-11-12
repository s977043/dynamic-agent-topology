# ウェーブ観察記録の設計案（#223）

状態: **非規範的な設計案（段階 3 実装中）**。段階 2 の schema（`schemas/run-observation.schema.json`）・validator（`scripts/validate_run_observation.py`）・fixture（`fixtures/run-observation/`）を [Issue #223](https://github.com/s977043/dynamic-agent-topology/issues/223) の段階 2 として追加しました。段階 3 の記録手順と合成値の記録例は `adapters/claude-code/RUN_OBSERVATION.md`・`adapters/codex/RUN_OBSERVATION.md` にあります。採否と新 artifact kind の追加は Human の判断です。`topologies/`・EXP-001 の Frozen file は変更しません。観察記録の有効性は **INCONCLUSIVE**（DAT 仕様としての実測 0 件）です。

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
| `rework.sources` | `rework.count` の出どころ別の内訳（`dat/v1alpha2` 以降。§5.5） | 出どころをキー、integer または `unknown` を値とする object | なし |
| `humanInterventions` | 人の介入の種別ごとの件数 | `{kind, count}` の配列 | trace `summary.humanInterventions`（合計） |

`reviewerKind` は `same-session` / `separate-session` / `separate-model` / `human` の enum。モデル名は `runtime` / `model` に置き、レビュー本文は書かない。

### 5.2 `topologyEquivalent` の判定基準

ウェーブに書かれた事実だけで判定する。計画にあるが実施の記録がない役割は数えない。

`topologyBasis` には次を記録する。各値は `yes` / `no` / `unknown`。

- `agentInvolved`: エージェントが実装または検証に関与したか
- `delegated`: Worker への委託があったか
- `verification`: 生成物を受け入れる前の検証の記録があるか。あれば `verifierKind`（`organizer` / `separate-session` / `separate-model` / `human`）も残す
- `independentReview`: 実装者と別の主体による助言のレビュー（受け入れ判断を持たない）があったか。`reviews[]` に `reviewerKind` が `separate-session` / `separate-model` / `human` の `role: advisory` が 1 件以上あれば `yes`（`same-session` の助言は実装者と別の主体ではないので数えない）
- `specialistRole`: Worker・Reviewer・Verifier 以外の専門役割が別タスクで実施されたか

各 `reviews[]` には `role`（`advisory`: 助言のみ / `verifier`: 受け入れ・merge の判断を持つ）を必須で持たせ、助言と検証を記録上で区別する。`role: verifier` のレビューは `verification`（と `verifierKind`）の根拠にだけ使い、`independentReview` には数えない。`role: advisory` は `independentReview` の根拠にだけ使い、`verification` には数えない。1 件のレビューが両方に数えられることはない（Reviewer ≠ Verifier）。

**正とする記録**: Organizer 以外による検証と助言のレビューは `reviews[]` を正とし、`topologyBasis` の `verification`・`verifierKind`・`independentReview` はそこから導く値として扱う。Organizer 自身の照合はレビューではないので `reviews[]` に入れず、`verifierKind: organizer` だけで記録する。**検証の根拠となるレビューの特定**: `reviews[]` は実施順に並べる。`role: verifier` のレビューのうち、最終的に受け入れた（merge した）`artifacts[].ref` を `target` に持つ最後の 1 件を「根拠レビュー」とする。同じ種別のレビューが複数あっても、根拠になるのはこの 1 件だけで、それより前の `role: verifier` のレビュー（差し戻しなど）は記録として残すが `verifierKind` の導出には使わない。

`verifierKind` は根拠レビューの `reviewerKind` から次の表で導く。

| 根拠レビューの `reviewerKind` | `verifierKind` |
|---|---|
| （根拠レビューなし、Organizer が照合） | `organizer` |
| `separate-session` | `separate-session` |
| `separate-model` | `separate-model` |
| `human` | `human` |
| `same-session` | 導出しない（同一セッションは検証主体の分離にならないため、`role: verifier` と組み合わせた記録は拒否する） |

段階 2 の validator は次の食い違いを拒否する（必須の負例に含める）。

- `verifierKind` が上の表で根拠レビューから導いた値と一致しない（例: `verifierKind: separate-session` なのに、根拠レビューが `reviewerKind: human`）
- `verifierKind` が `organizer` 以外なのに、根拠レビューがない（`role: verifier` のレビューがない、または受け入れた `artifacts[].ref` を `target` に持つものがない）
- `reviewerKind: same-session` かつ `role: verifier` のレビューがある
- `role: verifier` が `reviews[]` にあるのに `verification` が `yes` でない
- 独立した `reviewerKind`（`separate-session` / `separate-model` / `human`）の `role: advisory` の有無と `independentReview` の `yes` / `no` が一致しない（`reviews` 自体が `unknown` のときだけ `independentReview: unknown` を許す）

判定は上から順に適用し、最初に当たったものに決める（相互排他）。

| 順 | 判定 | 条件 |
|---|---|---|
| 1 | unknown | `agentInvolved`・`delegated`・`verification` のいずれかが `unknown` |
| 2 | P0 | `agentInvolved: no` で、決定的な処理だけで完了した |
| 3 | other | `agentInvolved: no` で、人だけで実施・検証した。または Worker がいない（例: 他者の PR のレビューだけ） |
| 4 | T0 | `verification: no`（検証の記録がない）。または委託がなく、検証が実装と同じ主体だけで行われた。助言のレビューだけがあっても T0 |
| 5 | unknown | 委託があり、検証の記録があり、上位の構成を区別できない: `independentReview: unknown`（T2/T3 の可能性が残る）、または `independentReview: yes` かつ `specialistRole: unknown`（T3 の可能性が残る） |
| 6 | T3 | 委託があり、検証の記録があり、`independentReview: yes`、`specialistRole: yes`。同じ役割の並列は専門役割に数えない |
| 7 | T2 | 委託があり、検証の記録があり、`independentReview: yes`、`specialistRole: no` |
| 8 | T1 | (a) 委託があり、検証の記録がある（`verifierKind` を問わない）。または (b) 委託がなく、別セッション・別モデル・人が `role: verifier` として検証した（Organizer を Worker とみなす） |
| 9 | unknown | 1〜8 のどれにも当たらない（全件が必ずどれか 1 つに分類される。該当した記録は判定基準の見直し候補として件数を併記する） |

**境界ケース「委託なし＋別モデルの独立レビュー」**: そのレビューの `role` で決める。`verifier` なら T1 (b)、`advisory` だけなら T0。根拠は、T1 の canonical 定義が「生成する主体と検証する主体の分離」であり委託の有無ではないこと、かつ Reviewer ≠ Verifier（ARCHITECTURE）であること。`role` が記録されていなければ `verification: unknown` となり unknown に落ちる。

### 5.3 `unknown` と 0 の区別

- 分からない値は文字列 `unknown`。0・空配列・`false` で補わない（METRICS の欠測値方針と同じ）
- レビューをしなかったときは `reviews: []`、手戻りがなかったときは `rework.count: 0` を明記する。これが H1 の「取得」に数えられる
- 時刻が分単位以上で両方分かるときだけ `wallClockMs` を出す
- 集計は `unknown` を分母から除き、除いた件数を併記する

### 5.4 段階 2 の実装で決めたこと

本書に明記がなく、段階 2 の実装で決めた規則。採否は段階 2 の Human 判断に含める。

- **merge しなかった回の根拠レビュー**: `artifacts[]` に `state: merged` が 1 件もないとき（中断・失敗など）は、`role: verifier` のレビューのうち最後の 1 件を根拠レビューとする。merge した artifact があるのに、それを `target` に持つ `role: verifier` のレビューがないときは、§5.2 のとおり拒否する
- **`verifierKind` の有無**: `verification: yes` のときは必須、それ以外のときは書かない
- **`reviews: unknown` のとき**: 根拠レビューを特定できないので `verifierKind` は `organizer` か省略だけを許し、`independentReview` は `unknown` とする
- **`topologyEquivalent` の照合**: `topologyBasis` だけでは「決定的な処理だけ（P0）」と「人だけ（other）」、委託なしのときの「Worker がいない（other）」を区別できないため、`agentInvolved: no` では `P0` と `other`、`delegated: no` では表の判定値に加えて `other` を許す
- **`runtime` / `model` の形**: trace の `runtime`・`model` の項目に `role`（`organizer` / `worker`）を足した object の配列、または `unknown`
- **`artifacts[].state`**: `open` / `merged` / `closed` / `unknown`。受け入れは `merged` で判定する
- **`verifierKind: organizer`**: 根拠レビューがあるときは拒否する（§5.2 の表のとおり、`organizer` は根拠レビューがないときだけ）
- **閉じた enum の拡張**: `outcome`・`reviewerKind`・`artifacts[].state` などの enum に値を足すときは、`apiVersion` を上げ（例: `dat/v1alpha1` → `dat/v1alpha2`）、schema は旧版の値も受け付けて既存記録を書き換えない。値の削除や意味の変更は、旧版の記録を集計から分けて扱う
- **トークン形式の負例**: 接頭辞の検査は、テストの実行時に接頭辞と `EXAMPLE` を連結して確かめる。リポジトリにトークン風の文字列を残さないため、fixture には置かない
- **件数の整合**: `wallClockMs` は `startedAt`・`endedAt` が両方分かるときだけ数値を許し、両方分かるときは差との誤差 60 秒以内とする。`tasks.delegated` は `tasks.total` 以下
- **秘匿の検査値**: 文字列値の長さ上限は 200 文字、`outcomeReason` は改行を含めない。トークン形式は `ghp_`・`gho_`・`ghu_`・`ghs_`・`ghr_`・`github_pat_`・`sk-` の接頭辞と、英大文字・小文字・数字を含む 32 文字以上でエントロピー 4.0 bit/文字以上の連続文字列。いずれも誤検知・見逃しがあり得る簡易検査で、人の差分確認（§6）を置き換えない

### 5.5 `rework.sources`（出どころ別の回数、#321）

`rework.count` の内訳を出どころ別に記録する任意項目。目的は、「1 件あたりの rework が T0〜T3 の順に多い」という観察に、レビュー指摘から数えられやすいという測定の偏りが混ざっていないかを**探索すること**。構成の優劣や因果は結論しない（§9）。版の扱いは Human 判断 V1（[#321 のコメント](https://github.com/s977043/dynamic-agent-topology/issues/321#issuecomment-6831840569)、2026-11-12）に従う。

**現状の事実**

- 現行 schema（`schemas/run-observation.schema.json`、`apiVersion: dat/v1alpha1`）の `rework` は `count`（必須）と `triggers`（出どころの集合。回数を持たない）だけで、`additionalProperties: false`
- `triggers` を案内しているのは `skills/dat-observe/SKILL.md` だけで、`adapters/claude-code/RUN_OBSERVATION.md`・`adapters/codex/RUN_OBSERVATION.md` の項目表は `rework.count` だけ。`scripts/run_observation.py sum` は `rework.count` の合計だけを出す
- 起票者のローカル store の 257 件で `rework.triggers` と `taskDifficulty` の記入は 0 件（出どころ: #321 本文、2026-11-13 の `sum` 再実行）。store は非公開のため第三者は再現できず、DAT 側では**未確認**
- `rework.sources` を書いた記録はまだない（項目が存在しないため）

#### 5.5.1 形と出どころの値

```yaml
apiVersion: dat/v1alpha2
rework:
  count: 3
  sources:
    review-finding: 2
    ci-failure: 1
```

キーは次の 6 つの閉じた enum。値は 0 以上の integer か `unknown`。キーを書かない出どころは 0 回。表の順が判定順（§5.5.2）。

| 順 | 出どころ | 意味 |
|---|---|---|
| 1 | `spec-change` | その回に要件（目的・受け入れ条件）の変更が含まれる。変えたのが Human か否か、差し戻しを伴うか否かを問わない |
| 2 | `human-return` | Human が成果物を差し戻した（`reviewerKind: human` のレビュー指摘を含む）。その回に要件の変更は含まれない |
| 3 | `review-finding` | `reviews[]` に記録した Human 以外のレビューの指摘を直した |
| 4 | `ci-failure` | CI・テスト・validator の失敗を直した |
| 5 | `self-correction` | Organizer・Worker が自ら誤りに気付いて直した |
| 6 | `unknown` | 再委託・再レビューはあったが、出どころが分からない |

#### 5.5.2 論点 (1) 数える単位

- **規則**: 単位は現行の `rework.count`（修正のための再委託・再レビューの回数、§5.1）のまま変えない。修正のための再委託と、その修正結果に対する再レビューは、合わせて **1 回**（1 修正サイクル）と数える。再委託を伴わない再レビュー（例: 指摘への回答だけを確かめる再レビュー）も 1 回。各回に出どころを**ちょうど 1 つ**割り当て、複数当てはまるときは §5.5.1 の表の順で最初に当たったものに数える
- **理由**: 定義を「修正の回数」に変えると、既存の `rework.count` と意味がずれ、旧新の記録を同じ列で集計できなくなる。「再委託 + 再レビュー = 1 回」は、内訳を `count` と同じ単位にするための明確化。`dat/v1alpha1` の記録者が再委託と再レビューを別々に数えていたかは**未確認**で、記録を遡って直さない。判定順は、要件の変化と人の判断を先に置き、記録者の裁量が大きい `self-correction` を後に置く
- **許容の例**:
  - レビュー指摘 2 件と CI 失敗を、1 回の再委託でまとめて直した → `count: 1`、`sources: {review-finding: 1}`
  - 指摘修正のために再委託し、その結果を再レビューした → `count: 1`、`sources: {review-finding: 1}`（2 回ではない）
  - 指摘修正の再委託・再レビューを 1 回、その後 CI 失敗修正の再委託を 1 回 → `count: 2`、`sources: {review-finding: 1, ci-failure: 1}`
  - Worker が自分で誤りに気付き、再委託して直した → `count: 1`、`sources: {self-correction: 1}`
- **数えない例**: 再委託・再レビューを伴わない自己修正（同じ委託の中で Worker が書き直しただけ）は `count` にも `sources` にも数えない
- **拒否の例**: 1 回を 2 つの出どころに数え、内訳の合計が `count` を超える（`count: 1`、`sources: {review-finding: 1, ci-failure: 1}`）

#### 5.5.3 論点 (2) `count: 0` と集計の分母

- **規則**: `count: 0` は版・`sources`・`triggers` の有無を問わず「内訳既知（全出どころ 0）」で、出どころ別の集計の分母に**含める**（§5.5.8 の表）。`dat/v1alpha2` で `count: 0` のときは `sources` を書かないか、`{}`、または全値が 0 の object だけを許し、値が 1 以上・`unknown` の出どころがあれば拒否する
- **理由**: rework 0 件の記録を「内訳不明」として分母から外すと、1 件あたりの値が過大になる。0 回の内訳は自明なので、記録者に追加の記入を求めず、旧記録も書き換えずに含められる
- **例**: 許容 `count: 0`（`sources` なし）、`count: 0, sources: {}`。拒否 `count: 0, sources: {ci-failure: 1}`、`count: 0, sources: {unknown: unknown}`
- **`count` ≥ 1 で `sources` なし**: 「内訳なし」として出どころ別の集計の分母から除き、除いた件数を併記する（§5.3）。`count` の合計（既存の列）には従来どおり含める

#### 5.5.4 論点 (3) 値 `unknown` の意味と合計検査

- **規則**: 値 `unknown` は「その出どころが**少なくとも 1 回あった**が、回数が分からない」。存在そのものが分からない回は、キー `unknown`（出どころ不明）に数える。合計検査は値 `unknown` を下限 1 として数える
  - `count` が integer で全値が integer: 内訳の合計 = `count`
  - `count` が integer で値 `unknown` がある: integer の合計 + 値 `unknown` の個数 ≤ `count`
  - `count` が `unknown`: 1 以上の値か値 `unknown` を 1 つ以上含む `sources` だけを許す。`sources: {}` や全値 0 は「全出どころ 0」すなわち `count: 0` を意味し `count: unknown` と矛盾するため拒否する。合計検査はしない
- **理由**: 「存在も不明」を値 `unknown` に含めると、キーなし（0 回）と区別できず、合計検査ができない。存在不明はキー `unknown` が既に表せる
- **例**: 許容 `count: 3, sources: {review-finding: 2, ci-failure: unknown}`（2 + 1 ≤ 3）、`count: unknown, sources: {review-finding: 1}`。拒否 `count: 2, sources: {review-finding: 2, ci-failure: unknown}`（2 + 1 > 2）、`count: 3, sources: {review-finding: 1}`（全値 integer で合計不一致）、`count: unknown, sources: {}`
- **集計**: 値 `unknown` を 1 つでも含む記録、`count: unknown` の記録は出どころ別の集計の分母から除き、件数を併記する。下限値で補わない。キー `unknown`（出どころ不明）の integer 値は集計に含め、その合計を併記する

#### 5.5.5 論点 (4) 仮説と採否・保留条件

**H-src（探索的）**: rework のうち、**レビュー指摘（`review-finding`）として記録されたもの以外**だけで見ると、全体の rework に比べて T0 と T3 の差が小さい。「以外」には出どころ不明（キー `unknown`）を含むため、結果には不明の件数を必ず併記し、不明が多いときは保留する（判定順 4）。支持されても「レビュー指摘として記録されたもの以外では差が小さい」という観察にとどまり、測定の偏りが原因とは結論しない。交絡を見るため `taskDifficulty` も記録する。

- **測定期間**: `dat/v1alpha2` を最初に含む plugin 版の GitHub Release 公開時刻を T（UTC）とし、`endedAt` が [T, T + 90 日) の半開区間に入る記録を対象とする。`endedAt: unknown` の記録は期間に置けないので対象外とし、件数を併記する（現行 `sum` の `endedAt unknown` 表示と同じ考え方）
- **母集団**: 測定期間内の `dat/v1alpha2` 記録。`dat/v1alpha1` の記録は期間内でも含めない
- **分母 N_t**: 母集団のうち topology `t` で、§5.5.8 の表で「含める」に当たる件数（`count: 0` を含む）
- **記入率 F_t**: 母集団のうち topology `t` で `count` ≥ 1 の記録に占める、内訳が既知（含める）の記録の割合。T0 と T3 で別々に出し、判定には小さい方（min(F_T0, F_T3)）を使う
- **算式**: R_t = Σcount / N_t、S_t = Σ(count − `review-finding`) / N_t、U_t = Σ`sources.unknown` / Σcount、D = (S_T3 − S_T0) / (R_T3 − R_T0)
- **判定順**（上から順に適用し、最初に当たったものに決める）:

| 順 | 条件 | 判定 |
|---|---|---|
| 1 | N_T0 または N_T3 が 0（分母 0）、または `count` ≥ 1 の記録が T0・T3 のどちらかで 0 件（F_t の分母 0） | 保留 |
| 2 | N_T0 または N_T3 が 20 件未満 | 保留 |
| 3 | min(F_T0, F_T3) が 50% 未満 | 保留 |
| 4 | U_T0 または U_T3 が 20% を超える（出どころ不明が多く「指摘以外」を解釈できない） | 保留 |
| 5 | R_T3 − R_T0 ≤ 0.2（D の分母が 0 以下または小さすぎる） | 保留 |
| 6 | D ≤ 0.5 | 支持 |
| 7 | それ以外 | 反証 |

- **項目の採否**: 初回の測定期間の終わりに min(F_T0, F_T3) で決める。80% 以上で採用、50% 以上 80% 未満は adapter・skills の案内を直して 90 日延長、50% 未満で不採用。F_t の分母が 0 なら保留として 90 日延長する。延長は 1 回だけで、延長期間は [T + 90 日, T + 180 日) とし、延長後の判定（採否と H-src）は初回と延長分を**合算した** [T, T + 180 日) の母集団で行う。延長後も 80% 未満、または分母 0 のときは不採用とする（項目の削除は §5.4 の規則で `apiVersion` を上げて行い、Human が判断する）
- **閾値の根拠**: 20 件・20%・50%・80%・0.2・0.5・90 日は**目安で、DAT 側の Evidence はない**。20 件は段階 4（§8）の件数に合わせた。判定結果とともに閾値の妥当性も記録し、変えるときは判定前に本書を更新する

#### 5.5.6 論点 (5) `human-return` と `spec-change` の境界

- **規則**: 境界は「その回に要件（目的・受け入れ条件）の変更が含まれるか」。含まれれば、差し戻しを伴っても `spec-change`（§5.5.1 の判定順 1）。含まれなければ `human-return`。同じ 1 回を両方に数えない
- **理由**: 要件変更は依頼側の変化で、構成の影響から最も遠い。差し戻しと要件変更が同時のとき要件変更を優先すると、`human-return` を「要件が同じままの成果物の不足」に限定でき、定義表・規則・例が一致する。1 回 1 出どころにすることで合計検査（§5.5.4）を保てる
- **例**:
  - Human が「受け入れ条件 A を満たしていない」と差し戻した → `human-return: 1`
  - Human が途中で受け入れ条件 B を追加し、再委託した → `spec-change: 1`
  - Human が差し戻しの際に条件 B を追加し、1 回の再委託で両方を直した → `spec-change: 1`
  - 上の後、条件 A の不足だけを再度差し戻した → `spec-change: 1, human-return: 1`
  - Human のレビュー（`reviewerKind: human`）の指摘を直し、要件は変わらない → `human-return`（`review-finding` には数えない）
- **`humanInterventions` との関係**: 構造は変えない。`human-return` を書いた記録でも `humanInterventions` は従来どおり記録し、両者の件数の一致は検査しない

#### 5.5.7 `triggers` との関係

- `dat/v1alpha2` で `triggers` は**非推奨**。新しい記録では `sources` を使う
- `dat/v1alpha2` の記録で `sources` と `triggers` の併記は拒否する（集合と回数が食い違ったときにどちらを正とするか決められないため）
- `triggers` は出どころ別の集計に使わない。`triggers` だけの記録の扱いは、他の記録と同じく §5.5.8 の表で `count` によって決まる（`count: 0` なら含める、`count` ≥ 1 なら内訳なし）
- `dat/v1alpha1` の記録の `triggers` は従来どおり受理し、`sources` へ変換しない（集合から回数を推測しない）
- `triggers` の削除は別の版で行い、本設計では決めない

#### 5.5.8 記録の扱い（集計の分母）

新版の `sum` と H-src は、すべての記録を次の表の 1 行に当てはめ、上から順に最初に当たった行で扱う。旧記録は書き換えない。出どころ別の表には「含める」の件数と、除外の件数を理由別に必ず併記する。

| 順 | 版 | `rework` の内容 | 扱い | 除外の理由（併記） |
|---|---|---|---|---|
| 1 | 問わない | validator を通らない | 集計しない（`skipped invalid`） | invalid |
| 2 | 問わない | `count: unknown` | 除外 | count unknown |
| 3 | 問わない | `count: 0`（`triggers` の有無、`sources` なし・`{}`・全値 0 を問わない） | 含める（全出どころ 0） | — |
| 4 | `v1alpha1` | `count` ≥ 1（`triggers` の有無を問わない） | 除外 | 内訳なし（旧版） |
| 5 | `v1alpha2` | `count` ≥ 1、`sources` なし（`triggers` だけの記録を含む） | 除外 | 内訳なし |
| 6 | `v1alpha2` | `count` ≥ 1、`sources` に値 `unknown` がある | 除外 | 内訳の回数不明 |
| 7 | `v1alpha2` | `count` ≥ 1、`sources` の全値が integer で合計 = `count` | 含める | — |

H-src（§5.5.5）は、このうち測定期間内の `v1alpha2` の行だけを使う。一般の `sum` は全版を対象にするので、同じ store でも両者の件数は異なり、出力には対象の版と期間を明記する。混在 store では、既存の列 `known rework / waves` の分母（waves）は validator を通った全記録（`count: unknown` を含む）、分子（known rework）は `count` が integer の記録の件数、`rework total` はその `count` の合計（現行 `summarize` の実装）で、出どころ別の表の母集団は「含める」の記録で、**両者は一致しない**。出どころ別の値を既存の合計と直接比べない。

#### 5.5.9 互換性・移行・公開

版の規則は §5.4「閉じた enum の拡張」と同じ扱い（Human 判断 V1）。新 schema は `apiVersion` の `dat/v1alpha1` と `dat/v1alpha2` を受理し、`rework.sources` は `dat/v1alpha2` だけで許可する。

| 記録 \ validator | 旧 validator（`dat/v1alpha1` のみ） | 新 validator |
|---|---|---|
| `dat/v1alpha1`（`sources` なし） | 受理 | 受理（集計の扱いは §5.5.8） |
| `dat/v1alpha1` で `sources` あり | 拒否 | 拒否（`sources` は v1alpha2 のみ） |
| `dat/v1alpha2`（`sources` あり・なし） | **拒否**（`apiVersion` の const） | 受理 |
| `dat/v1alpha2` で `sources` と `triggers` を併記 | 拒否 | 拒否 |

**旧 `sum` の挙動**（`scripts/run_observation.py` の `summarize`、origin/main `a24004f` で確認）: validator を通らない記録を `skipped invalid: ...` と出して飛ばし、残りの記録で表を出したうえで exit 1 を返す。このため、旧版で新形式を含む store を集計すると、**新形式を除いた部分集計**の表が出る。

移行手順:

1. 同じ store を読むすべての読取側（`sum` を実行する環境、記録を読む共有先・スクリプト）を新版に上げる
2. 全読取側の更新が終わるまで、記録側は新形式（`dat/v1alpha2`）を書かない。記録側の plugin を先に上げた場合も、`apiVersion: dat/v1alpha1` で書き続ける
3. 2 の唯一の例外: 旧版しか使えない読取側が長く残るときは、新形式の記録を別の store（例: `--store` で別ディレクトリ）に分けて保存し、旧版にはその store を読ませない。新版の `sum` は両方の store を別々に集計し、結果を合算するときは §5.5.8 の扱いに従う。現行 CLI の `observationId` 重複検査（`save` と `sum`）は 1 つの store の中だけなので、合算の前に両 store を横断して `observationId` の重複を確認し、重複があれば合算を止め、該当する実記録を照合してどちらを残すか決めてから集計し直す
4. 全読取側の更新後に、新しい記録から `apiVersion: dat/v1alpha2` と `rework.sources` を書く
5. 既存の `dat/v1alpha1` 記録は書き換えない。出どころを遡って推測で埋めない
6. `skipped invalid` を 1 件でも出して exit 1 になった `sum` の表は、全件集計として扱わない（DOGFOODING や Issue へ転記しない）。exit code を見ずに表を使う処理があれば、移行前に exit code を確認するよう直す

これらと「旧 validator が新しい記録を拒否すること」は、実装 PR の移行ガイド（CHANGELOG）にも書く。

**版と公開の判定**: plugin の minor を上げることは Human 判断 V1 として記録する。ただし `docs/RELEASE_READINESS.md` は `scripts/` の validator・CLI の入力・出力・exit code を公開契約とし、依存され得る出力の変更を breaking の例に挙げている。`sum` の出力の追加・変更が breaking かどうかは本設計では決めず、実装 PR と release PR で変更後の出力契約・判定根拠・利用者の移行方法を確定して記録する。breaking または判定不能なら、同文書の規定（判定不能時は STOP して Human が判断、breaking を含む版は Human が公開）に従い、最終的な版の数字は release 時の判定に従う。

## 6. 保存先と秘匿

- **保存先（既定）**: リポジトリの外のディレクトリ（`--store` か環境変数 `DAT_OBSERVATION_STORE`、例: `~/.dat/observations`）に 1 ウェーブ 1 ファイルで置く。CLI は git の作業ツリー内（保存先かその祖先に `.git` がある場所）を拒否し、記録がコミットされないようにする
- 含めないもの: 秘密情報、private source、未サニタイズのプロンプト・会話本文、レビュー本文、個人環境の絶対パス。`humanInterventions` は種別と件数だけ、`outcomeReason` は 1 行の要約だけ
- **秘匿規則は記録の全項目に適用する**。列挙した項目に限らない。対象は `metadata.*`、`runtime` / `model` の識別（名前・版・モデル ID・effort）、`reviews[].target`・`decision`、`artifacts[].ref`・`state`、`outcomeReason`、`topologyBasis`、`humanInterventions[].kind`、将来追加する項目を含む、すべての文字列値
- 参考: `schemas/execution-trace.schema.json` でも `runtime.name`、`model.id`、`events[].actor`・`target`・`artifact` は制約のない自由文字列で、識別情報が入り得る。`RunObservation` の同形の項目も同じく自由文字列として扱う
- 識別情報（PR URL・ブランチ名・private リポジトリ名・導入先名・個人名など）は、private な導入先では DAT 側へ転記するときに仮名（例: `project-a`、`pr-1`）へ置き換える
- **サニタイズ済み**の定義: (1) 上の「含めないもの」を含まない、(2) 識別情報が公開済みのもの（public リポジトリ名・公開 PR 番号）か仮名だけである、(3) 段階 2 の validator を通る、の 3 つをすべて満たすこと
- **YAML の読込み規則**: validator（`scripts/validate_run_observation.py`）と CLI（`save` / `sum`）は同じ読込みを使い、重複した mapping key と YAML merge key（`<<:`）を含む記録を拒否する。読込みに失敗した記録は traceback ではなく `cannot read: ...` の診断を出して exit 1 になる
  - **互換性**: 以前の validator は merge key を展開して受理していた。merge key を使った記録は、`<<:` を使わず各 key を直接書いた通常の YAML に展開して書き直す
- **保存前**（保存先への書き込み時）: 記録者が validator を実行し、通らない記録は保存しない
- 保存と集計の CLI: `scripts/run_observation.py`（`save` / `sum`）。validator を通った記録だけを保存する。手順は各 adapter の `RUN_OBSERVATION.md`
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

段階 4 の判定結果: H1・H2 とも支持（どちらも 23 件・7 project）。記録は #223 の [H1](https://github.com/s977043/dynamic-agent-topology/issues/223#issuecomment-6391127012)・[H2](https://github.com/s977043/dynamic-agent-topology/issues/223#issuecomment-6426770476) のコメント。H2 の判定で見つかった見直し候補は §10 の U4・U5。

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
- U4: merge した artifact が複数ある記録で、検証の記録（`role: verifier`）をすべての merge 済み artifact に求めるか
  - 観測: H2 の判定（23 件）で、判定者 B が 1 件（T2）について迷った。根拠レビューの `target` は merge 済み artifact の 1 件だけで、同じ記録の他の merge 済み artifact には `role: verifier` のレビューがない。それでも validator は通る。2 判定者の分類は一致した（A は迷った点なし）
  - 論点: §5.2 は「受け入れた `artifacts[].ref` を `target` に持つ最後の 1 件」を根拠レビューとし、`scripts/validate_run_observation.py` も merge 済み artifact のどれか 1 件を `target` に持つレビューがあれば通す。このため、一部の artifact だけを検証した記録も `verification: yes` として T1 以上に分類される
  - 選択肢と影響:
    - (a) 現状維持: validator・既存記録・H2 の結果は変わらない。一部だけ検証した記録と全件を検証した記録を区別できないまま
    - (b) merge 済み artifact すべてに `role: verifier` のレビューを求める: validator に拒否の条件と負例を足す。該当する既存記録は validator を通らなくなり、記録の書き直しか集計からの除外が要る。分類が変わる記録があれば H2 を再判定する
    - (c) 拒否はせず、検証していない merge 済み artifact の件数を項目として残す: schema に項目を足すため `apiVersion` を上げる（§5.4 の enum 拡張と同じ扱い）。既存記録はそのまま通り、分類は変わらないので H2 の再判定は不要
  - 判断者と時期: Agent が案を作り独立レビューを経て、段階 2 と同じく判定基準・新項目の採否は Human が判断する。段階 5（次版公開）の前に決める
- U5: `specialistRole: yes` の根拠を、`topologyBasis` 以外の記録から確かめられるようにするか
  - 観測: H2 の判定で、判定者 B が 2 件（T3）について迷った。`specialistRole: yes` の根拠は `topologyBasis` の値にしかなく、`reviews[]` などから確かめられない。2 判定者の分類は一致した
  - 論点: §5.2 で `reviews[]` を正とするのは `verification`・`verifierKind`・`independentReview` だけで、`specialistRole` には導出元の記録がない。T3 と T2 の区別は記録者（Organizer）の判断に依り、判定者はその値を引き継ぐしかない。H2 の一致率は分類規則の明確さを示すが、この値の正しさは確かめていない
  - 選択肢と影響:
    - (a) 現状維持: validator・既存記録・H2 の結果は変わらない。T3 の判定は記録者の自己申告のまま
    - (b) 専門役割の実施を記録する項目（例: 役割名とタスク数）を足し、`specialistRole` をそこから導く: schema に項目を足し `apiVersion` を上げ、validator に食い違いの拒否を足す。既存記録は旧版として扱い、`specialistRole: yes` の記録（H2 では 2 件）は新しい項目がないため確かめられない。H2 の再判定は新版の記録で行う
    - (c) 項目は足さず、`specialistRole: yes` のときの根拠を adapter の記録手順に書くだけにする: schema・validator は変わらない。記録から確かめられない点は残る
  - 判断者と時期: U4 と同じ
