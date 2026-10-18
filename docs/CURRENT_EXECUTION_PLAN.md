# 残タスクの実行計画

> **Current checkpoint: 2026-10-18 JST（read-only GitHub再確認）。** この文書は意思決定・実験起動・Merge承認そのものではありません。毎回main HEAD / Open Issue / PR / exact-head checks / 独立Reviewer / Human-owned判断を再取得してください。2026-10-16以前の状態はGit履歴を参照し、現在のGateへ転用しません。

## 正本と観測値

- Repository: [s977043/dynamic-agent-topology](https://github.com/s977043/dynamic-agent-topology)
- main = `56a10001cb716c230a5020dc0dcb65b0e1f348d4`（PR [#186](https://github.com/s977043/dynamic-agent-topology/pull/186)が**merge済み**）。確認時点のOpen Issues **12**、Open PR **9**。件数はスナップショットであり、作業ごとに再照合します。
- Release commit mainのGitHub check-runs（`validate` / `Analyze Python` / `Scorecard analysis`）は**3/3 SUCCESS**。[#31](https://github.com/s977043/dynamic-agent-topology/issues/31)の2026-10-18追補にjob URLとSHAを記録。
- **0.3.0はpublication pending:** `v0.3.0` tag/Releaseはともに未存在（tag ref 404、Release 0）。`CITATION.cff`の`version: 0.3.0` / `date-released: 2026-10-16`は**公開実績と不一致**。2026-10-16の仮予定を実公開日とみなさない。現在の`CHANGELOG.md`はrelease candidate/unpublished、日英READMEは「main未Release」。**ReleaseのHuman-owned Gateは未完了**。
- [EXP-001 #15](https://github.com/s977043/dynamic-agent-topology/issues/15)はcompleted/closed、18/18 Runs・9/9 paired blocks・pilot-only **Keep T0**。[Feature Freeze](../experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md) completed revision 3、33 original blobsは保全。新たなRun・Frozen改変・Topology採用の許可を意味しません。[#57](https://github.com/s977043/dynamic-agent-topology/issues/57)はread-only provenance auditの設計・実装終了でclosed。UNKNOWNをPASSとみなさない。
- [Harness rules](AGENT_HARNESS.md): 通常PRのAgent mergeには必要な独立別セッションReview＋最新HEAD必須CI＋未解決指摘0が必要。Harness/Permission/Guard、Frozen data、release/tag、force push、削除等のHuman専権を維持。自己承認・branch横取り・Ruleset bypassは禁止。

## 優先実行ボード

| 順位 | 対象 | 現在状態 / 次の小さな仕事 | 完了と権限境界 |
| --- | --- | --- | --- |
| P0 | [#31](https://github.com/s977043/dynamic-agent-topology/issues/31), merged [#186](https://github.com/s977043/dynamic-agent-topology/pull/186) | Release commitのCIは全SUCCESS。**タグ・Releaseは未公開、CITATION日付が過去の仮値**。実公開日とmetadataをHumanが選択し、必要な修正PRと新release commitの再CIを実施 | Humanが確定したexact SHAにimmutable tag `v0.3.0` とGitHub Releaseを公開。README/CHANGELOG/CITATION一致を再監査。セキュリティ6設定の未観測は残したまま |
| P0 | [#193](https://github.com/s977043/dynamic-agent-topology/pull/193) | 不一致のWrite ask rulesを消す設定修正。既存Edit対応、CI SUCCESSの履歴。現在のmainからbehind、Human-owned Harness変更 | 作成者branchを更新 → 実効権限・負側テスト検証 → 最新HEAD CI/独立Review → **Human自身がmerge**。強制が有効と静的設定だけで断定しない |
| P1 | [#194](https://github.com/s977043/dynamic-agent-topology/pull/194), [#93](https://github.com/s977043/dynamic-agent-topology/issues/93), [#88](https://github.com/s977043/dynamic-agent-topology/issues/88) | Cascade/Recovery/shadow gateの**Draft設計**。release**公開**までmerge hold。EXP-001の3 scenarioは全成功、#88のeligible failure母集団に流用しない | 公開後に最新mainへ同期・独立再Review・CI。U2〜U8（母集団、閾値、model/runtime、予算、権限、独立評価）を別途確定。設計mergeと実験開始を分離 |
| P1 | [#200](https://github.com/s977043/dynamic-agent-topology/pull/200), [#199](https://github.com/s977043/dynamic-agent-topology/issues/199) | Harnessのdeclared config/activation/実効拒否/Outcomeを分ける**Draft文書**。release publication holdあり | 公開後、最新baseでCI/独立Reviewerを再実行。#59固有のRuntime変更・権限を自動承認しない |
| P1 | [#202](https://github.com/s977043/dynamic-agent-topology/pull/202), [#204](https://github.com/s977043/dynamic-agent-topology/pull/204), [#205](https://github.com/s977043/dynamic-agent-topology/pull/205), [#206](https://github.com/s977043/dynamic-agent-topology/pull/206), [#207](https://github.com/s977043/dynamic-agent-topology/pull/207), [#208](https://github.com/s977043/dynamic-agent-topology/pull/208) | 複数の未採用研究PR。shared `knowledge/research/README.md` / `knowledge/sources.yaml` に同時変更あり。#207は旧HEADの別セッション技術レビュー記録があるが、GitHubのstrict Rulesetが古いbase/checkを405で拒否。#208は新mainに追随済みでもDraft | 各branchの所有者が新mainへ追従し、先行merge済みの出典行・`adopted: []`を保持。**変更後HEADでCI/別セッションReview**をやり直し、被依存Release holdは守る。外部OSSを取り込まない |
| P1 | [#159](https://github.com/s977043/dynamic-agent-topology/issues/159) | Observe/Promote正規GITHUB_TOKENのDraft PR作成が403。原因と管理者Actions policyは未実証。既存の手動診断PR/no-opを成功と誤認しない | 管理者がPR作成許可と上位policyを確認→Humanが権限変更可否判断→安全な新規入力で正規Draft/Observe+Promote no-op/CI/独立Reviewを実測 |
| P2 | [#59](https://github.com/s977043/dynamic-agent-topology/issues/59), [#63](https://github.com/s977043/dynamic-agent-topology/issues/63), [#82](https://github.com/s977043/dynamic-agent-topology/issues/82), [#150](https://github.com/s977043/dynamic-agent-topology/issues/150), [#162](https://github.com/s977043/dynamic-agent-topology/issues/162), [#166](https://github.com/s977043/dynamic-agent-topology/issues/166), [#201](https://github.com/s977043/dynamic-agent-topology/issues/201) | 未採用の仮説・残課題。Synthetic fixtureのPASSと本番効果を分離。Native controlで解決できる場合は増設しない | 代表性、再現失敗、Independent Ground Truth、paired treatment、全費用、Human budget/permissionを事前登録。未成立ならINCONCLUSIVE / DEFERを正当に記録 |

## 反復の単位（検討 → レビュー → 対応 → レビュー）

1. **Inspect:** 最新main・対象PR head/base・Issue・必須check-runs・Ruleset・Human承認記録を取得。旧headに付いた緑のCIや作者のCOMMENTは再利用しない。
2. **Challenge:** 変更の最小単位、負側ケース、fail-open、予算、モデル/effort/Topology等の交絡、rollbackを明記。設計助言AgentとIndependent Reviewerの役割は別。
3. **Change:** 1 branch=1 Agent。変更は自分のbranchへ、他Agent作業は横取りせずOwnerへ差分・必要作業を伝える。Frozen 33 files・accepted 18 Runsは改変しない。
4. **Verify:** deterministic positive/negative tests、最新headの`validate`/`Analyze Python`、適用対象ならScorecard、実行Evidenceを取得。失敗・UNKNOWN・観測限界を残す。
5. **Independent judgment:** 作成者と別セッションのread-only reviewerが**exact head**を検査（`scripts/review_package.py`を利用）。指摘修正時はCIとreviewを取り直す。GitHub Copilot quota exceededはACCEPTではない。
6. **Merge or hold:** 通常PRだけを保護Rulesetどおりmerge。Human-owned対象はOwner判断・Human操作待ち。strict up-to-date checkが拒否したらbypassせずbranch追従・新headのCIを再実行。各Issueに未達条件を残す。

## 終了基準・意図的な保留

- Issueを単に0件にすることは目標ではありません。測定前の効果・許可を捏造せず、価値がない仮説はEvidenceを記録して**DEFER / REJECT / INCONCLUSIVE**と判断できます。Human-owned判断や実験開始のPermissionをAIが自己生成しません。
- README「未Release」、CITATION「date-released」、Release/tagの不一致を解消するまで**published 0.3.0**とは宣言しない。GitHub PR #186のmergeはtag作成ではありません。
- 記録の自動同期は観測であって承認ではない。GitHub保護Rulesetを通る通常マージ成功で初めて採用済みmainとの差分が確定します。
