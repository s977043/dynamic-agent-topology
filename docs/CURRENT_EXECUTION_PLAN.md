# 残タスクの実行計画

> **As-of checkpoint: 2026-10-26 UTC（JSTでは10月27日、GitHub read-only再確認）。** これは実行許可・採用・Run acceptance・Merge承認そのものではありません。main / PR head / 必須CI / 独立レビュー / Human判断を作業ごとに再取得します。古いcheckpointはGit履歴を参照してください。

## 確認済みの到達点

- Repository: [s977043/dynamic-agent-topology](https://github.com/s977043/dynamic-agent-topology)。基準mainは `66f1683d92e2880b179a71e26401437fdc24d12d`。Open Issue **8**（#31/#88/#93/#159/#220/#223/#244/#248）、Open PR **2**（#257/#258、本計画PRの作成前）。一覧・個別GET・repo API総数10が一致。件数はcheckpointであり、本計画PRの作成/mergeや他者の更新で変動します。
- **v0.3.0公開済み:** [Release](https://github.com/s977043/dynamic-agent-topology/releases/tag/v0.3.0)は2026-10-21T01:13:38Zに公開、tagは `0dd236ee1bc5e69b5620af151e93537e32a987dc`。tag内の日付2026-10-20と実公開日の差は#221でmainを訂正し、Release本文にも説明済み。公開タグを移動しません。
- EXP-001 [#15](https://github.com/s977043/dynamic-agent-topology/issues/15)はcompleted/closed、18/18 Runs・9/9 paired blocks・Pilot限定 **Keep T0**。[Freeze](../experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md) completed revision3、33 original blobsを保持。過去Runの再実行・再prepare・Frozen変更の許可ではありません。[#57](https://github.com/s977043/dynamic-agent-topology/issues/57)のread-only provenance audit設計・実装も完了closed。
- #200はHarness enforcement評価方法としてmerge、文書scopeの#199はclosed。#202/#206/#208/#219は**未採用研究ノート**としてmerge。新Runtime・モデル比較実測・性能向上・設定採用の承認ではありません。source台帳の`adopted: []`を維持しています。
- #223は[#224](https://github.com/s977043/dynamic-agent-topology/pull/224)設計、[#226](https://github.com/s977043/dynamic-agent-topology/pull/226)schema/semantic validator/fixtures/CI、[#227](https://github.com/s977043/dynamic-agent-topology/pull/227)Claude Code/Codex記録手順と合成例がmerge済み。段階2/3を未実装として再起案しません。合成fixture・例のPASSは、段階4の実Runtime観察や比較効果の証拠ではありません。
- #205の研究文書と#235のYAML読込み統一はmerge済み。#235では重複キーを両入口で拒否し、直接validatorも既存CLIと同じくmerge keyを拒否します。未解決PRとして再計上しません。
- #215はHuman merge済み。#229の保存・集計CLI、#230のPluginとdat-select/dat-observe、#231のLearning ledgerも統合済み。#232で不正UTF-8のsave拒否とsum継続、#234でstore配下のGit作業ツリーへの保存拒否を回帰テスト付きで修正しました。
- #228で[#220](https://github.com/s977043/dynamic-agent-topology/issues/220)の静的宣言・研究重複を[環境台帳](ENVIRONMENT_USAGE.md)へ記録。2 Agentは`model: inherit`・Read/Grep/Glob、Editルールの対象を公式仕様と#193へ照合。Claude実モデル・契約枠・追加課金を防ぐ境界・実効permissionはNOT_TESTEDです。

## Cloudで実施した検証と限界

main `48421fc387ecd6a7ccbf453336208b15c5a73052`（#215/#229/#230/#231まで統合）で、`.github/workflows/spec-lint.yml`の依存installを除く40検証runステップ（workflowのrun定義は41個）をPython3.12・`PYTHONDONTWRITEBYTECODE=1`で実行し全exit0。CLI回帰・Plugin/Skill validatorも含みます。active retry専用ステップはcompleted状態により仕様どおりSKIPで、モデルを起動していません。RunObservationのschema/正負fixture/adapter例の検証も含みます。後続headのCIは、そのheadごとに別途確認します。

2026-10-21 checkpointのRepository targetの22項目はconnector GET snapshotを既存audit関数へ渡してPASS22 / DRIFT0 / UNKNOWN0。対象外のsecurity6設定の確認や#159のActions管理policy解消を意味しません。公式一次資料への接続は正規web connectorで可能になり、#202/#205/#206/#219の主要主張を照合しました。資料確認だけで有効性・実効権限・採用を認定しません。

### Plugin導入と観察の現状

このCodex Cloudでもmain48421fcのローカルmarketplaceからDAT Pluginの導入に成功し、cache内の2 Skillが参照sourceとbyte一致することを確認しました。現セッションへの自動再読込・新モデル起動・Claude Codeへの導入をこの確認から推定しません。開発mainの導入確認であり、v0.3.0公開タグにPluginが含まれるという意味ではありません。

[#223 H1再判定](https://github.com/s977043/dynamic-agent-topology/issues/223#issuecomment-6391127012)は23件/7projectで6項目すべて80%以上、支持と報告。startedAt unknown12件は期間判定不能として別掲し、感度分析も記録しています。[H2報告](https://github.com/s977043/dynamic-agent-topology/issues/223#issuecomment-6426770476)は同じ23件を2セッションが盲検分類し23/23一致、unknown0、支持と報告。Aのログは独立レビュー照合済み、Bの独立性はOrganizer確認依存で、コメントの独立レビュー履歴は2回のCHANGES_REQUIREDと説明修正までです。このCloudで原store・ログ全件を独立監査した結果ではなく、構成の効果証拠でもありません。母集団未照合のCloud記録を合算しません。

[#223のOwner方針](https://github.com/s977043/dynamic-agent-topology/issues/223#issuecomment-6327826768)どおり、仕様＋2 Skillsを維持し、CLIは裏方の任意検証道具として機能拡張しません。dat-observeでの保存前validator実行とrepo外保存の条件は維持します。

[#244の上限確定](https://github.com/s977043/dynamic-agent-topology/issues/244#issuecomment-6426773345)はscreening50M・評価1 Task39M・評価全体130M tokens。追加分の許容予算180M（支出済み較正を含め約203M）という上限の記録であり、事前登録成立・起動許可ではありません。確定版は#258でmerge済み。以下の完了追記と起動停止条件を参照してください。

### 今回Cloudで可能な検証

Python3.12の既存validator・回帰、Unix socketを使うローカル結合テスト、hard Taskの統計シミュレーション再現、33 original blobs監査、GitHubのhead/CI/独立レビュー照合を行います。モデルや有料APIを呼ばない検証です。較正キットの回帰テストはMac専用`/usr/bin/sandbox-exec`を呼ぶ箇所でCloudでは完走できず、環境制約として区別します。各結果は対象SHAとともにPRへ記録します。

Docker Desktopのnetwork隔離・mountの実測、Claude認証経路、契約/追加課金境界、Mac/ThinkPadの実環境、非公開storeはこの確認だけでは検証済みにしません。予備キットのFAIL/NOT_TESTEDが残る間、モデルを起動しません。

### 今回の対応結果（同日追記）

- #257: head `55003a6`、独立レビュー3ループ・必須0・CI3件成功でmerge（`e7c605ea448f79a9a20342beaaf246dd3376621d`）。18回帰成功。Docker確認2/3/4/7の未達を解消したことにはしません。readinessの「30秒」表現と実装のtimeout保証の差は非blocking推奨として残ります。
- #258: 許容予算を実消費の保証上界とする必須指摘1件を修正。head `557e7cc`、独立3ループ・必須0・CI3件成功でmerge（`0760b1b40767cec9622415c9aabd90f803dd8b93`）。計算表18セル・離散性2例・誤棄却0.087を再現。
- [#244の確定blob記録](https://github.com/s977043/dynamic-agent-topology/issues/244#issuecomment-6428095927): main `0760b1b` の文書blob `57007effd1fd502c86ea7e63029352df902670d0`、計算script blob `6199f01ce4982133658bb2f87fcb36a42e271a81`を記録し、§7の事前登録成立手順を完了。成立後も§5.1bのOperator判断まで起動停止。
- 上記merge後のOpen PRは本計画PRだけ（#259）。冒頭の8 Issue/2 PRは作業前snapshotとして保持します。

## 次の実行順序

| 順位 | 対象 | 次の具体的な作業・成果物 | 完了・停止条件 |
|---|---|---|---|
| 完了 | [#257](https://github.com/s977043/dynamic-agent-topology/pull/257) | network none / Unix socket relayの差分、ローカル結合テスト、最終head CIを独立レビュー | 通常PRのmerge条件を満たした場合だけ統合。Docker実測・認証経路の未達を解消したことにはしない |
| 完了 | [#258](https://github.com/s977043/dynamic-agent-topology/pull/258) | hard Task事前登録v2の確定値・統計計算の再現・独立レビュー | merge後、§7どおりmainの確定blob hashを#244へ記録して成立。モデル起動はOperator |
| P0 | 本計画の更新PR | 8 IssueとOpen PRの原本照合、別セッション3ループ、最新head CI | 通常文書PRの必須指摘0・必須CI成功・up-to-dateを満たしてmerge |
| P1 | #223 | 最新H1/H2報告と未決事項候補2件を照合し、必要なら独立レビューを経た最小提案を作る | 判定規則・schemaの変更と次版公開を混同しない。公開転記は設計§6の確認後 |
| P1 | #220 / #244 | 承認済み手順・予算・実行主体と、実測未達のpreflightを切り分ける | FAIL / UNKNOWNが残ればモデルを起動しない。Operatorの実行を代行しない |
| P1 | #31 / #159 | 管理者の確認事項・正規API/設定の証跡で再監査 | 設定を推測でPASSにせず、actor/credential切替で迂回しない |
| P2 | #88 / #93 / #248 | 代表fixture・独立oracle・対照・全費用・停止条件の不足を整理 | 事前条件未達はUNKNOWN/INCONCLUSIVE/DEFER。研究登録を採用としない |

## Open Issueの残タスクと再開条件

| Issue | 現在の証拠・Cloudで進める作業 | 残る判断・実行条件 |
|---|---|---|
| [#31](https://github.com/s977043/dynamic-agent-topology/issues/31) | v0.3.0公開済み。公開待ちを再計上しない | private vulnerability reporting / secret scanning / push protection / dependency graph / Dependabot alerts / security updatesの6設定未確認。closeはHuman判断 |
| [#88](https://github.com/s977043/dynamic-agent-topology/issues/88) | EXP-002→EXP-003の順序に従い、回復比較はその後。eligible baseline failureの母集団・抽出条件を整理し、#244の進展を参照 | EXP-001全成功を回復効果の母集団にしない。実測・独立評価・Operator条件が必要 |
| [#93](https://github.com/s977043/dynamic-agent-topology/issues/93) | Cascade/Recoveryなどの未採用設計を因子別に対応付ける | Human同意はEXP-002→EXP-003の順序だけで、予算・起動の承認ではない。#82/#211候補armも吸収済み。母集団・閾値・model/runtime・予算・権限・独立評価と事前登録が必要。parserや模擬計算のPASSはモデル優位の証明でない |
| [#159](https://github.com/s977043/dynamic-agent-topology/issues/159) | Observe39214997427 / Promote39217402283のAPI_HTTP_403と#216のoffline安全停止回帰を区別 | Actions PR作成許可・上位policyの管理者確認後、正規Draft/no-op/CI/独立レビューを実測。規則・Guard変更のmergeはHuman |
| [#220](https://github.com/s977043/dynamic-agent-topology/issues/220) | #249事前登録、#252の18 Task fixture、#254予備2 Runキットを再利用し、#257を検証 | PR報告ではDocker確認2が5回中4回FAIL、3/4/7はNOT_TESTED。Gate4の事前登録は成立済み。現行はproxy方式で、旧案Dは廃止済み。実効permission・認証・課金境界の実測PASSに置き換えない。/host_mntの許容は別判断 |
| [#223](https://github.com/s977043/dynamic-agent-topology/issues/223) | 段階1〜3・CLI/Plugin実装済み。最新報告はH1支持23件/7project、H2支持23/23。複数artifactのverification根拠とspecialistRole根拠の見直し候補を整理 | 原store・ログはこのCloudで未監査。H2のB独立性はOrganizer確認依存。公開転記は§6、段階5のrelease/tagはHuman専権 |
| [#244](https://github.com/s977043/dynamic-agent-topology/issues/244) | 旧版較正25 RunのOperator報告は22,977,578 tokens・hard帯0候補。v2確定版#258をmergeし、上記hash記録で成立。統計模擬は効果実測ではない | 旧版の残39候補は開始しない。上限確定は実効hard capや起動許可ではない。予算保証の独立レビュー指摘は修正済み。成立後も超過可能性に対するOperator判断を経てscreening、評価予算は選定後の見積もりで再承認 |
| [#248](https://github.com/s977043/dynamic-agent-topology/issues/248) | Subagent foldingの候補を同一model/effort・paired E2E評価へ具体化 | 外部記事の速度逸話をDATの効果にしない。独立評価・Human承認はfold対象外、事前登録・oracle・費用・Operator条件を満たしてから実行 |

## 変更ごとの3ループ

1. **検証→レビュー→修正→再レビュー:** 原Issue・一次資料・full diffを照合し、Source claim / DAT Evidence / Judgment、未知、最小変更因子を確認する。
2. **検証→レビュー→修正→再レビュー:** 最新mainへの通常同期、共有台帳の保全、正負検証、33 original blobs、Human-owned境界を確認する。
3. **検証→レビュー→修正→再レビュー:** 最終head・本文・CI・未解決指摘を一致させ、別セッション独立Reviewerが判断する。変更があれば影響を再検証する。

回数自体や作者の自己レビュー、Copilot quotaコメントを独立承認にしません。差分を作成したセッションは自己承認せず、別セッションへ原本・exact head・関連Issue・検証ログを渡します。[Harness](AGENT_HARNESS.md)に従い、通常PRのみ必要CI成功・独立レビュー必須指摘0・Ruleset順守後にmerge。AGENTS/CLAUDE/.claude/.codex/Harness規則等の変更、Freeze、release/tag、force push、削除はHuman専権を維持します。

## 終了・保留

Cloudで可能な差分・検証・レビュー・通常PR統合を完了し、残る条件は上表のOwnerと再開条件に結び付けます。Issue件数0を目的に未実測研究を完了化せず、効果なし・条件不成立はINCONCLUSIVE/DEFER/REJECTを認めます。モデル利用・追加費用・権限・Human判断をAIが自己生成しません。
