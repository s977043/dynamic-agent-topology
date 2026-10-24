# 難度の高い Task の較正 Run 手順書（最初の 25 Run）

状態: **実行キットの起案（未実行）**。本書とキットは model 起動の許可ではありません。較正 Run の起動は Operator（Human）が行います。承認範囲は [#244](https://github.com/s977043/dynamic-agent-topology/issues/244) の 2026-10-25 の記録どおり「最初の 5 候補 × n_cal 5 = 25 Run」に限ります。

- 正本: [HARD_TASK_T0_T1_PREREGISTRATION.md](../HARD_TASK_T0_T1_PREREGISTRATION.md)（blob `52b4a585…`）§2・§5・§6・§9、[CANDIDATES.yaml](CANDIDATES.yaml)（blob `aad6f236…`）の initial の order 1〜5
- キット: [`scripts/hard_task_calibrate.py`](../../scripts/hard_task_calibrate.py)、テスト [`scripts/test_hard_task_calibrate.py`](../../scripts/test_hard_task_calibrate.py)
- 隔離の前例: EXP-001 の [run-kit-g](../../experiments/EXP-001-t0-vs-t1/pilot/run-kit-g/README.md)（container の制約・seccomp・image digest・config）。Frozen file は読むだけで、変更・import していない
- 本書は事前登録・候補表・EXP-001 の Frozen file を変えない。食い違いがあれば正本が優先する

## 1. キットが固定するもの

| 項目 | 値 | 根拠 |
|---|---|---|
| Runtime | `codex-cli 0.160.1`（container 内の `codex --version` と trace の `cli_version` を照合） | U1、#244 の手順 5 の記録 |
| Model / Effort | `-m gpt-6.1-sol -c model_reasoning_effort=high` を起動時に明示。Run ごとの新しい `CODEX_HOME`（tmpfs）に EXP-001 と同じ内容の config.toml を書き、ローカルの既定（gpt-6-luna / medium）は読まない。グローバル設定は変えない | U1、#244 |
| 承認方式 | `approval_policy=never` | EXP-001 の config（run-kit-g `config-never.sh`）と同じ。非対話の `codex exec` では承認要求に答える人がいないため。EXP-001 と揃えることで、難度以外の条件の差を増やさない（事前登録 §2 の比較可能性） |
| Topology | T0 のみ（較正に T1 を使わない） | 設計案 §5 の 4 |
| 対象 | initial の order 1〜5、各 5 回。Run ID は `HTC-<order>-n<k>` | §5・§6、#244 の承認範囲 |
| 実行順 | rep 単位の巡回（全候補の n1、次に n2…）。時刻による変動を候補間で偏らせないため | キットの設計判断 |
| fresh workspace | Run ごとに新しいディレクトリへ clone し revision に detach、remote・ref を消して gc。修正 commit が workspace から到達できないことを確認する | 設計案 §6、§3 の 2 |
| fresh session・隔離 | Run ごとに新しい Docker container（§2）で新しい `codex exec` | 設計案 §6 |
| AC | Worker の終了後、workspace の複製に修正 commit のテストファイルを重ね、候補表の `command` を **sandbox-exec でネットワークを遮断して** 実行（exit 0）。AC のファイルは Run 開始前にメモリへ読み、clone は消す | §3 の 2・5、候補表の `mechanicalChecks` |
| negative oracle | `failingBeforeFix` の各テストを同じ sandbox で `-v` 実行し、すべて `... ok` であること（skip・未実行は不合格）。テストファイル自体は修正 commit の blob で上書きするので、Worker のテスト編集は AC に影響しない | 候補表の `negativeOracle` |
| token | trace の最終 `total_token_usage` の `input_tokens + output_tokens`（cached input を含む。EXP-001 と同じ定義） | §6、DECISION.md |

## 2. 隔離の方式と確認方法

方式（EXP-001 run-kit-g の container 制約に揃える）:

- Run ごとに `docker run` で container を 1 つ作り、Run の終わりに停止する（`--rm`）。image は EXP-001 と同じ `python@sha256:34386ef0…`
- bind mount は **その Run の** `workspace`（`/work`）、`prompt.md`（ro）、Codex の Linux バイナリのディレクトリ（`/cx`、ro）、`auth.json`（ro）の 4 つだけ。work root や他の Run のディレクトリは mount しない
- `--cap-drop ALL`、`--read-only`、`--security-opt no-new-privileges`、EXP-001 の seccomp profile（SHA-256 照合）、`--user <uid>:<gid>`、`CODEX_HOME` は tmpfs
- Codex の sandbox は EXP-001 と同じ permission profile で `CODEX_HOME`（auth.json）を読めなくする
- session trace は container の `CODEX_HOME/sessions` から tar で回収する（auth.json が含まれていれば停止）

確認（キットが Run ごとに機械的に行い、1 つでも満たさなければ model を起動せずに停止）:

1. 起動前: `docker` があり daemon に接続できる、image が手元にある、seccomp の SHA-256 が一致、`--codex-dir` に `bin/codex` がある、auth ファイルがある
2. container 起動後: `docker inspect` の bind mount が上の 4 つと **完全一致**（追加の mount、work root 全体や他 Run の mount があれば停止）、Privileged=false、CapAdd なし、CapDrop=ALL、ReadonlyRootfs=true、no-new-privileges と seccomp があり unconfined でない
3. container 内の `codex --version` が `codex-cli 0.160.1`
4. Codex sandbox からの probe で auth.json が読めない（`AUTH_DENIED`）
5. AC の sandbox: 起動前に sandbox-exec 内から外部への接続を試し、失敗することを確認（接続できたら停止）

確認結果は各 `run.json` の `isolation`（container 名、mount 先、Codex 版、probe 結果）に残る。Operator は最初の Run の後に `run.json` の `isolation` を目視で確認し、#244 に記録する。

## 3. 止める条件（キットが自動で止める）

| 条件 | 動作 |
|---|---|
| 事前登録・候補表の blob が記録値と違う | 起動前に停止 |
| §2 の確認 1・5 のいずれかを満たさない | 起動前に停止 |
| §2 の確認 2〜4 のいずれかを満たさない | その Run の model を起動せずに停止 |
| 結果ディレクトリ（`<work-root>/HTC-…`）が 1 つでも既にある | 起動前に停止（上書きしない）。`--skip-existing` を付けたときだけ、既存の Run に触れずに飛ばす |
| `--skip-existing` で再開し、既存 Run の `run.json` に `totalTokens` がない | 停止（使用量が分からないと予算の上限を守れないため）。既存 Run の `totalTokens` は予算の使用済みに加算する |
| `<work-root>/.calibration.lock` がある | 重複起動として停止。別の実行がないと確認してから Operator が手で消す |
| work root が DAT repo の中 | 停止 |
| trace の model / effort が `gpt-6.1-sol` / `high` 以外、または `cli_version` が違う | その Run を `control-deviation` として残し、バッチを停止（§2 の control deviation） |
| 1 Run の経過時間が `--timeout-s` を超えた | container を kill し `aborted-timeout` として残す。次の Run へ進む |
| 1 Run の token が `--max-run-tokens` を超えた | 記録した後バッチを停止（token は Run の終了後にしか分からないため、事後の検出） |
| 使用済み token + `--max-run-tokens` が `--budget-tokens` を超える | 次の Run を始めずに停止 |

## 4. Operator の手順

前提: 事前登録の成立（§9 手順 1）と候補表の固定（手順 3）は #244 に記録済み。手順 4（25 Run の予算承認）は 2026-10-25 に記録済み。上限は [#244 のコメント](https://github.com/s977043/dynamic-agent-topology/issues/244#issuecomment-6387347455) で確定済み（1 Run 30 分、1 Run 300,000 tokens、25 Run 全体 7,500,000 tokens）。キットは上限の既定値を持たず、毎回コマンドで渡す。

1. 準備: Docker Desktop を起動し、`docker pull python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258`。Codex 0.160.1 の Linux（arm64 musl）バイナリのディレクトリを用意する（`bin/codex`。取得方法は EXP-001 T1 r01 キット README の `CODEX_DIR` を参照）。DAT repo の外に、まだ存在しない作業ディレクトリを決める。
2. 本 PR の merge 後の main で、dry-run を実行して手順と出力を確認する（model も container も起動しない）:

   ```bash
   python3.12 scripts/hard_task_calibrate.py plan
   python3.12 scripts/hard_task_calibrate.py run --dry-run --work-root ~/dat-runs/dry --prompt <PROMPT> \
     --timeout-s 1800 --max-run-tokens 300000 --budget-tokens 7500000
   python3.12 scripts/hard_task_calibrate.py summarize --work-root ~/dat-runs/dry
   ```

3. 本番（25 Run。コマンド 1 つ）:

   ```bash
   python3.12 scripts/hard_task_calibrate.py run --work-root ~/dat-runs/hard-task-cal-1 --prompt <PROMPT> \
     --codex-dir <Codex 0.160.1 linux-arm64 musl のディレクトリ> \
     --timeout-s 1800 --max-run-tokens 300000 --budget-tokens 7500000
   ```

   `<PROMPT>` は §6 の未確定事項。決まった prompt の SHA-256（各 `run.json` の `promptSha256`）を #244 に記録してから起動する。
4. exit code が 0 なら 25 Run 完了。2 なら標準エラーの `STOP:` の理由を #244 に記録する。再開は、理由を解消した後に同じ上限で `--skip-existing` を付けて行う（既存の Run は作り直さず、その token は予算に数える）。
5. 集計を保存する: `python3.12 scripts/hard_task_calibrate.py summarize --work-root ~/dat-runs/hard-task-cal-1 --output ~/dat-runs/hard-task-cal-1-summary.json`
6. 集計の `m`、`updatedCalibrationEstimate`（5 × 44 × 68,022 × m）、`remainingCalibrationEstimate`（残り 39 候補）、各候補の `verifiedSuccesses` と `band` を #244 に記録する（§6）。残り 39 候補の較正は Operator の再承認まで始めない。

## 5. 保存されるもの

`<work-root>/HTC-<order>-n<k>/` に Run ごとに保存する。

| ファイル | 内容 |
|---|---|
| `run.json` | 宣言値、container と Codex の起動コマンド、上限、prompt の SHA-256、隔離の確認結果、trace から読んだ cli_version・model・effort・`total_token_usage`、totalTokens、wallClockMs、exit code、AC と negative oracle の結果、status |
| `prompt.md` | 実際に渡した prompt |
| `codex-events.jsonl` / `codex-stderr.log` | `codex exec --json` の出力 |
| `sessions/` | container から回収した session trace（実効値の照合元） |
| `workspace/` | Worker の作業後の状態 |
| `grade/`・`ac-output.txt`・`oracle-output.txt` | AC の実行結果 |

`summarize` は `band` を、5 回すべて `completed` の候補だけに付ける（0/5 は主集合から除外、1〜2/5 は hard、3/5 以上は not-hard）。timeout・停止を含む候補は `INCOMPLETE` とし、成功率を推測で埋めない。trace と結果は秘密や個人情報を確認するまで repo に commit しない（AGENTS.md）。

## 6. 未確定事項と確定済みの値

| 項目 | 状態 |
|---|---|
| 1 Run の経過時間の上限（`--timeout-s`） | **確定済み**: 30 分（1800）。[#244 issuecomment-6387347455](https://github.com/s977043/dynamic-agent-topology/issues/244#issuecomment-6387347455) |
| 1 Run の token 上限（`--max-run-tokens`） | **確定済み**: 300,000。同上 |
| バッチの token 予算（`--budget-tokens`） | **確定済み**: 25 Run 全体で 7,500,000。同上 |
| T0 の prompt（Worker に課題をどう示すか） | **未確定**。設計案・事前登録は「修正 commit とテストを渡さない」（§3 の 2）だけを定め、Task の提示方法の記述はない。比較: (a) 修正 commit の件名を渡す案は準備が要らないが、件名は修正内容を示しうる（例: 「parse CREATE TABLE TABLESPACE」は直す箇所と方法を示す）ため難度が下がり、候補間で漏れ方がばらつく。(b) 症状だけを書いた説明（再現手順と期待・実際の挙動。原因や修正方法は書かない）を渡す案は、候補ごとの作成が要るが、提示する情報の水準を揃えられる。**推奨: (b)**（理由: 難度を T0 の実測で定義する設計で、提示情報が修正内容を漏らすと難度の操作化が崩れるため。説明は較正前に、結果を見ずに作り、hash を記録する）。キットの `--prompt` は必須で `{repo}`・`{revision}`・`{fixSubject}` を置換できるが、(b) を採るなら候補ごとの説明を渡す仕組みの追加が要る |
| Codex 0.160.1 の Linux バイナリ | EXP-001 の container で使ったのは 0.160.0。0.160.1 の Linux バイナリの取得と SHA-256 の記録は未実施（**NOT_TESTED**） |
