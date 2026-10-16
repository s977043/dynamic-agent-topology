# 残タスクの実行計画

> Current checkpoint: 2026-10-16 JST（#195統合後）。これは実行時点のスナップショット。**各Issue・PR・main HEAD・CI・Human承認記録を作業直前に再取得する**。

## 目的と確認範囲

対象は s977043/dynamic-agent-topology。River Review / PlanGate自体のIssue棚卸しは本計画の対象外。
GitHub APIでopen issues/pulls、main、最新Actions、#186/#193/#194/#196/#197のexact-head check-runs、Releasesを取得し、origin/mainの既存計画と照合。Issueコメント全履歴・管理者設定・外部端末は今回未再監査。過去レビュー記録と今回のCI確認を分ける。

- main: `5bbccc6bc5476137ef4f0ecca2daf7d09b27e99a`（#195統合済み）。mainのspec-lint/codeql/Scorecard workflowはSUCCESS。
- Open Issue 10件（PRを除外）、Open PR 5件。GitHub Releases 0件。
- [EXP-001 #15](https://github.com/s977043/dynamic-agent-topology/issues/15): closed（completed）、18/18 empirical Runs ACCEPT、9/9 paired blocks、[PILOT COMPLETE — Keep T0](../experiments/EXP-001-t0-vs-t1/DECISION.md)。[Freeze](../experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md) completed revision 3（#183統合済み）。旧33 blobを保全し、過去Runを再実行・改変しない。観測はCodex / gpt-6.1-sol / high・3 ScenarioのPilot限定。両側成功率100%、T1平均Token量はT0の2.206倍であり、難しいTaskや他Runtimeへ一般化しない。
- 未公開版0.3.0は候補。公開予定日2026-10-16は公開完了の証拠ではない。

## PR棚卸し

| PR | exact head | CI | 次の行動・境界 |
|---|---|---|---|
| #186 Release Draft | 6a884787bff98601ef3b0f37745bc3b64587612c | validate/Analyze Python/CodeQL SUCCESS | 本文のCI待ち記載を同期。既実施の固定head独立レビュー記録を反映。Humanが最終版数・実公開日・merge/tag/Releaseを判断・実行 |
| #193 Claude設定修正 | 2ee6f3fc18618fe3ed34758df709b2c2b20a312e | 同3チェックSUCCESS | Python3.12検証/独立レビュー記録を本文と照合。Claude実環境の権限拒否・警告消失は未実測として残す。AGENTSのHuman merge対象 |
| #194 post-EXP001設計Draft | 915c47084df8c6db46347bf77762736994e4d0cb | 同3チェックSUCCESS | 独立レビュー後修正済みの記載と先頭の未レビュー表現を同期。#186公開までmerge hold。公開後にbase差分・CI・再レビューし通常merge条件を判定 |
| #196 学習L-009 | `78867dddc1b60cad764cd4c516496624335ea9bd` | 同3チェックSUCCESS | 独立3パス指摘0。candidate学習記録の事実追記で通常PR対象。統合後はRelease候補を再固定 |
| #197 review request executor matching | `6b311cb95d1acb678c1109b6ca9c34aa9ce4983b` | 同3チェックSUCCESS | 独立3パス指摘0。既存protocol観点の具体化で通常PR対象。統合後はRelease候補を再固定 |

[Open PR一覧](https://github.com/s977043/dynamic-agent-topology/pulls)

## 実行順と成果物

### P0 — 状態同期（Cloudで着手可能）

1. 作業直前にmain/head/Issue本文を再取得し競合を検知する。
2. docs/CURRENT_EXECUTION_PLAN.mdの古いmain、13Issue、#188進行中、#21/#42継続中を現行状態へ更新する案を作成。
3. #31の古いcandidate3b760ff/公開予定日15日を、現在のcandidate5bbccc6/head6a884787/予定日16日へ同期。過去記録は履歴として保持。
4. #59/#82/#162/#166はFreeze ACTIVE/#183未mergeという先頭状態が古い。一次ソース#183/Issue15/freeze.yamlを再取得後、completedと個別未達Gateを分けて追補。
5. #63の既達成チェックと未実証を整理。合成corpus通過を一般効果・研究完了へ読み替えない。
6. PR186/194のCI待ち・レビュー待ちをexact-headの証拠に合わせる。

成果物: 状態同期の小さなdocs PR、Issue/PR追補、証拠リンク一覧。
完了条件: 全10Issueと5PRが一覧に存在し、閉じた#21/#42/#57を再実行対象にしない。Freeze/版数/日付/headに矛盾がない。通常PRは独立レビュー・必須CI後のみ統合。
依存: ユーザーの通常PR統合指示に従い、#196/#197と計画同期PRは独立レビュー・CI後に統合する。main更新後、#186のcandidate/CHANGELOG/CI/独立レビューを一度に更新する。旧headの判断を新headへ流用しない。#194の明示的な公開待ちholdは維持する。

### P1 — Releaseの具体的な完了手順（#31/#186、Human所有）

1. Agentが現candidateと差分、固定headレビュー、CI証拠、未確認設定を一つの公開チェックリストへ整理。
2. Humanが最終版数と実公開日を確定。日付変更・内容変更時はmetadataとレビュー/CIを更新。
3. Humanが#186をmergeし、生成されたrelease commitのSHAを記録。
4. そのSHAのvalidate/Analyze Python/Scorecardを確認。失敗時は公開を止めて通常修正PRへ。
5. Humanが同じcommitを指すimmutable tagとGitHub Releaseを作成。タグを移動しない。
6. Agentがtag/Release/metadata/README日英/Quickstartを照合し、公開後文書の通常PRを作成。

完了条件: 実release SHA、必須CI、immutable tag、Release URL、metadataの整合。公開判断待ちだけを理由に#31のsecurity確認まで完了扱いしない。

### P2 — Release後の既存PR処理

- #196 / #197と計画同期はP0で通常merge条件を判定し、Release候補の再固定へ反映する。CI成功だけで独立レビュー済みとしない。
- #193: Human merge。直前のmainとの差分/CIを再確認し、Claude環境が利用可能なら禁止編集のnegative caseと起動警告を検証。CloudにClaude CLIがなければ未実測を残す。
- #194: 公開実績を確認してhold解除を判断。fresh contextの独立Reviewerが最新headを確認し、必須CI・未解決指摘0なら通常merge可。設計mergeは実験起動許可ではない。

### P3 — Harness自動化の運用受理（#159、管理者条件とCloud作業）

1. 管理者がActionsのPR作成許可と上位policyの現在値を確認。403の原因は未確定のまま扱う。
2. 権限変更の要否・許可範囲を判断。異なる認証で迂回しない。
3. 正規GITHUB_TOKENと正当な新規入力でObserve/Promoteを実測。生成済みbranchを削除・書換えしない。
4. draft=true、actor、base/head、生成差分を照合。Observe/Promoteの同入力no-opをそれぞれ実測。
5. tokenイベントのCI制約を確認し、正規イベントでexact-head CIを起動・独立レビュー。

完了条件: 新規自動Draft成功、双方no-op、CI、独立判断。手動診断PRや既存Promote no-opだけでは受理しない。

### P4 — 研究の開始条件を整える（モデル起動は別判定）

| Issue | 現在の残条件 | 最小作業 / Evidence | 終了判断 |
|---|---|---|---|
| #63 知識整合性 | #195で23行合成評価済み。自然発生incorrect母数0、OCR/人時/一般効果未測定 | 実際に発生した失敗事例と独立oracleを登録。代表性・誤拒否・人時の追加計画を事前レビュー | 限定報告維持 / 追加評価 / DEFER。常用gateへ直結しない |
| #93 compound | #194設計あり、混合母集団・閾値・モデル・予算未確定 | task候補revision/AC/観測欠陥/副作用隔離を登録。U2〜U8を確定しT0/F pairedとshadowを分離 | 実行可否判断。オンラインG効果は独立armなしで主張しない |
| #88 recovery | eligibleな再現可能baseline失敗0件 | 実失敗原文・runtime/model/effort・AC・verificationを1件登録。小さいPrompt/Harness修正で解消する例を分離 | 候補がなければDEFER。EXP-001成功18件を失敗層に転用しない |
| #150 hunk | 10fixture試行済み、実CLI/model利益は未実証 | T0b owner-only patchに対する必要性・代表case・最小有用効果をレビュー | 比較が必要な時のみ隔離CLI評価。未必要ならDEFER |
| #82 adversary | 既存Reviewerが見落とす再現欠陥と追加効用が未確保 | 欠陥原文と小さい既存review介入を比較する案 | 新Roleを先に追加しない |
| #59 Mods | Claude runtimeの実効拒否/監査のgap未確定 | native設定baseline、負側case、trust modelを設計 | Claude接続後に実効検証。Plugin登録をenforcement証明としない |
| #162 model移行 | intakeのみ、paired実測/owner判断なし | 匿名化正負fixture5件を開始案とし品質下限、修正人時、移行費を定義 | owner/モデル/予算/独立評価が揃ってからpaired実行 |
| #166 population | intakeのみ、population閾値未実証 | secret-free隔離設計、Worker1/2/4、協調有無・予算固定を分離 | 隔離と予算の事前審査後のみpilot。自己増殖・外部資源取得は行わない |
| #31 repository | security実設定未確認、Release未公開 | 管理権限で6項目とActions設定を確認し、read-only baseline再監査 | 未知項目をPASSにしない。外部貢献後再監査はイベント依存 |
| #159 Harness | 自動Draft経路未受理 | P3の正規運用証拠 | 全受入条件までopen |

優先案: 状態同期・通常PR統合 → Release候補再固定・公開 → 残る既存PR → #159管理者条件解消後の運用検証。待機中は#63/#93/#88の候補整理を並行。その他研究は必要性の比較を先に行い、全研究を一度に実行しない。

### P5 — Plugin・環境の適用

River Review1.129.0/PlanGate8.24.0は当CloudのCLIでinstalled/enabled。River Reviewは#186文書差分で使用済み。PlanGate doctorは登録YESだが7FAIL、workflow/rules/hook未統合。新セッションの自動選択・Mac/ThinkPad/Claude Cloudは未検証。

- 実行計画: プラグインread-only利用 → 新セッション検出確認 → 既存DAT運用とのgap比較 → 必要なら専用統合PR。
- PlanGate承認記録を代理発行しない。settings/AGENTS等はHuman merge境界を守る。
- 実環境のOS/arch/runtime/version/network/permission/model/計測/データ搬送を各端末で採取。Cloudのx86と既存EXP環境の同一性を推定しない。

## 各作業の3ループ（実施計画、未実施を完了扱いしない）

1. 検討→計画レビュー→開始条件/負側case修正→計画再レビュー。
2. 対応→検証→固定head独立レビュー→指摘修正。採用しない指摘にも根拠を残す。
3. 修正後検証→別セッション最終レビュー→exact-head CI/未解決0/承認範囲の照合→通常mergeまたはBLOCKED記録。

最終レビューに渡す材料: fresh main/head、diff、plan、実行command/raw出力、失敗・除外・未測定、対象AC。作成者の要約のみで承認しない。head変更時は判断対象を更新する。

## 本計画のセルフレビューと更新規則

- APIのissues一覧はPRを含むため除外して10件と数えた。
- CI成功とHuman許可を分離。Releases0から未公開と判断し、tag存在までは今回断定しない。
- 古いFreeze待ちを現在のblocked理由に使わない。Freeze完了も実験起動の包括許可にしない。
- PlanGate doctor7FAILをPlugin導入失敗・DAT欠陥7件と数えない。
- 全残タスク0は外部環境/管理者/予算に依存する。条件未充足時はowner・証拠・解除条件を記録し保留する。研究は反証/DEFERも正当な終了候補だが、独立判断前に勝手にcloseしない。
- 各PR/管理設定/モデル条件変更の直後に本計画を再評価する。本計画の同期は追加実験・PR mergeの包括許可ではない。

## 完了・終了済み項目と過去状態

- #21 / #42 はclosed（not planned）。新しい根拠と明示的な再計画なしに研究対象へ戻さない。
- #57 はclosed（completed）。#187と選定した#188は統合済み、#189は重複としてclosed/unmerged。監査の完了をhistorical acceptanceの変更や旧18 Runの再実行許可にしない。
- #190 / #191 は現在のopen PR一覧ではない。古い13 Issue、16/18 Run、safe-divide r03を次に実行、#165待ち、DECISION NOT RUN、Freeze ACTIVEは過去状態。履歴は[#15](https://github.com/s977043/dynamic-agent-topology/issues/15)と過去commitを参照する。
- 通常PRのmergeには必須CI・作成者と別セッションの独立レビュー・未解決必須指摘0と現行HOTL条件が必要。[AGENT_HARNESS.md](AGENT_HARNESS.md)に従い、guidance変更・Freeze改訂・release/tag・force push・削除などのHuman-owned境界を保持する。
- #159の手動診断PRやPromote no-op成功は正規自動Draft成功ではない。[Live operations](HARNESS_LIVE_OPERATIONS.md)を参照する。端末情報の過去値は[Environment usage](ENVIRONMENT_USAGE.md)にあり、承認済みRun条件へ転用しない。
