# 残タスクの実行計画

> **As-of checkpoint: 2026-10-21 JST（read-only GitHub再確認）。** この文書は意思決定・実験起動・Merge承認そのものではありません。毎回main HEAD / Open Issue / PR / exact-head checks / 独立Reviewer / Human-owned判断を再取得してください。2026-10-20以前の状態はGit履歴を参照し、現在のGateへ転用しません。

## 正本と観測値

- Repository: [s977043/dynamic-agent-topology](https://github.com/s977043/dynamic-agent-topology)
- main = `f0d3a0d249c87d1c180f915d48a858fe583638f7`（[#214](https://github.com/s977043/dynamic-agent-topology/pull/214) merge）。このSHAの[validate](https://github.com/s977043/dynamic-agent-topology/actions/runs/39543015865) / [Analyze Python](https://github.com/s977043/dynamic-agent-topology/actions/runs/39543015920) / [Scorecard analysis](https://github.com/s977043/dynamic-agent-topology/actions/runs/39543015926)はSUCCESS。確認時点のOpen Issues **14**（#31/#59/#63/#82/#88/#93/#150/#159/#162/#166/#199/#201/#211/#220）、Open PR **7**（#200/#202/#205/#206/#208/#215/#219）。PRをIssue件数へ混ぜない。件数はこの時点のスナップショットで、作業ごとに再照合します。
- **0.3.0は公開済み:** tag `v0.3.0` はrelease commit `0dd236ee1bc5e69b5620af151e93537e32a987dc`（[#218](https://github.com/s977043/dynamic-agent-topology/pull/218)のmerge）を指し、[GitHub Release](https://github.com/s977043/dynamic-agent-topology/releases/tag/v0.3.0)は2026-10-21T01:13:38Zに公開。release commitのvalidate / Analyze Python / Scorecard analysisはSUCCESS。tag内の`CITATION.cff` / CHANGELOGは2026-10-20のため、tagは動かさず[#221](https://github.com/s977043/dynamic-agent-topology/pull/221)でmainの日付を実公開日2026-10-21へ是正し、Release本文に注記した。[#213](https://github.com/s977043/dynamic-agent-topology/pull/213)はsupersededとしてclose済み。公開済みtagを付け替えない。
- [EXP-001 #15](https://github.com/s977043/dynamic-agent-topology/issues/15)はcompleted/closed、18/18 Runs・9/9 paired blocks・pilot-only **Keep T0**。[Feature Freeze](../experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md) completed revision 3、33 original blobsは保全。新たなRun・Frozen改変・Topology採用の許可を意味しません。[#57](https://github.com/s977043/dynamic-agent-topology/issues/57)はread-only provenance auditの設計・実装終了でclosed。UNKNOWNをPASSとみなさない。
- [Harness rules](AGENT_HARNESS.md): 通常PRのAgent mergeには必要な独立別セッションReview＋最新HEAD必須CI＋未解決指摘0が必要。Harness/Permission/Guard、Frozen data、release/tag、force push、削除等のHuman専権を維持。自己承認・branch横取り・Ruleset bypassは禁止。

## 優先実行ボード

| 順位 | 対象 | 現在状態 / 次の小さな仕事 | 完了と権限境界 |
| --- | --- | --- | --- |
| P0 | [#31](https://github.com/s977043/dynamic-agent-topology/issues/31) | 0.3.0の公開は完了。Issueには公開リポジトリ設定の他項目（セキュリティ6設定の未観測など）が残る | 公開結果（tag / Release / 日付是正）をIssueへ記録し、残項目で継続するかcloseするかはHumanが判断。セキュリティ6設定の未観測は残す |
| P1 | merged [#194](https://github.com/s977043/dynamic-agent-topology/pull/194), [#93](https://github.com/s977043/dynamic-agent-topology/issues/93), [#88](https://github.com/s977043/dynamic-agent-topology/issues/88) | Cascade/Recovery/shadow gateの**未採用設計**をmerge済み（独立Review MERGE_OK、最新CI SUCCESS）。EXP-001の3 scenarioは全成功、#88のeligible failure母集団に流用しない | U1〜U8（母集団、閾値、model/runtime、予算、権限、独立評価）はHuman回答待ち。設計mergeと実験開始を分離 |
| P1 | [#200](https://github.com/s977043/dynamic-agent-topology/pull/200), [#199](https://github.com/s977043/dynamic-agent-topology/issues/199) | Harnessのdeclared config/activation/実効拒否/Outcomeを分ける**Draft文書**。[comment 6250255673](https://github.com/s977043/dynamic-agent-topology/pull/200#issuecomment-6250255673)のpublication holdは0.3.0公開で前提が満たされた | 最新mainへ追従し、新headのCI/独立Reviewerを再実行。read-only技術レビューは実行許可ではない。#59固有のRuntime変更・権限を自動承認しない |
| P1 | [#202](https://github.com/s977043/dynamic-agent-topology/pull/202), [#205](https://github.com/s977043/dynamic-agent-topology/pull/205), [#206](https://github.com/s977043/dynamic-agent-topology/pull/206), [#208](https://github.com/s977043/dynamic-agent-topology/pull/208), [#219](https://github.com/s977043/dynamic-agent-topology/pull/219) | 複数の未採用研究PR。#204 / #207 / #212はmerge済み。shared `knowledge/research/README.md` / `knowledge/sources.yaml` に同時変更あり | 各PRのsource claim / DAT解釈 / 未採用`adopted: []`・ライセンス・引用をread-only reviewする。各branchの所有者が新mainへ追従し、先行merge済みの出典行・`adopted: []`を保持。**変更後HEADでCI/別セッションReview**をやり直す。外部OSSを取り込まない |
| P1 | [#211](https://github.com/s977043/dynamic-agent-topology/issues/211), [#220](https://github.com/s977043/dynamic-agent-topology/issues/220) | #211はAgency Agentsの専門Role知識をT0 ablationで評価する研究候補（研究ノートは#212でmerge済み）。#220は追加課金なしのClaude Codeモデル役割分担の比較検証候補 | 既存T0との比較に限定し、配布条件・ライセンス・未実証効果を確認。実験起動は別Operator/Human承認・予算・negative case後のみ |
| P1 | merged [#214](https://github.com/s977043/dynamic-agent-topology/pull/214), [#201](https://github.com/s977043/dynamic-agent-topology/issues/201) | #201経過時間シグナルの**未採用設計案**をmerge済み（競合解消後headの独立Review MERGE_OK、CI SUCCESS）。U1〜U6・事前登録は未確定 | 実験開始は別判断。事前登録・予算・Human承認なしにRunを起動しない |
| P1 | [#215](https://github.com/s977043/dynamic-agent-topology/pull/215), merged [#216](https://github.com/s977043/dynamic-agent-topology/pull/216) | #215はFreeze completed後のguidance修正案。旧headの独立Review / CI PASSは新headへ転用しない。#216の[保守調査](MAINTENANCE_COST_REVIEW.md)は統合済み | #215は最新mainとの差分・33 blob保全を再確認し、独立Review/最新CI後にHuman merge。C2はloopの追加検出/費用を記録、C3はCIのGET計測・shadow分類案まで。CI最適化・test削除・権限変更を実装しない |
| P1 | [#159](https://github.com/s977043/dynamic-agent-topology/issues/159) | Observe/Promote正規GITHUB_TOKENのDraft PR作成が403。原因と管理者Actions policyは未実証。最新Observe [39214997427](https://github.com/s977043/dynamic-agent-topology/actions/runs/39214997427) / Promote [39217402283](https://github.com/s977043/dynamic-agent-topology/actions/runs/39217402283)も`3504a78`で`API_HTTP_403`。#216のoffline test PASSはlive解消の証拠ではない。既存の手動診断PR/no-opを成功と誤認しない | 管理者がPR作成許可と上位policyを確認→Humanが権限変更可否判断→安全な新規入力で正規Draft/Observe+Promote no-op/CI/独立Reviewを実測 |
| P2 | [#59](https://github.com/s977043/dynamic-agent-topology/issues/59), [#63](https://github.com/s977043/dynamic-agent-topology/issues/63), [#82](https://github.com/s977043/dynamic-agent-topology/issues/82), [#150](https://github.com/s977043/dynamic-agent-topology/issues/150), [#162](https://github.com/s977043/dynamic-agent-topology/issues/162), [#166](https://github.com/s977043/dynamic-agent-topology/issues/166) | 未採用の仮説・残課題。Synthetic fixtureのPASSと本番効果を分離。Native controlで解決できる場合は増設しない | 代表性、再現失敗、Independent Ground Truth、paired treatment、全費用、Human budget/permissionを事前登録。未成立ならINCONCLUSIVE / DEFERを正当に記録 |

## 反復の単位（検討 → レビュー → 対応 → レビュー）

1. **Inspect:** 最新main・対象PR head/base・Issue・必須check-runs・Ruleset・Human承認記録を取得。旧headに付いた緑のCIや作者のCOMMENTは再利用しない。
2. **Challenge:** 変更の最小単位、負側ケース、fail-open、予算、モデル/effort/Topology等の交絡、rollbackを明記。設計助言AgentとIndependent Reviewerの役割は別。
3. **Change:** 1 branch=1 Agent。変更は自分のbranchへ、他Agent作業は横取りせずOwnerへ差分・必要作業を伝える。Frozen 33 files・accepted 18 Runsは改変しない。
4. **Verify:** deterministic positive/negative tests、最新headの`validate`/`Analyze Python`、適用対象ならScorecard、実行Evidenceを取得。失敗・UNKNOWN・観測限界を残す。
5. **Independent judgment:** 作成者と別セッションのread-only reviewerが**exact head**を検査（`scripts/review_package.py`を利用）。指摘修正時はCIとreviewを取り直す。GitHub Copilot quota exceededはACCEPTではない。
6. **Merge or hold:** 通常PRだけを保護Rulesetどおりmerge。Human-owned対象はOwner判断・Human操作待ち。strict up-to-date checkが拒否したらbypassせずbranch追従・新headのCIを再実行。各Issueに未達条件を残す。

## 終了基準・意図的な保留

- Issueを単に0件にすることは目標ではありません。測定前の効果・許可を捏造せず、価値がない仮説はEvidenceを記録して**DEFER / REJECT / INCONCLUSIVE**と判断できます。Human-owned判断や実験開始のPermissionをAIが自己生成しません。
- 公開状態はREADME/CHANGELOG/CITATIONの表記ではなく、実際のRelease/tagで判定する。次の版も、release commitの必須CI確認後にHumanがtag/Releaseを作成するまで公開済みとは宣言しない。
- 記録の自動同期は観測であって承認ではない。GitHub保護Rulesetを通る通常マージ成功で初めて採用済みmainとの差分が確定します。
