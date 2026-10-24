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
2. container 起動後の mount（EXP-001 run-kit-g `host/host-mounts.sh.in` と同じ考え方）:
   - `docker inspect` の全 mount を type・source・destination・RW で照合する。bind と tmpfs 以外の type（volume など）があれば停止
   - bind は inspect 側・期待側の両方の source を realpath で正規化し、4 つと **完全一致**（`/work` だけ RW、他は読み取り専用）
   - `HostConfig.Tmpfs` が `/tmp` と `/tmp/codex-home` の 2 つと完全一致（`Mounts` に tmpfs が載る場合も同じ集合）
   - Privileged=false、CapAdd なし、CapDrop=ALL、ReadonlyRootfs=true、no-new-privileges があり、seccomp が 1 つで unconfined でない
   - inspect の seccomp の値が、起動時に指定した profile（SHA-256 `085e468f…`）と JSON として一致する。両方の SHA-256 と一致の判定を `run.json` の `isolation` に残す
3. container 内の `codex --version` が `codex-cli 0.160.1`
4. auth（EXP-001 retry-t1-r01 `preflight-d.sh` と同じ probe）: host 側の auth ファイルが空でないこと、container 内の `/tmp/codex-home/auth.json` が空でないことを確かめた後、Codex sandbox 内で probe を実行し、次の 3 つを **別々に** 確かめる: (a) sandbox 内で開始した印 `SANDBOX_ALIVE` が出る、(b) `cat` の失敗が既知の拒否（`Permission denied` / `No such file or directory`）で `AUTH_DENIED` が出る（それ以外のエラーは `UNKNOWN` で停止）、(c) probe 自体が exit 0
5. AC の sandbox（起動前）: host でローカルの listen ソケットを開き、sandbox の外からは接続でき（対照）、sandbox-exec の中からは `EPERM` / `EACCES` で拒否されることを確かめる。対照が接続できない、sandbox 内の結果が timeout・refused・別の errno・probe の異常終了のときは、拒否を確認できないとして停止する。外部ネットワークに依存しない

確認結果は各 `run.json` の `isolation`（container 名、mount の一覧、HostConfig.Tmpfs、seccomp の SHA-256 と一致の判定、Codex 版、auth probe の exit code と出力）に残る。隔離の確認で止まった Run は `isolation-stop` として残し、model を起動する前なら totalTokens を 0 と記録する。Operator は最初の Run の後に `run.json` の `isolation` を目視で確認し、#244 に記録する。

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
   python3.12 scripts/hard_task_calibrate.py run --dry-run --work-root ~/dat-runs/dry --task-dir <TASK_DIR> \
     --timeout-s 1800 --max-run-tokens 300000 --budget-tokens 7500000
   python3.12 scripts/hard_task_calibrate.py summarize --work-root ~/dat-runs/dry
   ```

3. 本番（25 Run。コマンド 1 つ）:

   ```bash
   python3.12 scripts/hard_task_calibrate.py run --work-root ~/dat-runs/hard-task-cal-1 --task-dir <TASK_DIR> \
     --codex-dir <Codex 0.160.1 linux-arm64 musl のディレクトリ> \
     --timeout-s 1800 --max-run-tokens 300000 --budget-tokens 7500000
   ```

   `<TASK_DIR>` は §6 の決定に従って別 PR で作る、候補ごとの説明 `order-01.md`〜`order-05.md` のディレクトリ。キットはその内容をそのまま prompt として渡し（置換はしない）、修正 commit の hash・件名が含まれていれば止める。起動時に各ファイルの SHA-256 を表示するので、#244 に記録済みの hash と一致することを確かめてから進める（各 `run.json` の `promptSha256` にも残る）。
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
| T0 の prompt（Worker に課題をどう示すか） | **決定**（オーガナイザー、PR #251 のレビュー 2 回目の対応時）: 修正 commit の件名・修正内容・原因・テストを渡さず、**症状・再現手順・期待結果・実際の結果だけ** を書いた候補ごとの説明を渡す。説明は較正 Run の結果を見る前に作り、ファイルの hash を #244 に記録してから較正を始める。説明の作成は別 PR とし、作成者と別セッションのレビューで漏洩（原因・修正箇所の示唆）がないかを確かめる。キットは `--task-dir` で候補ごとの説明ファイルを受け取り、`{fixSubject}` などの置換機能は持たない（`{fixSubject}` が書かれていれば止まる）。理由: 件名は修正内容を示しうる（例: 「parse CREATE TABLE TABLESPACE」は直す箇所と方法を示す）ため、難度を T0 の実測で定義する設計で難度の操作化が崩れる。説明ファイルは未作成 |
| Codex 0.160.1 の Linux バイナリ | EXP-001 の container で使ったのは 0.160.0。0.160.1 の Linux バイナリの取得と SHA-256 の記録は未実施（**NOT_TESTED**） |
