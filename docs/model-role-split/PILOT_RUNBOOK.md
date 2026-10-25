# モデル役割分担の予備検証 手順書（#220、2 Run）

状態: **実行キットの起案（未実行）**。本書とキットは model 起動の許可ではありません。予備検証の起動は Operator（Human）が行います。承認範囲は [Issue #220 の 2026-10-25 の記録](https://github.com/s977043/dynamic-agent-topology/issues/220#issuecomment-6386579854)どおり「予備検証 2 Run（order 2 を arm A / B で 1 回ずつ）」に限ります。現時点の実測は 0 件です。

**資格情報の扱い（案 D、[Operator 承認 2026-10-26](https://github.com/s977043/dynamic-agent-topology/issues/220#issuecomment-6402829329)）**: 隔離の確認（§2.3）のうち確認 6（Worker の uid から資格情報ファイルを読めないこと）は FAIL です（§2.4）。この 1 項目だけを「既知のリスク（Operator 承認済み）」として扱い、承認コメントの URL を `--accept-credential-read-risk` で渡したときに限り起動を止めません。境界と根拠は §2.5 です。他の確認は従来どおり 1 つでも FAIL なら起動しません。

- 正本: [MODEL_ROLE_SPLIT_PREREGISTRATION.md](../MODEL_ROLE_SPLIT_PREREGISTRATION.md)（blob `5e757639…`）§4・§6・§7・§8、[CANDIDATES.yaml](CANDIDATES.yaml)（blob `3f75aed6…`）の order 2、[MODEL_ROLE_SPLIT_RUNBOOK.md](../MODEL_ROLE_SPLIT_RUNBOOK.md) の手順 11・12 と Gate 2
- キット: [`scripts/model_role_split_pilot.py`](../../scripts/model_role_split_pilot.py)、テスト [`scripts/test_model_role_split_pilot.py`](../../scripts/test_model_role_split_pilot.py)。workspace の作成と採点は fixture の [`scripts/model_role_split_fixture.py`](../../scripts/model_role_split_fixture.py)（`prepare` / `verify`）をそのまま使う
- 前例: [hard-task/CALIBRATION_RUNBOOK.md](../hard-task/CALIBRATION_RUNBOOK.md)（#244）の container の制約・mount の完全一致照合・auth probe・重複起動の防止・上書き拒否・trace 照合と不一致時の停止・予算の事後検出・再開時の予算加算・`modelLaunched`・ネットワーク遮断の対照 probe を踏襲する。EXP-001 の seccomp profile は読むだけで変更しない
- 本書は事前登録・候補表・fixture・Freeze 対象を変えない。食い違いがあれば正本が優先する

## 1. キットが固定するもの

| 項目 | 値 | 根拠 |
|---|---|---|
| Runtime | Linux 版 Claude Code `2.1.310`（npm `@anthropic-ai/claude-code-linux-arm64@2.1.310` の `claude`、SHA-256 `9c64d9a7…7d54`）。container 内の `claude --version` と、stream の init の `claude_code_version` を照合 | 事前登録 §4 |
| Run | `MRS-P02-A`（`claude-opus-5-5`）→ `MRS-P02-B`（`claude-sonnet-5-5`）。order 2（dnspython、易）。block 1 は奇数なので A→B | 事前登録 §8 の counterbalance の規則 |
| Model / Effort | `--model <完全な model ID> --effort high` を Run ごとに明示。alias は使わない。`CLAUDE_CODE_EFFORT_LEVEL` 等は container に渡さず、Operator の環境にあれば起動前に停止 | 事前登録 §8 |
| 非対話・trace | `docker exec -i … /cc/claude -p --output-format stream-json --verbose`。prompt は stdin、stdout をそのまま `stream.jsonl` に保存 | 事前登録 §6（U5） |
| 設定 | Run ごとの新しい `CLAUDE_CONFIG_DIR`（tmpfs `/cc-home`）に settings.json を書き、`--setting-sources user --strict-mcp-config --disable-slash-commands`。Operator の `~/.claude` は mount しない | fresh session、A/B の条件を model だけの差にするため |
| tool・permission | `--tools Bash,Read,Edit,Write,Glob,Grep`、`--permission-mode dontAsk`、`--permission-prompts none`。allow は `/work` の下のファイル操作と候補表の `allowedCommands`（読み取り専用のシェルコマンドは `ls` / `cat` / `grep`）。Bash は Claude Code の sandbox（bubblewrap、許可ドメインなし、`/cc-home` を denyRead） | 候補表 order 2 の `permissions` |
| fresh session | `--no-session-persistence` と Run ごとの新しい `--session-id`。自動継続は 0 回 | 事前登録 §7・§8 |
| fresh workspace | Run ごとに `prepare 2` で作る（revision の `git archive`、履歴なしの 1 commit。fixCommit・AC テストは入らない） | fixture README |
| prompt | `fixtures/model-role-split/tasks/order-02.yaml` の `statement` をそのまま。SHA-256 `a9f765e7…9784` を起動時に表示し `run.json` に残す | fixture README |
| 採点 | Run の後に host で `verify 2`（AC と negative oracle 4 check、sandbox-exec でネットワーク遮断） | 手順書 手順 12 |
| token | stream の `result.usage` の `input_tokens + cache_creation_input_tokens + cache_read_input_tokens + output_tokens`。m = totalTokens ÷ 68,022（EXP-001 T0） | 事前登録 §7 |
| A/B の差分 | 2 つの起動引数の差は model ID の 1 か所だけ（テストで機械的に確認。Gate 3 の材料） | 手順書 Gate 3 |

## 2. 隔離の方式と確認方法

### 2.1 方式（Run ごとの container）

- Run ごとに、internal の Docker network（外への経路なし）、proxy の container、Run の container を作り、Run の終わりに消す
- Run の container: #244 と同じ制約（`--cap-drop ALL`、`--read-only`、`--security-opt no-new-privileges`、EXP-001 の seccomp profile、`--user <uid>:<gid>`、tmpfs は `/tmp` と `/cc-home` だけ）。image は digest で固定した派生 image（§4 の 1）
- bind mount は **その Run の** `workspace`（`/work`、RW）、`input`（`/run-input`、ro、prompt）、Linux 版 Claude Code のディレクトリ（`/cc`、ro）、資格情報ファイル（`/cc-home/.credentials.json`、ro）の 4 つだけ
- 外向き通信: Run の container は internal network にだけつながる。出口は proxy の container（同じ image、キット自身を ro で mount して allowlist の CONNECT proxy として動かす）だけで、`api.anthropic.com:443` 以外の CONNECT を 403 で拒否し、全要求を `proxy.log` に残す。Claude Code には `HTTPS_PROXY` で proxy を渡し、`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` を付ける
- 資格情報: 長期 token を環境変数で渡す方式は使わない。Linux 版の資格情報ファイルを ro で mount する（取得は §4 の 1）

採らなかった案: (1) host の macOS で Claude Code 自身の制限だけに頼る案（初版）。Read / Edit / Write が作業ディレクトリ外にも及びうる、Write したスクリプトの実行で監視をすり抜けられる、確認を model なしでできない、の理由で独立レビューで差し戻された。(2) 長期 token を環境変数で渡す案。Worker のプロセスから環境変数を読める可能性があるため。

### 2.2 起動前の確認（バッチ開始時、1 つでも満たさなければ止める）

1. 事前登録（blob `5e757639…`）と候補表（blob `3f75aed6…`）が記録値と一致する
2. work root が DAT repo の外、結果ディレクトリ（`MRS-P02-*`）が未作成（`--skip-existing` のときだけ既存を飛ばす）、`<work-root>/.pilot.lock` がない、`<work-root>/quarantine/` に Run がない
3. Operator の環境に `ANTHROPIC_API_KEY`・`ANTHROPIC_AUTH_TOKEN`・`CLAUDE_CODE_OAUTH_TOKEN`・`ANTHROPIC_BASE_URL`・`CLAUDE_CODE_USE_BEDROCK` / `VERTEX` / `FOUNDRY`・`CLAUDE_CODE_EFFORT_LEVEL`・`ANTHROPIC_MODEL` がない
4. `docker` があり daemon に接続できる。`--image` が `name@sha256:` で固定され手元にある。seccomp の SHA-256 が一致。`--claude-dir/claude` の SHA-256 が `9c64d9a7…7d54`。資格情報ファイルが空でない（中身は読まない）
5. 採点の sandbox の対照 probe（host）: listen ソケットに sandbox の外からは接続でき、fixture と同じ sandbox-exec の profile の中からは `EPERM` / `EACCES` で拒否される

### 2.3 Run ごとの確認（container を作った後、model を起動する前。1 つでも満たさなければ `isolation-stop`・`modelLaunched: false` で止める）

| # | 確認 | 方法（model を起動しない） |
|---|---|---|
| 1 | network が internal | `docker network inspect` の `Internal` が true |
| 2 | mount と制約 | `docker inspect` の全 mount を type・source（realpath）・destination・RW で 4 つと完全一致。`HostConfig.Tmpfs` が `/tmp`・`/cc-home` と完全一致。`NetworkMode` が internal network。Privileged=false、CapAdd なし、CapDrop=ALL、ReadonlyRootfs=true、no-new-privileges、seccomp が起動時の profile と JSON として一致 |
| 3 | Runtime | container 内の `claude --version` が `2.1.310` |
| 4 | settings の適用と sandbox の可用性 | container 内の `claude sandbox status`（2.1.310 の隠しサブコマンド。posture を JSON で出すだけで model を起動しない）が `enabled: true`・`enabledSource: settings`・`unavailableReason: null`・`strictMode: true`・`filesystemPolicy: strict`・`autoAllowBashIfSandboxed: false` |
| 5 | 外向き通信の遮断（対照つき） | Run の container の中で: loopback の listen ソケットには接続できる（probe が動く対照）、`1.1.1.1:443` への直接接続が `ENETUNREACH` / `EHOSTUNREACH`、proxy 経由の `example.com:443` が 403、proxy 経由の `api.anthropic.com:443` が 200（TCP の接続だけで HTTP の要求は送らない）。timeout・別の errno・probe の異常終了は確認できないとして止める |
| 6 | 資格情報を Worker から読めない | #244 の auth probe と同じ形: 開始の印 `PROBE_STARTED`、`cat /cc-home/.credentials.json` の失敗が既知の拒否（`Permission denied` / `No such file or directory`）で `AUTH_DENIED`、probe の exit 0 を別々に確かめる。Claude Code 2.1.310 には model を起動せずに Bash sandbox の中でコマンドを動かす手段がない（`claude sandbox` は status だけ）ため、probe は Run の uid で sandbox の外から実行する（sandbox が効かなかった場合の最悪条件）。結果が `BLOCK: worker uid can read the credential file`（exit 3）のときだけ、§2.5 の既知のリスクとして、承認 URL があれば `isolation.authProbe.acceptedRisk` に URL を記録して進む。probe が始まらない・未知のエラー・他の exit code は止める |

確認結果は各 `run.json` の `isolation` に残る。model を起動する前に止まった Run は消化済みにせず、`--skip-existing` での再開時に `<work-root>/attempts/<runId>/attempt-<N>/` へ退避（上書きしない）してやり直す。

### 2.4 実測（2026-10-26、model は起動していない）

確認 1〜6 を実行する検査用のスクリプト（`isolate_and_check` だけを呼び、起動の関数は呼ばない）を、ダミーの資格情報ファイルで実行した。

| # | 結果 |
|---|---|
| 1〜2 | PASS（mount 4 つの完全一致、tmpfs 2 つ、seccomp 一致） |
| 3 | PASS（`2.1.310 (Claude Code)`） |
| 4 | PASS（派生 image）。`python@sha256:34386ef0…` のままでは `unavailableReason: bubblewrap (bwrap) not installed, socat not installed` で FAIL |
| 5 | PASS（LOOPBACK CONNECTED / DIRECT ENETUNREACH / example.com 403 / api.anthropic.com 200。proxy.log に 2 件） |
| 6 | **FAIL**（`BLOCK: worker uid can read the credential file`、exit 3）。Claude Code 自身が読む必要があるファイルなので、同じ uid の Worker のプロセスからも読める |

補足（観測）: 同じ制約の container の中で、同じ uid の別プロセスの `/proc/<pid>/mem` を開けた（`ptrace_scope` は読めない）。資格情報をファイルではなく file descriptor で渡しても、同じ uid の Worker からプロセスのメモリを読める可能性が残るため、その方式でも確認 6 に相当する確認は通らない見込み（未実装、**NOT_TESTED**）。

2026-10-26 の再実行（承認 URL あり、ダミーの資格情報、model 不起動）では、確認 1〜5 が PASS、確認 6 は `BLOCK` を既知のリスクとして記録し、全確認を通過した（起動の関数は呼んでいない）。

### 2.5 案 D の境界と既知のリスク

| 区分 | 内容 |
|---|---|
| 境界 1（毎 Run 必須） | container からの外向き通信は allowlist proxy 経由の `api.anthropic.com:443` だけ。§2.3 確認 5（直接接続が ENETUNREACH、proxy 経由の他の宛先が 403、対照の loopback は接続可）を Run ごとに確かめ、FAIL なら起動しない。Run 後に `proxy.log` の確認後の CONNECT がすべて許可済みの `api.anthropic.com:443` で、拒否・読めない行が 0 件であることを照合し、違えば `egress-anomaly` で止める |
| 境界 2（毎 Run 必須） | Run の保存物に資格情報の形の文字列があれば quarantine（mode 700）に移して停止し、commit しない（§3.2） |
| 既知のリスク（Operator 承認済み） | Worker の uid から、mount した Claude Code の資格情報ファイルを読めることがある（§2.4 確認 6。同じ uid の別プロセスのメモリも開けた） |
| 持ち出し経路が限られる根拠 | (1) Run の container は internal network にだけつながり、外への経路は proxy だけ（確認 1・5 の実測）。(2) proxy は `api.anthropic.com:443` 以外の CONNECT を拒否し、全要求を記録する（確認 5 と Run 後の照合）。(3) この宛先は Claude Code がもともと同じ資格情報を送る相手。(4) host の他の資格情報（`~/.claude`、`~/.ssh`、Keychain 等）は mount しない（確認 2 の mount の完全一致）。(5) 手元の保存物に写った場合は quarantine される |
| 残る限界 | 境界 2 は形で検出するため、形を変えて保存物に書かれた資格情報は検出できない。proxy は宛先だけを見て中身は見ない |
| 承認の扱い | キットはこの 1 項目だけを名前で固定し、`--accept-credential-read-risk` に承認コメントの URL（`…/issues/220#issuecomment-6402829329`）がちょうど渡されたときだけ進む。他の URL・未指定は起動前に止まる。URL は各 `run.json` の `preflight.credentialReadRiskApproval` と `isolation.authProbe.acceptedRisk` に残る。任意の項目を ack して進める仕組みはない |

## 3. 止める条件（キットが自動で止める）

| 条件 | 動作 |
|---|---|
| §2.2 の確認のいずれかを満たさない | 起動前に停止（exit 2） |
| §2.3 の確認のいずれかを満たさない | その Run を `isolation-stop`（`modelLaunched: false`）として残し、バッチを停止 |
| 実行中の stream の異常（§3.1） | その Run を停止して記録し、バッチを停止 |
| exit code が 0 以外、stream が result event で終わらない、tool_use と tool_result が対応しない、`is_error` | `runtime-error` として記録し、バッチを停止 |
| Run 中の proxy の記録に、拒否された CONNECT・読めない行がある、または許可された CONNECT が `api.anthropic.com:443` だけでない（0 件を含む） | `egress-anomaly` として記録し、バッチを停止 |
| result event がなく使用量が分からないまま止まった | `totalTokens` を記録しない（0 で埋めない。観測した累計は `runningTotalTokens`）。再開は Operator が使用量を `totalTokens` に記録してから |
| Run の保存物（stream・stderr・proxy.log・workspace など）に資格情報の形の文字列（`sk-ant-…`、`"accessToken"` / `"refreshToken"`、`Bearer …`、`CLAUDE_CODE_OAUTH_TOKEN=…`） | Run のディレクトリを `<work-root>/quarantine/<runId>-<時刻>/`（mode 700）へ移し、`secret-quarantined` として停止。該当ファイル名だけを表示し、文字列は表示しない |
| `--skip-existing` で再開し、既存 Run に `totalTokens` がない、または quarantine に Run がある | 停止 |
| 使用済み token + `--max-run-tokens` が `--budget-tokens` を超える | 次の Run を始めずに停止 |

1 Run でも `completed` 以外ならバッチを止める（予備検証は計測の成立を確かめるためのもので、異常のまま次の Run に進まない）。

### 3.1 stream の逐次検査（異常の早期検知）

event ごとに次を検査し、当たればその Run の container を kill する。**これは安全策ではなく異常の早期検知**で、検知は tool の実行の後になりうる。Write したスクリプトを後で実行するような経路は見えない。隔離の保証は §2.3 の確認に置く。

| 検査 | 停止時の status |
|---|---|
| init がちょうど 1 つで、`claude_code_version` = `2.1.310`、`model` = 宣言値、`permissionMode` = `dontAsk`、`tools` = 6 つの集合、`mcp_servers` が空 | `control-deviation` |
| assistant message の `model` が宣言値と一致 | `control-deviation` |
| Bash の command と Read / Glob / Grep のパスに、資格情報（`.claude`、`cc-home`、`credential`、`/proc/`、`env` 等）またはネットワーク（`curl`、`git push` 等、URL）の参照 | `policy-stop` |
| assistant message の usage の累計が `--max-run-tokens` を超えた | `token-limit` |
| 経過時間が `--timeout-s` を超えた | `aborted-timeout` |

### 3.2 秘密の扱い

- `<work-root>` と `quarantine/` は DAT repo の外に置き、commit・Issue への貼り付けをしない
- quarantine に入った Run は、該当ファイルの文字列が本物の資格情報かを Operator が確かめ、本物なら資格情報を失効させてから、ディレクトリを消す。使用量は `run.json` から Issue #220 に記録する（trace の本文は載せない）
- quarantine に入らなかった Run も、trace を repo や Issue に貼る前に Operator が中身を確かめる（AGENTS.md）

## 4. Operator の手順

前提: 事前登録の成立（Gate 4）と予備検証 2 Run の予算、案 D の承認は Issue #220 に記録済み。キットは上限の既定値を持たず、毎回コマンドで渡す。

1. 準備（model は起動しない）:
   - Linux 版 Claude Code の取得とハッシュの記録:

     ```bash
     npm view @anthropic-ai/claude-code-linux-arm64@2.1.310 dist.shasum dist.integrity   # shasum a4422178456dd0bc485451c99609cf1e629e4ee7
     npm pack @anthropic-ai/claude-code-linux-arm64@2.1.310 --pack-destination ~/dat-runs/cc-linux
     tar -xzf ~/dat-runs/cc-linux/anthropic-ai-claude-code-linux-arm64-2.1.310.tgz -C ~/dat-runs/cc-linux
     shasum -a 256 ~/dat-runs/cc-linux/package/claude   # 9c64d9a7442436b65fcd7cc02c1aa0051bb5a7041e7788576ed3b5f29c447d54
     ```

     npm の shasum と `claude` の SHA-256 を Issue #220 に記録する。`--claude-dir` には `~/dat-runs/cc-linux/package` を渡す
   - 派生 image（bubblewrap と socat を足す。Claude Code の Linux sandbox の依存）を作り、digest を記録する:

     ```dockerfile
     FROM python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258
     RUN apt-get update && apt-get install -y --no-install-recommends bubblewrap socat && rm -rf /var/lib/apt/lists/*
     ```

     `docker build --platform linux/arm64 -t mrs-pilot-sandbox:1 <dir>` の後、`docker image inspect mrs-pilot-sandbox:1 --format '{{.RepoDigests}}'` の `mrs-pilot-sandbox@sha256:…` を `--image` に渡し、Issue #220 に記録する（2026-10-26 の検査では bubblewrap `0.8.0-2+deb12u1`、socat `1.7.4.4-2`）
   - 資格情報ファイル: Linux 版の `.credentials.json` を、DAT repo の外の専用ディレクトリ（mode 700）に作る。作り方は未確定（§6）
2. Gate 1（U4 の 3 点）を予備検証の直前に再確認し、Issue #220 に記録する（事前登録 §5）。
3. 本 PR の merge 後の main で dry-run を実行する（model も container も起動しない。`--dry-run-grade` は GitHub から revision を取得して workspace の作成と採点まで通す）:

   ```bash
   python3.12 scripts/model_role_split_pilot.py plan
   python3.12 scripts/model_role_split_pilot.py run --dry-run --dry-run-grade --work-root ~/dat-runs/mrs-pilot-dry \
     --cache ~/dat-runs/mrs-cache --timeout-s <秒> --max-run-tokens <tokens> --budget-tokens <tokens>
   python3.12 scripts/model_role_split_pilot.py summarize --work-root ~/dat-runs/mrs-pilot-dry
   ```

4. 本番（2 Run。コマンド 1 つ）:

   ```bash
   python3.12 scripts/model_role_split_pilot.py run --work-root ~/dat-runs/mrs-pilot-1 --cache ~/dat-runs/mrs-cache \
     --image mrs-pilot-sandbox@sha256:<digest> --claude-dir ~/dat-runs/cc-linux/package \
     --credentials-file <資格情報ファイル> \
     --accept-credential-read-risk https://github.com/s977043/dynamic-agent-topology/issues/220#issuecomment-6402829329 \
     --timeout-s <秒> --max-run-tokens <tokens> --budget-tokens <tokens>
   ```

   `--accept-credential-read-risk` は、案 D の承認がいまも有効だと Operator が確かめたときだけ付ける（資格情報や境界の条件が変わったら付けずに、Issue #220 で判断し直す）。

   上限は Issue #220 の承認値を渡す（§6 のとおり見直しの見込みがあるため本書に固定しない）。起動時に表示される prompt の SHA-256 が dry-run と同じことを確かめる。
5. exit code が 0 なら 2 Run 完了。2 なら標準エラーの `STOP:` の理由を Issue #220 に記録する。再開は理由を解消し、同じ上限で `--skip-existing` を付けて行う。
6. 集計を保存する: `python3.12 scripts/model_role_split_pilot.py summarize --work-root ~/dat-runs/mrs-pilot-1 --output ~/dat-runs/mrs-pilot-1-summary.json`
7. [A] が手順書の手順 12 として、集計の `checks`（activationModel・activationEffort・traceComplete・toolCallsRecorded・tokens・cache・elapsed）、`proposedPilotJudgment`、`auxiliaryModels`、`quarantined`、各 Run の `totalTokens` と m、`mainRunEstimateTokens`（180 × 平均）、`proxy.log` の CONNECT 先の一覧を Issue #220 に記録する。`proposedPilotJudgment` は案。`activationEffort` が NOT_TESTED のときは PASS にしない。

## 5. 保存されるもの

`<work-root>/MRS-P02-<arm>/` に Run ごとに保存する。

| ファイル | 内容 |
|---|---|
| `run.json` | 宣言値、起動コマンド、上限、prompt と settings の SHA-256、session ID、container・proxy・network の名前、起動前の確認結果、`isolation`（§2.3 の結果）、trace から読んだ値（init、応答 model、effort の値、tool call と tool result の件数、完全性、usage、modelUsage）、totalTokens、runningTotalTokens、wallClockMs、exit code、採点結果、status、`modelLaunched` |
| `input/prompt.md` | 実際に渡した prompt |
| `stream.jsonl` / `stderr.log` | stream-json の出力（実効値の照合元） |
| `proxy.log` | proxy が受けた CONNECT の一覧（許可・拒否） |
| `workspace/` | Agent の作業後の状態 |

## 6. 未確定事項と NOT_TESTED

| 項目 | 状態 |
|---|---|
| 資格情報を Worker から読めないこと（§2.3 確認 6） | **FAIL（2026-10-26 実測）**。案 D により既知のリスク（Operator 承認済み）として扱う（§2.5）。Claude Code の Bash sandbox が実際に読み取りを防ぐかは **NOT_TESTED** |
| 資格情報ファイルの作り方 | Linux 版の `.credentials.json` の形式と、`claude auth login` を container 内で行う手順は未確認（**NOT_TESTED**）。ro mount のため、Run 中の token 更新が失敗する可能性がある |
| Claude Code の Bash sandbox が container 内で動くか | `sandbox status` は PASS だが、実際のコマンドが bubblewrap の中で動くかは未確認（**NOT_TESTED**）。同じ制約で `bwrap --unshare-user --unshare-net --unshare-pid` は動き、`--proc /proc` の mount は `Operation not permitted` だった。sandbox が動かなければ Bash が失敗し、Run は `runtime-error` などで止まる見込み |
| settings の deny・denyRead が実際に効いていること | `sandbox status` は enabled・strict を返すが、個々のルールの適用は出力に出ない（**NOT_TESTED**） |
| proxy 経由で Claude Code が API に届くか | `HTTPS_PROXY` の扱いと、`api.anthropic.com` 以外の宛先（token 更新など）が要るかは未確認（**NOT_TESTED**）。要る場合は proxy で拒否され、Run 後の照合で `egress-anomaly` になる |
| 1 Run・合計の上限（`--timeout-s`・`--max-run-tokens`・`--budget-tokens`） | 承認値は 1 Run 300,000 tokens・30 分、合計 600,000 tokens。**#244 の実測から上限の見直しが要る見込み**（#244 では本物の repo の Task で 1 Run 1M〜3.2M tokens、95% 以上がキャッシュ入力。Runtime・model は異なる）。値は本書で決めず、Operator が Issue #220 で決めた値をコマンドで渡す |
| stream-json の形式 | init の各キー、assistant の `message.model`・`usage`、result の `usage`・`modelUsage` は Source claim による想定で **NOT_TESTED**。キーが違えば `control-deviation` で止まる（安全側） |
| 実効 Effort が trace に出るか | **NOT_TESTED**。出なければ `activationEffort` は NOT_TESTED になり、予備検証を PASS にしない |
| 補助 model | `modelUsage` に宣言外の model が出た場合は止めずに `auxiliaryModels` として記録し、activation の判定に含めるかは [R] が判定する |
