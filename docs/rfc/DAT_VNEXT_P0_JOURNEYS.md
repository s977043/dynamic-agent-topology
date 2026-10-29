# DAT vNext — P0 Journey 実行記録（offline）

> **非規範的な記録（未採用）。** [P0 Baseline](DAT_VNEXT_BASELINE.md) §3 の Journey A〜D を、model を起動せずに offline で 1 回ずつ実行した観測を残す。正本は既存文書と各スクリプトで、矛盾する場合は正本が優先する。関連: [RFC](DAT_VNEXT_RFC.md)、[親Issue #268](https://github.com/s977043/dynamic-agent-topology/issues/268)。

- 実行日時: 2026-10-29（UTC。記録作成 2026-10-29T10:29Z）
- 対象: `main` `257f836d7dab5987538d890db2be25c4752a00a6`
- 実行者: Claude Code の subagent 1 セッション（Claude Opus 5.5）。人の操作は含まない
- 実行環境: macOS（darwin）、`uv 0.11.8`、`uv run --no-project --python 3.12 --with-requirements requirements-ci.txt`（Python 3.12.13）、`PYTHONDONTWRITEBYTECODE=1`
- model 起動・課金: なし。`dat-select` / `dat-observe` の Skill は起動していない

## 0. この記録の読み方

| 区分 | 意味 |
| --- | --- |
| agent 実行による計数 | この agent が実行したコマンド数、exit code、編集ファイル数、エラー。人が同じ作業をしたときの値ではない |
| NOT MEASURED | 人の操作時間、active/wall time、認知負荷、迷い、余分な質問への反応。agent には測れない |
| 観測した事実 | 実行出力・ファイル内容から直接言えること |
| 解釈 | 観測からの推測。採用判断ではない |

各 Journey は n=1 の feasibility-only。構成の優劣や vNext の要否は結論しない。

## 1. Journey A — 選択（Runtime 未使用・手動解釈）

**Runtime 未使用・手動解釈。** `dat-select` を Runtime で起動すると model セッションの起動になるため、[SKILL.md](../../skills/dat-select/SKILL.md) の手順を agent が手で当てはめた。

読んだファイル（agent 実行による計数）: 3 件（[skills/dat-select/SKILL.md](../../skills/dat-select/SKILL.md)、[policies/routing/R0_dynamic.yaml](../../policies/routing/R0_dynamic.yaml)、[policies/escalation/E0_default.yaml](../../policies/escalation/E0_default.yaml)）。

R0 の分岐（上から順）: (1) `complexity: low, ambiguity: low` → T0、(2) `existingEvidence: strong, risk: medium` → T1、(3) `risk: high` → T2。E0 の上限: `maxTopology: T2`、`maxAgents: 3`、`maxTransitions: 2`。

| 仮 Task（公開用の架空） | 読み取った入力 | 結果 | 該当した分岐 | 保留 | 追加入力が必要だった項目 |
| --- | --- | --- | --- | --- | --- |
| low-complexity: README の誤字 1 か所を直す | complexity low、ambiguity low | T0-single-agent | (1) | なし | なし |
| unknown-input: 「どこかの処理を速くしたい」 | complexity・ambiguity・risk・existingEvidence すべて不明 | 選択保留 | なし | あり | complexity、ambiguity、risk、existingEvidence |
| medium-risk: 共有ユーティリティの入力検証を変更。既存テストが十分 | complexity medium、ambiguity low、risk medium、existingEvidence strong | T1-worker-verifier | (2) | なし | なし（existingEvidence を「strong」と読む判断は記録者に依る） |
| high-risk: 認可チェックの変更 | complexity medium、risk high | T2-worker-reviewer-verifier（E0 上限内） | (3) | なし | なし |

観測した事実:
- 4 件中 3 件で分岐が決まり、1 件は SKILL.md 手順 2 どおり「選択保留」になった。
- R0 には `low` / `medium` / `strong` などの値の定義・判定基準がない。入力値は記録者が読み取った。
- R0 には既定（fallback）分岐がない。例: complexity medium・risk medium かつ existingEvidence が weak/unknown の Task はどの分岐にも当たらず保留になる（追加の仮ケースとして手で確認）。complexity low・ambiguity low なら (1) で T0 になる。
- 分岐は上から当てはめるため、complexity low・ambiguity low・risk high の Task は (1) で T0 になり、(3) に届かない（手で確認）。

解釈（痛点の候補）:
- G-A1: 入力値の尺度がなく、同じ Task でも記録者によって分岐が変わりうる。H2（判定の忠実性）の再現性に影響する可能性。
- G-A2: 低複雑・高リスクの Task が T0 になる順序は、意図した設計か未確認。正本の変更は本記録の範囲外。
- G-A3: 保留は正しく起きたが、どの値なら決まるかの例は SKILL.md・policy にない。

限界: model を使っていないため、実際の `dat-select` の返答、余分な質問、所要時間、ユーザー操作数は NOT MEASURED。

## 2. Journey B — 観察と保存

サンプル（完了・失敗・中断）の RunObservation 3 件を、架空の値・仮名 `sample-project` で作った。store はリポジトリ外の scratch ディレクトリ（`~/.dat` には書いていない）。

手順と結果（agent 実行による計数）:

| 段階 | コマンド | 結果 |
| --- | --- | --- |
| 1 回目 | `validate_run_observation.py` ×3、`run_observation.py save` ×3、`sum` ×1 | validate 3 件とも exit 1、save 3 件とも exit 1（NG）、`sum` exit 0（`observations: 0`） |
| 修正 | 3 ファイルから `verifierKind: none` の 1 行を削除 | 編集 3 ファイル × 1 行 |
| 2 回目 | 同じ 7 コマンド | validate 3 件 exit 0、save 3 件 exit 0、`sum` exit 0（`observations: 3`、T0 の completed/failed/interrupted 各 1、rework total 2、`endedAt unknown ... : 1`） |
| 負例 | リポジトリ内の `--store` へ save | exit 2、`store must be outside the DAT repository` |
| 負例 | 同じ `observationId` を再 save | exit 1、`observationId already recorded` |

- 手入力した項目（`key: value` の行数）: 完了 31、失敗 31、中断 33。
- NG: 6 回（validate 3 + save 3）、原因は 1 種類。`verification: 'no'` のときに `verifierKind: none` と書いた入力側の誤り。エラー文は `topologyBasis/verifierKind: 'none' is not one of [...]`。
- 再試行: 記録ごとに 1 回（計 3）。
- save の `OK` と一緒に `unknown:` の項目一覧が出た（完了・失敗: `model, usage.totalTokens, usage.costUsd`。中断: 加えて `endedAt, wallClockMs, taskDifficulty`）。
- `sum` は件数が 0 のレビュー表も見出しだけ出力した。

観測した事実:
- 「検証なしなら `verifierKind` を書かない」は [RUN_OBSERVATION_DESIGN.md](../RUN_OBSERVATION_DESIGN.md) §5 にあるが、[SKILL.md](../../skills/dat-observe/SKILL.md) と記録例（`verification: 'yes'` の T1 例のみ）からは読み取れなかった。schema のエラー文は「書かない」ことを示さない。
- 3 件で 31〜33 行の手入力が必要だった。T0・レビューなしでも項目数は大きく減らない。

解釈（痛点の候補）:
- G-B1: T0 / 検証なしの記録例がなく、初回に schema NG を起こしやすい。
- G-B2: 手入力量が多く、日常記録の負担になりうる（人の負担は NOT MEASURED）。
- G-B3: NG 時のエラーが「値を省く」修正方法を示さない。

限界: 架空の値。秘匿確認は agent が全文字列を目視した。人の作業時間・編集回数は NOT MEASURED。

## 3. Journey C — 比較と判断（凍結 Artifact は参照のみ）

コマンド（agent 実行による計数、すべて exit 0）: `validate_experiment_freeze.py`（`Freeze completed: revision=3`）、`audit_exp001_completed_snapshot.py`（`33 blobs intact`）、`validate_pilot.py ... --require-complete`（`expected_runs=18`）、`summarize_experiment.py` を 18 件版と 16 件版で各 1 回。計 5 コマンド。実行後の `git status --short` は空（凍結ファイルへの書き込みなし）。

[DECISION.md](../../experiments/EXP-001-t0-vs-t1/DECISION.md) との照合:

| 項目 | DECISION.md | 今回の出力 | 一致 |
| --- | --- | --- | --- |
| Run 数 | 18 | evaluation.yaml 18 ファイル、T0 `runs: 9` / T1 `runs: 9` | 一致 |
| paired blocks | 9 | summarizer は block を出力しない。ファイル名（3 Scenario × r01〜r03 × T0/T1）から 9 と数えた | 出力では照合不能、ファイル名で一致 |
| 平均 Token（18 件） | 68,022.0 / 150,080.67 | `68022.0` / `150080.66666666666` | 一致（丸め） |
| 平均 wall clock（18 件） | 44540.11 / 55777.78 | `44540.11111111111` / `55777.77777777778` | 一致（丸め） |
| 16 件版 Token | 65642.125 / 145717.0 | 同値 | 一致 |
| taskSuccessRate / regressionRate | 1.0 / 0.0 | 同値 | 一致 |
| executionContext | codex | `runtime: codex`、`effort: high`、model 1 種 | 一致 |

比較に必要で、summarizer の出力に欠けているもの（観測した事実）:
- block 別 paired delta と block 数。DECISION.md も「repo 外の読み取り専用スクリプトで作成し、手で転記した」と書いている。
- T1/T0 の比（2.206 など）。出力 JSON から手で計算する必要がある。
- Scenario 別の集計は、ファイルの glob を変えて別々に実行する必要がある。
- 判断基準（DECISION.md の 4 基準）との照合は出力にない。

解釈（痛点の候補）:
- G-C1: paired 比較の中心である block 単位の差が CLI で再現できず、手作業の転記に依存する。H3（再現可能な比較）の弱点候補。
- G-C2: 16 件版のような除外は shell の `grep -v` に依存し、除外理由は出力に残らない。

限界: 既存結果の再集計で、新しい Run ではない。人が DECISION を読み解く時間は NOT MEASURED。

## 4. Journey D — 新規プロジェクトへの導入

`examples/brownfield/.dat/` を scratch の一時ディレクトリにコピーし、コピー側だけを変更した（agent 実行による計数）。

| 手順 | 内容 | exit |
| --- | --- | --- |
| 1 | `.dat/` をコピー | — |
| 2 | floating のまま `validate_project.py --project <copy> --dat-root <repo>`（`--require-pinned` なし） | 0（WARNING 5 件） |
| 3 | floating のまま `--require-pinned` 付き | **1**（`ERROR: dat.lock.yaml: pinMode is floating`） |
| 4 | コピー側の `dat.lock.yaml` を `pinMode: pinned` に変え、`revision: "257f836..."`（repo の HEAD）を追加 | — |
| 5 | `--require-pinned` 付きで再実行 | **0**（WARNING 4 件） |

- 編集したファイル: 1（`dat.lock.yaml`。1 行変更 + 1 行追加）。設定の手順: 4（コピー、検証、lock 編集、再検証）。validator 実行 3 回。
- 元の `examples/brownfield/` との `diff -r` は lock の 2 行だけ。example 本体は変更していない。
- 残った WARNING（観測した事実）: `runtimes.yaml` の manual `configPath`（`AGENTS.md`・`CLAUDE.md`・`GEMINI.md`）がコピー先に存在しない 3 件、`.gitignore` がない 1 件。いずれも exit には影響しない。
- validator は pinned revision を `--dat-root` の HEAD と照合する実装になっている（[validate_project.py](../../scripts/validate_project.py) の `rev-parse` 比較）。不一致の負例は今回実行していない。

解釈（痛点の候補）:
- G-D1: example をそのままコピーすると、存在しない configPath の WARNING が 3 件出る。初回導入者には「失敗か」の判断材料が増える（人の受け止めは NOT MEASURED）。
- G-D2: pin の手順は QUICKSTART §5 で完結しているが、`--require-pinned` を付けないと floating でも exit 0 になる。

限界: 使い捨ての空ディレクトリで、git リポジトリ・実 consumer・Runtime Binding の実効性は確かめていない。

## 5. 痛点候補の一覧（未採用・優先度未決）

| ID | Journey | 観測した事実 | 解釈 |
| --- | --- | --- | --- |
| G-A1 | A | R0 に入力値の尺度がない | 判定の再現性が記録者に依存しうる |
| G-A2 | A | 分岐順で低複雑・高リスクが T0 になる | 意図の確認が必要 |
| G-A3 | A | 保留時にどの値なら決まるかの例がない | 追加入力の往復が増えうる |
| G-B1 | B | 検証なしの記録で `verifierKind: none` が NG（6 回） | 記録例・エラー文の不足 |
| G-B2 | B | 1 件 31〜33 行の手入力 | 日常記録の負担 |
| G-C1 | C | summarizer が paired block / 比を出さない | 比較の再現が手作業に依存 |
| G-C2 | C | 除外条件が shell 依存で出力に残らない | 感度分析の再現性 |
| G-D1 | D | example コピーで WARNING 4〜5 件 | 初回導入の判断負荷 |

優先順位付け（Baseline §6 の 3 つ目）は、人の計測と利用価値の確認を経てから行う。この表は vNext（B 案）の必要性を示すものではない。現行 A の局所改善（記録例の追加、エラー文、summarizer の出力追加）で足りる可能性も同じく未検証。

## 6. 範囲外・未実施

- 人の操作時間・active/wall time・認知負荷・操作数: NOT MEASURED。
- `dat-select` / `dat-observe` の Runtime 起動: 未実施（model 起動にあたるため）。
- スクリプトの不具合: 今回の実行範囲では、exit code・エラー文が `--help` と文書の記述どおりで、不具合と判断したものはない。
