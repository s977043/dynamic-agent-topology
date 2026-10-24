# 難度の高い Task の較正 Run 手順書（最初の 25 Run）

状態: **実行キットの起案（未実行）**。本書とキットは model 起動の許可ではありません。較正 Run の起動は Operator（Human）が行います。承認範囲は [#244](https://github.com/s977043/dynamic-agent-topology/issues/244) の 2026-10-25 の記録どおり「最初の 5 候補 × n_cal 5 = 25 Run」に限ります。

- 正本: [HARD_TASK_T0_T1_PREREGISTRATION.md](../HARD_TASK_T0_T1_PREREGISTRATION.md)（blob `52b4a585…`）§2・§5・§6・§9、[CANDIDATES.yaml](CANDIDATES.yaml)（blob `aad6f236…`）の initial の order 1〜5
- キット: [`scripts/hard_task_calibrate.py`](../../scripts/hard_task_calibrate.py)、テスト [`scripts/test_hard_task_calibrate.py`](../../scripts/test_hard_task_calibrate.py)
- 本書は事前登録・候補表・EXP-001 の Frozen file を変えない。食い違いがあれば正本が優先する

## 1. キットが固定するもの

| 項目 | 値 | 根拠 |
|---|---|---|
| Runtime | `codex-cli 0.160.1`（`codex --version` と trace の `cli_version` を照合） | U1、#244 の手順 5 の記録 |
| Model / Effort | `-m gpt-6.1-sol -c model_reasoning_effort=high` を起動時に明示。`--ignore-user-config` でローカルの既定（gpt-6-luna / medium）を読まない。グローバル設定は変えない | U1、#244 |
| Topology | T0 のみ（較正に T1 を使わない） | 設計案 §5 の 4 |
| 対象 | initial の order 1〜5、各 5 回。Run ID は `HTC-<order>-n<k>` | §5・§6、#244 の承認範囲 |
| 実行順 | rep 単位の巡回（全候補の n1、次に n2…）。時刻による変動を候補間で偏らせないため | キットの設計判断 |
| fresh workspace / session | Run ごとに新しいディレクトリへ clone し revision に detach、remote・ref を消して gc。修正 commit が workspace から到達できないことを確認する。Run ごとに新しい `codex exec` | 設計案 §6、§3 の 2 |
| AC | Worker の終了後、workspace の複製に修正 commit のテストファイルを重ね、候補表の `command` を実行（exit 0）。AC のファイルは Run 開始前にメモリへ読み、clone は消す | §3 の 2・5 |
| negative oracle | `failingBeforeFix` の各テストを `-v` で実行し、すべて `... ok` であること（skip・未実行は不合格）。テストファイル自体は修正 commit の blob で上書きするので、Worker のテスト編集は AC に影響しない | 候補表の `negativeOracle` |
| token | trace の最終 `total_token_usage` の `input_tokens + output_tokens`（cached input を含む。EXP-001 と同じ定義） | §6、DECISION.md |

## 2. 止める条件（キットが自動で止める）

| 条件 | 動作 |
|---|---|
| 事前登録・候補表の blob が記録値と違う | 起動前に停止 |
| `codex --version` が `codex-cli 0.160.1` でない | 起動前に停止 |
| 結果ディレクトリ（`<work-root>/HTC-…`）が 1 つでも既にある | 起動前に停止（上書きしない）。`--skip-existing` を付けたときだけ、既存の Run に触れずに飛ばす |
| `<work-root>/.calibration.lock` がある | 重複起動として停止。別の実行がないと確認してから Operator が手で消す |
| work root が DAT repo の中 | 停止 |
| trace の model / effort が `gpt-6.1-sol` / `high` 以外、または `cli_version` が違う | その Run を `control-deviation` として残し、バッチを停止（§2 の control deviation） |
| 1 Run の経過時間が `--timeout-s` を超えた | プロセスを kill し `aborted-timeout` として残す。次の Run へ進む |
| 1 Run の token が `--max-run-tokens` を超えた | 記録した後バッチを停止（token は Run の終了後にしか分からないため、事後の検出） |
| 使用済み token + `--max-run-tokens` が `--budget-tokens` を超える | 次の Run を始めずに停止 |

## 3. Operator の手順

前提: 事前登録の成立（§9 手順 1）と候補表の固定（手順 3）は #244 に記録済み。手順 4（25 Run の予算承認）は 2026-10-25 に記録済み。

1. DAT repo の外に、空の作業ディレクトリを決める（例: `~/dat-runs/hard-task-cal-1`。存在しないパスを指定する）。
2. 本 PR の merge 後の main で、dry-run を実行して手順と出力を確認する（model は起動しない）:

   ```bash
   python3.12 scripts/hard_task_calibrate.py plan
   python3.12 scripts/hard_task_calibrate.py run --dry-run --work-root ~/dat-runs/dry --prompt <PROMPT> \
     --timeout-s <TIMEOUT_S> --max-run-tokens <MAX_RUN_TOKENS> --budget-tokens <BUDGET_TOKENS>
   python3.12 scripts/hard_task_calibrate.py summarize --work-root ~/dat-runs/dry
   ```

3. 本番（25 Run。コマンド 1 つ）:

   ```bash
   python3.12 scripts/hard_task_calibrate.py run --work-root ~/dat-runs/hard-task-cal-1 --prompt <PROMPT> \
     --timeout-s <TIMEOUT_S> --max-run-tokens <MAX_RUN_TOKENS> --budget-tokens <BUDGET_TOKENS>
   ```

   `<PROMPT>`・`<TIMEOUT_S>`・`<MAX_RUN_TOKENS>`・`<BUDGET_TOKENS>` は §5 の未確定事項で、キットは既定値を持たない。決まった値と prompt の SHA-256（各 `run.json` の `promptSha256`）を #244 に記録してから起動する。
4. exit code が 0 なら 25 Run 完了。2 なら標準エラーの `STOP:` の理由を #244 に記録し、再開は理由を解消した後に `--skip-existing` で行う（既存の Run は作り直さない）。
5. 集計を保存する: `python3.12 scripts/hard_task_calibrate.py summarize --work-root ~/dat-runs/hard-task-cal-1 --output ~/dat-runs/hard-task-cal-1-summary.json`
6. 集計の `m`、`updatedCalibrationEstimate`（5 × 44 × 68,022 × m）、`remainingCalibrationEstimate`（残り 39 候補）、各候補の `verifiedSuccesses` と `band` を #244 に記録する（§6）。残り 39 候補の較正は Operator の再承認まで始めない。

## 4. 保存されるもの

`<work-root>/HTC-<order>-n<k>/` に Run ごとに保存する。

| ファイル | 内容 |
|---|---|
| `run.json` | 宣言値、起動コマンド、上限、prompt の SHA-256、trace から読んだ cli_version・model・effort・`total_token_usage`、totalTokens、wallClockMs、exit code、AC と negative oracle の結果、status |
| `prompt.md` | 実際に渡した prompt |
| `codex-events.jsonl` / `codex-stderr.log` | `codex exec --json` の出力 |
| `session-trace.jsonl` | Codex が保存した session trace の複製（実効値の照合元） |
| `workspace/` | Worker の作業後の状態 |
| `grade/`・`ac-output.txt`・`oracle-output.txt` | AC の実行結果 |

`summarize` は `band` を、5 回すべて `completed` の候補だけに付ける（0/5 は主集合から除外、1〜2/5 は hard、3/5 以上は not-hard）。timeout・停止を含む候補は `INCOMPLETE` とし、成功率を推測で埋めない。trace と結果は秘密や個人情報を確認するまで repo に commit しない（AGENTS.md）。

## 5. 未確定事項（キットは推測で埋めない）

| 項目 | 状態 |
|---|---|
| T0 の prompt（Worker に何を渡すか。課題の説明として修正 commit の件名などを渡すか） | 事前登録は「修正 commit とテストを渡さない」ことだけを定める。`--prompt` は必須で、`{repo}`・`{revision}`・`{fixSubject}` を置換できるが、どれを使うかは未決定 |
| 1 Run の経過時間の上限（`--timeout-s`） | 事前登録・設計案に値がない |
| 1 Run の token 上限（`--max-run-tokens`） | 同上 |
| バッチの token 予算（`--budget-tokens`） | 承認は「25 × 68,022 ≒ 1.7M tokens × m」で m が UNKNOWN のため、絶対値の上限が決まっていない |
| 隔離の程度 | キットは host 上で Codex の `workspace-write` sandbox を使う。この sandbox は読み取りを workspace に限らないため、Worker が過去の Run のディレクトリを読める可能性がある。EXP-001 の container 方式（[RUNBOOK.md](../../experiments/EXP-001-t0-vs-t1/pilot/RUNBOOK.md)）に揃えるかは未決定 |
| AC 実行時のネットワーク遮断 | 候補表の確認は sandbox-exec で遮断したが、キットの AC 実行は遮断しない |
| `approval_policy=never` | EXP-001 の構成に揃えたが、事前登録には記載がない |
