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

確認結果は各 `run.json` の `isolation`（container 名、mount の一覧、HostConfig.Tmpfs、seccomp の SHA-256 と一致の判定、Codex 版、auth probe の exit code と出力）に残る。隔離の確認で止まった Run は `isolation-stop` として残す。model を起動する前に止まった Run（`modelLaunched: false`）は消化済みとして扱わず、`--skip-existing` での再開時に `<work-root>/attempts/<runId>/attempt-<N>/` へ退避（上書きしない）してから同じ Run を新しく実行する。予算の加算と m の平均は model を起動した Run だけを対象にする。Operator は最初の Run の後に `run.json` の `isolation` を目視で確認し、#244 に記録する。

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
| 1 Run の経過時間が `--timeout-s` を超えた | container 内で Codex を kill し、その後に trace を回収して container を止める（各段階に 30 秒の上限。kill や回収が失敗・超過したら強制停止へ進む）。`aborted-timeout` として残す。kill が exit 0、kill 後の回収が成功、trace に `token_count` がある場合だけ `tokenUsageKnown: true` として次の Run へ進む。その値は kill 後の trace で観測した累積値で、停止直前の未記録分を含まない下限。それ以外はすべて `tokenUsageKnown: false`（`totalTokens` なし）で、推測せず停止し、停止失敗の根拠を `run.json` の `isolation.timeoutTrace` に残す。再開は §7 の解決の後に限る。`docker stop` が exit 0 でない（非ゼロ・上限超過・起動失敗）ときは、`true` でもバッチを停止する（記録と使用量の値は保持）。Operator が container の停止を確かめた後に `--skip-existing` で再開する（§7）。中止 Run は作り直さない |
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

## 7. スクリーニング（第 2 版の §3）

本節とキットは model 起動の許可ではありません。正本は [第 2 版](../HARD_TASK_T0_FAIL_T1_PREREGISTRATION.md) §3・§3.1・§5 と [補遺 1](../HARD_TASK_T0_FAIL_T1_PREREGISTRATION_ADDENDUM_1.md) で、食い違えば正本が優先します。§1・§2 の隔離と §3 の停止条件は、スクリーニングにもそのまま適用します（Run ID は `HTS-<order>-n<k>`）。

**起動の前提（すべて Operator が確認する）**: 補遺 1 の成立（#244 の blob 記録）。第 2 版 §5.1b の実効上限の確認、または超過可能性と処置についての Operator の判断。キットはこれらを判定しません。補遺 1 のファイル冒頭の「下書き」は成立前の文面で、成立の根拠は #244 の blob 記録です。

**キットの動作**:

| 対象 | 動作 |
|---|---|
| order 1〜5 | `--reuse-root` の `HTC-<order>-n1`〜`n3` の `run.json` だけを読む（新しい Run なし）。成功があれば打ち切り、3 回とも失敗なら 0/3。読めない、`completed` の実 Run でない（`modelLaunched`・Codex 版・model / effort の不一致を含む）、runId・repo・revision が固定候補と違うときは選別前に停止 |
| order 10・11・16・26・28・32・38 | 事前除外。Run も説明の読み込みもせず、失敗・0/3・budget-excluded に数えない |
| 残り 32 件 | order 昇順に T0 を最大 3 回。verified success で打ち切り。0/3 が 12 件（order 1〜5 を含む）そろったら停止 |

| 追加の停止条件 | 動作 |
|---|---|
| 第 2 版・補遺 1・候補表の blob が記録値と違う | 起動前に停止 |
| 候補の消費 + `--max-run-tokens` が `--max-candidate-tokens` を超える | その候補の次の Run を始めず budget-excluded とし、次の候補へ進む |
| スクリーニングの消費 + `--max-run-tokens` が `--budget-tokens` を超える | 次の Run を始めずに停止 |
| Run 後に `--max-run-tokens` を超えた | 記録して停止。その候補は budget-excluded（事後の検出で、実効 hard cap ではない） |
| 再開時に dry-run の記録と実 Run が混ざる | 停止 |

較正 25 Run の token は支出済みのためスクリーニング予算に数えません（第 2 版 §5.1）。集計の `reusedTokensNotCounted` に別に表示します。

**timeout**: `aborted-timeout` の候補は失敗に数えず budget-excluded とし、次の候補へ進みます。`tokenUsageKnown: true` の値は、kill 後の trace で観測した累積値で、停止直前の未記録分を含まない下限です（`tokenUsageBasis`）。これを確定値として予算に加算して次へ進むため、timeout が重なると不足分が累積します。この扱いを受け入れるかは、第 2 版 §5.1b の超過可能性と処置についての Operator の判断に含めます。

**非ゼロ終了**: スクリーニングでは、Codex の非ゼロ終了を採点せず `aborted-nonzero-exit` として残し、その候補を budget-excluded（理由に終了コード）として残りの Run を打ち切り、バッチを停止します。第 2 版 §3 に環境起因の判定基準がないため、非ゼロ終了を環境起因として保守的に扱う実装上の規則で、Operator の確認待ちです。Operator は `codex-stderr.log` などで原因を確かめて #244 に記録し、`--skip-existing` で再開します（次の候補へ進み、中止 Run は作り直しません）。使用量が trace から読めないときは、次の「使用量が不明なとき」の解決が先です。終了コード 0 でも、trace の回収に失敗した、trace を読めない、trace に使用量がない、のいずれかなら、同じ規則で `aborted-trace-unavailable` とします。採点に進むのは、終了コード 0、回収成功、trace 可読、使用量ありがすべてそろった Run だけです。回収に失敗した Run は、残った trace が読めても途中の累積値を確定値とせず、`tokenUsageKnown: false` とします。model 起動後の `docker stop` の失敗は `isolation.stopTrace` に残してバッチを停止し、container の停止を確かめた後に再開します。AC の実行自体が失敗した Run は `grade-error` として残して停止します。成否を分類する規則がないため、再開には Operator の判断が要ります。model 起動後のその他の例外（通信・trace 処理など）は `aborted-run-error`（`tokenUsageKnown: false`）として残して停止し、「使用量が不明なとき」の解決後に再開します。起動前の失敗（workspace の準備、prompt の SHA-256 不一致、`docker run`、Codex クライアントの起動など）は `isolation-stop` と原因を残し、`--skip-existing` で再試行します。これらの規則も Operator の確認待ちです。較正モードの扱いは変えていません。

**再利用する較正記録**: order 1〜5 の再利用には非ゼロ終了の除外を適用しません（`load_reuse` は終了コードを検査しません）。Operator はスクリーニングの起動前に、再利用する `HTC-<order>-n1`〜`n3` の `run.json` の `codexExitCode` を確認します。非ゼロや欠落の終了コードを見つけたら、スクリーニングを起動せずに停止し、Operator が扱いを判断します。

**使用量が不明なとき**: バッチが止まり、集計の `budgetExcluded[].usageUnknown` と `usageUnknownRuns` に表示されます。Operator は次の順で解決します。

1. `isolation.timeoutTrace` と `isolation.stopTrace` を読み、`forceKillExitCode` や `stopExitCode` が 0 でない、または null なら、container が止まったことを先に確かめる。
2. 根拠を確かめる。根拠は、その Run の **終了までの使用量を裏付ける記録** に限る。途中の累積値は解決にならない。裏付けられなければ再開しない。
3. 更新前の `run.json` を別ファイルに保存する。
4. `totalTokens` と `tokenUsageKnown: true` だけを更新する。`status`・`runId`・`modelLaunched` は変えず、中止 Run を作り直さない。`tokenUsageKnown: false` のままの `totalTokens` や、`totalTokens` のない `true` は解決済みと扱わず、再開も集計も停止する。
5. #244 に変更前後の値、根拠のファイルと hash、計算方法、Operator を記録し、`--skip-existing` で再開する。

起動通知の後に Ctrl-C や強制終了で `status: started`、`modelLaunched: true` が残った Run は、手順 4 の対象外で、Operator が判断します。

**trace の実効値**: `turn_context` や `cli_version` が trace にないだけなら、中止の状態を変えず、欠落を `traceControlsMissing` に併記します。終了コード 0 でも欠落があれば採点せず `aborted-trace-unavailable` とします。実際の model / effort / 版の不一致は `control-deviation`（中止だった場合は `abortedAs` に元の状態）として停止し、手順 4 では再開できません。再開は使用量の記録の有無によらず control deviation として拒否されます。`screen-summarize` は集計を出し、その候補を `control-deviation`、Run と停止理由を `controlDeviation` に表示します。

Docker 内での kill と回収の手順は合成テストだけで確認しており、実 container では未確認です（**NOT_TESTED**）。最初の本番前に Operator が次を確認します。

- 固定 image の container 内で kill が exit 0 で返り、Codex 配下が終了し、その後に trace を回収できること。
- **stop 失敗時の扱い**: timeout 後の `docker stop` が失敗すると、`stopExitCode: null` や非ゼロの値と `stopError` を `isolation.timeoutTrace` に残し、標準エラーに `WARNING` を出す。スクリーニングでは続けて `docker ps -a` で同じ名前の container を探し、応答があって見つからなければ（`--rm` で先に消えた場合など）`containerAbsent: true` を残し、`WARNING` を「container が見つからない。起動先と同じ daemon か確かめてから再開する」という趣旨の文面にする（`isolation.stopTrace` も同じ）。今の接続先にないことは起動した container が止まった証拠にならないため、この場合もバッチは停止する。記録は `aborted-timeout` のまま保存し、stop の失敗だけでは `tokenUsageKnown` と使用量の値を変えない。止まっていない container が残ったまま次の Run で課金が進むのを防ぐため、stop が失敗したら `true` でも、`containerAbsent: true` でもバッチを停止する。Operator は起動先の daemon（Docker context）で `docker ps` などを使い、container（`isolation.container` の名前）が止まったことを確かめ、必要なら止めて #244 に記録し、`--skip-existing` で再開する。`true` の記録は `run.json` を編集せずに再開できる。`false` なら「使用量が不明なとき」の解決も先に行う。
- **上限**: 30 秒は各待機（kill、Codex クライアントの終了待ち、回収、強制停止、stop、stop 失敗後の `docker ps`）それぞれの上限で、timeout 後の処理全体は最大 180 秒程度かかる。この間も Run の wall clock は `--timeout-s` を超えて進む。30 秒が実環境で十分かも確かめる。

**手順**:

1. dry-run で計画と出力を確認する（model も container も起動しない。`dry-run` の結果は合成で、選別に使わない）:

   ```bash
   python3.12 scripts/hard_task_calibrate.py screen-plan
   python3.12 scripts/hard_task_calibrate.py screen --dry-run --work-root ~/dat-runs/screen-dry \
     --reuse-root ~/dat-runs/hard-task-cal-1 --task-dir docs/hard-task/task-descriptions \
     --timeout-s 1800 --max-run-tokens 4000000 --max-candidate-tokens 10000000 --budget-tokens 50000000
   python3.12 scripts/hard_task_calibrate.py screen-summarize --work-root ~/dat-runs/screen-dry \
     --reuse-root ~/dat-runs/hard-task-cal-1
   ```

2. 本番（Operator のみ）: `--dry-run` を外し、新しい `--work-root` と `--codex-dir` を指定して同じ上限で実行する。上限は第 2 版 §5.2 の確定値で、キットは既定値を持たない。表示される説明の SHA-256 が #244 の記録と一致することを確かめる。
3. exit code が 2 なら標準エラーの `STOP:` の理由を #244 に記録する。理由の解消後に同じ上限で `--skip-existing` を付けて再開する。
4. `screen-summarize --output <ファイル>` で集計を保存し、候補ごとの n1〜nk、打ち切り、事前除外、budget-excluded（件数・理由・消費）、選ばれた 0/3 の一覧、使用 token、停止理由、`feasibilityOnly` を #244 に記録する。報告では、評価集合が E1 除外後の候補集合に条件付くことを併記する（補遺 1 §3）。
