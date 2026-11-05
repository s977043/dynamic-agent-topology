# Codex Cloudで進める検証

2026-11-02 UTCの作業記録と次の検証順序。非規範的なadapterメモであり、実験の事前登録、Runtimeの権限設定、規則変更、比較結果ではありません。

## 今回の対象と完了条件

PCでの複数モデル比較と分け、Codex Cloudで可能な既存offline検証を実行し、通常の別セッションへの委託とレビューの記録を残します。通常作業を通して得た観測であり、単一Agentと複数Agentのpaired実験ではありません。

- main: `5c36ed7040a78bd4fe3d3d75935300b43dc706c6`。
- 合成oracleの候補: [PR #288](https://github.com/s977043/dynamic-agent-topology/pull/288) head `bd3ca240db1f7374a97c4ef380909d8e756baed8`。未mergeの候補をmainとは別のworktreeで検証します。
- Python 3.12で必要な既存テストを実行し、正常・異常・境界の意味を照合する。回数合わせのテスト反復はしない。
- 文書作成と別セッションレビューを分け、5観点で検証・レビュー・必要修正・再確認する。最新headのCIと通常PR条件を満たす場合だけ本メモを統合する。

正本は[実験原則](../../docs/EXPERIMENTS.md)、[METRICS](../../docs/METRICS.md)、[Harness](../../docs/AGENT_HARNESS.md)、[観察記録手順](RUN_OBSERVATION.md)。CLI用の[capabilities.yaml](capabilities.yaml)の宣言を、このCloudホストの実効能力の証明として使いません。

## 検討する構成

| 構成 | Cloudでの使い方 | メリット | 限界・デメリット |
|---|---|---|---|
| Codex 1セッション | 小さい変更の作成・機械テスト。通常PRの独立レビューは別に依頼 | 引継ぎが少なく、最小の構成を保ちやすい | 自己点検だけでは独立レビューを満たさない |
| Codex作成担当＋別セッションの検証担当 | 対象SHA・原本・コマンドを渡し、結果と指摘を回収 | 作成と検証を分担し、Python結果を照合できる | 引継ぎ負担とモデル処理が増える。誤りの相関は未測定 |
| 上記＋独立レビュー担当 | 実装担当とレビュー担当の編集範囲を分ける | 通常PRの別セッションレビューを実施できる | 別モデル要件の代替にはならない。権限隔離は別問題 |

今回の作業ではモデル指定を上書きせず、offline検証担当と文書レビュー担当を別のサブエージェントに委託しました。実効model/effortの同一性を独立に確認していないため、「同一モデルに固定した比較」とは称しません。別セッションへの依頼は作業上の分担で、contextの完全分離・モデルの多様性を保証しません。

## 実行結果

以下は今回のCloud executorで実行した結果。Python **3.12.14**、全コマンドに`PYTHONDONTWRITEBYTECODE=1`を付け、各1回実行しました。

| 対象 | 固定SHA | コマンド（worktree root） | 結果 |
|---|---|---|---|
| 合成oracle | `bd3ca240`（候補） | `python3.12 scripts/test_subagent_folding_oracle.py` | 34 tests / OK、exit0 |
| paired集計の正常・異常・境界 | `5c36ed70` | `python3.12 scripts/test_compare_paired_blocks.py` | tests passed、exit0 |
| paired例データ | `5c36ed70` | `python3.12 scripts/compare_paired_blocks.py --baseline T0 --candidate T1 examples/experiment-run/*-evaluation.yaml` | PAIRED、1 block、exit0 |
| RunObservation検証器 | `5c36ed70` | `python3.12 scripts/test_validate_run_observation.py` | 正例10・負例23、exit0 |
| 観察CLI | `5c36ed70` | `python3.12 scripts/test_run_observation.py` | tests passed、exit0 |
| EXP-001履歴 | `5c36ed70` | `python3.12 scripts/audit_exp001_completed_snapshot.py` | 33 blobs intact、exit0 |

paired例のtoken比1.25は既存の合成データの再計算であり、今回のCodex構成の実測比ではありません。回帰では誤pair・重複/欠測・model/runtime/effort不一致・0分母・不正入力を、観察系ではunknownと0、YAML重複キー、不正UTF-8、保存path境界を検査します。oracleでは系列欠落・順序逆転・別order/run・失敗tool・retry・不正型・完全性不明を区別します。

検証担当は固定版テストとログをrepo外へ保存し、文書作成担当が実コマンド・exit・出力を照合しました。検証worktreeのtracked変更はなく、結果報告後にcleanを確認。別担当の文書レビューをこの後に実施します。これは機械検証と通常の分担運用の記録で、独立したモデル能力評価ではありません。

## 確認できることと未確認のこと

| 項目 | 今回の扱い |
|---|---|
| Pythonの正常・異常・境界処理 | 固定SHAのテストと出力で確認できる |
| paired集計の整合性 | 既存fixture・例データを使用。新しい実測値ではない |
| Codex別セッションへの委託と回収 | 通常の作業委託で観測できる。比較効果や成功率の推定ではない |
| worktreeの分離 | Gitの作業差分を分ける運用。全担当は共通filesystemへアクセス可能で、sandbox隔離ではない |
| read-onlyの依頼 | 担当に編集しないよう依頼する運用。権限の強制的な拒否を実測したことにはならない |
| モデル・費用 | 通常のサブエージェント委託はモデル処理を伴う。token/費用は未取得。費用ゼロ・契約枠内保証・速度向上は主張しない |
| 追加の実験起動 | この作業では実験用Codex/Claude CLI・モデルAPIを追加起動しない。通常作業の委託とは区別する |
| モデル比較・PC再現 | 今回は対象外。PC環境と各実効model/effort、権限、費用境界を確認して別に計画する |
| 人のAttention | 人の実測・回答採点は行わない。#290の教材準備やCIで代替しない |
| #288の採用 | 候補headのPASSはmain採用ではない。CIstep追加を含む規則変更PRの別モデルレビュー証跡・Human merge条件を維持する |

このCloudのネットワークは確認時点でrestricted/enforced、VPN未構成。設定済みsecret/outbound identityは空でした。これはモデル実行権限や課金境界の認定ではありません。secretを取得して検証範囲を広げず、取得不能な実行時情報はunknownのまま扱います。

## 次の検証順序

1. 今回の固定版offline結果を再利用し、変更が入った箇所だけ再検証する。合成oracleは開発用であり、未見のモデル品質評価セットへ流用しない。
2. Cloudで通常の開発作業を行う際に、既存[RunObservation手順](RUN_OBSERVATION.md)で委託・レビュー・欠測を記録する。原記録はrepo外に置き、公開転記は設計の仮名化・validator再実行・Human差分確認に従う。今回のテスト結果を実Runとして捏造しない。
3. 単一セッションと委託ありの優劣を調べる場合は、未見task・独立oracle・Runtime/実効model/effort・tools/権限・順序・freshness・全leg費用・欠測/停止条件を結果を見る前に固定する。今回の通常作業から因果効果を推定しない。追加課金やOperator要件が未確定なら起動しない。
4. 複数モデル・実効権限の拒否・PC固有のsandbox/認証の比較はPC側の条件成立後に進める。Cloudの別セッションレビューで既存の別モデル要件を外さない。

完了は「このCloudで確認できる機械検証と分担運用を記録したこと」。品質・総時間・費用で最良の構成を決めること、#248/#220の実験を完了すること、Human承認をなくすことではありません。

## Dockerを使う開発検証

2026-11-03には、モデルを起動しないPythonコンテナで、設定値と実際の拒否を照合しました。[Docker検証と運用メモ](DOCKER_VERIFICATION.md)に、16項目の結果、起動設定例、再確認手順と未検証境界を記録しています。これは上記の2026-11-02のoffline結果とは別の確認です。
