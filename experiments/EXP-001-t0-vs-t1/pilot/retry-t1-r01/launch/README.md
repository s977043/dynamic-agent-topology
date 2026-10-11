# EXP-001 T1 r01 retry 起動キット

[docs/EXP-001_RETRY_T1_R01_PYTHON_ENV.md](../../../../../docs/EXP-001_RETRY_T1_R01_PYTHON_ENV.md) の preflight〜model 起動手順を、本番前に練習課題で通しで確認するためのキット。本番手順の正は同文書であり、本キットはそれを置き換えない。

| パス | 内容 |
| --- | --- |
| `lib.sh` | 共通関数（ログ、STOP、SHA-256、権限、秘密値パターン検査。値は出力しない） |
| `doc-extracted/` | 同文書のコードブロックを抽出したスクリプト（preflight (d)、proc-check、host-mounts、証跡回収など） |
| `rehearsal/fixture/`・`rehearsal/prompt.md` | 実験枠外の練習課題（`leap.py` の不具合修正）。EXP-001 の fixture・prompt ではない |
| `rehearsal/run.sh` | リハーサル 1 回分の実行スクリプト |
| `SHA256SUMS` | 本ディレクトリの全ファイル（自身を除く）の SHA-256 |

## リハーサル手順

1. `shasum -a 256 -c SHA256SUMS` で全行 `OK` を確認する。
2. Git 管理外の作業ディレクトリを用意し、環境変数を与えて実行する。
   - `WORK_ROOT`: 出力先（`r<N>/` を作る。既存なら STOP）
   - `REPO`: 本リポジトリの clone（`origin/main` の seccomp profile を取り出し、SHA-256 を照合）
   - `CODEX_DIR`: Codex 0.160.0 linux-arm64 musl の vendor ディレクトリ（`/cx:ro` に mount）
   - 実行例: `WORK_ROOT=<dir> REPO=<clone> CODEX_DIR=<vendor dir> bash rehearsal/run.sh <N>`
3. 本物の `~/.codex/auth.json` を `:ro` で bind し、`codex exec --skip-git-repo-check` を 1 回実行する。スクリプトは auth の内容を読まず・出力しない。
4. `r<N>/status.log` の summary で、下記ゲートを判定する。`codex-stdout.log` は秘密値を含み得るため、確認は秘密値パターン検査の件数で行い、全文を共有しない。

## 必須ゲート（4 分類。1 つでも満たさなければ本番に進まない）

| 分類 | 条件 |
| --- | --- |
| 安全 | sandbox から auth が読めない（`AUTH_DENIED`）。コンテナ停止後の残存 0。session 記録上の実効 permission profile が `/tmp/codex-home` を deny している |
| 秘密値 | 証跡と stdout の秘密値パターン検出 0 件。evidence.tar に `auth.json` が無い |
| プロトコル | `codex-cli 0.160.0`、`login status` が行一致で `Logged in using ChatGPT`、`codex exec` が model 呼び出しまで到達し終了コードが `docker exec` の rc に伝播する |
| 回収不能 | 証跡回収 rc=0、`codex-exit`・開始/終了時刻・`codex-home/sessions` が evidence.tar にある |

## 推奨（事後改善。本番の可否には使わない）

- `--tmpfs /tmp/codex-home` 起因の警告 `could not create PATH aliases ... under temporary dir "/tmp"` は無害（動作に影響なし。r2〜r4 で確認）。抑止は不要。
- 証跡回収で `codex-home/sessions` が無い場合の tar エラーを、欠落ファイル名だけ記録する形に整える。
- 本番 Run 後も trace / session 記録で実効 model・effort・approval・permission profile を再確認する（r4 は練習課題での確認）。

## リハーサル結果（2026-10-11、オーガナイザー実測）

| 回 | 結果 | 内容 |
| --- | --- | --- |
| r1 | STOP（setup） | スクリプト不具合。`codex login status` は 1 行目に警告を出すため、`head -1` + pipefail の判定が失敗。行一致判定に修正 |
| r2 | 失敗（model 呼び出し前） | `codex exec -C /work -` が `Not inside a trusted directory and --skip-git-repo-check was not specified.` で exit 1。ヒアドキュメント末尾が `date` だったため `docker exec` rc=0 と誤報告。sessions 未作成で回収一部失敗（3 エントリ）。秘密値 0 件、残存 0 |
| r3 | 失敗（model 呼び出し前） | config に `[projects."/work"] trust_level = "trusted"` を追加しても同じエラーで exit 1（`exit $rc` で rc=1 を伝播）。回収一部失敗、秘密値 0 件、残存 0 |
| r4 | PASS | `--skip-git-repo-check` 付き。setup ok（0.160.0、login ok、AUTH_DENIED）。exec 04:55:22Z→04:55:45Z（23 秒）、codex-exit 0、docker exec rc=0。回収 rc=0（8 エントリ、auth.json なし）、秘密値 0 件、残存 0。tests FAILED→OK。session 記録の実効値: `gpt-6.1-sol` / `high` / `never` / `workspace-write`（network なし）/ `managed / restricted`（`/tmp/codex-home` を含む）/ `0.160.0` |
