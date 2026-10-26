# モデル役割分担の予備検証 手順書（#220、2 Run）

状態: **実行キットの起案（未実行）**。本書とキットは model 起動の許可ではありません。予備検証の起動は Operator（Human）が行います。承認範囲は [Issue #220 の 2026-10-25 の記録](https://github.com/s977043/dynamic-agent-topology/issues/220#issuecomment-6386579854)どおり「予備検証 2 Run（order 2 を arm A / B で 1 回ずつ）」に限ります。現時点の実測は 0 件です。

**資格情報の扱い（proxy 方式、2026-10-26 Human 承認）**: Run 専用の短命・低上限の資格情報を、Worker の container の外にある proxy の container にだけ置き、proxy が API 要求に認証を付けます。Worker の container には資格情報を mount しません。これにより確認 6 を「Worker が資格情報を読めない」と実測で示せる形にしました（§2.4）。案 D（資格情報を読めるリスクを承認 URL で受け入れて進む方式）と `--accept-credential-read-risk` は廃止しました。

**承認の前提（現在キットは model を起動しません）**:

- proxy 経由で Claude Code 2.1.310 の認証・課金経路が成り立つかは **NOT_TESTED**。確かめられるまで、キットは Run ごとの確認の後、model を起動せずに `isolation-stop` で止まる（キットの定数 `PROXY_AUTH_PATH = "NOT_TESTED"`）。NOT_TESTED を ack して進む引数はない。`PASS` に変えるのは、確認の証拠（§2.5）を添えたレビュー済みの変更だけ
- その確認が、承認済みの予算（1 Run 300k tokens・30 分、合計 600k）に収まらない場合は、Operator が予算を再承認する
- 資格情報の作成・ローテーション・失効は Human（Operator）の操作。キットと本書は手順と記録すべき項目（期限・上限・失効の確認）を示すだけ（§4 の 1・8）

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
- bind mount は **その Run の** `workspace`（`/work`、RW）、`input`（`/run-input`、ro、prompt）、Linux 版 Claude Code のディレクトリ（`/cc`、ro）の 3 つだけ。資格情報は mount しない
- 外向き通信と認証: Run の container は internal network にだけつながる。出口は proxy の container（同じ image、キット自身と Run 専用の資格情報だけを ro で mount、別の PID namespace）だけ。proxy は平文 HTTP の reverse proxy で、[Anthropic 形式の gateway として Claude Code が呼ぶ経路](https://code.claude.com/docs/en/llm-gateway-protocol)（`POST /v1/messages`、`POST /v1/messages/count_tokens`、`GET /v1/models`）だけを TLS で `api.anthropic.com` へ転送する。そのとき Worker が送る `Authorization` / `x-api-key` / `Proxy-Authorization`・hop-by-hop の header・`X-Forwarded-*` / `Forwarded` / `Via` / `Cookie` / `X-Real-IP` を捨て、資格情報を `x-api-key` として付ける（許可リストではなく削除リスト。必要な header を確定できないため）。CONNECT と他の経路は 403。`Transfer-Encoding: chunked` の要求は本文を読まずに 411 で拒否する。`POST /v1/messages` と `count_tokens` は body の `model` が宣言 model と一致しなければ 403
- proxy での使用量の強制: proxy は `POST /v1/messages` の応答から usage を読み、§1 の token の定義（`input_tokens + cache_creation_input_tokens + cache_read_input_tokens + output_tokens`）で Run の累計を取る。非 stream の JSON は応答の `usage`、SSE は `message_start` の `message.usage` に、`message_delta` の `usage`（公式 docs で累計値と明記: [Streaming messages](https://platform.claude.com/docs/en/build-with-claude/streaming)、2026-10-26 参照）を項目ごとに上書きした値。SSE が `message_stop` を受け取らずに終わった場合（途中切断）は usage が読めないものとして扱う。累計が `--max-run-tokens` を超えたら、以降の要求はすべて 403（理由 `token-limit`）で拒否する。`POST /v1/messages` の応答から usage が読めなければ、status が 200 以外（upstream への接続失敗を含む）でも以降をすべて拒否する（理由 `usage not measurable`。200 以外は課金されないというのは Source claim で未確認のため、安全側に倒す）。`POST /v1/messages` は同時に 1 本だけ転送し、転送中に届いた 2 本目は 429（理由 `concurrent billable request`）で拒否して記録する。上限の判定は転送前に行い、加算は応答の後なので、上限を超えうるのは最後に転送した 1 要求分まで。body の JSON に重複したキーがあれば 403（理由 `unreadable body`）、`Content-Length` が負・数字以外なら 400 で拒否する
- 全要求の method・path・status・拒否の理由・proxy が測った usage だけを `proxy.log` に残す（header と body は残さない）。proxy の stderr は `proxy.stderr.log` に残す
- Claude Code には `ANTHROPIC_BASE_URL=http://<proxy>:3128` と、資格情報ではない固定の placeholder の `ANTHROPIC_AUTH_TOKEN` を渡し、`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` を付ける（[gateway への接続](https://code.claude.com/docs/en/llm-gateway-connect)）
- 資格情報: Operator が作る Run 専用の短命・低上限の API 資格情報（§4 の 1）。proxy の container の `/proxy-secret/key` にだけ置く

採らなかった案: (1) host の macOS で Claude Code 自身の制限だけに頼る案（初版）。Read / Edit / Write が作業ディレクトリ外にも及びうる、Write したスクリプトの実行で監視をすり抜けられる、確認を model なしでできない、の理由で独立レビューで差し戻された。(2) 長期 token を環境変数で渡す案。Worker のプロセスから環境変数を読める可能性があるため。(3) 資格情報ファイルを Run の container に ro で mount し、読めるリスクを承認して進む案（案 D）。Worker の uid から読めることを実測した（§2.4 の旧方式）ため、資格情報を Worker に置かない本方式に替えた。

### 2.2 起動前の確認（バッチ開始時、1 つでも満たさなければ止める）

1. 事前登録（blob `5e757639…`）と候補表（blob `3f75aed6…`）が記録値と一致する
2. work root が DAT repo の外、結果ディレクトリ（`MRS-P02-*`）が未作成（`--skip-existing` のときだけ既存を飛ばす）、`<work-root>/.pilot.lock` がない、`<work-root>/quarantine/` に Run がない
3. Operator の環境に `ANTHROPIC_API_KEY`・`ANTHROPIC_AUTH_TOKEN`・`CLAUDE_CODE_OAUTH_TOKEN`・`ANTHROPIC_BASE_URL`・`CLAUDE_CODE_USE_BEDROCK` / `VERTEX` / `FOUNDRY`・`CLAUDE_CODE_EFFORT_LEVEL`・`ANTHROPIC_MODEL` がない
4. Run 専用の資格情報の記録: `--credential-expires-at`（UTC offset つき ISO 8601）が現在から 24 時間以内の未来、`--credential-limit`（Operator が設定した利用上限）が空でない。値は `run.json` の `preflight.runCredential` に残る（キットは上限を確かめられない。記録だけ）
5. `docker` があり daemon に接続できる。`--image` が `name@sha256:` で固定され手元にある。seccomp の SHA-256 が一致。`--claude-dir/claude` の SHA-256 が `9c64d9a7…7d54`。資格情報ファイルが空でない（キットの host 側は中身を読まない。読むのは proxy の container だけ）
6. 採点の sandbox の対照 probe（host）: listen ソケットに sandbox の外からは接続でき、fixture と同じ sandbox-exec の profile の中からは `EPERM` / `EACCES` で拒否される

### 2.3 Run ごとの確認（container を作った後、model を起動する前。1 つでも満たさなければ `isolation-stop`・`modelLaunched: false` で止める）

| # | 確認 | 方法（model を起動しない） |
|---|---|---|
| 1 | network が internal | `docker network inspect` の `Internal` が true |
| 2 | mount と制約 | proxy の container: bind mount がキットと資格情報の 2 つ（ro）と完全一致し、`PidMode` が空（PID namespace を共有しない）。Run の container: `docker inspect` の `Config.Env` が image の `Config.Env` と完全一致（Worker の環境変数は exec ごとに渡す）。`docker inspect` の全 mount を type・source（realpath）・destination・RW で 3 つと完全一致。`PidMode` が空。`HostConfig.Tmpfs` が `/tmp`・`/cc-home` と完全一致。`NetworkMode` が internal network。Privileged=false、CapAdd なし、CapDrop=ALL、ReadonlyRootfs=true、no-new-privileges、seccomp が起動時の profile と JSON として一致 |
| 3 | Runtime | container 内の `claude --version` が `2.1.310` |
| 4 | settings の適用と sandbox の可用性 | container 内の `claude sandbox status`（2.1.310 の隠しサブコマンド。posture を JSON で出すだけで model を起動しない）が `enabled: true`・`enabledSource: settings`・`unavailableReason: null`・`strictMode: true`・`filesystemPolicy: strict`・`autoAllowBashIfSandboxed: false` |
| 5 | 外向き通信の遮断（対照つき） | Run の container の中で: loopback の listen ソケットには接続できる（probe が動く対照）、`1.1.1.1:443`・internal network の IPAM Gateway の 443 への直接接続が `ENETUNREACH` / `EHOSTUNREACH`、`host.docker.internal` は名前解決できないか同じ errno、proxy の port には接続できる、proxy への `CONNECT api.anthropic.com:443` が 403（tunnel で認証を迂回できない）、許可外の経路 `GET /` が 403。許可された経路は課金が起きうるため probe しない。timeout・別の errno・probe の異常終了は確認できないとして止める |
| 6 | 資格情報が Worker の container にない | Run の uid・Worker と同じ環境変数で、Claude Code の Bash sandbox の外から実行する（sandbox が効かなかった場合の最悪条件。2.1.310 には model なしで sandbox の中でコマンドを動かす手段がない）。開始の印 `PROBE_STARTED` の後、`ANTHROPIC_API_KEY`・`CLAUDE_CODE_OAUTH_TOKEN`・`ANTHROPIC_CUSTOM_HEADERS` がない、`ANTHROPIC_AUTH_TOKEN` が placeholder と一致、環境変数の名前が image の ENV・Worker に渡す環境変数・`HOSTNAME` の和に収まる、`/proxy-secret`・`/proxy/kit.py`・`/cc-home/.credentials.json`・`/tmp/home/.claude` がない、`/proc` に proxy のプロセスが見えない、をすべて満たせば `CREDENTIAL_ABSENT`・exit 0。1 つでも当たれば `BLOCK: …`（exit 3）で止める。probe が始まらない・他の exit code も止める。承認で通す例外はない |
| 7 | 認証・課金経路・proxy の使用量の強制 | キットの定数 `PROXY_AUTH_PATH` が `PASS` であること。現在は `NOT_TESTED` のため、確認 1〜6 の後に必ず `isolation-stop`（`modelLaunched: false`）で止まる（§2.5） |

確認の後、model を起動する前に proxy の stderr が空であることも確かめる。確認結果は各 `run.json` の `isolation` に残る。model を起動する前に止まった Run は消化済みにせず、`--skip-existing` での再開時に `<work-root>/attempts/<runId>/attempt-<N>/` へ退避（上書きしない）してやり直す。

### 2.4 実測（2026-10-26、model は起動していない）

**proxy 方式（現行）**: キットの関数（`proxy_run_command`・`check_proxy_container`・`docker_run_command`・`check_container`・`EGRESS_PROBE`・`AUTH_PROBE`）を呼ぶ検査用のスクリプトを、ダミーの資格情報ファイルと派生 image（`mrs-pilot-sandbox@sha256:c8d259e6…`）で実 docker に対して実行した。Linux 版 `claude` は手元になかったため、確認 3・4 はこの回では実行していない（初回の結果は下の旧方式の表）。container・network は後片付け済み。

| # | 結果 |
|---|---|
| 1 | PASS |
| 2 | PASS（proxy: kit と資格情報の 2 つ・PID namespace 非共有。Run: 3 つの mount の完全一致・資格情報なし・PID namespace 非共有・seccomp 一致） |
| 3・4 | 今回は未実行（旧方式で PASS。mount から資格情報を除いた以外の変更はない） |
| 5 | PASS（LOOPBACK CONNECTED / DIRECT ENETUNREACH / PROXY_REACHABLE CONNECTED / `CONNECT api.anthropic.com:443` 403 / `GET /` 403。proxy.log に 2 件、ダミーの資格情報の文字列は proxy.log に出ない） |
| 6 | **PASS**（`CREDENTIAL_ABSENT`、exit 0）。対照: 同じ probe を proxy の container で動かすと exit 3、`BLOCK: env ANTHROPIC_AUTH_TOKEN is not the placeholder; path /proxy-secret; path /proxy/kit.py; proxy process visible`。probe が資格情報の存在を検出できることを確かめた |
| 7 | **NOT_TESTED**（認証・課金経路。model を起動しないと確かめられない） |

**旧方式（案 D、資格情報を Run の container に mount）**: 確認 1〜6 を、ダミーの資格情報ファイルで実行した。

| # | 結果 |
|---|---|
| 1〜2 | PASS（mount 4 つの完全一致、tmpfs 2 つ、seccomp 一致） |
| 3 | PASS（`2.1.310 (Claude Code)`） |
| 4 | PASS（派生 image）。`python@sha256:34386ef0…` のままでは `unavailableReason: bubblewrap (bwrap) not installed, socat not installed` で FAIL |
| 5 | PASS（LOOPBACK CONNECTED / DIRECT ENETUNREACH / example.com 403 / api.anthropic.com 200。proxy.log に 2 件） |
| 6 | **FAIL**（`BLOCK: worker uid can read the credential file`、exit 3）。Claude Code 自身が読む必要があるファイルなので、同じ uid の Worker のプロセスからも読める |

補足（観測）: 同じ制約の container の中で、同じ uid の別プロセスの `/proc/<pid>/mem` を開けた（`ptrace_scope` は読めない）。このため、資格情報を Worker と同じ container のプロセス（file descriptor を含む）に置く方式では確認 6 に相当する確認は通らない見込みだった。proxy 方式では資格情報を持つプロセスが別の container・別の PID namespace にあり、確認 6 の `/proc` の検査で見えないことを確かめる。

**2026-10-26 の追加の実測（独立レビュー後の変更、model は起動していない）**: 同じ派生 image・ダミーの資格情報で、新しい確認を実 docker に対して実行した（container の制約は簡略。後片付け済み）。

| 確認 | 結果 |
|---|---|
| 2 の `Config.Env` の完全一致 | PASS |
| 5 の IPAM Gateway | **FAIL**（`GATEWAY ERRNO ECONNREFUSED`。Docker Desktop の internal network でも Gateway の IP には到達でき、RST が返る。待ち受けている port があれば Worker から接続できうる）。キットは確認 5 で止まる |
| 5 の `host.docker.internal` | PASS（`NORESOLVE`） |
| 5 のその他・proxy の stderr | PASS（従来どおり。proxy.log に理由 `route` で 2 件、stderr は空） |
| 6 の環境変数の名前の検査 | PASS（`CREDENTIAL_ABSENT`）。対照: 余分な環境変数を 1 つ足すと `BLOCK`・exit 3 |

確認 5 の Gateway の FAIL は未解決で、解消（Gateway への経路を塞ぐ方式の追加など）まで、確認 7 と別に、キットは model を起動しない。

### 2.5 proxy 方式の境界と、起動前に確かめること

| 区分 | 内容 |
|---|---|
| 境界 1（毎 Run 必須） | 資格情報は proxy の container にだけある。§2.3 確認 2（Run の container の mount に資格情報がない、PID namespace 非共有）と確認 6（環境変数・パス・プロセスのどれにも資格情報がない、対照で検出力を確認済み）を Run ごとに確かめ、FAIL なら起動しない |
| 境界 2（毎 Run 必須） | Run の container の外への経路は proxy だけで、proxy は許可した 3 経路だけを転送する。§2.3 確認 5 を Run ごとに確かめる。Run 後に `proxy.log` の確認後の要求がすべて許可経路で、`POST /v1/messages` を含み、拒否・読めない行が 0 件であることを照合し、違えば `egress-anomaly` で止める。各要求の upstream の status（429 などの上限超過の拒否を含む）を `proxyRequests.statuses` に残す。proxy の stderr が空でなければ `egress-anomaly` |
| 境界 4（毎 Run 必須） | proxy が Run の使用量を測り `--max-run-tokens` を強制する（§2.1）。超過後の拒否が記録されれば `token-limit`。Run 後に proxy の累計と stream の `result.usage` の合計が一致しなければ `usage-mismatch` で止める |
| proxy の閉鎖（fail-closed） | `POST /v1/messages` の usage が読めないと、proxy はその後の要求をすべて 403 で拒否する（閉鎖）。usage のない 200 以外の応答、途中で切れた SSE、proxy 内の例外（理由 `proxy error <例外名>`）のどれでも閉鎖し、理由を `proxy.log` に残す。例外でも並行要求の枠は必ず解放する。**一時的な 429（rate limit）・529（overloaded）の応答 1 回でも閉鎖し、Run はそこで止まる**。Claude Code の再試行で続けられる場合でも続けない。この挙動の頻度は確認 7 の (10) で観察する |
| 本文サイズの上限 | proxy は `Content-Length` が 32 MiB（`MAX_BODY_BYTES`）を超える要求を、本文を読む前に 413 で拒否して記録し、接続を閉じる（閉鎖はしない）。根拠: Messages API の要求サイズの上限 32 MB（[API の概要](https://docs.claude.com/en/api/overview) の request size limits、2026-10-26 参照、Source claim）。これより大きい要求は API が受け付けないため、転送しても意味がなく、proxy のメモリを守るために先に拒否する |
| 境界 3（毎 Run 必須） | Run の保存物に資格情報の形の文字列があれば quarantine（mode 700）に移して停止し、commit しない（§3.2） |
| 残るリスク | Worker は資格情報を読めないが、proxy 経由で宣言 model の許可経路を使える。proxy は `--max-run-tokens` を超えた後の転送を拒否するが、並行要求の 1 件分は超えうる。資格情報の上限は最後の歯止めとして、Run 専用・短命・低上限にし、Run 後に失効させる（§4 の 1・8）。資格情報の上限の実効性はキットでは確かめられない |
| 起動前に確かめること（確認 7、現在 NOT_TESTED） | (1) Claude Code 2.1.310 が `ANTHROPIC_BASE_URL`・placeholder の `ANTHROPIC_AUTH_TOKEN` で起動し、proxy の付けた `x-api-key` で認証が通る。(2) 課金が Run 専用の資格情報の所有者（Console 側）に per-token で付く（公式 docs は gateway の資格情報を使うと subscription の上限ではなくその資格情報の所有者に per-token で課金されると書く: [Subscriptions and gateways](https://code.claude.com/docs/en/llm-gateway#subscriptions-and-gateways)）。これは U4（課金経路）の前提を変えるため、Gate 1 で再確認する。(3) 許可 3 経路以外が要らない。(4) 上限を超えた要求が拒否される（status の記録で確認）。(5) stream-json の init・usage が従来どおり出る。(6) proxy が実際の SSE・JSON の応答から usage を読めて、その累計が stream の `result.usage` と一致する（usage の形は公式 docs による Source claim で、実応答では未確認）。(7) Claude Code が chunked の要求を送らない。(8) Claude Code が `POST /v1/messages` を並行に送らない（429 の `concurrent billable request` が記録されない）。(9) 200 以外の応答（4xx・5xx）に課金が付かない（Source claim で未確認。キットは usage が読めなければ閉鎖するので、確認できるまで 200 以外の応答 1 回で Run は止まる）。(10) 一時的な 429・529 がどれだけ起き、それによる閉鎖で Run が止まるか（`proxy.log` の status と reason で観察し、頻度を Issue #220 に記録する） |
| 確認 7 の進め方 | 確認 7 は Worker 側に資格情報を置かない条件で行う。キットの外で試す場合も、資格情報は proxy（または同等の Worker と別の container・プロセス）にだけ置き、Worker の環境変数・ファイル・設定に入れない。上の確認には model の呼び出し（課金）が要る。確認の計画と見込み token を Issue #220 に書き、承認済みの予算（1 Run 300k tokens・30 分、合計 600k）に収まらない場合は Operator が予算を再承認する。結果（PASS / FAIL と根拠）を Issue #220 に記録し、PASS の場合に限り、その記録を添えたレビュー済みの変更で `PROXY_AUTH_PATH` を `PASS` にする。キットに NOT_TESTED を ack して進む引数はない |
| 出典 | [LLM gateway](https://code.claude.com/docs/en/llm-gateway)、[gateway への接続](https://code.claude.com/docs/en/llm-gateway-connect)、[gateway の互換性（呼ばれる経路・header）](https://code.claude.com/docs/en/llm-gateway-protocol)（2026-10-26 参照）。Source claim であり、2.1.310 での実際の挙動は確認 7 まで NOT_TESTED |

## 3. 止める条件（キットが自動で止める）

| 条件 | 動作 |
|---|---|
| §2.2 の確認のいずれかを満たさない | 起動前に停止（exit 2） |
| §2.3 の確認のいずれかを満たさない | その Run を `isolation-stop`（`modelLaunched: false`）として残し、バッチを停止 |
| 実行中の stream の異常（§3.1） | その Run を停止して記録し、バッチを停止 |
| exit code が 0 以外、stream が result event で終わらない、tool_use と tool_result が対応しない、`is_error` | `runtime-error` として記録し、バッチを停止 |
| Run 中の proxy の記録に、拒否された要求・読めない行がある、許可経路以外がある、`POST /v1/messages` が 0 件、または proxy の stderr が空でない | `egress-anomaly` として記録し、バッチを停止 |
| proxy が累計の超過で要求を拒否した | `token-limit` として記録し、バッチを停止 |
| proxy の usage の累計と stream の `result.usage` の合計が一致しない | `usage-mismatch` として記録し、バッチを停止 |
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

前提: 事前登録の成立（Gate 4）と予備検証 2 Run の予算、proxy 方式の承認は Issue #220 に記録済み。確認 7（§2.5）が PASS になるまで、手順 4 は model を起動せずに止まる。キットは上限の既定値を持たず、毎回コマンドで渡す。

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
   - Run 専用の資格情報（Operator の操作）: Run 専用の API 資格情報を、短い期限（24 時間以内）と低い利用上限を付けて作り、値だけを 1 行で DAT repo の外の専用ディレクトリ（mode 700）のファイルに保存する。Console で期限・上限をどう設定できるかは未確認（§6）。Issue #220 に、資格情報の識別名（値は書かない）・期限・上限・作成日時を記録する。値をこの repo・Issue・端末の出力に出さない。ローテーションが要るときは新しく作り直し、古いものを失効させて同じ項目を記録する
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
     --credential-expires-at <期限 例 2026-10-27T09:00:00+09:00> --credential-limit "<利用上限 例 USD 10>" \
     --timeout-s <秒> --max-run-tokens <tokens> --budget-tokens <tokens>
   ```

   資格情報ファイルは proxy の container にだけ mount される。確認 7 が NOT_TESTED の間は、確認 1〜6 の後に `isolation-stop`（`modelLaunched: false`）で止まる。

   上限は Issue #220 の承認値を渡す（§6 のとおり見直しの見込みがあるため本書に固定しない）。起動時に表示される prompt の SHA-256 が dry-run と同じことを確かめる。
5. exit code が 0 なら 2 Run 完了。2 なら標準エラーの `STOP:` の理由を Issue #220 に記録する。再開は理由を解消し、同じ上限で `--skip-existing` を付けて行う。
6. 集計を保存する: `python3.12 scripts/model_role_split_pilot.py summarize --work-root ~/dat-runs/mrs-pilot-1 --output ~/dat-runs/mrs-pilot-1-summary.json`
7. [A] が手順書の手順 12 として、集計の `checks`（activationModel・activationEffort・traceComplete・toolCallsRecorded・tokens・cache・elapsed）、`proposedPilotJudgment`、`auxiliaryModels`、`quarantined`、各 Run の `totalTokens` と m、`mainRunEstimateTokens`（180 × 平均）、`proxy.log` の要求の一覧（method・path・status）を Issue #220 に記録する。`proposedPilotJudgment` は案。`activationEffort` が NOT_TESTED のときは PASS にしない。
8. 失効（Operator の操作）: バッチが終わったら（停止を含む）Run 専用の資格情報を失効させ、失効の日時と、失効後に使えないことの確認方法・結果（Console 上の状態など。API 呼び出しで確かめる場合は課金に注意）を Issue #220 に記録する。資格情報ファイルを消す

## 5. 保存されるもの

`<work-root>/MRS-P02-<arm>/` に Run ごとに保存する。

| ファイル | 内容 |
|---|---|
| `run.json` | 宣言値、起動コマンド、上限、prompt と settings の SHA-256、session ID、container・proxy・network の名前、起動前の確認結果、`isolation`（§2.3 の結果）、trace から読んだ値（init、応答 model、effort の値、tool call と tool result の件数、完全性、usage、modelUsage）、totalTokens、runningTotalTokens、wallClockMs、exit code、採点結果、status、`modelLaunched` |
| `input/prompt.md` | 実際に渡した prompt |
| `stream.jsonl` / `stderr.log` | stream-json の出力（実効値の照合元） |
| `proxy.log` | proxy が受けた要求の method・path・許可・status・拒否の理由・usage（header・body・資格情報は残さない） |
| `proxy.stderr.log` | proxy の stderr（空であること） |
| `workspace/` | Agent の作業後の状態 |

## 6. 未確定事項と NOT_TESTED

| 項目 | 状態 |
|---|---|
| 資格情報が Worker の container にないこと（§2.3 確認 6） | **PASS（2026-10-26 実測、ダミーの資格情報、対照つき）** |
| proxy 経由の認証・課金経路（§2.3 確認 7） | **NOT_TESTED**。確かめるまでキットは model を起動しない（§2.5）。課金が per-token（Console）になると U4 の前提が変わるため Gate 1 で再確認する |
| Run 専用の短命・低上限の資格情報の作り方 | Console で期限・利用上限をどう付けられるか、上限超過がどの status で拒否されるかは未確認（**NOT_TESTED**）。Operator が作成時に確かめ、Issue #220 に記録する |
| Claude Code の Bash sandbox が container 内で動くか | `sandbox status` は PASS だが、実際のコマンドが bubblewrap の中で動くかは未確認（**NOT_TESTED**）。同じ制約で `bwrap --unshare-user --unshare-net --unshare-pid` は動き、`--proc /proc` の mount は `Operation not permitted` だった。sandbox が動かなければ Bash が失敗し、Run は `runtime-error` などで止まる見込み |
| settings の deny・denyRead が実際に効いていること | `sandbox status` は enabled・strict を返すが、個々のルールの適用は出力に出ない（**NOT_TESTED**） |
| proxy の usage の集計と上限の強制 | handler の部品（SSE・JSON の usage の読み取り、途中切断の SSE、上限・model・重複キー・chunked・不正な Content-Length の拒否、並行要求の 429、header の削除、本文サイズの上限の 413）はネットワークなしのテストで確認。handler 全体も、偽の upstream と 127.0.0.1 の実ソケットで結合テスト済み（途中切断の SSE・200 以外・例外での閉鎖、並行の 429、413）。実際の API の応答での集計は **NOT_TESTED**（確認 7） |
| 確認 5 の IPAM Gateway | Docker Desktop で **FAIL**（§2.4）。解消するまでキットは model を起動しない |
| proxy の許可経路で足りるか | 公式 docs の 3 経路以外が要るか、SSE の stream を proxy がそのまま中継できるかは未確認（**NOT_TESTED**）。要る場合は proxy で拒否され、Run 後の照合で `egress-anomaly` になる |
| 1 Run・合計の上限（`--timeout-s`・`--max-run-tokens`・`--budget-tokens`） | 承認値は 1 Run 300,000 tokens・30 分、合計 600,000 tokens。**#244 の実測から上限の見直しが要る見込み**（#244 では本物の repo の Task で 1 Run 1M〜3.2M tokens、95% 以上がキャッシュ入力。Runtime・model は異なる）。値は本書で決めず、Operator が Issue #220 で決めた値をコマンドで渡す |
| stream-json の形式 | init の各キー、assistant の `message.model`・`usage`、result の `usage`・`modelUsage` は Source claim による想定で **NOT_TESTED**。キーが違えば `control-deviation` で止まる（安全側） |
| 実効 Effort が trace に出るか | **NOT_TESTED**。出なければ `activationEffort` は NOT_TESTED になり、予備検証を PASS にしない |
| 補助 model | `modelUsage` に宣言外の model が出た場合は止めずに `auxiliaryModels` として記録し、activation の判定に含めるかは [R] が判定する |
