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

Reviewer が `ACCEPT N1 + G` を判断するための具体構成です。下記の検証はすべて **model 非起動**（`codex sandbox -P :workspace` による sandbox 単体の起動）で行い、retry allowance は消費していません。確認範囲は colima（docker v29.7.2）・arm64・kernel `7.0.12-linuxkit` に限られます。

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
- sandbox: Codex `workspace-write` 相当（Linux では bubblewrap）。
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

### 残るリスク

- user namespace の作成と `mount` / `pivot_root` をコンテナ内で許可するため、moby 既定より攻撃面が広がる（kernel の userns / mount 系脆弱性の影響を受けうる）。cap は全て落とし、非 root・`no-new-privileges`・read-only rootfs で緩和する。
- `clone` / `unshare` / `mount` は引数条件なしで許可するため、bwrap 自身だけでなく、Codex sandbox 内で model が実行するコマンドも入れ子の user / mount namespace を作れる。
- AppArmor の `docker-default` プロファイルが有効な host（Ubuntu 等）では `mount` が AppArmor 側で拒否され、本構成が再現しない可能性がある（確認環境の colima では未検証の論点）。その場合も `apparmor=unconfined` は使わず STOP し、Reviewer 判断を求める。
- 確認は colima・arm64・kernel `7.0.12-linuxkit` に限られる。別 host / 別 kernel / amd64 では再確認が必要。

### 認証

- ホストの `~/.codex/auth.json` **のみ**を `:ro` でマウントし、`CODEX_HOME` はコンテナ内の fresh なディレクトリとする（ホストの config・sessions・履歴は持ち込まない）。
- ログイン方式は ChatGPT（2026-10-08 にホストで `codex login status` を実測）。
- `auth.json` は `:ro` のため、model 起動後のトークン refresh は書き込めず失敗し得る。**refresh 不可を前提**とし、model 起動直前にコンテナ内で `/cx/bin/codex login status` を確認する。期限が近い・不明な場合は、host 側で通常どおり Codex を使ってトークンを更新してから開始する。失敗した場合は STOP（retry allowance 非消費）。
- model 起動後に認証エラーで中断した場合は infrastructure abort として STOP する（再 retry なし。本体手順書どおり）。
- `auth.json` を fresh `CODEX_HOME` へコピーして書き込み可能にする案は採らない（refresh 結果が host 側トークンと分岐し、host 側の認証状態に影響し得るため）。

### 最小 Codex config（fresh `CODEX_HOME/config.toml`）

```toml
model = "gpt-6.1-sol"
model_reasoning_effort = "high"
sandbox_mode = "workspace-write"
```

approval の扱い（根拠と Reviewer 判断事項）:

- `origin/main` の T0 r01 `trace.yaml` / `run-meta.yaml` / `execution-attestation.yaml`、`pilot/OPERATOR.md`、`docs/EXP-001_EXECUTION.md` を確認したが、approval / sandbox 設定値と、`codex exec` か対話かの実行方式の記録は**無い**。
- T0 `trace.yaml` には `cliExitCode: 0` と `humanInterventions: 0` があり、非対話実行（`codex exec`）と整合するが、実行方式を断定する記録ではない（**推測**）。
- Codex 0.160.0 の `codex exec` の approval 既定は、公式ドキュメント（[Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)、2026-10-08 参照）に記載が無い。同ページは sandbox 既定を read-only と記載する（このため `sandbox_mode` を明示する）。`codex exec --help`（0.160.0、model 非起動で確認）には `--ask-for-approval` が無く、承認を対話で求めるオプションは提供されていない。
- このため `config.toml` には `approval_policy` を書かない（実行方式の既定に従う）ことを提案する。次は **Reviewer 判断事項**:
  1. T1 retry を `codex exec` で実行するか、対話で実行するか（T0 の実行方式は記録が無い）。
  2. `approval_policy` を明示するか、明示するならどの値か。

### 推奨 `docker run` 構成

repo ルートから実行する想定。`<codex-linux-arm64-musl-dir>`・`<fresh-workspace>` は Operator が用意する（workspace は Gate 4 / 6 / 9 のとおり fresh）。`HOME` と `CODEX_HOME` は tmpfs `/tmp` 上に置き、起動後に `mkdir -p "$HOME" "$CODEX_HOME"` で作成する（fresh `config.toml` もここに置く）。codex は PATH を変更せず `/cx/bin/codex` の**絶対パス**で起動する。

```bash
docker run --rm -it \
  --platform linux/arm64 \
  --security-opt seccomp=experiments/EXP-001-t0-vs-t1/pilot/retry-t1-r01/codex-bwrap-seccomp.json \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  --user "$(id -u):$(id -g)" \
  --read-only --tmpfs /tmp \
  -e HOME=/tmp/home \
  -e CODEX_HOME=/tmp/codex-home \
  -v "$HOME/.codex/auth.json":/tmp/codex-home/auth.json:ro \
  -v <codex-linux-arm64-musl-dir>:/cx:ro \
  -v <fresh-workspace>:/work -w /work \
  python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 \
  bash -l
```

この `HOME=/tmp/home`・`CODEX_HOME=/tmp/codex-home` 設定（auth マウントなし、config.toml なし）で、`/cx/bin/codex sandbox -P :workspace -C /work -- bash -lc 'echo ok'` が model 非起動で `ok` / rc=0 となることを 2026-10-08 に docker（colima、arm64）で確認した。このとき `/cx/bin/codex --version` は `codex-cli 0.160.0`、Codex は `CODEX_HOME` が `/tmp` 配下のため PATH 用 helper を作らない旨の WARNING を出したが、sandbox 起動には影響しなかった。コンテナ内の `$SHELL` は `/bin/sh`、`getent passwd "$(id -u)"` は該当なし（host uid がイメージの passwd に無い）、`ps` はイメージに無く、`readlink /proc/$$/exe` は `/usr/bin/bash` だった。

## 非model確認手順（Gate 10 evidence）

**Codex model を起動しない**状態で、retry に使う normal experimental sandbox 内の、fresh workspace（Gate 6 で reprepare 済み）をカレントディレクトリとして実行します。Gate 12 のため bytecode 書き込みを抑止します。

手順 2〜5 は、実 Run と同じ login shell 起動方式（候補 G ではイメージ既定の bash による `bash -lc '<cmd>'`。zsh は追加しない）で実行し、その表記のまま記録します。login shell が読む Run 環境既定の初期化（イメージ / OS の標準状態）は Run と同条件として扱い、Operator が追加・変更した設定（rc ファイル追記、`export PATH=...`、`alias`、venv activate 等）が無いことを Operator が明記します。

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

   ```bash
   bash -lc 'PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests'
   echo "exit=$?"
   ```

   - command が起動すること（exit 127 でないこと）= Gate 10。
   - 未変更 fixture で期待どおりの初期 Evidence FAIL になること = Gate 11。

6. Gate 12 として fixture file set / bytes を再照合する（既存手順どおり）。

### 記録方法

- 上記 1〜5 の command（手順 2〜5 は Run と同じ login shell 起動の表記のまま。G では `bash -lc`）と出力全文、実行日時（タイムゾーン付き）、Operator 名を、retry の preflight 記録として Issue #15 側の reviewed disposition に添付する（runs/ や archive には書き込まない）。
- 「normal experimental sandbox 内で実行した」ことは、sandbox mode 設定値（Codex の sandbox / approval 設定）と、確認を同じ sandbox・同じ workspace パスで行った旨を併記して示す。host shell で代替確認した結果は Gate 10 evidence として扱わない。
- 1 項目でも条件を満たさなければ STOP。retry allowance は消費しない。

## Reviewer が ACCEPT した場合の後続手順

1. Reviewer Judgment（例: `EXP-001 T1 r01 Gate 10 environment: ACCEPT N1 + G (python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258, arm64, Codex 0.160.0 workspace-write via bwrap, seccomp codex-bwrap-seccomp.json sha256:085e468fa8e70d8c839a9abab4d74a1ab2abad74a8c26f15234ba62a8ac2e1e8, cap-drop ALL, non-root)`）を Issue #15 に記録する。構成は「候補 G の提案構成（Reviewer 判断材料）」節のとおりとし、変更する場合は再度 Reviewer 判断を求める。
2. 本体 [EXP-001_RETRY_T1_R01.md](EXP-001_RETRY_T1_R01.md) の Gate 10 直後にある本文書への参照行の「（Reviewer判断待ち）」を、承認済み表記（Issue #15 の Reviewer Judgment へのリンク付き）へ更新する PR を出す。本体の Gate 1〜13 の文言は変えない。

## 比較妥当性の limitation

- T0 r01 の実行環境（host、イメージ、OS、Python 版）は記録が無く特定不能です。T1 r01 retry の環境（G）と一致していることは保証できません。
- shell 起動方式が異なる（T0 r01: `/usr/bin/zsh -lc` / T1 r01 retry: `bash -lc`）。
- CPU アーキテクチャ: T1 r01 retry は arm64 固定。T0 r01 のアーキテクチャは記録が無く不明。
- Codex config: T0 r01 側の approval 等の config 記録が無いため、T1 r01 retry の approval 設定が T0 と同一であることは保証できない。
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
