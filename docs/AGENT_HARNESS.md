# Agent Development Harness

このRepositoryを開発するCoding Agent（Claude Code / Codex など）が、自分の失敗やレビュー指摘から学び、再発防止を仕組みに変えていくための開発ハーネスです。

これはDATの仕様（Topology / Role / Runtime Mapping / Evaluation）ではなく、DATを開発する作業環境の運用です。EXP-001のFrozen artifactや評価semanticsは変更せず、EXP-001 Runにも影響しません（Runは外部のfresh workspaceで実行されます）。

## 原則

- **HOTL（Human-on-the-loop）で運用する。** 人間は事前承認したポリシー（下記の自律境界）の範囲で、監視・停止・事後受理を担います。範囲内の操作は Agent が機械ゲートを満たしたうえで実行し、各段階の結果を Issue / PR に記録します。人間だけが確認・判断する手順は減らし、基本は Agent が進めます（オーナー指示、2026-10-23）。
- **人間への確認は Human 専権の操作と STOP 条件に限る。** それ以外は Agent が判断して進め、結果と根拠を報告します。
- **規則変更 PR は Agent が起案とレビューまで、merge は人間が行う。** 規則変更 PR（`AGENTS.md`、`CLAUDE.md`、`.claude/`、`.codex/`、本書の規則、`docs/RELEASE_READINESS.md` の権限・Evidence・Publication・failure の規則、`scripts/validate_agent_guidance.py`、Guard の hook や検査スクリプトを変える PR）は、Agent が差分・理由・影響範囲・ロールバック案を PR に書き、別モデルの独立レビューまで行い、人間が merge します。作成者と同じ主体がレビューを手配して merge できる構造では、自己承認を文書だけでは防げないためです。GitHub の保護ルールで別主体のレビューを強制できるようになったら見直します。merge 後に Agent が設定と実効権限を再確認します。
- **自己承認をしない。** 判断材料・変更を作成または修正した Agent セッションは、それを承認しません。
- **Evidenceのない学びは昇格しない。** PR / commit / CI run / Issueへのリンクがない記録は候補のままです。
- **Proseより機械的なGuardを優先する。** 昇格先は CI・validator → hook → permission設定 → `AGENTS.md` の文章 → skill の順に検討します。

## ループ

| 段階    | 内容                                                                    | 担い手                   |
| ------- | ----------------------------------------------------------------------- | ------------------------ |
| Observe | CI失敗、レビュー指摘、validator失敗、permission拒否、ユーザー訂正を拾う | Agent                    |
| Learn   | 下の Learning ledger に、Evidence・発生回数・状態を追記する             | Agent                    |
| Promote | 同種が2回以上でEvidenceが揃ったら、改善PRを出す                         | Agentが起案、自律境界に従いmerge |
| Enforce | 採用した対策をCI / hook / 設定として常時有効にする                      | Harness                  |
| Measure | 再発率、CI初回pass率、レビューループ数を見る（permission prompt 数は記録が残らないため対象外。下記「Measure」） | 定期棚卸し               |

## Fast Feedback と相談エージェント

[Fast Feedback workflow](FAST_FEEDBACK_WORKFLOW.md) は **開発・Operator作業を小さく検証するための任意の助言フロー**です。EXP-001のFrozen実験条件や本書の自律境界、Run acceptanceは変更しません。必須の安全・権限検査が不合格/不明なら停止します。

- **Agile Coach**（`.claude/agents/agile-coach.md`）: 実測の学習目標、最小の安全な確認、準備の肥大化を見直す。
- **Scrum Master**（`.claude/agents/scrum-master.md`）: impediment、判断待ち、次の一手を可視化する。
- 助言ロールはClaude Codeの`.claude/agents/`のみ。Codexには登録しない。Codexのsubagentは親のsandboxを引き継ぎ、ロール設定のread-onlyを保証できないため（PR #124の負側テスト）。
- 両ロールともread-onlyの**助言**専用（`tools: Read, Grep, Glob`）。Claude Code 2.1.296でWrite・Edit・Bash・WebFetchが使えないことを確認済み。WebSearch・MCPはNOT_TESTEDだが、どちらもtoolsに含まれない。独立Reviewer、Verifier、Humanの承認権限を持たない。どちらか一方または両方を必要な時だけ呼び、全Run必須の新Gateを作らない。
- 実験用のfresh Codex sessionへ過去Runの出力や相談記録を入力しない。現在のRun実行権限はIssue #15と承認済み手順で判断する。

## 自律境界

| 操作 | 実行者 | 条件 |
| --- | --- | --- |
| Learning ledger・Issue への記録、draft PR、validator / test、自分の branch への push | Agent | 記録と通知を残す |
| 規則変更 PR 以外の PR の merge（docs・実験・コード・依存の追加を含む） | Agent | 次をすべて満たす: 必須 CI 全 pass、PR 作成セッションと別セッション（別モデル推奨）の独立レビューで未解決の必須指摘 0、Human 専権の対象を含まない。依存を追加する PR は別モデルの独立レビューが必須。レビュー対象の head・差分・判定・CI 結果を PR に記録する |
| 規則変更 PR（`AGENTS.md`、`CLAUDE.md`、`.claude/`、`.codex/`、本書の規則、`docs/RELEASE_READINESS.md` の権限・Evidence・Publication・failure の規則、`scripts/validate_agent_guidance.py`、Guard の hook や検査スクリプトを変える PR）の起案とレビュー | Agent | 別モデルの独立レビューまで行い、レビュー対象の head・差分・判定・CI 結果を PR に記録する。検査を弱める変更（validator・Guard の判定を緩める、必須チェックを外す）はその旨を PR 本文に明記する。起案したら Issue #159 にその PR のリンクを残す。merge は Human 専権 |
| リリースの公開の承認（版ごと） | 人間 | Agent が版番号と release PR の head SHA を示して y/N で確認し、人間が y と答える。Agent はこの承認（版・head SHA・日時・回答者）を release PR に記録してから公開に進む。承認後に head が変わり、公開日の記入以外の差分が出たら承認は無効になり、もう一度承認を得る。GitHub の保護設定ではまだ別主体による承認を強制できない（ruleset の evaluate が使えないプランの制約）ため、同じ主体がレビューを手配して公開まで完結しないよう人間の承認を挟む。保護設定で別主体の承認を強制できるようになったら見直す |
| リリースの公開（公開日の記入、release PR の merge、新しい version tag の作成、GitHub Release の公開、公開後の確認） | Agent | `docs/RELEASE_READINESS.md` の手順に従い、段階ごとに次をすべて満たす。**merge の前**: 上の版ごとの承認が有効で PR に記録済み。release PR の最終 head で必須 CI 全 pass。PR 作成セッションと別セッションの独立レビューを 2 本（記載の網羅性と公開可否。少なくとも 1 本は別モデル）行い、どちらも未解決の必須指摘 0。レビュー済み head から最終 head までの差分が公開日の記入だけ。release PR が open の間は他の PR を merge しない。`docs/RELEASE_READINESS.md` の Compatibility boundary で破壊的変更なしと判定済み。**tag を作る前**: release commit で main の必須 CI と Scorecard が success（過去の Scorecard 結果は使わない）。作る tag が新しく、既存の tag と重ならない。**公開の後**: tag と GitHub Release が release commit を指し、README・`CHANGELOG.md`・`CITATION.cff` と版が一致することを確かめ、Publication gate の各項目を PR に記録する。release PR が規則変更 PR に当たる変更や下の Human 専権の対象を含むときは対象外。異常時は停止し、公開済みと主張しない（Publication failure 節） |
| Reviewer Judgment（Run acceptance、disposition の ACCEPT 等） | 独立 Agent Reviewer または人間 | 作成者と別セッション。Frozen 例外など高リスクの判断は別モデルも用いる（例: Codex（GPT 系）、Antigravity CLI（`agy`、Gemini 系）。下記）。記録には runtime・model・session ID・根拠リンクを書く |
| EXP-001 の一回限りの model 起動（retry allowance の消費） | Agent（文書化された retry 手順の範囲に限る: `AGENTS.md`、`docs/EXP-001_RETRY_51.md`、`docs/EXP-001_RETRY_T1_R01.md`、本書の HOTL 条件） | 手順書の全 Gate と preflight を機械的に検査して合格、Reviewer Judgment が記録済み、retry 未消費、Runtime/Model/Effort が固定、重複起動を防止、attestation・trace・Evidence を保存。異常時は停止し、追加起動はしない |
| Human 専権（下表） | 人間 | Agent は起案と材料の準備まで |

Human 専権として残す操作と理由:

| 操作 | 理由 |
| --- | --- |
| 規則変更 PR の merge | 作成者と同じ主体がレビューを手配して merge できるため、自己承認を文書だけでは防げない。GitHub の保護ルールで別主体のレビューを強制できるようになったら見直す |
| Feature Freeze の改訂、Frozen artifact の変更 | 実験条件を固定した前提が崩れ、EXP-001 の結果の比較可能性を失う。上記の EXP-001 retry 例外はそのまま |
| 既存 tag の移動・削除、GitHub Release の削除 | 公開した境界を書き換え、利用者が参照した版と食い違う。取り消せない |
| 破壊的変更を含む版の公開（1.0.0 以降の major 版、1.0.0 の初公開、0.x で破壊的変更を含む版。公開契約と破壊的変更の定義は `docs/RELEASE_READINESS.md` の Compatibility boundary。判定できないときも Human が判断する） | 互換性の方針を決めるのは人間のため。新しい tag は動かせないので公開後に取り消せない |
| Feature Freeze に関わる版の公開（Frozen artifact や評価 semantics の変更・例外を含む版） | 上の Feature Freeze の行と同じ |
| force push | 他者の commit を消すおそれがあり、取り消せない |
| ブランチ・ファイル・issue などの削除 | 取り消せない、または復元に人手が要る |
| 予算の承認と、課金が発生する model 起動（Operator） | 費用の責任者が人間のため。上記の EXP-001 retry 例外はそのまま |
| secret の作成・ローテーション・削除・公開設定・権限付与 | 漏洩すると取り消せない |
| GitHub の branch protection / ruleset / 必須 CI の設定変更（repo 外の設定） | merge の機械ゲートそのものを変えるため、Agent が変えると自己承認になる |

STOP 条件（当たったら Agent は進行を止め、状態と根拠を記録して人間に確認する）:

- 必須の安全・権限検査が FAIL / UNKNOWN: `.github/workflows/spec-lint.yml` の必須 step、`scripts/validate_experiment_freeze.py`、`scripts/validate_agent_guidance.py`、`scripts/learning_ledger.py`、`.claude/hooks/guard_frozen_bash.py` の ask
- Gate / preflight の判定ができない
- 予算・費用・実行主体（Operator）が不明、または明示的な Operator 要件と衝突する
- secret へのアクセス権限が不明、または漏洩の疑いがある
- ツールや permission による拒否
- 自分が作っていない変更が worktree や branch にある
- 独立レビューの必須指摘が解消できない
- Human 専権の操作が必要になった

監視と介入:

- 人間はいつでも停止・差し戻し・PR の revert を指示できます。停止の指示を受けたら、Agent は進行中の操作を安全な状態で止め、状態を報告します。
- Agent は merge した PR と判断の根拠（CI run、独立レビューの記録、STOP 条件に当たらなかったこと）を PR / Issue に記録し、人間が事後に確認できるようにします。

Reviewer Judgment の別モデルに Antigravity CLI を使う場合は、headless（`-p`）で `--mode plan --sandbox` を付けて起動します。この起動ではシェルが必要な tool が自動で拒否されることを確認しています。書き込み tool が拒否されるかは確認していないため、レビュー対象は使い捨ての checkout にします。headless では作業ディレクトリと `--add-dir` の外のファイル読み取りが拒否されるため、レビュー対象の checkout を作業ディレクトリにして起動し、それ以外の判断材料はローカルファイルにまとめて `--add-dir` で渡します。tool が 1 つでも拒否されると判断を出力せずに終わる（`denied_actions` に記録され、`response` は空）ため、依頼文に「シェルは使えないので、ハッシュの再計算やテストの再実行はせず記録の値どうしを照合する」ことと、読めるディレクトリの絶対パスを書きます。`--dangerously-skip-permissions` は使いません。記録の session ID には `--output-format json` の `conversation_id` を、model には `--model` で明示した値を書きます（usage に model が出ないため）。

独立 Reviewer（Codex・Antigravity）への依頼は `scripts/review_package.py` で準備します（L-009・L-010 の対策）。Reviewer の起動と PR への投稿はこのスクリプトではせず、表示されたコマンドで行います。

- `build <PR> --out <dir> [--issue N] [--comment ID]`: `materials/`（PR 本文とコメント、base との差分、Issue 本文、Issue コメント、main の SHA）と、PR head の detached checkout（`checkout/`。`--no-checkout` で省略）を作ります。
- `prompt --package <dir> --reviewer codex|agy [--template <file>]`: 観点テンプレート（`scripts/review_templates/`）に、PR 番号・head SHA・読めるディレクトリの絶対パス・判定基準（必須は 4 分類）を埋めた依頼文を `<dir>/prompt-<reviewer>.md` に書き、起動コマンド例を表示します。agy 向けには「シェルは使えない」を入れ、Codex 向けには入れません。
- `record --head <SHA> --package <dir> [--codex <file> --codex-session <ID>] [--agy <json>]`: Verdict と必須・推奨の件数の表、runtime・model・session ID を含む記録コメントを標準出力に出します。`--head` が package の head と違えば止まります。Verdict と件数は所定のサマリー行からだけ読み、行が無い・複数あるときは `不明` と理由を書きます。公開されるため、Reviewer の出力（agy の `denied_actions` を含む）から `file://` リンクを除き、checkout と materials のパスを `<checkout>` / `<materials>` に、ホームディレクトリを `~` に、それ以外の `/Users/…`・`/home/…`・`/private/tmp/…`・`/tmp/…` の絶対パスを `<local-path>` に置き換えます。

1 branchは1 Agentが担当します。同じbranchに別Agentがpushしている場合は、上書きせず最新のheadに積み直し、pushは `--force-with-lease` に限ります。

## Guard

| Guard                                      | 状態       | 検出するもの                                                                                                                |
| ------------------------------------------ | ---------- | --------------------------------------------------------------------------------------------------------------------------- |
| `scripts/validate_agent_guidance.py`（CI） | 有効       | `AGENTS.md` / `CLAUDE.md` が参照する存在しないpath、`freeze.yaml` と `.claude/settings.json` のask ruleのずれ（漏れ・過剰） |
| `.claude/settings.json` ask rule           | 有効       | Claude CodeのEdit/WriteによるFrozen fileの変更                                                                              |
| `.claude/settings.json` / `.codex/config.toml`（`shell_environment_policy`）の `PYTHONDONTWRITEBYTECODE=1` | 有効（Claude Code / Codex） | Agent実行時の `__pycache__` 生成。Gemini CLIなどでは別途設定が必要 |
| `.claude/hooks/guard_frozen_bash.py`（PreToolUse） | 有効 | Bash経由のFrozen fileへの書き込み（redirect先、`sed -i`・`cp`・`git checkout` などの書き込みcommand）。heuristicのため検出漏れはありうる（下記Known gaps） |
| `.prettierignore` | 有効（`.prettierignore` を尊重する整形hook） | Agentの自動整形による `experiments/`・`freeze.yaml` が固定する `topologies/`・`roles/`・`schemas/` のファイル・`docs/EXP-001_*.md`・本書（ハッシュ照合対象・レビュー済み表）の書き換え。整形hookはsessionのproject root（worktree作業時は親checkout）の `.prettierignore` を読むため、そこに本設定が無い間は効かない |
| `.github/workflows/harness-metrics.yml`（週次、月曜 06:43 UTC と手動実行） | 有効（読み取り専用、必須 check ではない） | 直近 7 日の merged PR の CI 初回 pass 率・レビューループ数と Learning ledger の集計（下記「Measure」）。失敗しても merge は止めない |

Codexにはローカルの Frozen file guardがありません（`workspace-write` sandboxのため、Frozen fileへの書き込みも止まりません）。Codexでの変更は CI の `scripts/validate_experiment_freeze.py` だけが検出します。

`guard_frozen_bash.py` のKnown gaps:

- `cd dir && ...` のように作業directoryを変えた後の相対pathは解決しない
- 変数展開、`$(...)`、script fileやinterpreter経由の間接的な書き込みは検出しない
- 書き込みcommandの判定は正規表現のheuristicで、未知のcommandは見逃す
- 内部エラー時はfail open（promptを出さずに通す）

## Learning ledger

共有するプロジェクト知識はrepo、端末固有の観測は環境memoryに記録します。[知識とメモリの分担](KNOWLEDGE_OWNERSHIP.md)に保存先・再確認・引き継ぎをまとめています。独立レビュー・Human 専権・実験Freezeの境界は「自律境界」に従います。

正本は `knowledge/learning-ledger.json` です。以下の表は `python scripts/learning_ledger.py --write` で生成し、CI が schema・ID 重複・日付の Evidence 原文への明記・日付と回数の整合・表の同期を検証します。追記・訂正は JSON に行い、表を再生成します。状態変更や Guard の採用は「自律境界」に従います（規則・Guard の変更は規則変更 PR として Human が merge）。

`observedDates` は Evidence に明記された観測日のみです。不明なら空配列とし、PR 作成日から推測しません。回数は旧台帳の集計を保持し、日付の件数は全発生回数を表しません。Evidence の原文と確認可能な GitHub リンクを保存し、local 観測に公開リンクがない場合は `urls: []` を保持します。

<!-- learning-ledger:generated:start -->
| ID | 観測 | Evidence | 回数 | 状態 | 対策 |
| --- | --- | --- | --- | --- | --- |
| L-001 | Agent guidanceの記述がRepositoryの実態とずれる（fixturesの説明、schema適用範囲、freeze範囲、permissionの効果） | PR #84 / #85 のレビューループ | 4 | promoted | `validate_agent_guidance.py` |
| L-002 | ask ruleがBash経由の書き込みを検出しない | PR #85 review | 1 | promoted | `.claude/hooks/guard_frozen_bash.py` |
| L-003 | 複数のAgentや操作者が同じbranch・worktree・PRを並行して変更する | PR #85 commit `792102d`、worktree内のhook編集、PR #86 が確認前に別の操作者によりmerge | 3 | promoted | 本書の1 branch 1 Agent rule、`AGENTS.md` のpush手順 |
| L-004 | Frozen fixtureでtest実行時に `__pycache__` が生成される | PR #85 作業時のlocal観測 | 1 | promoted | `PYTHONDONTWRITEBYTECODE=1` |
| L-005 | branch切替の失敗後も `;` で連結したcommit/pushが続き、別PRのbranchへpushされた | PR #85 / #87（commit `9ba8208`） | 1 | candidate | git書き込みは `&&` で連結し、push元branchを確認 |
| L-006 | CIと異なるlocalのPythonでのみ検証し、CI（Python 3.12）で `validate` が失敗した | PR #85 CI run 37541615338 | 1 | promoted | `AGENTS.md` の Python 3.12 検証ルール |
| L-007 | push/API の権限エラーを回避するため、ワーカーが `gh auth switch` で active アカウントを変更した。active アカウントは同一マシンの全セッションで共有されるため、並行セッションの書き込み先が変わり得る | PR #110 作業時（2026-10-08） | 1 | candidate | アカウント切替はせず、コマンド単位で認証トークンを渡す。委託プロンプトの境界に明記 |
| L-008 | Agent の Edit 後に走る自動整形 hook が、レビュー済み SHA-256 表を含む文書の表の空白を書き換えた（ワーカーが気づき HEAD から作り直した） | PR #110 作業時（2026-10-08）、`docs/EXP-001_RETRY_T1_R01.md`。PR #112 作業時の再発（PR #112 本文に記録） | 2 | promoted | `.prettierignore`（併せて、編集後に意図した行以外の差分が無いことを `git diff` で確認する） |
| L-009 | 独立 Reviewer の判断が判断材料不足で誤判定・無効化した（基準文書の取得がネットワークで失敗したまま ACCEPT を出した、Issue コメント未提供で前提を確認できず NO-GO、指定外参照の禁止と Reviewer 起動時の作業ディレクトリ確認が衝突して判定無効、パッケージに存在する `materials/pr.md` を「ない」として CHANGES_REQUIRED） | PR #130 の Run acceptance レビュー（Issue #15 comment 6106366753 に至る 4 回）。PR #194 の 5 回目レビュー（2026-10-15、必須 0 件で材料欠落のみを理由に CHANGES_REQUIRED、同一材料の新規セッション再実行で MERGE_OK。PR #194 comment 6203136254） | 4 | candidate | 判断材料（基準文書・関連 Issue コメント・PR 本文と diff・Artifact）を 1 ディレクトリにまとめ依頼書と共に渡す。作業ディレクトリの確認は許可し、禁止範囲はその外とする。材料欠落だけを理由とする判定は、材料の実在を確認し、実在すれば同一材料の新規セッションで再実行して両結果を記録する |
| L-010 | 『指摘ゼロ』を完了の定義にした机上レビューの往復が収束せず（15 回以上）、Run が進まなかった | PR #110・#116・#121・#122 のレビュー往復、本番スクリプトの NO-GO 3 回 | 2 | candidate | 必須を安全・秘密値・プロトコル違反・回収不能の 4 分類に絞り、推奨は事後改善に回す。同箇所の指摘が続く場合はドライランやリハーサルで実際に動かして確かめる |
| L-011 | Judgment の適用範囲（scenario・rep）が引き継ぎや依頼文で略記（「r01」）されてセッション間に伝わり、範囲が広がって読まれた（対象は train/normalize-name の r01 ペアだけなのに、全 r01 を除外する集計案になりかけた） | Issue #15 comment 6072534007（T1 r01 retry の環境判断。当時の r01 は train/normalize-name だけ）、環境 Judgment 6107822908（条件 4「集計時の開示」の充足は判断していないと明記）、2026-10-12 の #15 本文「現在地」の訂正 | 1 | candidate | Judgment の条件を引き継ぐときは、scenario・rep・条件を一次ソースの文言どおりに書き、comment ID を添える |
| L-012 | GitHub自動観測（comment、原因未分類） | 2026-10-11 recommended=1; source timestamp=2026-10-11T07:12:30+00:00 | 1 | candidate | 原因確認と改善案の検討待ち |
| L-013 | GitHub自動観測（ci、原因未分類） | 2026-10-12 CI conclusion=failure; run_id=38316631318; run_attempt=1; final job completed_at; source timestamp=2026-10-12T22:26:33+00:00 | 1 | candidate | 原因確認と改善案の検討待ち |
| L-014 | GitHub自動観測（comment、原因未分類） | 2026-10-12 recommended=4; source timestamp=2026-10-12T07:56:34+00:00 | 1 | candidate | 原因確認と改善案の検討待ち |
| L-015 | release PR が open の間に別の PR を merge し、release PR を update-branch した。CHANGELOG と record に固定した content candidate（`24fa06b`）と head の内容が合わなくなり、独立レビューで major 指摘を受けて再レビューが 1 周増えた | 2026-10-14 PR #186（candidate `24fa06b`）の open 中に #187（`5c31094`）を merge し、merge commit `23ee816` で main を取り込んだ。PR #186 comment 6166299468（2 回目レビュー REQUEST_CHANGES）、`604723c` で candidate を更新し comment 6166648419 で ACCEPT | 1 | candidate | release PR が open の間は他の PR を merge しない。merge するときは、candidate の更新と CHANGELOG への追記まで同じ作業で行う |
| L-016 | Human しか決められない `CITATION.cff` の `date-released` に根拠のない仮の値を入れ、独立レビューで major 指摘を受けた | 2026-10-14 PR #186 の 1 回目レビュー（head `254f2c6`、REQUEST_CHANGES、major: `date-released` の根拠がない）。comment 6166299468 の表に記録 | 1 | candidate | Human しか決められない値は仮の値で埋めず、PR 本文に Human の確定項目として書く |
| L-017 | release PRの初回CIで `validate_project.py` が失敗した（`examples/brownfield` の `dat.lock.yaml` の版数0.2.1がDATの0.3.0と不一致）。ローカル検証の実施範囲は公開Evidenceから確認できない | 2026-10-14 PR #186 初回 push `273f888` の spec-lint run 38538541183 が failure（Validate external project adoption）。`254f2c6` で修正し run 38538844027 は success | 1 | candidate | 版数を変更するPRではCITATION・lock・文書例の整合と対象validatorを確認し、実施した検証コマンド・head・結果を記録する。必須CIの失敗は修正後のheadで再確認する |
| L-018 | 独立レビューの依頼文と方針の正本がオーナー判断に追従しておらず、レビュアーが材料の誤りに基づく must を出してレビュー回数が増えた（依頼文に古い記述「datVersion にプラグイン版を使う」が残っていた。方針を変えた後、正本を更新する前に再レビューを出した） | 2026-10-22 merge の PR #230 で独立レビューを 2 観点で計 5 回実施（記録は PR #230 comment 6329253089）。方針の補足は Issue #223 comment 6328933361 | 1 | candidate | 方針を変えたら再レビューの前に正本を更新し、依頼文は正本から作り直す。依頼文に確定したオーナー判断を明記し、それに反する指摘は must に数えない |
| L-019 | エージェント（ワーカー）による `AGENTS.md` の編集が auto mode の分類器に Self-Modification として拒否され、PR の途中で Human による適用に切り替えた | 2026-10-22 merge の PR #230。`AGENTS.md` の追記は Human が commit `852aab7` で適用した | 1 | candidate | 規則変更 PR（`AGENTS.md` / `CLAUDE.md` / `.claude/` など）は Agent が起案と別モデルの独立レビューまで行い、merge は Human が行う。`AGENTS.md` などの編集や push が拒否されたら回避せず STOP し、適用すべき差分を残して Human に依頼する（STOP 条件「ツールや permission による拒否」） |
| L-020 | RunObservation の H1（取得率）で `endedAt` だけが 80% に届かず、判定が INCONCLUSIVE（中間）になった（他の 5 項目は 95% 以上）。未取得の主因は推測・未確認 | 2026-10-23 の測定。21 件・6 リポジトリで `endedAt` 13/21（61.9%）、`model` 20/21、他 4 項目 21/21。`docs/DOGFOODING.md` の OBS-H1 | 1 | candidate | 候補: dat-observe の記録手順で `endedAt` に記録時刻を入れ、変更後の新しい記録で H1 を判定し直す |
| L-021 | RunObservation の集計が再現できなかった: 期間の件数をファイル mtime で数えた、入れ子ディレクトリや重複 observationId を検出しなかった、same-session の助言だけで `independentReview: 'yes'` とした自己矛盾の記録が保存できた | 2026-10-25 の観測記録 45 件に対する 4 本の独立レビュー。対策は PR #250 | 1 | candidate | `docs/OBSERVATION_MEASUREMENT.md` の集計規則（endedAt 基準・store 直下のみ）、validator の independentReview 整合検査、`run_observation.py` の重複・入れ子検出 |
<!-- learning-ledger:generated:end -->

状態は `candidate` / `promoted` / `rejected` のいずれかです。回数1件でも、Frozen artifactやEvidenceの完全性に関わるものは先行して対策してかまいません（L-002、L-004、L-006。L-006 は検証結果の報告が実態とずれたEvidence完全性の問題）。昇格には原則2回以上の観測が必要で、これらはその例外です。

## Measure

`scripts/harness_metrics.py` が読み取り専用で集計します（GitHub API の GET のみ、既定は直近 7 日に merge された PR）。週次 workflow `harness-metrics.yml` は Markdown を Job Summary に、JSON を artifact `harness-metrics`（14 日保持）に出力します。

| 指標 | データソース | 算出方法 |
| --- | --- | --- |
| CI 初回 pass 率 | merged PR の commits と、その commit の check run `validate` | PR 作成時刻以前に commit された最後の commit を最初の head commit とみなし（committer date からの推定。作成後の rebase / force push で別の commit を選ぶことがある）、その `validate` の完了 run のうち最も早いものの conclusion を見る。`success` の件数 ÷ 判定できた件数。run が無い、または `cancelled`・`skipped`・`neutral`・`stale` だけの PR は判定不能として分母から外し、件数を別に出す |
| レビューループ数 | merged PR の review（submitted_at）、review comment、commits | 時刻順に並べ、review / review comment の後に commit が来るたびに 1 ループと数える（連続する指摘は 1 回）。PR ごとの値から中央値と p90 を出す。GitHub に review / review comment として残らないレビュー（口頭・チャット・ローカル指摘）は数えない |
| Learning ledger | `knowledge/learning-ledger.json`（本書の表は生成表示） | 状態別（`candidate` / `promoted` / `rejected`）の件数、回数 2 以上の `candidate`（昇格の検討対象）、Evidence 欠落の ID |

取れない指標:

- **permission prompt 数** — GitHub にも Repository にも記録が残らないため集計しない
- **再発率** — 過去の ledger は日付不明が多く、全発生を日付別に記録していないため直接は出せない。週次棚卸しで前週の集計と比べた「回数」の増分で代替する

## 週次棚卸し

1. 月曜の `harness-metrics.yml` の Job Summary と artifact を Agent が読む（必要なら `workflow_dispatch` で再実行）。
2. 前週との差分を見る: CI 初回 pass 率の低下、レビューループ数の多い PR、回数 2 以上の candidate、Evidence 欠落。
   CI 初回 pass 率は committer date からの推定値で誤分類があり得るため、確定値ではなく傾向として見る。
3. 新しい観測や回数の増加は、Evidence を添えて Learning ledger に追記する（事実の追記は Agent が行える）。
4. 回数 2 以上で Evidence の揃った candidate は、`promoted` への変更と対策（Guard の追加・規則の変更）を draft PR として起案する。規則・Guard の変更は規則変更 PR として、Agent が別モデルの独立レビューまで行い、Human が merge する（「原則」「自律境界」に従う）。
5. 棚卸しの結果（見た run、追記・起案した PR）を PR 本文または Issue に記録する。

## Roadmap

1. **P1** — guidance drift validator、本書、Learning ledger（本PR）
2. **P2** — PreToolUse hookでBash経由のFrozen file書き込みを検出（実装済み）
3. **P3** — 指標の定期集計と週次棚卸し（実装済み。集計スクリプトのテスト `scripts/test_harness_metrics.py` は CI で実行。週次 workflow `harness-metrics.yml`（Job Summary と artifact に出力）。手順は「Measure」「週次棚卸し」。機械可読 ledger と既知の観測日は記録する。未決: 全発生の日時・観測期間を揃えた再発率の定義）
4. **P4（post-EXP-001）** — このハーネス自体をDATの実験として評価する（#21、#59 と関連）
