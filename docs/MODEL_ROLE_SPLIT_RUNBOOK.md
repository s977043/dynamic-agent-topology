# モデル役割分担の比較検証の実行手順書（#220）

状態: **非規範的な実行手順書（未採用・独立レビュー前）**。実験開始・model 起動（予備検証を含む）・予算消費・Runtime 変更・`.claude/` 設定変更の許可ではありません。予算の承認と、課金が発生する model 起動は Human（Operator）専権で、Agent は代行しません（[AGENT_HARNESS.md](AGENT_HARNESS.md) の自律境界）。`experiments/`、`schemas/`、`topologies/`、`roles/`、`adapters/`、EXP-001 の Frozen file は本書で変更しません。現時点の効果は **INCONCLUSIVE**（実測 0 件）です。

- 起案日: 2026-10-24 / 基準: origin/main `e48cb0e`
- 対象: [Issue #220](https://github.com/s977043/dynamic-agent-topology/issues/220) の実行計画 G0〜G4 を、[MODEL_ROLE_SPLIT_DESIGN.md](MODEL_ROLE_SPLIT_DESIGN.md)（以下「設計案」）に沿って実行する手順。G5（設定変更の提案）は手順の終点として触れるだけ
- 一次ソース: 設計案、Issue #220 の 2026-10-21 実行計画コメント、[AGENT_HARNESS.md](AGENT_HARNESS.md)、[EXPERIMENTS.md](EXPERIMENTS.md)、[METRICS.md](METRICS.md)、[RUN_OBSERVATION_DESIGN.md](RUN_OBSERVATION_DESIGN.md)、[HARD_TASK_T0_T1_PREREGISTRATION.md](HARD_TASK_T0_T1_PREREGISTRATION.md)（手順の書式の参考）
- 本書は設計案の判断を変えません。設計案と矛盾する場合は設計案を優先し、本書を直します

## 0. 実行者の区別

| 記号 | 実行者 | できること |
|---|---|---|
| **[H]** | Operator（Human） | 予算の承認、追加課金ゼロの実環境確認、model 起動（予備検証・本 Run）、介入、Human 専権の merge |
| **[A]** | Agent（オーガナイザー） | 文書・事前登録ファイル・検査スクリプトの起案、model を起動しない機械的確認、集計、Issue への記録、独立レビューの手配 |
| **[R]** | 独立 Reviewer | 作成者と別セッション（別モデル推奨）。事前登録と結果のレビュー、違反分類の判定、Judgment |

Agent は [H] の手順を代行しません。[H] の手順の結果が Issue に記録されるまで、次の手順に進みません。

## 1. 比較条件

設計案 §4 のとおり、arm A と arm B だけを比べます。C（Haiku read-only 探索委任）と D（高リスク時のみ Opus escalation）は本手順の範囲外です。

| 項目 | arm A | arm B |
|---|---|---|
| Topology | T0 Single Agent | T0 Single Agent（A と同一） |
| メインのモデル | 現行の既定（実効値は手順 G0-2 で記録） | Sonnet（具体 model ID は U3） |
| Effort・tool・permission・prompt・Runtime / CLI 版 | 固定 | A と同一 |
| subagent | 使わない | 使わない |

- A と B の差分は model binding だけ。Run の前に設定差分を機械的に確認します（実行前 Gate 3）。
- paired block 内で A/B の順序を counterbalance し、fresh workspace / fresh session で実行します。
- task / fixture・閾値・budget は事前登録ファイル（§4）で固定し、結果を見て変えません。

## 2. 測定項目

設計案 §6 の指標をそのまま使い、新しい canonical metric を追加しません。

| 指標 | 取得方法 | 取得者 |
|---|---|---|
| quality（verified success） | task ごとの Verification command と、生成 Agent 以外の Evaluator による AC 照合 | [A] 集計 / [R] 照合 |
| false accept | Agent の完了申告と AC 判定の突き合わせ | [A] |
| negative oracle 違反 | 事前登録した check の実行結果 | [A] |
| boundary violation | Runtime の tool call 記録（trace）と workspace 差分を許可範囲と照合。完全性条件を確認できない Run は NOT_TESTED | [A] 集計 / [R] 迷う事例を判定 |
| token / cache | provider usage の input / output、cache read / write。課金換算は #162 の定義 | [A]（[H] が取得した usage から） |
| elapsed | Harness の単調時計 | [A] |
| intervention | Operator の介入回数と種類 | [H] 記録 |
| activation trace | 実際に応答したモデル ID と arm 宣言の一致 | [A]（trace から） |
| 停止理由 | 完了・timeout・上限到達・abort | [H] / [A] |

- 取得できない値は 0 で埋めず欠測とします。失敗・中断・timeout Run も除外せず保持します。
- activation が宣言と一致しない、または確認できない Run は効果の解釈から除き、欠測として arm 別に件数を報告します。

## 3. 記録先

| 対象 | 記録先と形式 |
|---|---|
| 事前登録 | 事前登録ファイル（§4）を commit し、その blob hash を Issue #220 に記録する |
| 実行前 Gate の結果 | Issue #220 のコメント。確認方法・日時・結果（PASS / FAIL / NOT_TESTED）。secret・trace 本文は載せない |
| 予備検証（設計案 §8） | Run Artifact を repo に残さない。実施日時・Runtime / Model / Effort・確認結果だけを Issue #220 に記録する |
| 本 Run | 既存の `ExecutionTrace`（`schemas/execution-trace.schema.json`）と `RunEvaluation`（`schemas/evaluation.schema.json`）の形式で記録する。`metadata.experiment` 等に入れる experiment Artifact の追加は、事前登録と同じ別 PR で行う |
| 結果の集計と Judgment | Issue #220 のコメント（§7 の判定、欠測件数、独立 Reviewer の runtime・model・session ID・根拠リンク） |
| 準備作業のウェーブ | 通常の `RunObservation`（dat-observe）で記録してよい。ただし実験 Run の代わりにしない（`RunObservation` は日常開発のウェーブ用で、`experiment`・`condition`・`blockId` を持たない） |

## 4. 手順

### G0: 現況の確認（model を起動しない）

1. [A] PR #206・#208・#194 の状態と、設計案の基準以降の main の変更を確認し、本書と矛盾がないかを Issue #220 に記録する。
2. [H] 利用環境の `claude` CLI の版と、arm A の現行既定モデルの実効値・arm B に使う Sonnet の model ID が利用可能かを確認し、Issue #220 に記録する（U3）。Agent はこの確認のために model を起動しない。

### G1〜G2: 事前登録

3. [A] U1・U2・U4・U5 の確定案を起案する（推奨案と採らなかった案、根拠を書く）。task / fixture の条件は設計案 §5、閾値の項目は設計案 §5「判定閾値」に従う。
4. [A] 確定値を 1 つの事前登録ファイルにまとめる。含める項目: arm A・B の model ID、task 集合と想定難度、AC と Verification command、negative oracle の check、task ごとの許可範囲と trace の完全性条件、δ_q・δ_c・最小 paired block 数・欠測率上限・activation 未確認率上限、budget（総 Run 数上限、1 Run あたり token / wall clock の hard limit、自動継続の上限回数）、counterbalance の順序、介入規則。
5. [A] 事前登録ファイルを commit し、その blob hash を確定して Issue #220 に記録する（レビュー対象の固定）。
6. [R] 手順 5 の hash と一致するファイルを独立レビューする。必須指摘があれば [A] が直し、新しい hash を確定・記録して手順 6 をやり直す。
7. [A] 必須指摘 0 のレビューを受けた hash のファイルを含む PR を、AGENT_HARNESS.md の自律境界に従って merge する。
8. [A] merge 後の main で事前登録ファイルの blob hash を計算し、レビュー済みの hash と一致することを確認して Issue #220 に記録する。この時点で事前登録が成立し、Gate 4 が PASS になる。以後、結果を見て書き換えない。

手順 7・8 は G3 のどの手順（実行承認・予備検証）よりも前に終える。

### 実行前 Gate の一覧

| Gate | 内容 | 判定者 | PASS が必要な時点 |
|---|---|---|---|
| 1 | 追加課金ゼロ: 既存契約の範囲内で追加 API 課金が発生しない（または無効化されている）ことを実環境で確認し、確認方法と日時を記録。利用枠の残量と追加請求の有無を混同しない | [H] | 予備検証の前（model 起動前） |
| 2 | activation 計測の成立: 利用 Runtime の trace / usage に応答モデル ID と tool call が出る仕様・設定であることを、model を起動せずに確認（CLI の出力形式・設定の確認） | [A] 確認案 / [H] 実環境で確定 | 予備検証の前（model 起動前） |
| 3 | A/B の設定差分が model binding だけであることの機械的確認 | [A] | 予備検証の前（model 起動前） |
| 4 | 事前登録の成立: レビュー済み hash と merge 後の blob hash の一致（手順 8） | [A] 照合 / [R] レビュー | 手順 8 の完了時（G3 の開始前） |

1 つでも FAIL / NOT_TESTED なら model を起動せず、状態を Issue #220 に記録して停止する。

**再確認の範囲**（ここだけで定める）:

| 時点 | 再確認する Gate | 実行者 |
|---|---|---|
| 本 Run の実行承認（手順 13）の前 | Gate 1〜4 すべて（Gate 4 は main 上の blob hash の再計算と照合） | [H] Gate 1・2 / [A] Gate 3・4 |
| 本 Run の各 paired block の前 | Gate 3 と Gate 4 の hash 照合 | [A] |

再確認で 1 つでも PASS でなければ、§5 の停止条件として扱う。

### G3: 予備検証と実行承認

順序: 事前登録 PR の merge と hash 照合（手順 7・8、Gate 4）→ Gate 1〜3 の PASS → budget と実行の承認 → 予備検証 → 予備検証の判定 → 再確認 → 本 Run の実行承認 → 本 Run。

9. [H] Gate 1 を確認して記録する。[A] は Gate 2・3 の結果を記録し、[H] が Gate 2 を実環境で確定する。Gate 4 は手順 8 で PASS 済みであることを確認する。
10. [H] 事前登録した budget（hash 記録済みのファイルの上限）を承認し、予備検証の実行を明示的に承認したことを Issue #220 に記録する。承認の記録には事前登録の hash を書く。
11. [H] **予備検証**（設計案 §8）: 1 task を A/B で 1 回ずつ実行する。
12. [A] 予備検証の結果から、activation trace（arm 宣言との一致）・token・cache・elapsed・tool call が欠測なく取れたかを判定し、PASS / FAIL を Issue #220 に記録する。結果は効果推定に使わない。FAIL なら本 Run に進まず、設計案の見直しを Issue #220 で提起する。
13. [H] 手順 12 が PASS で、上の「再確認の範囲」の確認が済んでいることを確かめ、本 Run の実行を明示的に承認したことを、事前登録の hash と budget とともに Issue #220 に記録する。承認の記録がない限り本 Run を始めない。

### G3: 本 Run

14. [H] 事前登録の順序で paired block を実行する。各 block の前の再確認は「再確認の範囲」に従う。block 内で Runtime・CLI 版・Effort・tool 版を固定し、記録する。介入は事前登録の介入規則の範囲で行い、arm 別に記録する。
15. [A] 各 Run の後に `ExecutionTrace` / `RunEvaluation` を作り、§2 の指標を記録する。activation 不一致を検出したら §5 の停止条件として [H] に報告する。

### G4: 判定

16. [A] 設計案 §7 の判定規則で集計案を作る。最小 paired block 数に満たない場合は feasibility-only とし、効果を主張しない。
17. [R] exact head・差分・Evidence を評価し、PASS / FAIL / INCONCLUSIVE の Judgment を Issue #220 に記録する。
18. PASS でも既定化しない。設定変更（`.claude/`・`CLAUDE.md`・`AGENTS.md`・Harness rules）は G5 として別 PR で起案し、Human が merge する。

## 5. 停止条件

次のいずれかに当たったら、[H] は Run を止め、[A] は進行を止めて状態と根拠を Issue #220 に記録します。再開は事前登録の再登録（新しい版と hash の記録）を要します。

- budget の上限（総 Run 数、1 Run の token / wall clock、自動継続回数）に到達した
- 追加課金の兆候があった、または追加課金ゼロの確認が失効した（契約・設定の変更など）
- Runtime・CLI 版・Effort・tool 版が block 内で変わった
- activation trace が arm 宣言と一致しない、または確認できない Run が出た（その Run は欠測として保持する）
- 欠測率・activation 未確認率が事前登録の上限を超えた
- [AGENT_HARNESS.md](AGENT_HARNESS.md) の STOP 条件（Gate 判定不能、予算・Operator 不明、secret の疑い、permission による拒否、Human 専権の操作が必要など）に当たった

## 6. 未確定事項

設計案 §10 の U1〜U6 は本書でも未確定です。手順 3 で U1・U2・U4・U5 を、手順 2 で U3 を確定します。U6（C/D の導入判断）は A/B の Judgment の後に別の事前登録で扱います。
