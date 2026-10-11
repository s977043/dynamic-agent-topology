# EXP-001 r02 以降の候補 G 起動キット（run-kit-g）

r02 以降の残り 16 Run を、T0・T1 とも候補 G の同一構成で 1 Run ずつ実行するためのキットです。Issue #15 の環境 disposition 提案（[6105758769](https://github.com/s977043/dynamic-agent-topology/issues/15#issuecomment-6105758769)）と、独立 Reviewer の `CONDITIONAL ACCEPT`（[6106413517](https://github.com/s977043/dynamic-agent-topology/issues/15#issuecomment-6106413517)）の条件 1〜3 に対応します。

- このキットは model 起動の許可ではありません。Run の prepare・起動は、条件の充足を確認した環境 Judgment と、Issue #15 の進行 Gate（前 Run の `EXP-001 Run acceptance: ACCEPT`）の後に限ります。
- 元にしたのは [T1 r01 起動キット](../retry-t1-r01/launch/README.md) と [docs/EXP-001_RETRY_T1_R01_PYTHON_ENV.md](../../../../docs/EXP-001_RETRY_T1_R01_PYTHON_ENV.md) の (a)〜(g)・証跡回収です。T1 r01 のキットと文書は変更していません。
- 変えたのは Run 固有の値（runId、workspaceId、fixture、prompt の SHA-256、Gate 11 の期待 FAIL）だけです。環境の構成は `environment.conf` に固定しています。

## ファイル

| パス | 内容 |
| --- | --- |
| `run.sh` | 1 Run 分の実行スクリプト（preflight 全項目 → (g) → 証跡回収 → 後始末）。`--dry-run` は (g) の直前で止める |
| `environment.conf` | 環境の想定値（image digest、Codex 版・バイナリ SHA-256、seccomp・config・(g) の SHA-256、起動行、docker context・server version・kernel） |
| `expectations/gate11.tsv` | Scenario 別の Gate 11 期待 FAIL（model 非起動で記録した値） |
| `expectations/fixtures.sha256` | Scenario 別の fixture のファイル集合と SHA-256 |
| `container/*.sh.in`・`host/*.sh.in` | T1 r01 の doc-extracted スクリプトから、Run 固有の値だけを `@@KEY@@` に置き換えたテンプレート |
| `container/proc-check.sh`・`container/config-never.sh`・`host/collect-evidence.sh` | T1 r01 の doc-extracted と同一のバイト列 |
| `container/g.sh` | T1 r01 の (g) ブロックと同一のバイト列（唯一の model 起動操作） |
| `host/render.py` | テンプレートの描画。値は許可パターンに一致するものだけ受け付ける |
| `host/gates.py` | host 側の検査（matrix 順、run-meta、fixture、bind 元、記録フォーマット）と attempt の予約 |
| `selftest.sh` | T1 r01 の値で描画すると T1 r01 のスクリプトとバイト単位で一致することの確認と、記録フォーマット・attempt 予約・引数の陰性テスト（Docker・Codex・gh 不要） |
| `rehearsal/` | 実験枠外の練習課題（T1 r01 キットの `leap.py` 課題と prompt を流用）と、練習用 run-meta のテンプレート |
| `SHA256SUMS` | 本ディレクトリの全ファイル（自身を除く）の SHA-256 |

## 使い方

前提: Operator host（Docker Desktop、context `desktop-linux`）、Python 3.12 + PyYAML、Codex 0.160.0 linux-arm64 musl の vendor ディレクトリ（取得方法は T1 r01 キット README の `CODEX_DIR`）、`gh`（実 Run のみ。`GH_TOKEN` はコマンド単位で渡す）。

1. `bash selftest.sh <python3.12>` が `PASS: selftest` になることを確認する。
2. 実 Run（Issue #15 の進行 Gate を満たした後だけ）:

   ```bash
   GH_TOKEN=... bash run.sh \
     --run-id EXP-001-train-normalize-name-r02-T1 \
     --workspace-id <新しい opaque ID> \
     --fixture fixtures/exp-001/train/normalize-name \
     --work-root <repo 外の作業ディレクトリ> --repo <clone> \
     --codex-dir <vendor/aarch64-unknown-linux-musl> --python <python3.12> \
     --prior-accept-comment <前 Run の ACCEPT コメント ID> \
     --env-judgment-comment <条件充足後の環境 Judgment コメント ID>
     # 同じ runId に attempt の記録がある場合だけ: --slot-disposition-comment <ID>
   ```

   キットは `origin/main` に merge 済みのものと同一でなければ STOP します。prepare は `pilot/OPERATOR.md` の `prepare_pilot_run.py` を、`<work-root>/runs/<runId>/<時刻>/checkout`（`origin/main` の detached worktree）で実行します。
3. 練習課題: `--mode practice --run-id PRACTICE-leap-r01 --fixture experiments/EXP-001-t0-vs-t1/pilot/run-kit-g/rehearsal/fixture` に、上と同じ `--workspace-id`・`--work-root`・`--repo`・`--codex-dir`・`--python` を付けて実行する。練習モードは常に dry-run（(g) の直前で停止）です。model を起動する練習は `--practice-model` を付けたときだけ (g) に進み、オーガナイザーの判断があるまで使わない。

`<work-root>/runs/<runId>/<時刻>/status.log` に全工程を記録します。`<work-root>/locks/<runId>.lock` は (g) の直前に作り、存在すれば同じ runId では起動しません。

### attempt の記録（実 Run のみ）

`pilot/OPERATOR.md` の「通常Runでは同じrunIdを再prepareしません」を機械的に守るため、実 Run は prepare の直前に `<home>/.exp001-run-kit-g/attempts/<runId>/attempt-<N>` を `mkdir` で原子的に予約します。

- `<home>` は OS のユーザー DB（`pwd.getpwuid`）から引きます。環境変数 `HOME` にも `--work-root` にも依存しません。
- `HOME` がユーザー DB の home と食い違う場合は STOP します。台帳ディレクトリが無い・ディレクトリでない・Operator 所有の mode 700 でない・読めない場合も STOP します。
- 台帳は最初に一度だけ Operator が作ります: `mkdir -p -m 700 ~/.exp001-run-kit-g/attempts`。キットは自動では作りません（別の場所に新しい台帳ができるのを防ぐため）。
- 記録は preflight の STOP や `--dry-run` の後も残し、キットは削除しません。
- 記録がある runId を再実行すると、引数検査の段階で STOP します。続けるには、Issue #15 にレビュー済みの slot disposition を記録し、そのコメント ID を `--slot-disposition-comment` で渡します。このコメントには、次の attempt 番号が書かれている必要があります。
- 練習モードには、この制約を掛けません。

この仕組みは、うっかり起きる同じ slot の再 prepare・再実行を防ぐためのものです。Security Boundary ではありません（`pilot/FREEZE.md` と同じ立場）。台帳を手で消す、別のユーザーや別のマシンで実行する、といった意図的な迂回は防げません。Run の記録は最終的に Issue #15 と `runs/` で照合します。

## パラメータ

| パラメータ | 内容 | 照合 |
| --- | --- | --- |
| `--run-id` | matrix の runId（練習は `PRACTICE-` 始まり） | matrix 順で次の Run であること、前の Run がすべて結果 Artifact を持つこと |
| `--workspace-id` | 非秘密の opaque ID | 形式、既存 run-meta・infrastructure-failures の ID と重複しないこと |
| `--fixture` | repo 相対の fixture パス | 期待値表と、凍結 scenario の `fixturePath` と一致すること |
| prompt | prepare が生成する `runs/pilot-codex/<runId>/prompt.md`（指定しない） | SHA-256 が `run-meta.yaml` の `promptSha256` と一致、先頭行の runId |
| Gate 11 期待 FAIL | `expectations/gate11.tsv` の Scenario 行（run-meta の scenario で選ぶ） | sandbox 内の Evidence command の出力 |
| `--prior-accept-comment` | 直前の matrix Run の acceptance コメント | 投稿者 `s977043`、下記「Run acceptance」の記録フォーマット。フォーマット導入前の T1 r01 の acceptance は、#15 の 6106366753 に限り判定行だけで受け付ける |
| `--env-judgment-comment` | 環境 Judgment のコメント（Issue #15） | 投稿者 `s977043`、下記「環境 Judgment」の記録フォーマット（無条件の ACCEPT。`CONDITIONAL` は STOP） |
| `--slot-disposition-comment` | 記録済み attempt がある runId を進めるための disposition（Issue #15） | 投稿者 `s977043`、下記「slot disposition」の記録フォーマット、attempt 番号 = 記録済み件数 + 1 |
| `--practice-model` | 練習モードで model 起動まで進める | 実 Run では指定すると STOP。指定しない練習モードは常に dry-run |
| `--work-root`・`--repo`・`--codex-dir`・`--python`・`--auth-file` | 実行場所・入力 | `--work-root` が repo 外、`--auth-file` は既定 `~/.codex/auth.json`（内容は読まない） |

## 記録フォーマット（機械照合）

キットは、コメント本文の各行の前後の空白を除いたうえで、次の行が**完全一致**で存在することを確認します。投稿者（`s977043`）と Issue も照合します。本文はログに残しません。

3 つの形式のいずれにも、`docs/AGENT_HARNESS.md` の自律境界が求める独立 Reviewer の記録として、`Reviewer:` で始まり `runtime:`・`model:`・`session:`（8 文字以上の ID）を含む行が必須です。例: `Reviewer: 独立 Reviewer（runtime: codex 0.160.1、model: gpt-6-luna、session: <session ID>）`。この行が無ければ STOP します。

### 環境 Judgment（`--env-judgment-comment`、Issue #15）

```text
Reviewer: <runtime: …、model: …、session: <ID>>
EXP-001 r02+ environment disposition: ACCEPT
kit: PR #<番号> merge <40 桁の merge commit SHA>
condition-1: <Scenario 別 Gate 11 期待 FAIL の根拠へのリンク>
condition-2: <一般化キットとリハーサル・レビューの根拠へのリンク>
condition-3: <Run ごとの構成照合の根拠へのリンク>
```

- `environment disposition: CONDITIONAL` を含む行が 1 つでもあれば STOP します。
- `kit:` の SHA は `origin/main` に含まれている必要があります。その SHA の `run-kit-g/SHA256SUMS` が、実行するキットの `SHA256SUMS` とバイト単位で一致しなければ STOP です（キットを変更したら Judgment を取り直す）。
- `condition-1`〜`3` は、それぞれちょうど 1 行の `https://github.com/s977043/dynamic-agent-topology/...` リンクです。
- 条件 4（r01 の開示）は集計時の条件のため、ここでは照合しません。

### Run acceptance（`--prior-accept-comment`）

```text
Reviewer: <runtime: …、model: …、session: <ID>>
EXP-001 Run acceptance: ACCEPT
runId: <直前の matrix Run の runId>
```

`runId:` 行が対象の runId と一致し、他の runId を名指ししていないことを確認します。

### slot disposition（`--slot-disposition-comment`、Issue #15）

```text
Reviewer: <runtime: …、model: …、session: <ID>>
EXP-001 slot disposition: NEW-ATTEMPT
runId: <runId>
attempt: <記録済み attempt 数 + 1>
reason: <同じ slot の新しい attempt を認める理由（10 文字以上）>
```

T1 r01 の acceptance（6106366753）は、フォーマット導入前の例外として、直前 Run が r01-T1 の場合に限り判定行だけで受け付けます（このコメントにも Reviewer 行はあります）。

## Scenario 別の Gate 11 期待 FAIL

2026-10-11 に、各 fixture を repo 外の新しい一時ディレクトリへコピーし、候補 G の image・seccomp・コンテナ制約（`--network none` を追加、auth なし、`config.toml` は (c) のバイト列）で `codex sandbox -P t1-workspace -C /work -- bash -lc 'PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests'` を実行して記録しました。model は起動していません。

| Scenario | exit | `Ran N tests` | 結果行 | 失敗項目 | アサーション |
| --- | --- | --- | --- | --- | --- |
| train-normalize-name | 1 | 2 | `FAILED (failures=1)` | `FAIL: test_trims_and_lowercases` | `AssertionError: 'ALICE' != 'alice'` |
| test-clamp-boundaries | 1 | 3 | `FAILED (failures=1)` | `FAIL: test_low_boundary` | `AssertionError: 10 != 0` |
| regression-safe-divide | 1 | 2 | `FAILED (failures=1)` | `FAIL: test_zero_division_contract` | `AssertionError: None != 0.0` |
| practice-leap（練習課題） | 1 | 3 | `FAILED (failures=1)` | `FAIL: test_century_is_not_leap` | `AssertionError: True is not false` |

各 fixture は `freeze.yaml` の gitBlobSha と一致し、実行前後でファイル集合と SHA-256 が一致しました（`__pycache__` なし）。`nonmodel-1-5.sh` は、exit 1・出力に `bwrap:` / `command not found` が無い・`Ran N tests`・結果行の完全一致・FAIL/ERROR 項目がちょうど 1 つ・その項目名・アサーション行の完全一致をすべて満たす場合だけ PASS します。

## preflight（毎 Run・省略不可）

T1 r01 の Gate 1〜13 の番号を残し、retry 固有の項目を通常 Run の同等の検査に置き換えています。

| Gate | 通常 Run での内容 | T1 r01 との違い |
| --- | --- | --- |
| 1 | `validate_experiment_freeze.py` PASS | 同じ |
| 2 | matrix 順で直前の Run が single-run validation PASS、ACCEPT コメントを確認 | T0 r01 固定 → 直前の Run |
| 3 | 対象と以降の slot に run directory・infrastructure-failures が無い | archive 照合 → 未試行の確認 |
| 4 | `origin/main` の clean な detached checkout、workspace が未作成 | 同じ |
| 5 | workspaceId の形式と一意性 | 旧 preparation の退避 → 不要（再 prepare しない） |
| 6 | 無変更の `prepare_pilot_run.py` で prepare し、差分が run directory だけ | reprepare → 通常の prepare |
| 7 | prompt の SHA-256 = run-meta `promptSha256`、先頭行の runId | archive の prompt との一致 → run-meta との一致 |
| 8 | run-meta の runId・workspaceId・blockId・scenario・condition・repetition・executionOrder が matrix・引数と一致、fixture が凍結 scenario と一致 | archive との一致 → matrix との一致 |
| 9 | workspace = fixture（ファイル集合・SHA-256）= 記録済みハッシュ | 同じ（記録済みハッシュを追加） |
| 10 | sandbox 内で literal `python` が起動（`nonmodel-1-5.sh` 手順 1〜5） | 同じ |
| 11 | Scenario 別の期待 FAIL（上の表） | train 固定 → Scenario 別 |
| 12 | preflight 後の workspace 再照合（bytecode 抑止） | 同じ |
| 13 | mount 監査（bind 4 件・tmpfs 2 件、`runs/` を含まない）、`/work` = fixture、`/run-input` = prompt のみ | 同じ |

加えて、毎 Run で次を行います（いずれも T1 r01 と同じスクリプト）: 静的 bind 元監査（`audit_exp001_g_bind_sources.py` を無変更で呼び、prompt の SHA-256 だけ run-meta の値で照合）、コンテナ制約（Privileged false、CapDrop ALL、read-only rootfs、no-new-privileges、seccomp、unconfined なし、非 root）、`preflight-d.sh`（Codex 版、login、config、doctor、prompt SHA-256、sandbox 起動、auth 読み取り拒否、コンテナ・sandbox の環境変数キー、`/run-input`）、`proc-check.sh`（Codex 本体の `/proc` 7 経路が denied）、preflight ログの秘密値パターン検査、(f) 直前の再 fetch と Judgment の再確認。

### 構成の照合

`environment.conf` の値と実測が 1 つでも違えば `ENV-MISMATCH` で STOP し、環境 Judgment を取り直します。照合対象は image digest（RepoDigests）と arm64、`bin/codex` の SHA-256 と `codex-package.json`（0.160.0、aarch64-unknown-linux-musl）とコンテナ内 `codex-cli 0.160.0`、seccomp の SHA-256、`config.toml` のバイト列（host 側とコンテナ内）、(g) ブロックの SHA-256 と起動行、docker context・server version・kernel・architecture・OS、コンテナ内 `uname` の kernel です。

## STOP 条件

検査の失敗、判定不能（読み取り不能、コマンド不在、空出力、タイムアウト、想定外の出力）、証跡不足はすべて STOP です。`STOP [<分類>]` の分類は報告用で、検査は分類によらず全項目を順に実行します。

| 分類 | 例 |
| --- | --- |
| SAFETY | auth が sandbox から読める・判定不能、Codex 本体の `/proc` に到達できる、mount が許可リスト外、コンテナ制約の不一致、コンテナが停止できない |
| SECRET | preflight ログ・stdout・証跡に秘密値パターン、環境変数に認証関連キー、証跡に `auth.json` |
| PROTOCOL | Freeze・matrix 順・ACCEPT・Judgment（`CONDITIONAL` を含む）・slot disposition・attempt の重複・prompt・metadata・fixture・Gate 10/11/12/13 の不一致、キットの改変、`ENV-MISMATCH`、`--practice-model` なしで練習課題が (g) に到達 |
| UNRECOVERABLE | (g) 後の終了コード・session・開始/終了時刻・`evidence.tar` の回収失敗、timeout 後に Codex の停止を確認できない |

(g) 後の結果は `COMPLETED` / `INFRASTRUCTURE ABORT` / `UNDETERMINED` / `CONTAINER-NOT-STOPPED` のいずれかです（T1 r01 本番スクリプトと同じ分類）。秘密値パターンの検出は Run 結果を変えず、`HANDLING: quarantine` として Issue に添付しません。COMPLETED 以外は同じ runId で再実行せず、Issue #15 に記録して reviewed disposition を求めます。

## T1 r01 キットとの差分

| 項目 | T1 r01 | run-kit-g |
| --- | --- | --- |
| 対象 | `EXP-001-train-normalize-name-r01-T1` の one-time retry | r02 以降の matrix Run（T0・T1）と練習課題 |
| Run 固有の値 | スクリプトに固定（prompt SHA-256 `d98fdfb3…`、train の期待 FAIL） | パラメータ。テンプレートを描画し、描画後の SHA-256 を記録・コンテナ内で照合 |
| retry 固有の処理 | archive 照合、retry allowance、旧 preparation の退避、`--require-new-workspace-id` | 持ち込まない。Gate 2・3・5〜8 を通常 Run の検査に置き換え |
| 構成の照合 | context と seccomp・(g) の SHA-256 | 加えて docker server version・kernel・OS、Codex バイナリ SHA-256、config.toml のバイト列 |
| Judgment 確認 | T1 r01 の Gate 10 Judgment 3 件 | 環境 Judgment 1 件 + 直前 Run の ACCEPT |
| bind 元監査 | `audit_exp001_g_bind_sources.py`（prompt SHA-256 が T1 r01 固定） | 同じスクリプトを無変更で呼び、prompt SHA-256 の照合だけ run-meta の値に置き換え |
| ロック / attempt | 固定パス 1 つ | (g) 直前のロックは runId ごと。prepare 前に runId ごとの attempt を固定パスへ予約し、再実行には slot disposition が必要 |
| コンテナ名 | `exp001-t1-r01` | `exp001-runkit-<runId 小文字>` |
| Run 後の host での tests 実行 | あり（参考値） | なし（model が書いたコードを host で実行しない） |

`selftest.sh` は、T1 r01 の値で描画したテンプレートが T1 r01 の doc-extracted スクリプトとバイト単位で一致すること、変更していないスクリプトと (g) が T1 r01 と同一であることを確認します。

## Run 後（Operator）

1. `status.log` の summary で結果分類を確認する。`<RD>/sink/evidence.tar`（600）は Operator だけが `<RD>/sink` 配下で展開し、実効 model / effort / approval / permission profile、session id、exit-code を抜粋する。抜粋に同じ 5 パターンの秘密値検査をかけて 0 件を確認してから Issue #15 に添付する。
2. `<RD>/checkout` の `runs/pilot-codex/<runId>/run-meta.yaml`・`prompt.md` と、workspace `<RD>/ws` の結果から作った Artifact を、新しい作業ブランチの同じパスに置く。欠けた Artifact は作らない。
3. `pilot/OPERATOR.md` の「実行後Attestation」と single-run validation、手動 cross-artifact review を行い、結果 PR で `EXP-001 Run acceptance: ACCEPT` を受けるまで次の slot に進まない。
4. 後始末として `git -C <clone> worktree remove <RD>/checkout` を行う（結果 Artifact の転記後）。

## 限界

- 練習課題の dry-run は prepare（`prepare_pilot_run.py`）と Gate 2・3・8 の matrix 照合、Judgment コメントの取得を通らない（実 runId に対して prepare を実行しないため）。これらは実 Run で初めて実行される。
- `codex exec` 実行時の permissions profile と effort の実効値は、Run 後の session 記録で確認する（T1 r01 と同じ扱い）。
- 確認範囲は Docker Desktop（context `desktop-linux`、server 29.7.2）・arm64・kernel `7.0.12-linuxkit` に限る。
