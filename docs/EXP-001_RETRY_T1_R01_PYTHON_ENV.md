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

Operator host の測定（2026-10-08 09:30、macOS + Homebrew）:

| 項目                        | 結果                  |
| --------------------------- | --------------------- |
| `command -v python`         | exit 127（未解決）    |
| `/opt/homebrew/bin/python3` | 存在                  |
| `python`（unversioned）     | default PATH 上に無し |

これは元attemptの exit 127（`zsh: command not found: python`、[STOP-REPORT](../experiments/EXP-001-t0-vs-t1/runs/infrastructure-failures/EXP-001-train-normalize-name-r01-T1/01a1132a-1de0-70d2-b810-c500b79430c9/STOP-REPORT.md)）と同じ原因です。この状態のままではGate 10でSTOPになります。

参考: accepted T0 r01 の `trace.yaml` は Evidence command を `/usr/bin/zsh -lc 'python -m unittest discover -s tests'` として記録しています。`/usr/bin/zsh` は macOS 標準（`/bin/zsh`）と異なるため、T0 は現在の Operator host とは別の環境で実行された可能性があります。これは trace からの推測であり、確定事実ではありません（「未解決の論点」参照）。

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

**推奨: 解釈 N1 を採用し、候補 G（Linux コンテナで、イメージ既定状態として `python` が Python 3.12 系 CPython に解決する環境）を T1 r01 retry の Run 環境とする。**

理由:

1. **要件適合性**: macOS host 系の候補（A〜F）は、いずれも既定状態では `python` が解決せず、解決させるには PATH mutation・shim・Operator 作成の symlink のどれかが必要で、Gate 10 の禁止事項に直接該当します。G だけが「Operator の追加操作なしに、Run 環境の既定状態で literal command が解決する」を構成できます。
2. **安全性 / 再現性**: イメージ digest を記録すれば、Reviewer が同じ解決経路を後から再確認できます。host の rc ファイルや Homebrew の状態に依存しません。
3. **T0 との比較可能性**: accepted T0 の trace に `/usr/bin/zsh` が記録されており、T0 も macOS 標準以外の環境だった可能性があります。G はこれと整合しやすい一方、T0 と同一環境である確認は取れていません（論点 2）。
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

## 非model確認手順（Gate 10 evidence）

**Codex model を起動しない**状態で、retry に使う normal experimental sandbox 内の、fresh workspace（Gate 6 で reprepare 済み）をカレントディレクトリとして実行します。Gate 12 のため bytecode 書き込みを抑止します。

1. 環境識別を記録する。

   ```bash
   uname -a
   cat /etc/os-release
   echo "$SHELL"
   ```

   コンテナの場合はイメージ名と digest を host 側で記録する（例: `docker image inspect --format '{{.RepoDigests}}' <image>`）。

2. 解決先を記録する（追加設定を一切読み込まない状態で）。

   ```bash
   command -v python
   type -a python
   python --version
   ```

   - `command -v python` が exit 0 で絶対パスを返すこと。
   - `type -a python` に `alias` / `function` が出ないこと。

3. 解決先が shim / wrapper でないことを確認する。

   ```bash
   ls -l "$(command -v python)"
   python -c 'import sys; print(sys.executable); print(sys.version)'
   file -L "$(command -v python)"
   readlink -f "$(command -v python)"
   ```

   - `file -L` が ELF / Mach-O 実行ファイルを示すこと（`shell script` / `text` は不可）。
   - 解決経路に symlink がある場合は、全段の symlink とその所有パッケージ（例: `dpkg -S`、イメージ定義）を記録し、Operator が作成したものではないことを示す。
   - パスに `shims` / `.pyenv` / `.asdf` / venv ディレクトリが含まれないこと。

4. PATH が既定状態であることを記録する。

   ```bash
   printenv PATH
   ```

   retry 用に PATH を変更していないことを Operator が明記する。

5. Gate 10 / 11 を確認する（model 起動なし）。

   ```bash
   PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests
   echo "exit=$?"
   ```

   - command が起動すること（exit 127 でないこと）= Gate 10。
   - 未変更 fixture で期待どおりの初期 Evidence FAIL になること = Gate 11。

6. Gate 12 として fixture file set / bytes を再照合する（既存手順どおり）。

### 記録方法

- 上記 1〜5 の command と出力全文、実行日時（タイムゾーン付き）、Operator 名を、retry の preflight 記録として Issue #15 側の reviewed disposition に添付する（runs/ や archive には書き込まない）。
- 「normal experimental sandbox 内で実行した」ことは、sandbox mode 設定値（Codex の sandbox / approval 設定）と、確認を同じ sandbox・同じ workspace パスで行った旨を併記して示す。host shell で代替確認した結果は Gate 10 evidence として扱わない。
- 1 項目でも条件を満たさなければ STOP。retry allowance は消費しない。

## 未解決の論点

1. N1（配布物内 symlink の許容）を Gate 10 の正当な解釈として認めるか。
2. T0 r01 の実行環境（`/usr/bin/zsh` の記録）と T1 retry 環境の同等性。T0/T1 間で OS・Python 版が異なると paired comparison の交絡要因になり得るため、T0 環境が特定できるなら同一環境を優先すべきか。
3. コンテナ内で Codex の normal experimental sandbox が host 実行時と同等の write allow/deny 制御を持つことの確認方法。
4. 本 disposition を残り matrix slot（T0 側を含む）にも適用するか。本文書は T1 r01 retry のみを対象とし、他 Run には流用しない。
