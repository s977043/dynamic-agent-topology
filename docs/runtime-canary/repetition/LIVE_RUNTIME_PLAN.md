# 実モデル反復のランタイム準備案

2026-11-04、基準main `f9a9b68509d531794188443ba0311a1d22985081`。状態は **PREPARATION / NO-GO for live**。本書は候補と未確定条件を整理する準備案で、実験事前登録の成立・model起動・新規課金の承認ではない。#300の6件は保存成果物の再採点、live handoffは保存candidateへのVerifier1件であり、この計画の実モデル試行は0件。

## 候補と選択

| 候補 | 確認できたこと | live開始に足りないもの |
|---|---|---|
| 現在のhost collaboration | 通常subagentの起動・返答は#293/#300で観測 | 実効model/effort・provider usage・platform session IDの取得、強制隔離の根拠がない。controlled比較には選ばない |
| 現在のCloud Codex CLI | 親のローカル確認では0.159.2、`exec --help`にmodel/JSON/sandbox指定あり。Docker client/server 28.4.0、bwrapあり、claude/ollama/agyなし。PATH alias作成にread-only警告 | 認証・追加課金なしの経路・実traceの取得可否・正常な初期化・隔離は未確認。helpの存在は実行成功ではない |
| 既存MacのClaude Code | ユーザーが使用中という会話上の情報 | 本タスクから端末へ接続できること、版、実効model/effort、使用量、追加課金の有無、実験workspace隔離は未確認 |
| 既存の隔離キット | #244のCodex較正、#220のClaude役割比較に計測・隔離チェックの実装がある | 各キットは別task/model/budgetに固定。今回へそのまま流用できず、#220 proxy認証経路はNOT_TESTED。既存承認は転用しない |

**第一候補は既存Mac上のClaude Code**とする。ただし「利用中」だけで追加課金ゼロや隔離を推定しない。まずOperatorが同じ端末で下記の非model確認を行い、取得可能な非秘密の結果だけを渡す。満たせなければCloudを無理に動かさず候補を再選定する。新規CLI導入・設定変更・認証コピー・proxy導入は今回の前提にしない。

## modelを起動しない確認

既存DAT checkoutで実行する。これは実行例であり、Macで実施済みではない。失敗・未インストールはそのまま記録し、認証や権限を変更して通さない。

```sh
command -v claude
claude --version
claude --help
command -v codex
codex --version
codex exec --help
python3 --version
git rev-parse HEAD
git status --short --branch
```

CLI helpの出力から、当該版にmodel/effort/stream-jsonまたはJSON出力、tool制限・sandbox・セッションID取得手段があるかを確認する。設定値だけで実効値を確定しない。authファイル、環境変数一覧、ログ全文、credentials、個人ホーム全体を収集・公開しない。認証状態の確認を理由にmodelへpromptを送らない。

既存の非model入口は次のとおり。Python3.12と既存依存が揃っている場合だけ実行し、依存追加は別判断にする。

```sh
PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/model_role_split_pilot.py plan
PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/hard_task_calibrate.py plan
PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/test_model_role_split_pilot.py
PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/test_hard_task_calibrate.py
```

`plan`と単体テストは既存キットの構成・synthetic契約を確認するだけで、今回のlive条件がPASSになったとは扱わない。`run`、`--dry-run-grade`、既存の認証probeはこの一覧には含めない（それぞれ起動・ネットワーク取得・認証アクセスに別前提がある）。

隔離方式は[Codex較正手順](../../hard-task/CALIBRATION_RUNBOOK.md)と[Claude pilot手順](../../model-role-split/PILOT_RUNBOOK.md)の、mount完全一致・credential分離・正常操作の対照と禁止操作の拒否・trace回収の確認を参考にする。これらのチェックを今回のruntimeで再現した実測がない限り隔離はUNKNOWN。既存kitの規則や`PROXY_AUTH_PATH`を緩めない。

## 今回の非model確認の途中記録

親担当の観測: `model_role_split_pilot.py plan` は成功。`run --dry-run` は新規scratchへ2件の `dry-run-ungraded` を作り、両方 `modelLaunched: false`。渡した60秒・1,000 tokens/Run・総2,000 tokens・模擬100 tokensは検査パラメータで、今回のlive予算承認ではない。#220の既存ID/modelを用いるsynthetic検査であり、本計画のモデル試行0件を変えない。

`test_model_role_split_pilot.py` は先行21テストのOK後、`test_relay_flow` のpaced readが0.9秒で閾値1.0秒以下となりexit1。後続のrelay EAGAIN・stalled reader・teardownは独立実行で成功したが、最初のsuite失敗を打ち消さない。独立担当が待機イベントの完了でpacingが消えるテスト不具合を再現し、完了イベントから独立したsleepへ修正した。閾値・assertion・production runtimeは不変。修正後は該当テストと全25テストが成功した。初回失敗はこの履歴として保持する。live前提は課金・実効metadata・隔離の未確認により未完了。

## 開始前に固定する条件

| 項目 | 現在 | 必要な根拠 |
|---|---|---|
| Operator・実行端末・CLI版・binary hash | UNSET | 既存端末での非model出力と実行担当 |
| 追加課金なしの経路 | UNKNOWN | Operatorが既存契約・API課金経路・追加利用設定を確認した日時と結論。利用枠残量だけでは代用しない |
| model / effort | UNSET | 設定と、既存の公開可能な実行metadataでの実効値取得方法。aliasや継承値の推定は不可 |
| session ID / usage | UNSET | CLI出力またはtraceのfield、全legの終端/中断時の取得方法 |
| worker/verifier各legのtoken上限・timeout、総token上限 | UNSET | Operatorによる今回専用の上限。#220/#244の値を転用しない |
| USD上限・計算方法 | UNSET | 追加課金なし確認と使用量会計。subscription枠内でもモデル利用のUSDを0と推定しない |
| workspace・権限・隔離 | UNKNOWN | 同等のtool/ネットワーク/書込範囲、他arm・oracle・認証へのアクセス拒否と許可操作の対照 |
| input/oracle/prompts・記録方法 | 起案済み | 最終commit/hash、独立レビュー、実行前の固定記録 |

未確定項目が残る間はcontrolled liveを開始しない。追加課金または認証変更が必要なら、用途と最小変更を提示してOperator判断を待つ。秘密値をチャットへ求めない。

## 最小のpaired実行案（未実行）

問うのは「同条件の修正と独立Verifierの判定を、追跡可能な証跡付きで反復できるか」。2 blockで統計的優位を判断しない。T0を既定とする方針は変更しない。

- scenarioは公開合成task `../task.md`、各workerは `../initial.py` から開始。最終解・他arm・過去の採点結果を渡さない。
- 既存独立oracle `../evaluate.py` SHA256は `fc5a50aca33f897c54c2f0afc6500f878a8fd37f5d2ab04764551e11d1b97fd6`。採点条件は18/18成功、初期コードの負対照は6/18・exit1を固定。oracleをworker/verifierのworkspaceへ置かない。
- block `live-readiness-b01`: T0→T1、`live-readiness-b02`: T1→T0。armごとにfresh worker/session/workspace、T1のみfresh Verifierを追加。合計worker4件・Verifier2件を上限案とする。準備用model probeが必要なら、この6件とは別の許可・予算・記録が必要。
- 両workerのprompt/model/effort/権限/予算を同じにする。T1 Verifierのmodel/effortも同じ固定値。Verifierはcandidateを編集しない。今回は修正round0、retry0とし、検出・判定の付加価値を観察する。修正効果の実験ではない。
- T0の完了申告とT1のVerifier判定を、両方同じ独立oracleへ照合する。false acceptは完了/PASS申告なのに18/18未達の場合。未完了・INCONCLUSIVE・欠測は別に保持する。
- 独立Evaluatorにはopaque candidate名を渡し、採点確定後にarm対応表を開示する。公開fixtureの既知性・modelの事前学習汚染は除去できず、厳密な盲検と主張しない。対応表を見られる共有FSならその制約を明記し、隔離済みとはしない。
- 各legの開始/終了monotonic時刻、UTC、requested/effective modelとeffort、session ID、usage（入力/出力/cacheを重複加算しない定義）、終了理由、成果物hashを保存する。worker/verifierコストを別々に残し、T1合計にも含める。unknownはnullと理由。
- cache消去・既存session再開・結果を見て順序変更はしない。cache量が取れれば保存し、host負荷/時刻/順序効果を限界に残す。EvaluatorとOperatorの時間はworker latencyに混ぜない。人間active attentionは実参加者の計時がない限りnull。

[Verifierテンプレート](VERIFIER_TEMPLATE.md)の正確な依頼・返答要約・入力hash・実行IDを保存し、再現可能な検査コードとexitを添える。raw runtime traceは秘密や非公開contextを含みうるためrepo外でOperator管理とし、公開するのは秘密・個人情報・private内容・raw reasoningを除いたsummary。収集時点で非公開データを新しい外部サービスへ送らない。

## 中止・再開と採否

入力/oracle/hash drift、model/effort不一致、usage欠測、予算/timeout不明、隔離FAIL/UNKNOWN、予期しない課金経路・private送信・permission拒否、Macで同じrunが進行中なら開始しない。起動後は実行ID・部分usage・停止理由を残し、上限超過や実効条件不一致なら残りのbatchを止める。結果directoryを上書きせず、重複・不確実な起動結果を確認する前に再試行しない。採点不能・timeoutを成功や0費用に変えない。

2 block終了でも記述的結果に限定し、同点ならT0維持、欠測や統制不成立ならINCONCLUSIVEとする。既知の易しいtaskなので天井効果があり、#244の難課題比較・#248 folding・#295の品質ゲート比較を完了したとは扱わない。

再開の最小入力は、**既存Macでの非model確認結果、Operatorと追加課金なし経路の確認、今回6 leg用の上限案、実効metadata/usageの取得方法と隔離を確認できる場所**。これらを既存runtimeで確認後、未確定値を埋めて独立レビューし、固定commitの計画を成立させる。新しいランタイム実装は、既存機能で不足する具体的な証拠が出るまで追加しない。
