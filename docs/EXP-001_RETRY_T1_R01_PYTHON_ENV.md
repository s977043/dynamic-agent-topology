# EXP-001 T1 r01 retry — Gate 10 実行環境 disposition（draft / Reviewer判断待ち）

## Status

**Draft. Reviewer Judgment required.** この文書は [T1 r01 one-time infrastructure retry](EXP-001_RETRY_T1_R01.md) の Gate 10 を満たす実行環境の判定基準と、model起動前の非model確認手順を提案します。merge前、またはReviewerが下記「判定基準」を承認する前に、retryを開始してはいけません。

この文書は次を**変更しません**:

- 凍結Evidence command `python -m unittest discover -s tests`
- Prompt、Fixture、Topology、Role Contract、Runtime `codex`、Model `gpt-6.1-sol`、Effort `high`
- Evaluation semantics、Run Matrix、Feature Freeze revision 3
- retry entry gate 1〜13 の文言と順序、single permitted retry、Result handling、Counting

変更対象は「Gate 10 を満たすとみなす実行環境の扱い」だけです。この文書に従う確認作業は **retry allowance を消費しません**（allowanceは model invocation 開始時に消費されます）。

## Problem

Gate 10 の要求:

> In the normal experimental sandbox, without invoking the model, prove that the frozen command `python -m unittest discover -s tests` can start. Do not make it pass by adding an alias, shim, symlink, wrapper, PATH mutation, or by substituting `python3`; the literal frozen command must be natively resolvable in the Run environment.

出典: [EXP-001_RETRY_T1_R01.md](EXP-001_RETRY_T1_R01.md) Gate 10。改訂時は原文が優先します。

Operator host の測定（2026-10-08 09:30、macOS + Homebrew）:

| 項目                        | 結果                  |
| --------------------------- | --------------------- |
| `command -v python`         | exit 127（未解決）    |
| `/opt/homebrew/bin/python3` | 存在                  |
| `python`（unversioned）     | default PATH 上に無し |

これは元attemptの exit 127（`zsh: command not found: python`、[STOP-REPORT](../experiments/EXP-001-t0-vs-t1/runs/infrastructure-failures/EXP-001-train-normalize-name-r01-T1/01a1132a-1de0-70d2-b810-c500b79430c9/STOP-REPORT.md)）と同じ原因です。この状態のままではGate 10でSTOPになります。

## T0 r01 実行環境の特定調査（結果: 特定不能）

T1 retry を「T0 と同一環境」で実行できるかを確認するため、accepted T0 r01 の実行環境を調べました（2026-10-08、オーガナイザー測定）。

| 確認項目                                                                         | 結果                                                                                             | 確認元                |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | --------------------- |
| T0 `execution-attestation.yaml` / `trace.yaml` の sessionId                      | `01a10975-1997-7e33-bcb3-3d6c855b6471`                                                           | repo（`origin/main`） |
| T0 `trace.yaml` の command 表記                                                  | `/usr/bin/zsh -lc ...`。Evidence command `python -m unittest discover -s tests` は起動できている | repo（`origin/main`） |
| Operator macOS host の `~/.codex/sessions/` に上記 sessionId の rollout ファイル | **存在しない**（後日の別セッションがこの ID に言及しているのみ）                                 | オーガナイザー測定    |
| 同日の Codex 記録の shell 表記                                                   | `zsh` のみ（`/usr/bin/zsh` の記録なし）                                                          | オーガナイザー測定    |
| 失敗した T1 original attempt の stderr                                           | `zsh: command not found: python`（現 Operator macOS host の測定と整合）                          | repo（`origin/main`） |

解釈（**推測**）: macOS の zsh は通常 `/bin/zsh` であり、`/usr/bin/zsh` と `python` 解決可能という記録は現 Operator macOS host と整合しません。T0 r01 は Operator の macOS host 以外（Linux 系の可能性）で実行されたと推測されます。ただし host・コンテナイメージ・OS・Python 版はいずれも記録が無く、**T0 r01 の実行環境は特定できません**。

帰結:

- 「T0 と同一環境で T1 retry を実行する」という選択肢は**採れません**。T1 retry の Run 環境は、下記の推奨に従い**新しく定めます**。
- T0/T1 間の実行環境の一致は保証できません（「比較妥当性の limitation」参照）。

## 「native」の解釈（Reviewer判断事項）

Gate 10 の禁止事項を文字どおり「解決経路上に symlink が一切無いこと」と読むと、主要な配布形態のほぼすべてで `python` 自体が配布物内部の symlink（例: `python -> python3`）であるため、満たせる環境がほとんど存在しません。そこで次の解釈を提案します。

**提案解釈 N1:** Gate 10 が禁じるのは、Gate 10 を通すために **Operator が追加・変更した** alias / shim / symlink / wrapper / PATH mutation / `python3` 置換である。Run環境の**既定状態**（イメージ定義またはOS/パッケージの標準インストール結果）として、既定 PATH 上で `python` が CPython 実行ファイルへ解決するなら、その解決経路に**配布物自身が含む** symlink があっても native とみなす。ただし次はいずれも不可:

- 解決先が shell script / launcher / version-manager shim（pyenv / asdf 等）である
- 解決のために rc ファイル、`export PATH=...`、`alias`、venv activate 等の追加設定が必要
- retry のために Operator が手作業で作成した symlink
- `python` の実体が Python 3.12 系以外（CI基準）であることを記録せずに使う

N1 を採らず文字どおりの解釈を採る場合、下表の多くは「不可」に倒れ、Gate 10 を満たす環境が見つからない可能性があります。その場合は EXP-001 Gate 10 の文言自体の reviewed disposition が別途必要です（本文書のスコープ外）。

## 候補比較

判定列は「Gate 10 文言のみ」と「N1 採用時」の両方を示します。

| 候補                                                                                                           | `python` の提供形態                                                                       | 追加操作                                                                        | Gate 10 文言のみ                                | N1 採用時                        | 備考                                                                                         |
| -------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ----------------------------------------------- | -------------------------------- | -------------------------------------------------------------------------------------------- |
| A. 現状 macOS + Homebrew (`/opt/homebrew/bin`)                                                                 | 無し（`python3` のみ）                                                                    | —                                                                               | **不可**                                        | **不可**                         | 現状。exit 127                                                                               |
| B. Homebrew `$(brew --prefix python)/libexec/bin`                                                              | unversioned `python` は libexec/bin 内の **symlink**（→ `python3.x`）                     | PATH に libexec/bin を追加                                                      | **不可**（symlink + PATH mutation）             | **不可**（PATH mutation が必要） | Homebrew 自身が「使うなら PATH に追加」と案内する形態であり、既定 PATH では解決しない        |
| C. python.org 公式インストーラ (macOS)                                                                         | `python3` / `python3.x` のみ。unversioned `python` は提供されない                         | 自作 symlink か alias が必要                                                    | **不可**                                        | **不可**                         | インストールしても A と同じ状態                                                              |
| D. pyenv / asdf                                                                                                | `~/.pyenv/shims/python` 等の **shim**                                                     | shell init / PATH 追加                                                          | **不可**                                        | **不可**                         | shim は明示的に禁止                                                                          |
| E. uv 管理 (`uv python install --default`)                                                                     | `~/.local/bin/python` に uv が作る symlink / 実行ファイル                                 | `~/.local/bin` の PATH 追加が必要な場合あり、`--default` は Operator の追加操作 | **不可**                                        | **要 Reviewer 判断**             | ツールによる生成だが Operator 起点の追加操作に近い                                           |
| F. venv (`python -m venv` + activate)                                                                          | venv/bin/python は symlink、activate は PATH mutation                                     | activate                                                                        | **不可**                                        | **不可**                         |                                                                                              |
| G. Linux コンテナ（例: 公式 `python:3.12` 系イメージ、または `python-is-python3` 入り Debian/Ubuntu イメージ） | イメージ定義により既定 PATH 上に `python` が存在（実体は配布物内 symlink 経由で CPython） | Run 環境としてイメージを選ぶこと自体のみ。rc / PATH / alias 追加なし            | **要 Reviewer 判断**（配布物内 symlink を含む） | **可**（下記条件付き）           | Codex の normal experimental sandbox をコンテナ内で成立させられるか、T0 との環境同等性が論点 |

## 推奨（Reviewer判断を要する）

**推奨（確定案）: 解釈 N1 を採用し、候補 G — digest 固定の Linux コンテナで、イメージ既定の `python` が CPython 3.12 系に解決するもの — を T1 r01 retry の Run 環境として新しく定める。** 「T0 と同一環境」は選択肢に含めません（「比較妥当性の limitation」参照）。

理由:

1. **要件適合性**: macOS host 系の候補（A〜F）は、いずれも既定状態では `python` が解決せず、解決させるには PATH mutation・shim・Operator 作成の symlink のどれかが必要で、Gate 10 の禁止事項に直接該当します。G だけが「Operator の追加操作なしに、Run 環境の既定状態で literal command が解決する」を構成できます。
2. **安全性 / 再現性**: イメージ digest を記録すれば、Reviewer が同じ解決経路を後から再確認できます。host の rc ファイルや Homebrew の状態に依存しません。
3. **T0 との比較可能性**: T0 r01 は Linux 系環境で実行された可能性があり（推測）、G はこれと矛盾しにくい選択です（「比較妥当性の limitation」参照）。
4. **凍結物への非影響**: 凍結 command・prompt・fixture・scripts を一切変えずに済みます。

結論は **Reviewer Judgment** で確定してください。推奨文言（例）:

`EXP-001 T1 r01 Gate 10 environment: ACCEPT N1 + G`

Reviewer が N1 を採らない、または G の sandbox 同等性を認めない場合は STOP し、retry allowance を消費しないまま新たな reviewed disposition を求めます。

### G を採る場合の条件

- コンテナイメージは **イメージ名 + digest（`sha256:...`）** で固定し、記録する。
- `python` が既定 PATH で解決し、`python --version` が `Python 3.12.x` であること。
- コンテナの entrypoint / shell init / Dockerfile 追加レイヤで `python` を作る・PATH を変えることをしない（既存イメージの既定状態のまま使う）。
- Codex の normal experimental sandbox（同じ Runtime `codex`、同じ sandbox mode、write allow/deny 設定）を、そのコンテナ内で成立させる。sandbox mode を host 実行時から緩めない。
- 新しい workspace は Gate 4 / 6 / 9 のとおり fresh に作る。

## 候補 G の提案構成（Reviewer 判断材料）

Reviewer が `ACCEPT N1 + G` を判断するための具体構成です。この節で「確認した」と書く検証はすべて **model 非起動**（`codex sandbox -P :workspace` による sandbox 単体の起動、および `--version` / `--help` の表示）で行い、retry allowance は消費していません。確認範囲は Docker Desktop（docker context `desktop-linux`、docker v29.7.2）・arm64・kernel `7.0.12-linuxkit` に限られます。

**確認済みの範囲**はイメージ・seccomp プロファイル・コンテナ制約・sandbox 単体の挙動までです。最終構成（auth マウント済みの `CODEX_HOME`、`config.toml` の読み込み、ログイン状態、モデルとの通信）は**未確認**であり、Run 当日に下記「preflight〜model 起動の順序付き手順」の (d)〜(e) で確認します（モデル通信そのものは (g) の model 起動まで確認できません）。

### イメージと Python

| 項目                | 値                                                                                                                                       |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| イメージ            | `python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258`（`python:3.12-slim-bookworm`）                                                                                                 |
| CPU アーキテクチャ  | arm64（`linux/aarch64`）固定                                                                                                             |
| `python` の解決経路 | `/usr/local/bin/python` → `python3` → `python3.12`（公式 Dockerfile が作る symlink。Operator 追加なし）                                  |
| Python 版           | Python 3.12.15                                                                                                                           |
| shell               | イメージ既定の bash による `bash -lc`（zsh はイメージに存在しない）                                                                      |

### Codex CLI と sandbox

- Codex CLI **0.160.0**（T0 trace と同版）の linux-arm64 musl バイナリ（`aarch64-unknown-linux-musl`）を read-only でマウントして使う。イメージにレイヤは追加しない。
- sandbox: Linux では bubblewrap。`sandbox_mode` ではなく permissions profile `t1-workspace` で与える。`t1-workspace` は **built-in `:workspace` を継承し、認証領域 `CODEX_HOME`（`/tmp/codex-home`）を追加 deny した派生 profile** であり、`:workspace` と完全同一ではない。T0 の normal experimental sandbox（`workspace-write`）と同一とは認定しない（「比較妥当性の limitation」参照。「認証隔離・CODEX_HOME 所有権・証跡回収の検証」参照）。
- docker seccomp: moby 既定プロファイル（moby/profiles seccomp v0.2.3。docker `v29.7.2` タグの `vendor/modules.txt` で `github.com/moby/profiles/seccomp v0.2.3` を確認、取得元 `https://raw.githubusercontent.com/moby/profiles/seccomp/v0.2.3/seccomp/default.json`、取得ファイル SHA-256 `536529b665dd0972c37bfb569f5d4ac8a53592e7b00752bc39ff063ca9864c74`）に、`clone` `unshare` `mount` `umount2` `pivot_root` の **5 syscall のみ** を `SCMP_ACT_ALLOW` で追加した最小プロファイル。
  - 配置: [`experiments/EXP-001-t0-vs-t1/pilot/retry-t1-r01/codex-bwrap-seccomp.json`](../experiments/EXP-001-t0-vs-t1/pilot/retry-t1-r01/codex-bwrap-seccomp.json)
  - SHA-256: `085e468fa8e70d8c839a9abab4d74a1ab2abad74a8c26f15234ba62a8ac2e1e8`
  - 生成スクリプト: [`experiments/EXP-001-t0-vs-t1/pilot/retry-t1-r01/build.py`](../experiments/EXP-001-t0-vs-t1/pilot/retry-t1-r01/build.py)（`python3 build.py default.json codex-bwrap-seccomp.json clone mount umount2 pivot_root unshare` で上記 SHA-256 と一致するバイト列を再生成できることを確認済み。moby 既定ファイル自体は repo に含めない）
- `--privileged`、`seccomp=unconfined`、`apparmor=unconfined` は**使わない**。

追加 5 syscall の必要性（1 つずつ外して bwrap を起動した結果）:

| 外した syscall | 失敗内容                                        |
| -------------- | ----------------------------------------------- |
| `clone`        | `bwrap: No permissions to create a new namespace` |
| `unshare`      | `bwrap: unshare user ns: Operation not permitted` |
| `mount`        | `bwrap: Failed to make / slave`                 |
| `umount2`      | `bwrap: unmount old root`                       |
| `pivot_root`   | `bwrap: pivot_root: Operation not permitted`    |

### 併用するコンテナ制約

- 非 root（host の uid:gid で実行）
- `--cap-drop ALL`（cap の追加なし）
- `--read-only` + `--tmpfs /tmp`
- `--security-opt no-new-privileges`
- `--network none` は**不採用**（モデル通信が必要なため）。sandbox 内の network は EPERM で拒否されることを確認。

### 検証結果（model 非起動、`codex sandbox -P :workspace`）

取得条件: 上記 5 syscall プロファイル + 非 root（host uid:gid）+ `--cap-drop ALL` + `--read-only` + `--tmpfs /tmp` + `--security-opt no-new-privileges` + `/work` への host bind で、`codex sandbox -P :workspace` を使って取得した。`CODEX_HOME`・auth マウント・`config.toml` を含む最終構成（下記「推奨 `docker run` 構成」）では**未検証**であり、認証を伴うため model 起動前の preflight（「認証」節）で確認する。

| 確認                                                   | 結果                         |
| ------------------------------------------------------ | ---------------------------- |
| workspace 内への書き込み                               | 成功                         |
| workspace 外・`/etc` への書き込み                      | 拒否                         |
| sandbox 内の network                                   | EPERM                        |
| Evidence command `python -m unittest discover -s tests` | 起動し、初期 FAIL（rc=1）    |

### 認証隔離・CODEX_HOME 所有権・証跡回収の検証（2026-10-09、ダミー auth、model 非起動）

Issue #15 の preflight STOP（`CODEX_HOME` が root:root 755 で config.toml を書けない、sandbox から auth.json を読める）を受けて、下記「推奨 `docker run` 構成」と「最小 Codex config」の修正版で再測定した。auth は**本物ではないダミー**（JWT 形式の偽トークン）を `/tmp/codex-home/auth.json:ro` に bind し、本物の `~/.codex/auth.json` は読まず・mount していない。`codex exec`・`codex login`・model 起動は行っていない。環境は Docker Desktop（docker context `desktop-linux`、docker v29.7.2）・kernel `7.0.12-linuxkit`・arm64、Codex 0.160.0 musl、イメージ・seccomp は本節の digest / SHA-256 のとおり。

| 確認 | 旧構成（auth を `/tmp/codex-home` 直下へ bind、`sandbox_mode = "workspace-write"`、`-P :workspace`） | 修正構成（`--tmpfs /tmp/codex-home:uid=<uid>,gid=<gid>,mode=700` + permissions profile `t1-workspace`） |
| --- | --- | --- |
| `ls -ld /tmp/codex-home` | `drwxr-xr-x root root`（Docker が作成） | `drwx------ 502 dialout`（tmpfs の mount option） |
| `config.toml` 作成（非 root） | `Permission denied` | 成功 |
| `codex login status`（ダミー auth） | — | `Logged in using ChatGPT` |
| doctor `model` | `<default> · openai` | `gpt-6.1-sol · openai` |
| doctor sandbox / approval | `approval OnRequest` | `[ok] sandbox  restricted fs + restricted network · approval Never` |
| doctor config / auth | `[ok] config loaded` | `[ok] config loaded`・`config.toml parse ok`・startup warning なし・`[ok] auth  auth is configured`（`auth file /tmp/codex-home/auth.json`、`stored auth mode chatgpt`） |
| sandbox 内 `cat /tmp/codex-home/auth.json` | **読める（BLOCK）** | 読めない。`ls /tmp/codex-home` も `Permission denied`（PASS） |
| sandbox 内 `/proc/self/root/...`・`/proc/<pid>/root/...` 経由 | 読める（BLOCK） | すべて読めない（PASS） |
| sandbox 内 `unshare -Ur cat ...` | — | 読めない（PASS） |
| sandbox 内 `grep -r` によるダミートークン文字列の全 fs 走査（`/proc`・`/sys` 除く） | auth.json がヒット（BLOCK） | 検査スクリプト自身以外ヒットなし（PASS） |
| sandbox 内 `/work` 書き込み・`/etc` 書き込み・`python` 起動 | 成功・拒否・成功 | 成功・拒否・成功（変化なし） |
| sandbox 内 network（コンテナ自体は network あり） | — | `socket()` が `EPERM`。コンテナの通常 shell からは接続可 |
| `CODEX_HOME/sessions/...` への書き込み（uid 502、ダミー rollout） | 不可（親が root 755） | 成功 |
| `docker exec <name> tar -C /tmp -cf - codex-home/sessions exit-code > <host sink>/evidence.tar` | — | 成功。tar に `sessions/.../rollout-dummy.jsonl` とダミー終了コードを含み、auth.json は含まない（パスを列挙して除外） |

#### 環境変数・Codex 本体プロセスへの到達性（未実施、model 起動前 STOP 条件）

independent review の指摘により、次の 2 経路をダミー auth・model 非起動で確認する計画とした。2026-10-09 の作業では、ダミー auth を使うコンテナ起動が Operator 側ツールの実行許可で拒否され、**実施できていない**。結果は**未確認**であり、(d) の該当項目が PASS するまで model を起動しない。

| 確認 | 結果 |
| --- | --- |
| コンテナ・sandbox 内の環境変数キーに `OPENAI` / `TOKEN` / `KEY` / `AUTH` を含むものが無い | 未実施 |
| sandbox 内から外側の codex プロセスの `/proc/<pid>/environ`・`fd`・`mem`・`maps` が参照できない | 未実施 |

根拠（公式、2026-10-09 参照）:

- [Config reference](https://learn.chatgpt.com/docs/config-file/config-reference): `default_permissions`（built-in は `:read-only` / `:workspace` / `:danger-full-access`、「Don't combine with `sandbox_mode` or `[sandbox_workspace_write]`」）、`permissions.<name>.extends`、`permissions.<name>.filesystem.<path-or-glob>`（`"read" | "write" | "deny"`、「Use `"deny"` to deny reads for matching paths」）。
- [Permissions](https://learn.chatgpt.com/docs/permissions)（**Beta**）: `deny` は「Denies both reads and writes under the path」、`:workspace` は「allows writes inside the active workspace roots and system temp directories」。`sandbox_mode` がどこかの config にあると「Codex uses those older sandbox settings instead of `default_permissions`」となるため、修正版 config からは `sandbox_mode` を**削除**する。
- 0.160.0 の `codex sandbox --help`: `-P, --permission-profile <NAME>  Named permissions profile to apply from the active configuration stack`（`-P` 必須）。

解釈と限界:

- `CODEX_HOME` 全体を deny しても、Codex 本体（sandbox 外のプロセス）は auth を読め（`[ok] auth`）、sessions を書ける。sandbox 内コマンドだけが `CODEX_HOME` を参照できない。
- **確認済み**: `codex sandbox -P t1-workspace`（profile を明示した sandbox 単体）の挙動と、doctor の sandbox 行（`restricted fs + restricted network · approval Never`）。**未確認**: `codex exec` 実行時に `default_permissions = "t1-workspace"` が実効適用されること。後者は model 非起動では**直接確認できない**。doctor の sandbox 行と、同じ profile を明示した `codex sandbox -P t1-workspace` の結果からの推定である。Run 後に trace / session 記録で profile と sandbox の実効値を確認し、異なれば limitation として記録する。ただし Run 後の確認は事後であり、**Run 前に確認できないことを Reviewer が承知のうえで受容するか**を判断事項とする（「未解決の論点」10）。
- permissions profile は公式に Beta であり、版が変わると挙動が変わり得る（0.160.0 固定で確認）。
- session 記録の回収はダミーファイルで実証した。Codex が `exec` 時に実際に書く rollout の形式・場所は model 非起動では未確認。Run では model 終了後・コンテナ停止前に `docker exec` で `codex-home/sessions` を回収し、回収できなければ limitation として記録する。
- 単一のプローブ群はあらゆる exfiltration 経路を否定しない（既存の注記どおり）。
- 残余リスク（非 model の確認では否定できない経路）: Codex 本体プロセスのメモリ上のトークン（`/proc/<pid>/mem` が拒否されても、kernel / bwrap の脆弱性経由の参照は否定できない）、Codex 本体が model 通信で送る認証ヘッダ自体、sandbox 外で Codex が実行するツール（MCP 等。本構成では設定しない）、Docker Desktop VM / host 側からの参照。
- Gate 10 との関係: `--tmpfs /tmp/codex-home` の mount option（所有者・mode）と、`/tmp/codex-home` だけを deny する profile は、`python` の解決経路（PATH・`/usr/local/bin`・イメージ既定の login shell 初期化）に触れない。Operator が rc ファイル・PATH・alias・venv を追加する操作ではない。sandbox 内の `python` 起動は修正構成でも確認した。

### 残るリスク

- user namespace の作成と `mount` / `pivot_root` をコンテナ内で許可するため、moby 既定より攻撃面が広がる（kernel の userns / mount 系脆弱性の影響を受けうる）。cap は全て落とし、非 root・`no-new-privileges`・read-only rootfs で緩和する。
- `clone` / `unshare` / `mount` は引数条件なしで許可するため、bwrap 自身だけでなく、Codex sandbox 内で model が実行するコマンドも入れ子の user / mount namespace を作れる。
- AppArmor の `docker-default` プロファイルが有効な host（Ubuntu 等）では `mount` が AppArmor 側で拒否され、本構成が再現しない可能性がある（確認環境の Docker Desktop では未検証の論点）。その場合も `apparmor=unconfined` は使わず STOP し、Reviewer 判断を求める。
- 確認は Docker Desktop（docker context `desktop-linux`、docker v29.7.2）・arm64・kernel `7.0.12-linuxkit` に限られる。別 host / 別 kernel / amd64 では再確認が必要。

### 独立レビューで確認した停止条件（比較妥当性・認証・証跡）

この節は候補 G の**追加検証要求**であり、`ACCEPT N1 + G` や retry 開始を宣言するものではありません。以下の3点はPR #116で「確認済み」としたsandbox起動テストからは導けないため、Reviewer判断と実hostでの非model evidenceが必要です。

1. **比較妥当性（交絡）**: accepted T0 r01のOS・Python・CPUアーキテクチャ・起動方式・approval設定は復元できません。T1をG（arm64/Linux/bash）で計測した場合、r01のT0/T1差をTopologyの因果効果と断定しません。RunのArtifact acceptanceと、Topology効果の主張を分離し、Issue #15と最終集計に `environment-confounded / descriptive-only` を明示してください。残りのペアで環境が同等と実測できるかも別途確認します。Freezeのmetricや18-slot countは変更しません。
2. **認証情報の機密性**: `auth.json:ro` が保証するのは**書き込み不可**であって、modelが実行するコマンドからの**読み取り不可**ではありません。最終構成で `login status` が有効になった後、**model非起動**の `codex sandbox` から読み取れないことを値を表示せずに確認してください。読める、判定不能、sandbox実行失敗のいずれも**STOP**。代替認証・隔離方法を独立レビューするまでmodel起動禁止です。単一のnegative testはあらゆるexfiltration経路を否定するものではなく、最小確認にすぎません。
3. **実行証跡の残存**: 推奨Docker起動は `--rm`、`CODEX_HOME` はtmpfs `/tmp`配下です。コンテナ終了時にセッション記録が失われます。また標準の `codex exec` 出力だけでWorker→Verifierの全eventやtoken計測を取得できるとは限りません。**model起動前**に、ホスト側の安全な保存先（model workspaceにマウントせず、Gitに入れない）へ必要な観測データ・終了コードを確実に取り出せる方式を非modelで試験し、その方式・権限・sanitize手順をIssue #15で独立レビューしてください。セッションがコンテナ内に残る方式なら、`--rm`で消える前に取り出す手順と異常終了時の制約を明示します。未実証ならSTOPです。生のsession log・認証情報・hidden reasoningを公開しないでください。

安全なnegative testの例（**実際にauthをmountし、ログインが確認された同じ構成のsandbox**で実施。内容を出力しない）:

```bash
/cx/bin/codex sandbox -P t1-workspace -C /work -- bash -lc 'if cat /tmp/codex-home/auth.json >/dev/null 2>&1; then echo "BLOCK: sandbox can read auth file"; exit 1; elif test -e /tmp/codex-home/auth.json; then echo "PASS: auth file exists but is not readable by sandbox process"; else echo "PASS: auth file not visible to sandbox process"; fi'
```

`login status` / Docker mountの確認によってhost側のauthファイルが確実に配置されたことを確認したうえで、この結果を解釈します。検査時には認証ファイルの内容・環境変数に含む秘密情報をstdoutやIssueへ載せません。PASSでもmodelの秘密アクセスを完全に否定できるわけではありません。

**Reviewer gate**: N1の解釈、比較交絡を許す範囲、sandboxの認証情報隔離、証跡回収手段、起動方式、approval policyを**個別に**判断し、#15へ根拠を記録します。1つでもBLOCK/UNKNOWNなら `ACCEPT N1 + G` のみを根拠にmodelを開始してはいけません。

### 認証

- ホストの `~/.codex/auth.json` **のみ**を `:ro` でマウントし、`CODEX_HOME` はコンテナ内の fresh なディレクトリとする（ホストの config・sessions・履歴は持ち込まない）。
- `CODEX_HOME` は `--tmpfs /tmp/codex-home:uid=<host uid>,gid=<host gid>,mode=700` で非 root の実行ユーザー所有にする。auth.json の bind 先だけを Docker に作らせると親ディレクトリが root:root 755 になり、`config.toml` と session 記録を書けない（2026-10-09 実測）。
- sandbox 内コマンドからの auth 読み取りは、permissions profile `t1-workspace` の `"/tmp/codex-home" = "deny"` で遮断する（ダミー auth で実測、上記検証表）。
- ログイン方式は ChatGPT（2026-10-08 にホストで `codex login status` を実測）。
- `auth.json` は `:ro` のため、model 起動後のトークン refresh は書き込めず失敗し得る。**refresh 不可を前提**とし、model 起動直前にコンテナ内で `/cx/bin/codex login status` を確認する。期限が近い・不明な場合は、host 側で通常どおり Codex を使ってトークンを更新してから開始する。失敗した場合は STOP（retry allowance 非消費）。
- model 起動後に認証エラーで中断した場合は infrastructure abort として STOP する（再 retry なし。本体手順書どおり）。
- `auth.json` を fresh `CODEX_HOME` へコピーして書き込み可能にする案は採らない（refresh 結果が host 側トークンと分岐し、host 側の認証状態に影響し得るため）。

### 最小 Codex config（fresh `CODEX_HOME/config.toml`）

```toml
model = "gpt-6.1-sol"
model_reasoning_effort = "high"
approval_policy = "never"
default_permissions = "t1-workspace"

[permissions.t1-workspace]
description = "workspace-write equivalent; CODEX_HOME (auth.json) hidden from sandboxed commands"
extends = ":workspace"

[permissions.t1-workspace.filesystem]
"/tmp/codex-home" = "deny"
```

`sandbox_mode` は置かない（置くと `default_permissions` が無視される。公式 [Permissions](https://learn.chatgpt.com/docs/permissions)）。`approval_policy` の行は下記の推奨値です。Reviewer が別の値・省略を判断した場合はその判断に従って差し替え、記録します。

approval の扱い（根拠と Reviewer 判断事項）:

- `origin/main` の T0 r01 `trace.yaml` / `run-meta.yaml` / `execution-attestation.yaml`、`pilot/OPERATOR.md`、`docs/EXP-001_EXECUTION.md` を確認したが、approval / sandbox 設定値と、`codex exec` か対話かの実行方式の記録は**無い**。T0 の起動方式は記録上不明である。
- T0 `trace.yaml` には `cliExitCode: 0` と `humanInterventions: 0` があり、非対話実行（`codex exec`）と整合するが、実行方式を断定する記録ではない（**推測**）。
- 版の区別: Operator host にインストールされている Codex CLI は 0.160.1（`codex exec --help` に `--ask-for-approval` がある）。T1 retry で使うのは T0 trace と同版の **0.160.0**（linux-arm64 musl）であり、根拠は 0.160.0 側の help で取る。
- 0.160.0 musl バイナリの help（2026-10-08、`--rm --network none` のコンテナで `--version` / `--help` / `exec --help` / `features list` / `login --help` を実行。model 非起動、`CODEX_HOME` は空の tmpfs）:
  - `codex --version` → `codex-cli 0.160.0`
  - `codex exec --help` → `Run Codex non-interactively`。オプションに `--ask-for-approval` は**無い**。approval に関係するのは `-c, --config <key=value>`、`--approve-for-me`（`Route approval requests through automatic review using the workspace-write sandbox`）、`--dangerously-bypass-approvals-and-sandbox` のみ。
  - `codex --help`（対話 CLI）→ `-a, --ask-for-approval <APPROVAL_POLICY>`、値は `on-request`（`The model decides when to ask the user for approval`）と `never`（`Never ask for user approval Execution failures are immediately returned to the model`）の 2 つ。
  - `codex exec --help` に `--strict-config`（`Error out when config.toml contains fields that are not recognized by this version of Codex`）がある。
  - `codex exec --help` の `[PROMPT]` 引数の説明は ``Initial instructions for the agent. If not provided as an argument (or if `-` is used), instructions are read from stdin. If stdin is piped and a prompt is also provided, stdin is appended as a `<stdin>` block``。(g) の `codex exec -C /work - < /run-input/prompt.md` は、この `-` 指定で prompt を stdin から読む形である。
- 0.160.0 musl バイナリでの config 読み込み確認（2026-10-08、推奨構成と同じ候補 G イメージ・5 syscall seccomp・非 root・`--cap-drop ALL`・`--read-only`・`--tmpfs /tmp`・`HOME=/tmp/home`・`CODEX_HOME=/tmp/codex-home` に `--rm --network none` を加えたコンテナ。auth なし、model 非起動。`codex exec` は実行していない）:
  - `--strict-config` を受け付ける非 model サブコマンドの確認: `codex --strict-config features list` / `login status` / `mcp list` / `sandbox ...` はいずれも ``Error: `--strict-config` is not supported for `codex <sub>` ``（rc=1）で拒否された。受け付けたのは `codex --strict-config doctor` のみだった。
  - 陽性コントロール（4 キー + 未知キー `zz_unknown_key = "x"`）: `codex --strict-config doctor --all` は**エラー終了せず**、Configuration 欄が `[!!] config  config loaded`、`startup warning  Codex is ignoring 1 unrecognized configuration setting.`、``user (/tmp/codex-home/config.toml): `zz_unknown_key` is ignored.`` となった。つまり doctor では `--strict-config` が厳格エラーにならず、未知キーは警告として検出される。
  - 値の陰性コントロール（`model_reasoning_effort = "bogus"`、`sandbox_mode = "bogus"`）: `[XX] config  config could not be loaded`（`error  invalid data`）。
  - (c) の 4 キー config: `[ok] config  loaded`、`config.toml parse  ok`、startup warning 行なし、`model  gpt-6.1-sol · openai`、`[ok] sandbox  restricted fs + restricted network · approval Never`。auth なしのため `[XX] auth` と、`--network none` のため websocket / reachability が DNS 解決失敗で `[XX]` / `[!!]` となり、doctor 全体の rc は 1。
  - 確認できたこと: 4 キーがいずれも 0.160.0 で未知キー扱いされず、型として受理され（不正値は読み込み失敗になる）、`model` と `approval_policy = "never"` が反映されること。
  - **未検証**: `codex exec --strict-config` で 4 キーの config がエラーにならないこと（exec は model 起動を伴うため実行していない）、`sandbox_mode = "workspace-write"`（修正版では permissions profile `t1-workspace`。`codex sandbox -P t1-workspace` と doctor では確認済み、`codex exec` 時の実効適用は未確認）と `model_reasoning_effort = "high"` の値が実効設定に反映されること（doctor の出力に表示項目が無い）、auth マウント後の `login status`。これらは (d) の preflight 項目とし、exec 時の反映は Run の trace / session 記録で確認する。
- 公式 config 仕様: [Config reference](https://learn.chatgpt.com/docs/config-file/config-reference)（旧 URL `https://developers.openai.com/codex/config-reference` から 308 リダイレクト、2026-10-08 参照）は `approval_policy` を「Controls when Codex pauses for approval before executing commands」とし、値を `on-request | never | { granular = {...} }`、`untrusted` は非サポート、`on-failure` は deprecated とする。対話には `on-request`、非対話には `never` を推奨している。`codex exec` の approval 既定値の記載は無い。sandbox 既定は [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode) が read-only と記載する（このため sandbox を明示する。修正版では `sandbox_mode` の代わりに `default_permissions = "t1-workspace"` で与える）。
- **推奨: `codex exec` で起動し、`approval_policy = "never"` を `config.toml` に明示する。** 理由: (1) `codex exec` は非対話で承認に答える人がおらず、0.160.0 の exec には approval を対話で求めるオプションが無い。(2) 公式仕様が非対話には `never` を推奨している。(3) exec の approval 既定値は公式に記載が無いため、既定任せにすると Run 記録から挙動を再構成できない。明示すれば sandbox 外の操作は承認待ちで止まらず失敗として model に返り、`workspace-write` の境界は sandbox 側で維持される。`--approve-for-me`・`--dangerously-bypass-approvals-and-sandbox` は使わない。
- 最終決定は **Reviewer 判断事項**（「未解決の論点」5・6）:
  1. T1 retry を `codex exec` で実行するか、対話で実行するか。
  2. `approval_policy` を明示するか、明示するならどの値か（推奨: `never`）。

### 推奨 `docker run` 構成

repo ルートから実行する想定。先に次の変数を host shell で設定する（`/abs/path/to/...` は例であり、実行時は下表の条件を満たす実在の絶対パスに置き換える。変数を設定せずに下の `docker run` を実行してはいけない）。

```bash
CODEX_DIR=/abs/path/to/node_modules/@openai/codex/node_modules/@openai/codex-linux-arm64/vendor/aarch64-unknown-linux-musl
WS=/abs/path/to/fresh-external-workspace
PROMPT=/abs/path/to/T1-r01/prompt.md
SECCOMP="$PWD/experiments/EXP-001-t0-vs-t1/pilot/retry-t1-r01/codex-bwrap-seccomp.json"
```

| 変数        | 条件                                                                                                                                                                                                                                                     |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CODEX_DIR` | Codex CLI **0.160.0** の `@openai/codex-linux-arm64` パッケージ内 `vendor/aarch64-unknown-linux-musl`（`bin/codex` を含む）。取得は `npm i -g @openai/codex@0.160.0` 相当（例: `npm i -g --prefix <scratch> @openai/codex@0.160.0 --os=linux --cpu=arm64` で linux-arm64 の optional dependency を取得）。host にインストール済みの別版（0.160.1 等）を使わない。コンテナ内で `/cx/bin/codex --version` が `codex-cli 0.160.0` であることを (d) で確認する |
| `WS`        | Gate 4 / 6 のとおり新しく作った fresh external workspace（Gate 6 で reprepare 済み、Gate 9 の条件を満たすもの）                                                                                                                                         |
| `PROMPT`    | Gate 7 で SHA-256 `d98fdfb3c56ecc5659466d8b4ba607bb94e77c2a7d74360175b9657b6b93bf86` を確認した T1 `prompt.md`                                                                                                                                           |
| `SECCOMP`   | 本 repo の `codex-bwrap-seccomp.json`。SHA-256 `085e468fa8e70d8c839a9abab4d74a1ab2abad74a8c26f15234ba62a8ac2e1e8` を `shasum -a 256 "$SECCOMP"` で確認する                                                                                              |

コンテナ起動前にhost側でbind元ファイルの存在・canonical path・凍結PromptとseccompのSHA-256・外部workspace・認証ファイルの権限を**read-only**確認します（認証ファイルの内容は読みません）。

```bash
python scripts/audit_exp001_g_bind_sources.py \
  --workspace "$WS" \
  --prompt "$PROMPT" \
  --codex-dir "$CODEX_DIR" \
  --seccomp "$SECCOMP" \
  --auth-file "$HOME/.codex/auth.json"
```

このscriptのPASSは**bind元の静的検査だけ**です。Docker mountの実効状態、sandboxの書込許可・拒否、credential隔離、Codex認証、有効なReviewer Judgmentは証明しません。Dockerの `-v` はbind元が無いとディレクトリを自動作成し得るため、事前に存在を検査します。すべてのpathを絶対pathとし、realpathが元attemptのarchiveやRepository内workspaceを指さないことを再確認してください。

`HOME` は tmpfs `/tmp` 上に、`CODEX_HOME` は実行ユーザー所有・mode 700 の専用 tmpfs `/tmp/codex-home` に置く（auth.json はその中へ `:ro` bind）。Run 後の証跡回収のため、Operator は `docker run` に `--name <name>` を付けてよい（mount・権限は変えない）。codex は PATH を変更せず `/cx/bin/codex` の**絶対パス**で起動する。

```bash
docker run --rm -it \
  --platform linux/arm64 \
  --security-opt seccomp="$SECCOMP" \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  --user "$(id -u):$(id -g)" \
  --read-only --tmpfs /tmp \
  --tmpfs /tmp/codex-home:uid="$(id -u)",gid="$(id -g)",mode=700 \
  -e HOME=/tmp/home \
  -e CODEX_HOME=/tmp/codex-home \
  -v "$HOME/.codex/auth.json":/tmp/codex-home/auth.json:ro \
  -v "$CODEX_DIR":/cx:ro \
  -v "$PROMPT":/run-input/prompt.md:ro \
  -v "$WS":/work -w /work \
  python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 \
  bash -l
```

shell の関係: `docker run ... bash -l` はコンテナ内の対話用 login shell（Operator が (b) 以降を入力する shell）であり、非model preflight の `bash -lc '<cmd>'` はその中から起動する子の login shell である。どちらも login shell として `/etc/profile` 等のイメージ既定の初期化を読み、Operator は rc ファイルを追加しない。Run 時に Codex が model 生成コマンドを実行する shell は Codex が決める（T0 trace では `/usr/bin/zsh -lc`。G では zsh が無いため bash の `bash -lc` 相当になる想定で、実際の表記は Run の trace に残るものを記録する）。

この `HOME=/tmp/home`・`CODEX_HOME=/tmp/codex-home` 設定（auth マウントなし、config.toml なし）で、`/cx/bin/codex sandbox -P :workspace -C /work -- bash -lc 'echo ok'` が model 非起動で `ok` / rc=0 となることを 2026-10-08 に Docker Desktop（docker context `desktop-linux`、docker v29.7.2）・arm64 で確認した。このとき `/cx/bin/codex --version` は `codex-cli 0.160.0`、Codex は `CODEX_HOME` が `/tmp` 配下のため PATH 用 helper を作らない旨の WARNING を出したが、sandbox 起動には影響しなかった。コンテナ内の `$SHELL` は `/bin/sh`、`getent passwd "$(id -u)"` は該当なし（host uid がイメージの passwd に無い）、`ps` はイメージに無く、`readlink /proc/$$/exe` は `/usr/bin/bash` だった。

## 非model確認手順（Gate 10 evidence）

**Codex model を起動しない**状態で、retry に使う normal experimental sandbox 内の、fresh workspace（Gate 6 で reprepare 済み）をカレントディレクトリとして実行します。Gate 12 のため bytecode 書き込みを抑止します。

手順 2〜4 は通常のコンテナshellで解決経路を診断します。手順 5 のEvidence commandは同じ `bash -lc` 起動方式を **Codex sandbox内で**実行し、その表記のまま記録します。login shell が読む Run 環境既定の初期化（イメージ / OS の標準状態）は Run と同条件として扱い、Operator が追加・変更した設定（rc ファイル追記、`export PATH=...`、`alias`、venv activate 等）が無いことを Operator が明記します。

1. 環境識別を記録する。

   ```bash
   uname -a
   cat /etc/os-release
   echo "$SHELL"
   getent passwd "$(id -u)" || true
   ps -p $$ -o comm= 2>/dev/null || readlink /proc/$$/exe
   command -v bash
   command -v zsh
   ```

   Run 環境の login shell を記録する（G では bash。zsh はイメージに存在しないため `command -v zsh` は不在を示す）。`$SHELL` は非 root の host uid では未設定または `/bin/sh` になり得るため、`getent passwd` と実行中 shell（slim イメージには `ps` が無いので `readlink /proc/$$/exe`）を併記する。

   コンテナの場合はイメージ名と digest を host 側で記録する（例: `docker image inspect --format '{{.RepoDigests}}' <image>`）。

2. 解決先を記録する（Run と同じ起動方式で、Operator が追加した設定が無い状態で）。

   ```bash
   bash -lc 'command -v python'
   bash -lc 'type -a python'
   bash -lc 'python --version'
   ```

   - `command -v python` が exit 0 で絶対パスを返すこと。
   - `type -a python` に `alias` / `function` が出ないこと。

3. 解決先が shim / wrapper でないことを確認する。

   ```bash
   bash -lc 'ls -l "$(command -v python)"'
   bash -lc "python -c 'import sys; print(sys.executable); print(sys.version)'"
   bash -lc 'file -L "$(command -v python)"'
   bash -lc 'readlink -f "$(command -v python)"'
   ```

   - `file -L` が ELF / Mach-O 実行ファイルを示すこと（`shell script` / `text` は不可）。
   - 解決経路に symlink がある場合は、全段の symlink とその所有パッケージ（例: `dpkg -S`、イメージ定義）を記録し、Operator が作成したものではないことを示す。
   - パスに `shims` / `.pyenv` / `.asdf` / venv ディレクトリが含まれないこと。

4. PATH が既定状態であることを記録する。

   ```bash
   bash -lc 'printenv PATH'
   ```

   retry 用に PATH を変更していないことを Operator が明記する。

5. Gate 10 / 11 を確認する（model 起動なし）。

   **コンテナ通常shellでの成功はGate 10の証明ではありません。** Codex が生成コマンドを実行する Bubblewrap sandboxを経由し、Runと同じ `bash -lc` で frozen Evidence command を起動します。bytecode抑止はpreflightのみで、Evidence command自体は変えません。

   ```bash
   /cx/bin/codex sandbox -P t1-workspace -C /work -- bash -lc 'PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests'
   echo "sandbox-test-exit=$?"
   ```

   - **Gate 10**: sandbox内で `python` が起動し、実際にunittestの収集・実行まで到達したことを出力で確認する。exit 127、sandbox起動失敗、予期せぬ環境エラーはSTOP。
   - **Gate 11**: untouched fixtureで期待された具体的なテストfailureが確認できること。**exit 1だけではPASSにしない**（bwrap起動エラー等も同じexit codeになり得る）。
   - 実際のmodel Runが別sandbox policyでcommandを実行するならpreflightの適合性は未証明としてSTOPし、Reviewer判断を求める。
   - stdout/stderr、終了コード、sandbox起動コマンドを記録し、通常shellの解決経路診断と区別する。

6. Gate 12 として fixture file set / bytes を再照合する（既存手順どおり）。

### 記録方法

- 上記 1〜5 の command（手順 2〜4 の通常shell診断と手順 5 のCodex sandbox内Evidenceを区別する）と出力全文、実行日時（タイムゾーン付き）、Operator 名を、retry の preflight 記録として Issue #15 側の reviewed disposition に添付する（runs/ や archive には書き込まない）。
- 「normal experimental sandbox 内で実行した」ことは、sandbox mode 設定値（Codex の sandbox / approval 設定）と、確認を同じ sandbox・同じ workspace パスで行った旨を併記して示す。host shell で代替確認した結果は Gate 10 evidence として扱わない。
- 1 項目でも条件を満たさなければ STOP。retry allowance は消費しない。

## preflight〜model 起動の順序付き手順

次の (a)〜(g) を**この順で 1 回だけ**実行する。(a)〜(f) はすべて model 非起動で、どこで STOP しても retry allowance は消費しない。本体 [EXP-001_RETRY_T1_R01.md](EXP-001_RETRY_T1_R01.md) の「The retry allowance is consumed when the model invocation starts.」のとおり、**allowance は (g) の開始で消費される**。

### (a) コンテナ起動

「推奨 `docker run` 構成」の変数を設定し、その `docker run` を実行する。

### (b) ディレクトリ作成

コンテナ内で次を実行する。

```bash
mkdir -p "$HOME" "$CODEX_HOME"
```

### (c) `config.toml` 作成

Reviewer Judgment の `approval_policy` に応じて、次のどちらか**一方だけ**を実行する（各ブロックが config.toml の全文）。

明示する場合（推奨 `never`。別の値と判断された場合は `never` をその値に置き換える）:

```bash
cat > "$CODEX_HOME/config.toml" <<'EOF'
model = "gpt-6.1-sol"
model_reasoning_effort = "high"
approval_policy = "never"
default_permissions = "t1-workspace"

[permissions.t1-workspace]
description = "workspace-write equivalent; CODEX_HOME (auth.json) hidden from sandboxed commands"
extends = ":workspace"

[permissions.t1-workspace.filesystem]
"/tmp/codex-home" = "deny"
EOF
```

省略と判断された場合（`approval_policy` 行を含めない）:

```bash
cat > "$CODEX_HOME/config.toml" <<'EOF'
model = "gpt-6.1-sol"
model_reasoning_effort = "high"
default_permissions = "t1-workspace"

[permissions.t1-workspace]
description = "workspace-write equivalent; CODEX_HOME (auth.json) hidden from sandboxed commands"
extends = ":workspace"

[permissions.t1-workspace.filesystem]
"/tmp/codex-home" = "deny"
EOF
```

### (d) 非model preflight

「非model確認手順」の手順 1〜6 を実行し、特に手順 5 の**sandbox内**Evidence commandがunittest収集と期待する初期FAILへ到達したことを確認する。加えて次を実行して出力を記録する。

```bash
/cx/bin/codex --version
/cx/bin/codex login status
cat "$CODEX_HOME/config.toml"
/cx/bin/codex --strict-config doctor --all --ascii --no-color
sha256sum /run-input/prompt.md
/cx/bin/codex sandbox -P t1-workspace -C /work -- bash -lc 'echo ok'
/cx/bin/codex sandbox -P t1-workspace -C /work -- bash -lc 'if cat /tmp/codex-home/auth.json >/dev/null 2>&1; then echo "BLOCK: sandbox can read auth file"; exit 1; elif test -e /tmp/codex-home/auth.json; then echo "PASS: auth file exists but is not readable by sandbox process"; else echo "PASS: auth file not visible to sandbox process"; fi'
env | cut -d= -f1 | grep -E 'OPENAI|TOKEN|KEY|AUTH' || echo "PASS: no auth-like env keys"
/cx/bin/codex sandbox -P t1-workspace -C /work -- bash -lc 'env | cut -d= -f1 | grep -E "OPENAI|TOKEN|KEY|AUTH" || echo "PASS: no auth-like env keys in sandbox"'
# Codex 本体プロセスの同定（コンテナ側シェルで実行。sandbox 内の probe は 5 秒待ってから走る）
/cx/bin/codex sandbox -P t1-workspace -C /work -- bash -lc 'sleep 5; for p in /proc/[0-9]*; do st=$(cut -d" " -f22 $p/stat 2>/dev/null || echo unknown); echo "pid ${p#/proc/} starttime $st"; for f in environ maps; do if head -c1 $p/$f >/dev/null 2>&1; then echo "  BLOCK: $f reachable"; else echo "  $f denied"; fi; done; if (exec 3<$p/mem) 2>/dev/null; then echo "  BLOCK: mem reachable"; else echo "  mem denied"; fi; if ls $p/fd >/dev/null 2>&1; then echo "  BLOCK: fd reachable"; else echo "  fd denied"; fi; done' > /tmp/proc-probe.txt 2>&1 &
TARGET=$!
sleep 1
# $! 自身の exe が /cx/bin/codex ならそれを、そうでなければ子孫のうち exe が /cx/bin/codex の最上位プロセスを候補にする
find_codex() { if [ "$(readlink /proc/$1/exe 2>/dev/null)" = /cx/bin/codex ]; then echo "$1"; return; fi; for s in /proc/[0-9]*/stat; do c=${s#/proc/}; c=${c%/stat}; if [ "$(cut -d' ' -f4 "$s" 2>/dev/null)" = "$1" ]; then find_codex "$c"; fi; done; }
CODEX_PID=$(find_codex "$TARGET")
echo "launcher pid $TARGET candidates: ${CODEX_PID:-none}"
echo "codex pid $CODEX_PID exe $(readlink /proc/$CODEX_PID/exe 2>/dev/null || echo unreadable)"
tr '\0' '\n' < /proc/$CODEX_PID/cmdline | head -n 2
echo "codex pid $CODEX_PID starttime $(cut -d' ' -f22 /proc/$CODEX_PID/stat)"
ps -o pid,ppid,lstart,args -p "$CODEX_PID"
wait "$TARGET"
cat /tmp/proc-probe.txt
find /work -maxdepth 3
ls -la /run-input
```

- `--version` が `codex-cli 0.160.0`、`login status` がログイン済み（ChatGPT）、prompt の SHA-256 が Gate 7 の値、sandbox が `ok` であること。
- `doctor` の Configuration 欄が `[ok] config  loaded`・`config.toml parse  ok` で、`unrecognized configuration setting` / `is ignored` の startup warning が無く、`model` が `gpt-6.1-sol`、sandbox 行の approval が (c) の判断どおり（明示 `never` なら `approval Never`）、`[ok] auth  auth is configured` であること。auth 読み取りテストが `PASS` であること（`BLOCK`・判定不能・sandbox 実行失敗は STOP）。以上は**本物の auth を mount した Run と同一構成**での再確認であり、ダミー auth での事前確認では代替しない。
- 環境変数: コンテナ・sandbox の両方で認証関連キー（`OPENAI` / `TOKEN` / `KEY` / `AUTH` を含むキー名）が無いこと。キー名のみを出力し、値は出力しない。
- Codex 本体プロセス: PASS は、**対象の Codex 本体プロセスを確実に同定でき、その `environ` / `maps` / `mem` / `fd` のすべてへのアクセスが denied の場合に限る**。同定は cmdline の `codex` 文字列一致に頼らず、次の手順で行う。
  1. コンテナ側シェル（sandbox の外）で `codex sandbox` をバックグラウンド起動し、`$!` を起点 PID とする。**同定の必須条件は `readlink /proc/<pid>/exe` が `/cx/bin/codex`（(a) の `docker run` で `CODEX_DIR` を `/cx` に mount した Codex 0.160.0 バイナリの絶対パス）と一致すること**であり、判定は exe だけで行う。`$!` はシェルの subshell・`timeout` 等のラッパーの pid になり得るため、`$!` 自身の exe が一致しなければ、`/proc/*/stat` の第 4 フィールド（ppid）をたどって `$!` の子孫を探索し、exe が一致する最上位のプロセスを候補とする（一致したプロセスの子孫は探索しない。Codex が同一バイナリで起動する sandbox helper を本体と取り違えないため）。候補がちょうど 1 つの場合に限りそれを対象 PID とする。あわせて `/proc/<pid>/cmdline` の argv[0..1] が `codex sandbox`（argv[0] は `/cx/bin/codex`）であることを補助情報として記録する（cmdline は判定に使わない）。対象 PID について `ps -o pid,ppid,lstart,args` で起動時刻を、`/proc/<pid>/stat` の第 22 フィールド（starttime。boot 起点の clock tick で pid namespace に依存しない）を記録する。記録するのは pid・exe・argv[0..1]・starttime・ps 出力のみで、`environ` 等の秘密値は出力しない。
  2. sandbox 内の probe は cmdline で絞らず、見えるすべての pid について pid・starttime・各ファイルの到達可否を出力する（内容は `/dev/null` に捨て、秘密値は出力しない。`mem` は offset 0 の読み取りが未マップで失敗し得るため open 可否で判定する）。
  3. 対応付け: probe 出力のうち starttime が手順 1 の値と一致するエントリがちょうど 1 つあり、pid namespace が共有されている場合は pid も一致することを確認し、そのエントリを対象とする。
  - 1 つでも `BLOCK`、対象 PID の exe が `/cx/bin/codex` と一致しない・`readlink` で読めない・exe が一致する候補が 0 個または複数で一意に特定できない、対象を対応付けできない（starttime 一致なし・複数一致・`stat` を読めず `unknown`）、sandbox 内から対象プロセスが見えない（pid namespace 分離等。見えないことは到達拒否の証明にならない）、または sandbox 実行失敗なら **STOP（判定不能、model 起動前）**。0.160.0 の doctor は `--strict-config` を受け付けるが未知キーでエラー終了しない（警告のみ）ため、判定は rc ではなくこれらの行で行う（「最小 Codex config」節の陽性コントロール参照）。
- 次は model 非起動では**未検証**のため、記録対象として扱う: `codex exec --strict-config` で config がエラーにならないこと、`codex exec` 実行時の permissions profile `t1-workspace` の実効適用（`codex sandbox -P t1-workspace` での挙動は確認済みだが exec 時の適用は未確認）と `model_reasoning_effort = "high"` の実効値。Run 後に trace / session 記録で実効値を確認し、異なれば limitation として記録する。
- Gate 13（過去 attempt の情報を持ち込まない）: `find /work -maxdepth 3` の出力全文を記録し、Gate 6 で reprepare した fixture のファイル集合と照合して、それ以外のファイル（過去 T1 attempt の archive、patch、messages、STOP-REPORT 等）が無いことを確認する。`ls -la /run-input` が `prompt.md` のみであることを確認する。あわせて host 側で、(a) の `docker run` の `-v` 一覧が auth.json・`CODEX_DIR`・`PROMPT`・`WS` の 4 つだけであり、repo の `runs/`・`infrastructure-failures/` やそれらを含む親ディレクトリがマウントされていないこと、`$WS` 自体がそれらの配下でないことを記録する。

### (e) STOP 判定

(a)〜(d) と本体 Gate 1〜13 のいずれかを満たさない、`login status` が未ログイン・期限不明、sandboxからauthが読み取れる、本物の auth を mount した同一構成での auth 読み取り拒否・証跡回収の非model再確認が未完了、環境変数に認証関連キーがある、sandbox から Codex 本体プロセスの `environ` / `maps` / `mem` / `fd` のいずれかに到達できる、または対象プロセスの exe が `/cx/bin/codex` と一致しない・読めない・一意に特定できない、対象を対応付けできない・sandbox 内から見えないために到達可否を判定できない、または (d) の出力が想定と異なる場合は STOP し、retry allowance を消費しない。

### (f) Reviewer Judgment の確認

Issue #15 に `ACCEPT N1 + G` と approval / 実行方式（「未解決の論点」5・6）に加え、比較交絡の扱い・auth読み取り隔離テスト・host側の証跡保存方式についての**個別のReviewer Judgment**が記録済みであることを確認する。未記録またはBLOCKなら STOP。

### (g) 唯一の model 起動操作

直前に開始時刻を ISO 8601 + タイムゾーンで記録し、続けて model を起動する。この起動は 1 回だけで、失敗しても再実行しない（本体手順書の Result handling に従う）。

```bash
date '+%Y-%m-%dT%H:%M:%S%z'
/cx/bin/codex exec -C /work - < /run-input/prompt.md
```

- `-m` / `-s` / `-c` は付けず、Model・Effort・sandbox・approval は (c) の `config.toml` だけから与える。Reviewer が対話実行を選んだ場合は、この行を Reviewer Judgment に記された対話起動コマンドに置き換える。

## Reviewer が ACCEPT した場合の後続手順

1. Reviewer Judgment（例: `EXP-001 T1 r01 Gate 10 environment: ACCEPT N1 + G (python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258, arm64, Codex 0.160.0 permissions profile t1-workspace (:workspace + deny /tmp/codex-home) via bwrap, seccomp codex-bwrap-seccomp.json sha256:085e468fa8e70d8c839a9abab4d74a1ab2abad74a8c26f15234ba62a8ac2e1e8, cap-drop ALL, non-root)`）を Issue #15 に記録する。構成は「候補 G の提案構成（Reviewer 判断材料）」節のとおりとし、変更する場合は再度 Reviewer 判断を求める。
2. 本体 [EXP-001_RETRY_T1_R01.md](EXP-001_RETRY_T1_R01.md) の Gate 10 直後にある本文書への参照行の「（Reviewer判断待ち）」を、承認済み表記（Issue #15 の Reviewer Judgment へのリンク付き）へ更新する PR を出す。本体の Gate 1〜13 の文言は変えない。

## 比較妥当性の limitation

- T0 r01 の実行環境（host、イメージ、OS、Python 版）は記録が無く特定不能です。T1 r01 retry の環境（G）と一致していることは保証できません。
- shell 起動方式が異なる（T0 r01: `/usr/bin/zsh -lc` / T1 r01 retry: `bash -lc`）。
- CPU アーキテクチャ: T1 r01 retry は arm64 固定。T0 r01 のアーキテクチャは記録が無く不明。
- Codex config: T0 r01 側の approval 等の config 記録と起動方式（`codex exec` / 対話）の記録が無いため、T1 r01 retry の approval 設定・起動方式が T0 と同一であることは保証できない（「未解決の論点」5・6 の Reviewer 判断で T1 側の値を確定し、その値を開示する）。
- sandbox profile: T1 r01 retry は `:workspace` を継承し認証領域を追加 deny した派生 profile `t1-workspace` を使い、T0 の normal experimental sandbox（`workspace-write`）と同一とは認定しない。T0/T1 比較は引き続き `environment-confounded / descriptive-only` とする。
- OS・shell・Python 版の差は paired comparison（T0 vs T1）の交絡要因になり得ます。本 limitation は EXP-001 summary で**開示対象**とし、`normalize-name` r01 の T0/T1 比較を解釈する際に併記します。
- この limitation は Evaluation semantics・Counting を変更しません。開示のみを求めます。

## 今後の Run での実行環境記録

同種の特定不能を繰り返さないため、本 disposition の適用対象である T1 r01 retry では、上記非model確認手順 1〜4 の出力をそのまま実行環境の記録項目とします（コンテナの場合は手順 1 の digest を含む）。

- 記録先は既存方針どおり **Issue #15 側の reviewed disposition への添付**とし、Frozen artifact・`runs/`・schema・scripts は変更しません。
- 残り matrix slot への適用は未解決の論点 4 を参照。

## 未解決の論点

1. N1（配布物内 symlink の許容）を Gate 10 の正当な解釈として認めるか。
2. T0 r01 環境が特定不能であることを前提に、「新しく定めた環境（G）での T1 retry + limitation 開示」で paired comparison を成立させてよいか（Reviewer 判断）。
3. コンテナ内で Codex の normal experimental sandbox が host 実行時と同等の write allow/deny 制御を持つことの確認方法。
4. 本 disposition を残り matrix slot（T0 側を含む）にも適用するか。本文書は T1 r01 retry のみを対象とし、他 Run には流用しない。
5. T1 retry を `codex exec` で実行するか、対話で実行するか（T0 の起動方式は記録上不明。推奨: `codex exec`）。limitation「Codex config」に対応。
6. `approval_policy` を明示するか、明示するならどの値か（推奨: `never`。根拠は「最小 Codex config」節）。limitation「Codex config」に対応。
7. sandbox内でmodelが起動するコマンドから `auth.json` を読み取れないことを非modelで確認できたか（不能ならSTOP）。
8. `--rm` + tmpfs `CODEX_HOME` が消える前に、必要な観測事実を機密保護したhost-side sinkへ保存できることを確認したか（不能ならSTOP）。
9. G環境のT1とT0 r01の環境不一致を踏まえ、当該ペアを `environment-confounded / descriptive-only` として扱うか（Topology効果の因果主張を禁じる判断）。
10. `codex exec` 実行時に permissions profile `t1-workspace` が実効適用されることは Run 前に確認できない（`codex sandbox -P t1-workspace` と doctor のみ確認済み）。Run 後の trace 確認だけでなく、この未確認を Reviewer が承知のうえで受容するか。
