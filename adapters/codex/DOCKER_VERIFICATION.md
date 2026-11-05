# Codex CloudのDocker検証と運用メモ

2026-11-03 UTC、基準main `2bc20c47bd6acef9d81ea315a4fa51f5228264bb`。このCloudで行った開発用コンテナの確認記録です。非規範的なadapterメモで、必須Gate・Runtime設定・実験起動権限を追加しません。

## 目的と対象

Codexで作成した変更を検証する際、Pythonの単体テストに加えて、Dockerの設定値と実動作を照合できるようにします。今回動かしたのはPythonだけのダミー処理で、Codex/Claude CLIや実験用モデルAPIではありません。通常委託のモデル処理・費用と、追加の実験起動は区別します。

[Cloud検証記録](CLOUD_VERIFICATION.md)に続く確認です。[#220の予備キット](../../docs/model-role-split/PILOT_RUNBOOK.md)と[#244の較正手順](../../docs/hard-task/CALIBRATION_RUNBOOK.md)が使うDocker制約の一部を参考にしましたが、キットの`run`やisolation関数は呼び出していません。Operator用の実験を代行する検証ではありません。

## 実行環境・入力

| 項目 | 今回の観測・指定 |
|---|---|
| daemon | 明示したローカルsocket `unix:///var/run/docker.sock`、Docker Engine 28.4.0 |
| OS / architecture / kernel | Linux x86_64、kernel 6.18.57、storage driver vfs |
| image | `python:3.12-slim`をlinux/amd64で取得後、以下のRepoDigestを固定して起動 |
| RepoDigest | `python@sha256:b18b261e1b4974b4f321451ad5251ded85abb22c2b8b262da527dda1d031ab30` |
| 入力 | 自作の秘密を含まないdummy.txtだけ。ホスト側の一時fixtureをreadonly bind |
| user / 権限 | `65534:65534`、cap-drop ALL、no-new-privileges、privilegedなし |
| filesystem | read-only rootfs、`/tmp`だけtmpfs（16MiB、noexec/nosuid、mode1777） |
| network | `none`、port公開なし。Docker socketや認証ファイルはmountしない |
| resource設定 | memory128MiB、pids64、CPU0.5 |

Dockerのendpoint/context/TLS選択環境変数をコマンド単位で外してローカルdaemonを指定しました。既存DOCKER_CONFIG・registry認証・proxy・CAは保持しています。image取得は正規経路で行い、コンテナの通信遮断とは別の段階として扱います。制限を回避するhost networkやdaemon再設定はしていません。

## 実測結果

全体で16項目PASS。設定値の照合、処理の正常対照、拒否の実測を分けます。

| 観点 | 証拠・結果 | 分かる範囲 |
|---|---|---|
| daemon / image | Linux/amd64を確認 | 今回のCloud環境。arm64互換性ではない |
| inspect | network none、ReadonlyRootfs、CapDrop、SecurityOpt、UID、limits、tmpfs、非privileged、公開portなしが指定と一致 | Dockerへの設定反映 |
| mount | 自作fixture1件だけ、destination/RW=false/source一致 | 今回のbind構成。秘密が漏れない一般的証明ではない |
| container処理 | exit0、uid/gid65534 | 指定したPython処理の正常終了・非root実行 |
| 正常対照 | dummy読取り、`/tmp`書込み、loopback自己接続が成功 | Pythonやsocket操作自体が動くこと |
| rootfs書込み | `/var/tmp`で`EROFS`（errno30） | 単なる非rootのpermission不足と区別するため本来書込可能な場所を使用 |
| readonly bind書込み | dummy.txtで`EROFS`（errno30） | fixtureは元々mode0666。UIDだけの拒否をreadonlyの効果にしない |
| 実プロセス状態 | CapEff=0、NoNewPrivs=1 | 実プロセスの可視状態。全権限昇格経路の試験ではない |
| 経路 | 非loopbackのIPv4/IPv6 route件数0 | 当該network namespaceの経路表 |
| UDP送信 | 文書用IP `192.0.2.1:9`への送信が`ENETUNREACH`（errno101） | 当該試行で経路なし。timeoutやECONNREFUSEDを遮断成功にはしない |
| cgroup | memory.max=134217728、pids.max=64、cpu.max=`50000 100000` | 設定値が見えること。OOM/PID枯渇/CPU時間のstress試験は未実施 |

自身で作成したcontainerとfixtureが正常終了後に削除されたことも確認しました。image cacheは保持。他のcontainer・volume・ファイルを削除していません。Docker呼出しにtimeout（通常30秒、pull180秒）とfinallyの後片付けを設けましたが、異常注入によるcleanup保証の検証はしていません。

## Codex作業での再確認手順

既存の実験キットや必須CIを変更せず、必要な開発作業に対して使う任意の確認です。

1. 作業規約と対象SHAを確認し、実行対象をPython等の非model処理へ限定する。実験キットの`run`、実認証、モデル起動へ切り替えない。
2. ローカルsocketへの接続、daemon/OS/architecture、固定image digestを確認する。別daemonへ向け直したり、動作中daemonを再起動して通過させない。
3. 秘密を含まない専用fixtureと固有container名を用意する。readonly検査対象は元々そのUIDで書けるようにし、正常書込み対照はtmpfsに分ける。
4. 以下の設定例でcreateし、**start前に**inspectから選択したHostConfig・UID・mountだけを照合する。Config.Envやregistry認証を出力しない。不一致は停止し、権限を追加して検査を通さない。
5. dummy読取/tmp書込/loopback自己接続の正常対照と、EROFS/CapEff/NoNewPrivs/経路表/UDP errnoを確認する。取得不能やtimeoutはUNKNOWN/失敗として残す。
6. exitと原出力を記録し、自身のcontainer/fixtureだけを後片付けする。検証担当と文書・変更のレビュー担当を分け、5観点で照合する。設定・版を変えた場合だけ影響する検証をやり直す。

次は今回使用したcreateの設定パターンです。`<固有名>`と`<自作fixtureの絶対path>`はその作業専用の値、`<固定RepoDigest>`は上記等の確認済み値へ置き換えます。これは処理内容を省略した起動例であり、実測16項目を自動採点するコマンドではありません。

```text
env -u DOCKER_HOST -u DOCKER_CONTEXT -u DOCKER_TLS \
  -u DOCKER_TLS_VERIFY -u DOCKER_CERT_PATH \
  docker --host=unix:///var/run/docker.sock create \
  --name <固有名> --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --user 65534:65534 \
  --pids-limit 64 --memory 128m --cpus 0.5 \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m,mode=1777 \
  --mount type=bind,src=<自作fixtureの絶対path>,dst=/fixture,readonly \
  <固定RepoDigest> python -I -c '<秘密を含まない検証処理>'
```

実行記録には対象SHA、image digest、daemon/arch、設定照合、正常/拒否結果、errno、exit、cleanup、未確認事項を残します。dummy以外の実sourceや生の観察記録を公開せず、秘密・個人情報・環境固有の一時pathは公開文書から省きます。今回の原コマンド・JSON・ログはrepo外で保存し、文書作成担当と別セッションReviewerが照合します。

## この結果から認定しないもの

- Codex自身のsandbox、roleごとのtool権限、authファイルを読めないこと、context分離、実traceの完全性。
- EXP-001の固定arm64/runtime/config/独自seccomp、Macのsandbox-exec、Docker Desktop固有mountの再現。
- #220のproxy認証・課金経路やsettings deny、#244の予算上限の実効強制、Operator実測の受理。
- コンテナの全攻撃経路の安全性、resource上限到達時の強制挙動、異常終了時のcleanup保証。
- 単一/複数Agent・複数モデルの品質/時間/費用の優劣、無料・追加課金ゼロの保証。

この検証ではseccomp profileを明示指定せず、Docker daemonの既定に従いました。EXP-001の独自profileと同じだとは扱いません。モデルを追加起動する実験、認証情報や設定の変更、既存のHuman専権の操作は[Harness](../../docs/AGENT_HARNESS.md)と各手順書の条件に従います。#288の規則変更PRの別モデルレビュー証跡・Human merge条件も維持します。
