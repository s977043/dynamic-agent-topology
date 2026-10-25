# モデル役割分担の予備検証 手順書（#220、2 Run）

状態: **実行キットの起案（未実行）**。本書とキットは model 起動の許可ではありません。予備検証の起動は Operator（Human）が行います。承認範囲は [Issue #220 の 2026-10-25 の記録](https://github.com/s977043/dynamic-agent-topology/issues/220#issuecomment-6386579854)どおり「予備検証 2 Run（order 2 を arm A / B で 1 回ずつ）」に限ります。現時点の実測は 0 件です。

- 正本: [MODEL_ROLE_SPLIT_PREREGISTRATION.md](../MODEL_ROLE_SPLIT_PREREGISTRATION.md)（blob `5e757639…`）§4・§6・§7・§8、[CANDIDATES.yaml](CANDIDATES.yaml)（blob `3f75aed6…`）の order 2、[MODEL_ROLE_SPLIT_RUNBOOK.md](../MODEL_ROLE_SPLIT_RUNBOOK.md) の手順 11・12
- キット: [`scripts/model_role_split_pilot.py`](../../scripts/model_role_split_pilot.py)、テスト [`scripts/test_model_role_split_pilot.py`](../../scripts/test_model_role_split_pilot.py)。workspace の作成と採点は fixture の [`scripts/model_role_split_fixture.py`](../../scripts/model_role_split_fixture.py)（`prepare` / `verify`）をそのまま使う
- 前例: [hard-task/CALIBRATION_RUNBOOK.md](../hard-task/CALIBRATION_RUNBOOK.md)（#244）の重複起動の防止、上書き拒否、trace 照合と不一致時の停止、予算の事後検出、再開時の予算加算、`modelLaunched`、ネットワーク遮断の対照 probe を踏襲する
- 本書は事前登録・候補表・fixture・Freeze 対象を変えない。食い違いがあれば正本が優先する

## 1. キットが固定するもの

| 項目 | 値 | 根拠 |
|---|---|---|
| Runtime | Claude Code CLI `2.1.310`（起動前の `claude --version` と、stream の init event の `claude_code_version` を照合） | 事前登録 §4 |
| Run | `MRS-P02-A`（`claude-opus-5-5`）→ `MRS-P02-B`（`claude-sonnet-5-5`）。order 2（dnspython、易）。block 1 は奇数なので A→B | 事前登録 §8 の counterbalance の規則 |
| Model / Effort | `--model <完全な model ID> --effort high` を Run ごとに明示。alias は使わない。`CLAUDE_CODE_EFFORT_LEVEL` などの上書き変数は子プロセスに渡さず、Operator の環境にあれば起動前に停止 | 事前登録 §8 |
| 非対話・trace | `claude -p --output-format stream-json --verbose`。prompt は stdin で渡し、stdout をそのまま `stream.jsonl` に保存 | 事前登録 §6（U5） |
| 設定 | `--restricted`（user / project / local の settings を読まない）、`--safe-mode`（CLAUDE.md・skills・plugins・hooks・MCP を無効）、`--strict-mcp-config`、`--disable-slash-commands`、`--settings <Run の settings.json>` | fresh session と、A/B の条件を model だけの差にするため |
| tool・permission | `--tools Bash,Read,Edit,Write,Glob,Grep`、`--permission-mode dontAsk`、`--permission-prompts none`。allow は候補表の `allowedCommands`（読み取り専用のシェルコマンドは `ls` / `cat` / `grep` に対応させる）、deny は資格情報のパス・`security`・`env`・`curl` 等。Bash は Claude Code の sandbox（`sandbox.enabled`、許可ドメインなし） | 候補表 order 2 の `permissions` |
| fresh session | `--no-session-persistence` と Run ごとの新しい `--session-id`。自動継続（`--continue` / `--resume`）は使わない（0 回） | 事前登録 §7・§8 |
| fresh workspace | Run ごとに `prepare 2` で作る（revision の `git archive`、履歴なしの 1 commit。fixCommit・AC テストは入らない） | fixture README |
| prompt | `fixtures/model-role-split/tasks/order-02.yaml` の `statement` をそのまま。SHA-256 を起動時に表示し `run.json` に残す（dry-run の値 `a9f765e7…9784`） | fixture README |
| 採点 | Run の後に `verify 2`（AC と negative oracle 4 check、sandbox-exec でネットワーク遮断）。予備検証では効果推定に使わない | 手順書 手順 12 |
| token | stream の `result.usage` の `input_tokens + cache_creation_input_tokens + cache_read_input_tokens + output_tokens`。m = totalTokens ÷ 68,022（EXP-001 T0） | 事前登録 §7 |
| A/B の差分 | 2 つの起動コマンドの差は model ID の 1 か所だけ（テストで機械的に確認。Gate 3 の材料） | 手順書 Gate 3 |

## 2. 隔離の方式と確認方法

### 2.1 方式の比較

| 案 | 方式 | 長所 | 短所 |
|---|---|---|---|
| **A（推奨）** | host の macOS で、Claude Code 自身の制限（`--restricted` でファイル tool を作業ディレクトリに限定、`--safe-mode`、permission の allow / deny）と Bash sandbox（Seatbelt、ネットワーク不可）を使い、stream をキットが逐次監視して違反で即停止する | 既存のログイン（subscription）をそのまま使い、新しい長期 token を作らない。U4 の確認済みの経路から変えない。部品が少ない | Bash sandbox の実効（資格情報の読み取り不可・ネットワーク不可）と Keychain への IPC の遮断を model なしで確かめられない（NOT_TESTED）。sandbox は Claude Code の実装に依存する |
| B | Docker container で Linux 版の `claude` を動かし、`claude setup-token` の長期 token を環境変数で渡す。外向き通信は Anthropic の API だけを通す proxy を置く | #244 と同じく mount の照合で workspace 以外を見せないことを機械的に確かめられる | token が container 内の環境変数にあり、Agent の Bash から読める可能性がある（scrub の有無は NOT_TESTED）。長期 token の新規発行は U4 の確認の範囲外で、Human 判断が要る。egress proxy は未作成。Linux 版 2.1.310 の取得と hash の記録も未実施 |

**推奨は案 A**。理由: 案 B は資格情報（長期 token）を Run の環境に持ち込むため、漏洩した場合の影響が案 A より大きく、proxy と Linux バイナリという未検証の部品が増える。案 A の未検証点は、下の NOT_TESTED として Operator が明示的に受け入れない限り起動しない設計にし、stream の逐次監視で検出したら止める。

### 2.2 起動前の確認（キットが機械的に行い、1 つでも満たさなければ model を起動しない）

1. 事前登録（blob `5e757639…`）と候補表（blob `3f75aed6…`、fixture スクリプトが照合）が記録値と一致する
2. work root が DAT repo の外、結果ディレクトリ（`MRS-P02-*`）が未作成（`--skip-existing` のときだけ既存を飛ばす）、`<work-root>/.pilot.lock` がない
3. Operator の環境に `ANTHROPIC_API_KEY`・`ANTHROPIC_AUTH_TOKEN`・`CLAUDE_CODE_OAUTH_TOKEN`・`ANTHROPIC_BASE_URL`・`CLAUDE_CODE_USE_BEDROCK` / `VERTEX` / `FOUNDRY`・`CLAUDE_CODE_EFFORT_LEVEL`・`ANTHROPIC_MODEL` がない（U4-1 の再確認と Effort の上書き防止）。子プロセスには `PATH`・`HOME`・`USER`・`LOGNAME`・`SHELL`・`TMPDIR`・`LANG`・`TERM` だけを渡す
4. `--acknowledge-not-tested` に §2.4 の 5 項目がちょうど並んでいる（Operator が未検証の項目を受け入れた記録。1 つでも欠ければ停止）
5. macOS で `sandbox-exec` がある。`claude --version` が `2.1.310`（model は起動しない）
6. 採点の sandbox の対照 probe: host で listen ソケットを開き、sandbox の外からは接続でき、fixture と同じ sandbox-exec の profile の中からは `EPERM` / `EACCES` で拒否される。それ以外（timeout・refused・別の errno・probe の異常終了）は停止
7. `prepare 2` が成功する（失敗は `isolation-stop`、`modelLaunched: false`）

### 2.3 実行中の確認（stream の event ごとに検査し、違反でプロセスグループごと停止）

| 検査 | 停止時の status |
|---|---|
| init event がちょうど 1 つで、`claude_code_version` = `2.1.310`、`model` = 宣言値、`permissionMode` = `dontAsk`、`tools` = 6 つの集合、`mcp_servers` が空 | `control-deviation` |
| assistant message の `model` が宣言値と一致 | `control-deviation` |
| Bash の command と Read / Glob / Grep のパスに、資格情報（`.claude`、Keychain、`security`、`env` / `printenv`、`/proc/`、`.ssh`、`oauth` 等）またはネットワーク（`curl`、`wget`、`ssh`、`git push` / `fetch` / `clone`、`pip install`、URL 等）の参照がない | `policy-stop` |
| assistant message の usage の累計（message id ごと）が `--max-run-tokens` 以下 | `token-limit` |
| 経過時間が `--timeout-s` 以下 | `aborted-timeout` |

### 2.4 認証情報を読み出せない・持ち出せないことの確認方法と NOT_TESTED

| 項目 | 確認方法 | 状態 |
|---|---|---|
| ファイル tool（Read / Glob / Grep / Edit / Write）が `~/.claude` などを読めない | `--restricted` が作業ディレクトリに限定する（help の記述、Source claim）＋ deny ルール＋実行中の `policy-stop` 検査。予備検証後に trace の全 tool call を [A] が照合 | 起動前は NOT_TESTED（help の記述のみ）。実行中は検査で検出 |
| `bash-sandbox-denies-credential-read`: Bash（とそこから動く Python）が `~/.claude`・Keychain のファイルを読めない | Claude Code の sandbox（Seatbelt）と deny ルール。model なしで sandbox だけを動かす手段が CLI にない | **NOT_TESTED** |
| `bash-sandbox-denies-network`: Bash から外部へ送れない | `sandbox.network.allowedDomains: []`。同上 | **NOT_TESTED** |
| `keychain-ipc-from-sandbox`: sandbox 内から `securityd` への IPC で Keychain を読めない | Seatbelt のファイル制限では IPC を止められない可能性がある。`security` コマンドは deny と検査で止めるが、Python 等からの直接の IPC は止められると確かめていない | **NOT_TESTED** |
| `settings-file-applied`: `--settings` の内容が実際に効いている | `-p` では検証に失敗した settings が黙って無視される（help の記述）。init event の `permissionMode` と `tools` は照合するが、sandbox・deny の適用は stream に出ない | **NOT_TESTED**（一部だけ init で確認） |
| `effort-visible-in-trace`: 実効 Effort が trace に出る | stream の中の `effort` を含むキーの値をすべて集め、`high` だけかを見る。キー名は文書化されていない | **NOT_TESTED**（予備検証で確かめる対象） |

持ち出しの事後確認（[A]、予備検証の後）: `stream.jsonl` の全 tool_use を読み、資格情報のパス・環境変数・ネットワークの参照が 0 件であることを Issue #220 に記録する。`run.json`・`stream.jsonl` に token や資格情報の文字列が含まれていないかを確かめるまで、trace を repo や Issue に貼らない。

## 3. 止める条件（キットが自動で止める）

| 条件 | 動作 |
|---|---|
| §2.2 の確認のいずれかを満たさない | 起動前に停止（exit 2） |
| §2.3 の検査に当たった | その Run を停止して記録し、バッチを停止 |
| exit code が 0 以外、stream が result event で終わらない、tool_use と tool_result が対応しない、`is_error` | `runtime-error` として記録し、バッチを停止 |
| result event がなく使用量が分からないまま止まった | `totalTokens` を記録しない（0 で埋めない。累計の観測値は `runningTotalTokens`）。再開は Operator が使用量を `totalTokens` に記録してから |
| `--skip-existing` で再開し、既存 Run の `run.json` に `totalTokens` がない | 停止。既存 Run の `totalTokens` は予算の使用済みに加算する |
| 使用済み token + `--max-run-tokens` が `--budget-tokens` を超える | 次の Run を始めずに停止 |
| model を起動する前に止まった Run（`isolation-stop` かつ `modelLaunched: false`） | 消化済みにせず、再開時に `<work-root>/attempts/<runId>/attempt-<N>/` へ退避（上書きしない）してやり直す |

1 Run でも `completed` 以外ならバッチを止める（手順書 §5、予備検証は計測の成立を確かめるためのもので、異常のまま次の Run に進まない）。

## 4. Operator の手順

前提: 事前登録の成立（Gate 4）は Issue #220 に記録済み。予備検証 2 Run の予算は承認済み。キットは上限の既定値を持たず、毎回コマンドで渡す。

1. Gate 1（U4 の 3 点）を予備検証の直前に再確認し、Issue #220 に記録する（事前登録 §5）。Gate 2・3 の [A] の記録（本書 §1・§2 とテスト）を確かめる。
2. 本 PR の merge 後の main で dry-run を実行する（model は起動しない。`--dry-run-grade` は GitHub から revision を取得して workspace の作成と採点まで通す）:

   ```bash
   python3.12 scripts/model_role_split_pilot.py plan
   python3.12 scripts/model_role_split_pilot.py run --dry-run --dry-run-grade --work-root ~/dat-runs/mrs-pilot-dry \
     --cache ~/dat-runs/mrs-cache --timeout-s <秒> --max-run-tokens <tokens> --budget-tokens <tokens>
   python3.12 scripts/model_role_split_pilot.py summarize --work-root ~/dat-runs/mrs-pilot-dry
   ```

3. 本番（2 Run。コマンド 1 つ）:

   ```bash
   python3.12 scripts/model_role_split_pilot.py run --work-root ~/dat-runs/mrs-pilot-1 --cache ~/dat-runs/mrs-cache \
     --timeout-s <秒> --max-run-tokens <tokens> --budget-tokens <tokens> \
     --acknowledge-not-tested bash-sandbox-denies-credential-read,bash-sandbox-denies-network,keychain-ipc-from-sandbox,settings-file-applied,effort-visible-in-trace
   ```

   上限の値は Issue #220 の承認値（現時点は 1 Run 1800 秒・300,000 tokens、合計 600,000 tokens）を渡す。§6 のとおり見直しの見込みがあるため、本書には固定しない。起動時に表示される prompt の SHA-256 が dry-run と同じことを確かめる。
4. exit code が 0 なら 2 Run 完了。2 なら標準エラーの `STOP:` の理由を Issue #220 に記録する。再開は理由を解消し、同じ上限で `--skip-existing` を付けて行う。
5. 集計を保存する: `python3.12 scripts/model_role_split_pilot.py summarize --work-root ~/dat-runs/mrs-pilot-1 --output ~/dat-runs/mrs-pilot-1-summary.json`
6. [A] が手順書の手順 12 として、集計の `checks`（activationModel・activationEffort・traceComplete・toolCallsRecorded・tokens・cache・elapsed）、`proposedPilotJudgment`、`auxiliaryModels`（`modelUsage` に宣言外の model があれば、補助的な呼び出しかを [R] が判定）、各 Run の `totalTokens` と m、`mainRunEstimateTokens`（180 × 平均）を Issue #220 に記録する。`proposedPilotJudgment` は案で、PASS / FAIL の記録は手順書の手順 12 に従う。`activationEffort` が NOT_TESTED のときは PASS にしない。

## 5. 保存されるもの

`<work-root>/MRS-P02-<arm>/` に Run ごとに保存する。

| ファイル | 内容 |
|---|---|
| `run.json` | 宣言値、起動コマンド、上限、prompt と settings の SHA-256、session ID、起動前の確認結果、NOT_TESTED の一覧、trace から読んだ値（init の version・model・permissionMode・tools、応答 model、effort の値、tool call と tool result の件数、完全性、usage、modelUsage）、totalTokens、runningTotalTokens、wallClockMs、exit code、採点結果、status、`modelLaunched` |
| `settings.json` | Run に渡した settings（両 arm で同一） |
| `prompt.md` | 実際に渡した prompt |
| `stream.jsonl` / `stderr.log` | stream-json の出力（実効値の照合元） |
| `workspace/` | Agent の作業後の状態 |

## 6. 未確定事項

| 項目 | 状態 |
|---|---|
| 1 Run・合計の上限（`--timeout-s`・`--max-run-tokens`・`--budget-tokens`） | 承認値は 1 Run 300,000 tokens・30 分、合計 600,000 tokens。**#244 の実測から上限の見直しが要る見込み**（#244 では本物の repo の Task で 1 Run 1M〜3.2M tokens、95% 以上がキャッシュ入力。Runtime・model は異なる）。値は本書で決めず、Operator が Issue #220 で決めた値をコマンドで渡す。上限で止まった Run も m の下限の手がかりとして残す |
| token の定義 | キャッシュ入力（read / creation）を含めて数える（#244・EXP-001 と同じ考え方）。課金換算は #162 の定義で別に行う |
| 隔離 | §2.4 の 5 項目は NOT_TESTED。案 B（container）を採るかは予備検証の結果を見て Human が判断する |
| stream-json の形式 | init の各キー（`claude_code_version`・`permissionMode`・`tools`・`mcp_servers`）、assistant の `message.model`・`usage`、result の `usage`・`modelUsage` は Source claim と既存の利用例による想定で、2.1.310 での実際の形は予備検証で確かめる。キーが違えばキットは `control-deviation` で止まる（安全側）。その場合は Run の結果を記録し、キットを直す別 PR を起案する |
| 補助 model | Claude Code が補助的な処理に別 model を呼ぶ場合、`modelUsage` に現れる。activation の判定に含めるかは [R] が判定する（キットは止めずに `auxiliaryModels` として記録する） |
