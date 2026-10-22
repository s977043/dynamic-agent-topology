# 残タスクの実行計画

> **As-of checkpoint: 2026-10-22 UTC（GitHub read-only再確認）。** これは実行許可・採用・Run acceptance・Merge承認そのものではありません。main / PR head / 必須CI / 独立レビュー / Human判断を作業ごとに再取得します。古いcheckpointはGit履歴を参照してください。

## 確認済みの到達点

- Repository: [s977043/dynamic-agent-topology](https://github.com/s977043/dynamic-agent-topology)。この計画の基準mainは `29f22ff4d759a75b1f90d90fe560e378831edf2e`。Open Issue **14**（#31/#59/#63/#82/#88/#93/#150/#159/#162/#166/#201/#211/#220/#223）、Open PR **2**（#205と本計画PRを含む）。PRとIssueを混ぜず、件数はこの時点のsnapshotとして扱います。
- **v0.3.0公開済み:** [Release](https://github.com/s977043/dynamic-agent-topology/releases/tag/v0.3.0)は2026-10-21T01:13:38Zに公開、tagは `0dd236ee1bc5e69b5620af151e93537e32a987dc`。tag内の日付2026-10-20と実公開日の差は#221でmainを訂正し、Release本文にも説明済み。公開タグを移動しません。
- EXP-001 [#15](https://github.com/s977043/dynamic-agent-topology/issues/15)はcompleted/closed、18/18 Runs・9/9 paired blocks・Pilot限定 **Keep T0**。[Freeze](../experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md) completed revision3、33 original blobsを保持。過去Runの再実行・再prepare・Frozen変更の許可ではありません。[#57](https://github.com/s977043/dynamic-agent-topology/issues/57)のread-only provenance audit設計・実装も完了closed。
- #200はHarness enforcement評価方法としてmerge、文書scopeの#199はclosed。#202/#206/#208/#219は**未採用研究ノート**としてmerge。新Runtime・モデル比較実測・性能向上・設定採用の承認ではありません。source台帳の`adopted: []`を維持しています。
- #223は[#224](https://github.com/s977043/dynamic-agent-topology/pull/224)設計、[#226](https://github.com/s977043/dynamic-agent-topology/pull/226)schema/semantic validator/fixtures/CI、[#227](https://github.com/s977043/dynamic-agent-topology/pull/227)Claude Code/Codex記録手順と合成例がmerge済み。段階2/3を未実装として再起案しません。合成fixture・例のPASSは、段階4の実Runtime観察や比較効果の証拠ではありません。
- #215はHuman merge済み。#229の保存・集計CLI、#230のPluginとdat-select/dat-observe、#231のLearning ledgerも統合済み。#232で不正UTF-8のsave拒否とsum継続を回帰テスト付きで修正しました。
- #228で[#220](https://github.com/s977043/dynamic-agent-topology/issues/220)の静的宣言・研究重複を[環境台帳](ENVIRONMENT_USAGE.md)へ記録。2 Agentは`model: inherit`・Read/Grep/Glob、Editルールの対象を公式仕様と#193へ照合。Claude実モデル・契約枠・追加課金を防ぐ境界・実効permissionはNOT_TESTEDです。

## Cloudで実施した検証と限界

main `48421fc387ecd6a7ccbf453336208b15c5a73052`（#215/#229/#230/#231まで統合）で、`.github/workflows/spec-lint.yml`の依存installを除く40検証runステップ（workflowのrun定義は41個）をPython3.12・`PYTHONDONTWRITEBYTECODE=1`で実行し全exit0。CLI回帰・Plugin/Skill validatorも含みます。active retry専用ステップはcompleted状態により仕様どおりSKIPで、モデルを起動していません。RunObservationのschema/正負fixture/adapter例の検証も含みます。後続headのCIは、そのheadごとに別途確認します。

2026-10-21 checkpointのRepository targetの22項目はconnector GET snapshotを既存audit関数へ渡してPASS22 / DRIFT0 / UNKNOWN0。対象外のsecurity6設定の確認や#159のActions管理policy解消を意味しません。公式一次資料への接続は正規web connectorで可能になり、#202/#205/#206/#219の主要主張を照合しました。資料確認だけで有効性・実効権限・採用を認定しません。

### Plugin導入と観察の現状

このCodex Cloudでもmain48421fcのローカルmarketplaceからDAT Pluginの導入に成功し、cache内の2 Skillが参照sourceとbyte一致することを確認しました。現セッションへの自動再読込・新モデル起動・Claude Codeへの導入をこの確認から推定しません。開発mainの導入確認であり、v0.3.0公開タグにPluginが含まれるという意味ではありません。

[#223のOwner報告](https://github.com/s977043/dynamic-agent-topology/issues/223#issuecomment-6329830368)では、両CLIのPlugin導入と新セッションでのSkill認識、観察6件/2repo、最新3件unknownなし、記録漏れ1件を報告しています。これは公開コメントの照合であり、Cloudによる元store全件の独立監査ではありません。母集団・重複識別子未照合のCloud記録とは合算しません。

## 次の実行順序

| 順位 | 対象 | 次の具体的な作業・成果物 | 完了・停止条件 |
|---|---|---|---|
| P0 | 本計画の更新PR | 最新main同期、下表14 IssueとPR状態の照合、独立別セッション3ループ、最新head CI | 必須指摘0・必須CI成功・strict up-to-dateを満たした通常文書PRのみmerge |
| P1 | [#205](https://github.com/s977043/dynamic-agent-topology/pull/205) | AIDLE一次記事と解釈を照合済み。最新台帳を保持して同期し、新headのCI/独立レビューとHuman判断材料を完成 | 本PRで明示されたHuman C4/mergeを維持。研究mergeを実験承認にしない |
| P1 | #223 | 完了時の記録をrepo外のstoreへ継続し、重複・欠測・収集漏れを記録。2repo以上/20件以上でH1/H2を規定順に判定 | 観察は効果証拠でない。公開転記は§6の仮名化・validator再実行・Human差分確認後。CLI修正やPlugin導入をH1支持としない |
| P1 | #220 | 宣言・重複棚卸しを再利用し、契約内枠と実モデル/実効permissionの確認条件を具体化 | 未確定なら比較モデル起動・設定変更・追加支出をしない |
| P1 | #31 / #159 | 管理者に必要な確認事項を具体化し、正規API/設定の証跡で再監査 | 設定を推測でPASSにせず、別actor/credentialへの切替で迂回しない |
| P2 | その他研究Issue | 代表fixture・独立oracle・対照・全費用・停止条件のうち不足する最小項目を準備 | 事前条件を満たすものだけ比較へ進める。未知はUNKNOWN/INCONCLUSIVE/DEFER |

## Open Issueの残タスクと再開条件

| Issue | 現在の証拠・Cloudで進める最小作業 | 残る判断・実行条件 |
|---|---|---|
| [#31](https://github.com/s977043/dynamic-agent-topology/issues/31) | Release公開・日付訂正の追記は反映済み。公開待ちを再計上しない | private vulnerability reporting / secret scanning / push protection / dependency graph / Dependabot alerts / security updatesの6設定未確認。closeはHuman判断 |
| [#59](https://github.com/s977043/dynamic-agent-topology/issues/59) | Modsの宣言・activation・実効拒否・Outcomeの差を#200の方法で整理 | 承認されたRuntimeでdummy正負probeを行い、実効拒否・false blockを測る。宣言のみで採用しない |
| [#63](https://github.com/s977043/dynamic-agent-topology/issues/63) | 既存syntheticコーパスの範囲を保持し、未使用の自然例と正解基準を選ぶ | 一般的抽出精度・Human時間削減は未確認。注入破損/OCR/自然例を区別 |
| [#82](https://github.com/s977043/dynamic-agent-topology/issues/82) | 再現可能な見逃しと反証objectiveの候補を用意 | 独立Ground Truthとfalse positive上限が必要。Role追加自体を改善としない |
| [#88](https://github.com/s977043/dynamic-agent-topology/issues/88) | eligible baseline failureの母集団・抽出条件を定義 | EXP-001は全成功で回復効果の母集団に流用しない。#194設計U1〜U8を確定 |
| [#93](https://github.com/s977043/dynamic-agent-topology/issues/93) | #194の未採用Cascade/Recovery設計、#206/#208/#219を統合せず因子別に比較計画へ対応付け | U1〜U8（母集団・閾値・model/runtime・予算・権限・独立評価）と事前登録が必要。parser fixtureはモデル優位の証明でない |
| [#150](https://github.com/s977043/dynamic-agent-topology/issues/150) | mock Git事例の範囲を明示し、実CLI比較の受入条件を準備 | mock成功と実Runtimeの利益を区別。新しい非対話Git操作は別の許可範囲で判断 |
| [#159](https://github.com/s977043/dynamic-agent-topology/issues/159) | Observe39214997427 / Promote39217402283の`API_HTTP_403`記録を保持。#216はoffline安全停止回帰 | Actions PR作成許可・上位policyの管理者確認→Human判断→安全な入力で正規Draft/no-op/CI/独立レビューを実測。offline PASSはlive解消でない |
| [#162](https://github.com/s977043/dynamic-agent-topology/issues/162) | モデル切替前後の代表タスク・品質下限・総費用・cache/orderを事前定義 | モデル・effort・workflow変更の交絡を分け、Operator/予算の成立後にfresh paired比較 |
| [#166](https://github.com/s977043/dynamic-agent-topology/issues/166) | population比較の仮説・対照・停止条件を準備 | toyの結果を実Agent集団の安全性証明へ一般化しない。実行条件・独立oracle未達なら保留 |
| [#201](https://github.com/s977043/dynamic-agent-topology/issues/201) | #214の未採用経過時間シグナル設計は統合済み | U1〜U6・事前登録・予算・Operator/Human条件は未確定。設計mergeは起動許可でない |
| [#211](https://github.com/s977043/dynamic-agent-topology/issues/211) | #212のAgency Agents研究登録を使い、既存T0との差分・ライセンス・配布条件を整理 | 予定8 Runは未実行。専門Role知識の採用・効果は独立した比較後 |
| [#220](https://github.com/s977043/dynamic-agent-topology/issues/220) | #228の宣言棚卸しと重複表を再利用。完了扱いは重複整理のみ | 実モデル/契約内枠/追加課金ゼロの実行境界/実効permission、fixture/oracle/停止条件をOperatorと確定。G0全体やG1〜G5は未完 |
| [#223](https://github.com/s977043/dynamic-agent-topology/issues/223) | 段階1〜3とCLI/Plugin統合済み。段階4はOwner報告6件/2repoで進行中、H1は20件未満のためINCONCLUSIVE。新セッションから継続収集し漏れも記録 | H1は6項目のunknownを分母に残し、2repo/20件成立後に6項目のいずれかが50%未満なら棄却→全項目80%以上なら支持→中間の順で判定。H2は同じ全件を記録者以外の2独立セッションが互いを見ず分類し、一致率とunknownを報告。原store監査・重複照合・§6公開転記前確認を経る。段階5の次版公開はHuman専権 |

## 変更ごとの3ループ

1. **検証→レビュー→修正→再レビュー:** 原Issue・一次資料・full diffを照合し、Source claim / DAT Evidence / Judgment、未知、最小変更因子を確認する。
2. **検証→レビュー→修正→再レビュー:** 最新mainへの通常同期、共有台帳の保全、正負検証、33 original blobs、Human-owned境界を確認する。
3. **検証→レビュー→修正→再レビュー:** 最終head・本文・CI・未解決指摘を一致させ、別セッション独立Reviewerが判断する。変更があれば影響を再検証する。

回数自体や作者の自己レビュー、Copilot quotaコメントを独立承認にしません。差分を作成したセッションは自己承認せず、別セッションへ原本・exact head・関連Issue・検証ログを渡します。[Harness](AGENT_HARNESS.md)に従い、通常PRのみ必要CI成功・独立レビュー必須指摘0・Ruleset順守後にmerge。AGENTS/CLAUDE/.claude/.codex/Harness規則等の変更、Freeze、release/tag、force push、削除はHuman専権を維持します。

## 終了・保留

Cloudで可能な差分・検証・レビュー・通常PR統合を完了し、残る条件は上表のOwnerと再開条件に結び付けます。Issue件数0を目的に未実測研究を完了化せず、効果なし・条件不成立はINCONCLUSIVE/DEFER/REJECTを認めます。モデル利用・追加費用・権限・Human判断をAIが自己生成しません。
