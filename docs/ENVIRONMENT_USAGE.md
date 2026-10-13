# 開発・レビュー・実験環境の比較と使い分け

2026-10-14 JSTの検討記録。Codexクラウド、Claude Codeクラウド、Mac、ThinkPadを用途別に比較するための非規範的な台帳と提案です。実行許可、環境Judgment、Run acceptance、新しい必須Gateを定義しません。自律境界は[AGENT_HARNESS.md](AGENT_HARNESS.md)、実験の進行状況は[Issue #15](https://github.com/s977043/dynamic-agent-topology/issues/15)を正本とします。

## 確認済みの実績と限界

確認時のmainは `3c54e583b289582e0873e567249818bce96a9db2`。EXP-001は受理・merge済み15/18 Run、7/9ペアで、Feature Freeze revision 3はACTIVEです。これはチェックポイントであり、以後の最新状態はIssue #15を参照します。

Codexクラウドで以下を実施しました。

| 検証・操作 | 結果 | 対象・限界 |
|---|---|---|
| PythonとCI依存 | Python 3.12.14、requirements-ci.txtの依存を導入 | 環境を再作成した後の維持は未確認 |
| Freeze / agent guidance検証 | PASS | 上記main、Frozen Artifact 33件 |
| PR #165 single-run / Freeze検証 | PASS | head `e8cb223950729974a2f74d050b07cb5e8e4ce39f`。正式ACCEPTではない |
| PR #168 review package tests | PASS | head `cd64d6ceef269c18f4c1a597ef8a046d0003b133`。独立レビューではない |
| run-kit-g selftest | PASS | main上のテンプレート・Gate等の非modelテスト。sandbox実測やmodel起動ではない |
| Git fetch / main SHA照合 | 成功 | 上記mainとの一致を確認 |
| Git push | 成功 | 後続のPR #169作成・修正時に同クラウドからbranchへpush。main更新やAPI認証とは別 |
| クラウドのgh api | Forbidden | api.github.comがHTTP許可先に含まれていない |
| GitHubコネクターのコメント投稿 | 成功 | クラウドCLIの認証・通信成功を意味しない |

操作記録: [PR #165への環境確認コメント](https://github.com/s977043/dynamic-agent-topology/pull/165#issuecomment-6150512620)。selftestやdaemon情報の追加実測は今回の作業セッションで確認したもので、EXP-001実Runの証跡ではありません。生ログ原本の公開や再実験は行っていません。

追加観測の採取日は2026-10-14 JST、環境IDは `ccarenv_b64_Y2NhcmVudl85MWMzNTlkNmNlMDA4MTkxODc1MDJiYmUyYzRiNzUwOA` です。対象mainは上記SHAで、`bash experiments/EXP-001-t0-vs-t1/pilot/run-kit-g/selftest.sh python` は `PASS: selftest` を出力しました。`docker info --format '{{json .}}'` の非秘密フィールドから、ServerVersion=28.4.0、KernelVersion=6.18.44、OperatingSystem=Debian GNU/Linux 13 (trixie) (containerized)、Architecture=x86_64、OSType=linuxを採取しました。これらは作業セッションの観測記録であり、独立再現や外部保存済みの原本ログは未確認です。

複数Agentは実験比較可能性、開発運用、権限・証跡の3視点で検討しました。結論は「クラウドは開発・機械検証・レビュー材料整理に使用し、EXP-001残りRunは承認済みOperator環境で完了する」という提案です。親contextとファイルシステムを共有する助言を正式独立Reviewerの承認へ転用しません。

## 環境一覧

設定上の値、実測値、用途ごとの承認は別に扱います。候補Gは[run-kit-g/environment.conf](../experiments/EXP-001-t0-vs-t1/pilot/run-kit-g/environment.conf)の固定値であり、現在のMac実測値ではありません。各端末のhost、Docker daemon、container、model sandboxも区別します。

| 項目 | Codexクラウド（今回の観測） | Claude Codeクラウド | Mac（現在） | ThinkPad（現在） | EXP-001承認済み候補G（基準） |
|---|---|---|---|---|---|
| OS / kernel | Docker daemon: Debian 13 containerized / 6.18.44 | 未確認 | 未確認 | 未確認 | daemon: Docker Desktop / 7.0.12-linuxkit |
| CPU architecture | host uname / daemon: x86_64 | 未確認 | 未確認 | 未確認 | aarch64 / arm64 |
| Python | 3.12.14 | 未確認 | 未確認 | 未確認 | Operator: Python 3.12、image digest固定 |
| インストール済みCLI | codex-cli 0.159.2 | 未確認 | 未確認 | 未確認 | Codex 0.160.0 linux-arm64 musl、binary SHA固定 |
| 実効model / effort | CLI版からアプリ会話の実効値を推定しない | 未確認 | 未確認 | 未確認 | 実験: gpt-6.1-sol / high |
| Docker server / context | 28.4.0 / default | 未確認 | 未確認 | 未確認 | 29.7.2 / desktop-linux |
| HTTP policy | restricted / enforced、api.github.comなし | 未確認 | 未確認 | 未確認 | 今回未再実測 |
| CLI認証 | 環境statusのsecret / outbound identity設定は空。認証ready未確認 | 未確認 | 未確認 | 未確認 | 毎Run、隔離・negative checkを確認 |
| GitHub操作経路 | Git fetch / branch push成功、gh api Forbidden、コネクター投稿成功 | 未確認 | 未確認 | 未確認 | ghでJudgment / ACCEPT照合 |
| sandbox / 権限 | 作業sessionはdanger-full-access。実験sandboxとは別 | 未確認 | 未確認 | 未確認 | 固定config / Bubblewrap等をGate実測 |
| #165原本証跡 | Operator側status.log / evidence.tar未取得 | 未確認 | 未確認 | 未確認 | Operator側で保存・回収 |

Codex CLIの版を合わせるだけではCPU・kernel・Docker・sandboxの一致を示せません。ARM emulationや同じcontainer imageもhostや計測条件の同一性を保証しません。[run-kit-g](../experiments/EXP-001-t0-vs-t1/pilot/run-kit-g/README.md)は構成不一致をENV-MISMATCHでSTOPします。新しいJudgmentだけで既存の不一致検査を通過できるわけではなく、キット変更・レビュー・統合・Judgmentと各Gateの実測が必要です。Frozen入力や評価意味論へ波及する場合は既存Freeze手順を適用します。

## 選択肢のメリット・デメリット

| 選択肢 | メリット | デメリット・未検証事項 |
|---|---|---|
| 4環境を記録して用途を分担する（推奨案） | 既存実験条件を維持しつつ開発を並行できる。障害原因と証跡の所在が明確になる | 台帳更新と材料の引き継ぎが必要。4環境すべての維持価値はまだ不明 |
| 全環境をできるだけ統一する | Python・依存・検証コマンドを共有しやすい | CPU・kernel・認証は完全統一が難しい。管理負担が増え、実験条件の変更判断も必要 |
| Codexクラウドへ集約する | 手元PCへの依存を減らし、作業・並行検討を進めやすい | CLIのAPI接続・認証・永続保存は未整備。途中移行では環境と反復が重なり比較に交絡が入る |
| 現行Operator環境を中心に維持する | 既存の承認構成と実験証跡を継続できる | Operatorと端末の稼働に依存し、開発作業との競合や待ち時間が残る |

全環境の同一化を目的とせず、用途に必要な条件を揃えるのが推奨です。これは運用上の見込みであり、4環境比較による効率改善の実測結果ではありません。

## Issue・PRへの適用案

| 対象 | クラウド利用の利益 | 残条件・リスク |
|---|---|---|
| #15 / PR #165 | Artifact照合・集計再現を進め、Operatorは実Runへ集中できる | 生ログ照合を含む独立Reviewerの正式ACCEPTが必要。環境台帳は代替にならない |
| PR #168 | Python 3.12で修正と負側テストを再現できる | 別セッションの独立レビューと必須CI等のmerge条件が残る |
| #159 施策②〜⑤ | ledger、Observe、Promoteの検証環境を共有できる | API認証・定期実行・証跡保存の準備が必要。ハーネス規則の変更は既存Human承認に従う |
| #31 | コネクターでRepository設定の確認・証跡記録を進められる | cloud CLIとは別経路。セキュリティ設定の未確認とRelease判断を完了扱いしない |
| #162 / #166等 | post-freezeの複数環境・複数model検証を設計できる | 環境差とmodel差を同時に変更すると原因を分離しにくい。現在のEXP-001へ反映しない |

## 次の検証順序

1. Claude Codeクラウド、Mac、ThinkPadで、確認日時・環境ID・repo SHA・実行階層を付けて同じ項目を採取する。未確認値を推測で埋めない。
2. 各開発環境でPython 3.12とrequirements-ci.txtを使用し、[spec-lint.yml](../.github/workflows/spec-lint.yml)の関連検証を再現する。PYTHONDONTWRITEBYTECODE=1でFrozen fixtureの生成物を防ぐ。
3. #165の原本証跡を独立Reviewerへ提供し、正式ACCEPT・merge後、承認済みOperator環境でregression r03 T0 → T1を進める。各Runで前RunのGateを守る。
4. クラウドのレビュー材料取得と保存を整える。標準review_package.py buildはgh pr view / gh apiに依存するため、コネクター利用だけでは動かない。当面は原文材料をコネクターで取得して取得元と不足を記録する。継続使用するなら正式な環境設定手順でAPI宛先・認証を構成し、通信と認証を別々に検証する。
5. 18/18受理・集計再現・独立レビュー・最終Judgment・Freeze解除後、クラウド用実験を別系列で検討する。環境ごとにT0/T1完全ペアと順序反転を確保し、予算・CPU割当・実効model/effort・image/CLI hash・計測境界を事前定義する。

原本証跡の保管と公開用派生資料は分けます。秘密値・認証ファイル内容・未加工traceを公開せず、原本との照合に必要なhashや編集範囲を残します。クラウドの保存・破棄仕様は未確認なのでworkspaceを唯一の証跡保管先にしません。環境移設でhome依存のattempt台帳が失われると重複実行を防げないため、Issue #15と過去attemptを照合する必要があります。

独立レビューには作者と別のfresh sessionへhead固定の実ファイル・差分・Issue/PR原文・基準文書・必要な証跡を渡し、runtime/model/session IDと根拠リンクを記録します。共有contextの複数Agentによる検討、CI成功、権限表示はそれぞれ独立判断や実操作成功の代替ではありません。

## 台帳の更新方法

各値に採取日時、環境ID、実行階層、コマンドまたは設定ソース、証跡リンクを付けます。Git read / pushとAPI read / write、設定値 / 実測値 / 承認範囲を別々に記録します。設定変更や実験・レビュー開始前に必要な項目を再照合し、今回のチェックポイントを恒久的な保証として扱いません。新しい必須チェックリストを増やさず、既存Issueと手順に必要な情報を集約します。
