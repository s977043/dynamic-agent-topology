# 残タスクの実行計画

> **As-of checkpoint: 2026-11-08 UTC（GitHub read-only再確認）。** これは実行許可・採用・Run acceptance・Merge承認そのものではありません。main / PR head / 必須CI / 独立レビュー / Human判断を作業ごとに再取得します。古いcheckpointはGit履歴を参照してください。

## 確認済みの到達点

- Repository: [s977043/dynamic-agent-topology](https://github.com/s977043/dynamic-agent-topology)。基準mainは `0db01af6896a7ac3a11e62cd75eeb8e56c9f3f36`（#307まで統合）。取得時点でOpen Issue **12**（#31/#88/#93/#159/#220/#223/#244/#248/#268/#287/#295/#302）、Open PR **1**（Draft #288、本計画PRの作成前）。件数はcheckpointであり、本計画PRや他者の更新で変動します。
- **v0.5.0公開済み**（2026-11-02T01:53:57Z、#283）。v0.4.0（#264）・v0.4.1（#267）も公開済み。公開タグを移動しません。
- EXP-001 [#15](https://github.com/s977043/dynamic-agent-topology/issues/15)はcompleted/closed、Pilot限定 **Keep T0**。[Freeze](../experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md) completed revision3、33 original blobsを保持。過去Runの再実行・再prepare・Frozen変更の許可ではありません。
- 2026-10-26以降に通常PR・release PRとして#256〜#307の43件がmerge済み。主なもの:
  - #220予備キット: #257 network none、#261 teardown検出、#262 CI配線、#263 事後改善。
  - #244: #258 事前登録第2版確定、#266 較正テストのCI配線、#304 order 6〜44の症状説明、#305 スクリーニング前除外の補遺、#307 スクリーニングモード（規則変更PRとしてHuman merge）。
  - #268 vNext: #269 RFC・P0 Baseline、#271 P0 Journey A〜D、#273〜#275、#278/#279 paired block集計CLI（#276）、#280 R0の尺度（#277）、#281。
  - #287 Human Attention: #289 paired比較の修正、#290 1ペア計測パケット（計測は未実施）。
  - #291/#292 Codex Cloud検証・Docker実測手順、#293 手動dispatchの1組canary、#300 canary反復採点、#301 live比較のruntime条件、#296/#298 Auctopus研究ノート（#295、未採用）、#297/#299/#303 review packageの互換性・テスト、#306 タスク単位の選定と観測の接続。
- 研究ノートは未採用候補のままで、source台帳の`adopted: []`を維持しています。canaryや合成fixtureのPASSは構成の効果証拠ではありません。

## #244 スクリーニング起動前の状態

証拠（Agentの記録）:

- [実containerのリハーサル](https://github.com/s977043/dynamic-agent-topology/issues/244#issuecomment-6712281649)（main `0db01af`）: S1〜S10の停止・再開経路が期待と一致。dry-run（`screen-plan`、`screen --dry-run`）はexit 0。**本物のCodexは起動していない**（偽の`bin/codex`とダミーauth）。`codex --version`・auth probeはSIMULATEDで、本物のCodexのtrace形式とkillへの反応は未検証。1GBを超えるtraceは未測定。
- キットの不具合候補4件: `control-deviation`で`screen-summarize`がrc=2で止まる、`--rm`由来の`docker stop`のWARNING誤報、停止経路で`phase`が入らない、回収の30秒上限がhost側の展開に効かない（推定）。修正はブランチ `fix/244-screening-rehearsal-findings` で作業中（取得時点でPR・remoteブランチなし）。

Operatorの判断（[判断材料](https://github.com/s977043/dynamic-agent-topology/issues/244#issuecomment-6712373806)）:

| # | 決めること | 状態 |
|---|---|---|
| D1 | #307の実装上の規則5件 | 未回答 |
| D2 | 第2版§5.1bの停止条件 | [案A（実効上限の確認）と回答](https://github.com/s977043/dynamic-agent-topology/issues/244#issuecomment-6712396184)。仕組み・上限値・4M/10M/50Mとの関係・確認方法と日時の記録待ちで、**§5.1bは未解消** |
| D3 | Codex 0.160.1 Linuxバイナリの採用 | 未回答（Agentが計算したSHA-256は過去の記録と一致。公式hashとの照合は未実施） |
| D4 | gpt-6.1-sol / highの提供 | 未回答・未確認 |

D1〜D4が揃い、キット修正がmergeされるまでスクリーニングを起動しません。起動はOperatorが行い、最初のRunでSIMULATEDの項目と実際のtraceの大きさを確かめます。

## 次の実行順序

| 順位 | 対象 | 次の具体的な作業・成果物 | 完了・停止条件 |
|---|---|---|---|
| 完了 | #257 / #258 / #307 ほか | 上記到達点のとおり | 再計上しない |
| P0 | 本計画の更新PR | Open Issue/PRの原本照合、別セッションの独立レビュー、最新head CI | 通常文書PRの必須指摘0・必須CI成功でmerge |
| P0 | #244 キット修正 | `fix/244-screening-rehearsal-findings` のPR化、独立レビュー | 規則・必須CIのテストを変えるなら規則変更PRとしてHuman merge |
| P0 | #244 Operator判断 | D1・D3・D4の回答、D2案Aの仕組みの記録 | 揃うまでスクリーニングを起動しない。Agentは判断を代行しない |
| P1 | #288 / #248 | Draftの合成oracleと最小検証計画 | Human merge待ち。合成oracleのPASSを効果証拠にしない |
| P1 | #302 | Mac Claude CodeでのT0/T1実モデル反復の実行条件 | Operator判断待ち。model起動はOperator |
| P1 | #223 / #268 / #287 / #295 | 未決事項・計測・研究ノートの次段階 | 判定規則の変更と公開を混同しない。未計測を計測済みにしない |
| P2 | #31 / #159 / #88 / #93 / #220 | 管理者確認・事前登録・実測条件の整理 | 設定を推測でPASSにしない。前提未達はUNKNOWN/DEFER |

## Open Issueの残タスクと再開条件

| Issue | 現在の証拠 | 残る判断・実行条件 |
|---|---|---|
| [#31](https://github.com/s977043/dynamic-agent-topology/issues/31) | v0.5.0まで公開済み | security関連6設定は未確認。closeはHuman判断 |
| [#88](https://github.com/s977043/dynamic-agent-topology/issues/88) | 再現可能なbaseline failureが未取得。#244の進展を参照 | EXP-001全成功を回復効果の母集団にしない |
| [#93](https://github.com/s977043/dynamic-agent-topology/issues/93) | #82/#211を候補armとして吸収済み | 母集団・予算・事前登録が必要。Human同意はEXP-002→EXP-003の順序だけ |
| [#159](https://github.com/s977043/dynamic-agent-topology/issues/159) | 規則変更PRの記録先。最新は#307 | Actions PR作成許可の管理者確認。規則・Guard変更のmergeはHuman |
| [#220](https://github.com/s977043/dynamic-agent-topology/issues/220) | 予備キット#254と修正#257/#261/#263。資格情報は案D（Operator承認） | 実効permission・認証・課金境界は未実測。FAIL/NOT_TESTEDが残る間model起動なし |
| [#223](https://github.com/s977043/dynamic-agent-topology/issues/223) | H1支持23件/7project、H2支持23/23（Agent報告） | 原store・ログの独立監査は未実施。公開転記は設計§6、release/tagはHuman |
| [#244](https://github.com/s977043/dynamic-agent-topology/issues/244) | 上記「#244 スクリーニング起動前の状態」 | D1〜D4とキット修正。評価予算は選定後の見積もりで再承認 |
| [#248](https://github.com/s977043/dynamic-agent-topology/issues/248) | Draft #288（合成oracle 34テスト） | 事前登録・独立oracle・費用・Operator条件を満たしてから実行 |
| [#268](https://github.com/s977043/dynamic-agent-topology/issues/268) | RFC・P0 Journey・#276/#277の対応がmerge済み | 分岐順の変更（breaking）は仮説H-A2の検証後 |
| [#287](https://github.com/s977043/dynamic-agent-topology/issues/287) | 1ペア計測パケット（#290）を用意 | 秒数・回答・品質判定は未取得 |
| [#295](https://github.com/s977043/dynamic-agent-topology/issues/295) | 研究ノート（#296/#298）とschema-only負の対照 | C1〜C8のOracle・T0/T1比較・有料モデル実行は未実施 |
| [#302](https://github.com/s977043/dynamic-agent-topology/issues/302) | relayテストはMacで20/20成功（初回の失敗は再現せず、原因未特定） | 実モデル反復の起動条件はOperator判断 |

## 変更ごとの3ループ

1. **検証→レビュー→修正→再レビュー:** 原Issue・一次資料・full diffを照合し、Source claim / DAT Evidence / Judgment、未知、最小変更因子を確認する。
2. **検証→レビュー→修正→再レビュー:** 最新mainへの通常同期、共有台帳の保全、正負検証、33 original blobs、Human-owned境界を確認する。
3. **検証→レビュー→修正→再レビュー:** 最終head・本文・CI・未解決指摘を一致させ、別セッション独立Reviewerが判断する。変更があれば影響を再検証する。

回数自体や作者の自己レビューを独立承認にしません。差分を作成したセッションは自己承認せず、別セッションへ原本・exact head・関連Issue・検証ログを渡します。[Harness](AGENT_HARNESS.md)に従い、通常PRのみ必要CI成功・独立レビュー必須指摘0・Ruleset順守後にmerge。AGENTS/CLAUDE/.claude/.codex/Harness規則等の変更、Freeze、release/tag、force push、削除はHuman専権を維持します。

## 終了・保留

可能な差分・検証・レビュー・通常PR統合を完了し、残る条件は上表のOwnerと再開条件に結び付けます。Issue件数0を目的に未実測研究を完了化せず、効果なし・条件不成立はINCONCLUSIVE/DEFER/REJECTを認めます。モデル利用・追加費用・権限・Human判断をAIが自己生成しません。
