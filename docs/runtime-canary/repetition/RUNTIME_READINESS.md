# 実モデル比較のruntime readiness（2026-11-04）

開始main `f9a9b68509d531794188443ba0311a1d22985081`。open PRは#288のみ。#298/#299/#300はmerged。Macの並行作業があるため、push・merge直前にもremoteを確認する。今回のモデル呼出しは0。過去の再生6件やVerifier1件を新しいモデル試行へ加算しない。

## 実測

| 候補 | 今回確認できたこと | 未確認・判定 |
|---|---|---|
| このCloudのCodex CLI | 0.159.2。`exec --help`に`--json`、`--model`、sandbox、ephemeralの引数あり | model/effort/usage実データ、課金経路、認証、隔離未確認。PATH alias作成にread-only警告。model起動は試していない |
| このCloudのClaude Code | `command -v claude`で見つからない | 利用不可。新規インストール・認証設定なし |
| Cloud host collaboration | 既存handoffの実績は#300参照 | 実効model/effort/usage/課金確認・強制隔離が取得できずcontrolled比較の候補外 |
| Mac Claude Code | ユーザーが別作業で利用中との情報のみ | 当環境から実機に接続できる経路は未確認。版・課金・権限を推定しない。候補として現地確認が必要 |
| local OSS runtime | `command -v ollama`で見つからない | モデル配置・license・resource予算未確認、導入しない |

Docker client/server 28.4.0、bubblewrap executable、Python3.12.14を確認。daemon稼働はworkspace/credential/network隔離の証明ではない。実験containerは作成していない。認証ファイル・環境変数の秘密値を読んでいない。

## 既存基盤の無課金検査

`python scripts/model_role_split_pilot.py plan` は既存#220のMRS-P02-A/Bを表示した。これは別studyで、予算・Operator承認・model構成を今回へ転用しない。`PROXY_AUTH_PATH=NOT_TESTED`の解除もしない。

```sh
PYTHONDONTWRITEBYTECODE=1 python scripts/model_role_split_pilot.py run --dry-run \
  --work-root <new-scratch-directory> --timeout-s 60 \
  --max-run-tokens 1000 --budget-tokens 2000 --dry-run-tokens 100
```

2件とも `dry-run-ungraded`、tokens=100（合成値）、success=None。model/containerを起動せず、fixtureの取得・採点なし。この1000/2000はdry-run検査用の値で実モデル予算の承認ではない。`--dry-run-grade`は使用していない。#300のreplayとは異なる既存基盤の合成trace経路の確認だけで、実効modelやbillingを実証しない。

既存test_model_role_split_pilot.py初回実行は21テスト成功後に `test_relay_flow` が失敗（paced read 0.9秒、必要>1秒）。未実行だったrelay_eagain/stalled_reader/teardownは別途実行して成功。全suite初回成功とは記録しない。独立担当が同じ失敗を再現。server完了時のdone.set後はdone.wait(0.01)が即時returnし、pacingが消えていた。time.sleep(0.01)へ置換して閾値・assertion・productionを保持。修正後は該当テストと全25テストが成功。初回失敗は保持する。

## 再開に必要な最小の入力

[実行計画](LIVE_RUNTIME_PLAN.md)に沿い、実際に利用する既存端末の担当者から、CLI版・OS/arch、追加従量課金なしの経路と利用枠、既存権限で可能な隔離方式、取得できるmodel/effort/usage項目の確認結果を受け取る。秘密値や認証ファイルを共有する必要はない。

認証変更・有料probe・新しいprivateデータ送信が必要なら開始前に止める。既存subscriptionも無制限・無料とは推測しない。今回の公開fixtureを使う新しいstudyの実行予算・Operator・完全なmodel ID・effort・block条件が確定するまで、live起動コマンドを実行しない。人間注意時間は参加者の計時がなければnull、provider原価換算と追加請求額は別にする。
