# Agent Development Harness

このRepositoryを開発するCoding Agent（Claude Code / Codex など）が、自分の失敗やレビュー指摘から学び、再発防止を仕組みに変えていくための開発ハーネスです。

これはDATの仕様（Topology / Role / Runtime Mapping / Evaluation）ではなく、DATを開発する作業環境の運用です。EXP-001のFrozen artifactや評価semanticsは変更せず、EXP-001 Runにも影響しません（Runは外部のfresh workspaceで実行されます）。

## 原則

- **HOTL（Human-on-the-loop）で運用する。** 人間は事前承認したポリシー（下記の自律境界）の範囲で、監視・停止・事後受理を担います。範囲内の操作は Agent が機械ゲートを満たしたうえで実行し、各段階の結果を Issue / PR に記録します。
- **ハーネスの規則変更は人間が承認する。** `AGENTS.md`、`CLAUDE.md`、`.claude/`、`.codex/`、本書の規則・自律境界・Guard、`scripts/validate_agent_guidance.py` の変更は、Agent が起案（差分・理由・影響範囲・ロールバック案）まで行い、人間が承認して merge します。merge 後に Agent が設定と実効権限を再確認します。Learning ledger への事実に基づく追記は例外として Agent が行えます。
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

## 自律境界

| 操作 | 実行者 | 条件 |
| --- | --- | --- |
| Learning ledger・Issue への記録、draft PR、validator / test、自分の branch への push | Agent | 記録と通知を残す |
| 通常 PR の merge | Agent | 次をすべて満たす: 必須 CI 全 pass、作成者と別セッションの独立レビューで指摘解消、下記「人間が承認」の対象パスを含まない |
| Reviewer Judgment（Run acceptance、disposition の ACCEPT 等） | 独立 Agent Reviewer または人間 | 作成者と別セッション。Frozen 例外など高リスクの判断は別モデルも用いる。記録には runtime・model・session ID・根拠リンクを書く |
| EXP-001 の一回限りの model 起動（retry allowance の消費） | Agent | 手順書の全 Gate と preflight を機械的に検査して合格、Reviewer Judgment が記録済み、retry 未消費、Runtime/Model/Effort が固定、重複起動を防止、attestation・trace・Evidence を保存。異常時は停止し、追加起動はしない |
| ハーネス規則・自律境界・権限・Guard の変更 | 人間が承認して merge | Agent は起案まで |
| Feature Freeze の改訂、Frozen artifact の変更、release / tag、force push、削除、secret | 人間 | — |

人間はいつでも停止・差し戻しができます。停止の指示を受けたら、Agent は進行中の操作を安全な状態で止め、状態を報告します。

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

| ID    | 観測                                                                                                           | Evidence                      | 回数 | 状態      | 対策                         |
| ----- | -------------------------------------------------------------------------------------------------------------- | ----------------------------- | ---- | --------- | ---------------------------- |
| L-001 | Agent guidanceの記述がRepositoryの実態とずれる（fixturesの説明、schema適用範囲、freeze範囲、permissionの効果） | PR #84 / #85 のレビューループ | 4    | promoted  | `validate_agent_guidance.py` |
| L-002 | ask ruleがBash経由の書き込みを検出しない | PR #85 review | 1 | promoted | `.claude/hooks/guard_frozen_bash.py` |
| L-003 | 複数のAgentや操作者が同じbranch・worktree・PRを並行して変更する | PR #85 commit `792102d`、worktree内のhook編集、PR #86 が確認前に別の操作者によりmerge | 3 | promoted | 本書の1 branch 1 Agent rule、`AGENTS.md` のpush手順 |
| L-004 | Frozen fixtureでtest実行時に `__pycache__` が生成される                                                        | PR #85 作業時のlocal観測      | 1    | promoted  | `PYTHONDONTWRITEBYTECODE=1`  |
| L-005 | branch切替の失敗後も `;` で連結したcommit/pushが続き、別PRのbranchへpushされた | PR #85 / #87（commit `9ba8208`） | 1 | candidate | git書き込みは `&&` で連結し、push元branchを確認 |
| L-006 | CIと異なるlocalのPythonでのみ検証し、CI（Python 3.12）で `validate` が失敗した | PR #85 CI run 37541615338 | 1 | promoted | `AGENTS.md` の Python 3.12 検証ルール |
| L-007 | push/API の権限エラーを回避するため、ワーカーが `gh auth switch` で active アカウントを変更した。active アカウントは同一マシンの全セッションで共有されるため、並行セッションの書き込み先が変わり得る | PR #110 作業時（2026-10-08） | 1 | candidate | アカウント切替はせず、コマンド単位で認証トークンを渡す。委託プロンプトの境界に明記 |
| L-008 | Agent の Edit 後に走る自動整形 hook が、レビュー済み SHA-256 表を含む文書の表の空白を書き換えた（ワーカーが気づき HEAD から作り直した） | PR #110 作業時（2026-10-08）、`docs/EXP-001_RETRY_T1_R01.md`。PR #112 作業時の再発（PR #112 本文に記録） | 2 | promoted | `.prettierignore`（併せて、編集後に意図した行以外の差分が無いことを `git diff` で確認する） |
| L-009 | 独立 Reviewer の判断が判断材料不足で誤判定・無効化した（基準文書の取得がネットワークで失敗したまま ACCEPT を出した、Issue コメント未提供で前提を確認できず NO-GO、指定外参照の禁止と Reviewer 起動時の作業ディレクトリ確認が衝突して判定無効） | PR #130 の Run acceptance レビュー（Issue #15 comment 6106366753 に至る 4 回） | 3 | candidate | 判断材料（基準文書・関連 Issue コメント・PR 本文と diff・Artifact）を 1 ディレクトリにまとめ依頼書と共に渡す。作業ディレクトリの確認は許可し、禁止範囲はその外とする |
| L-010 | 『指摘ゼロ』を完了の定義にした机上レビューの往復が収束せず（15 回以上）、Run が進まなかった | PR #110・#116・#121・#122 のレビュー往復、本番スクリプトの NO-GO 3 回 | 2 | candidate | 必須を安全・秘密値・プロトコル違反・回収不能の 4 分類に絞り、推奨は事後改善に回す。同箇所の指摘が続く場合はドライランやリハーサルで実際に動かして確かめる |

状態は `candidate` / `promoted` / `rejected` のいずれかです。回数1件でも、Frozen artifactやEvidenceの完全性に関わるものは先行して対策してかまいません（L-002、L-004、L-006。L-006 は検証結果の報告が実態とずれたEvidence完全性の問題）。昇格には原則2回以上の観測が必要で、これらはその例外です。

## Measure

`scripts/harness_metrics.py` が読み取り専用で集計します（GitHub API の GET のみ、既定は直近 7 日に merge された PR）。週次 workflow `harness-metrics.yml` は Markdown を Job Summary に、JSON を artifact `harness-metrics`（14 日保持）に出力します。

| 指標 | データソース | 算出方法 |
| --- | --- | --- |
| CI 初回 pass 率 | merged PR の commits と、その commit の check run `validate` | PR 作成時刻以前に commit された最後の commit を最初の head commit とみなし（committer date からの推定。作成後の rebase / force push で別の commit を選ぶことがある）、その `validate` の完了 run のうち最も早いものの conclusion を見る。`success` の件数 ÷ 判定できた件数。run が無い、または `cancelled`・`skipped`・`neutral`・`stale` だけの PR は判定不能として分母から外し、件数を別に出す |
| レビューループ数 | merged PR の review（submitted_at）、review comment、commits | 時刻順に並べ、review / review comment の後に commit が来るたびに 1 ループと数える（連続する指摘は 1 回）。PR ごとの値から中央値と p90 を出す。GitHub に review / review comment として残らないレビュー（口頭・チャット・ローカル指摘）は数えない |
| Learning ledger | 本書の「Learning ledger」表 | 状態別（`candidate` / `promoted` / `rejected`）の件数、回数 2 以上の `candidate`（昇格の検討対象）、Evidence 欠落の ID |

取れない指標:

- **permission prompt 数** — GitHub にも Repository にも記録が残らないため集計しない
- **再発率** — ledger に日付列が無いため直接は出せない。週次棚卸しで前週の集計と比べた「回数」の増分で代替する

## 週次棚卸し

1. 月曜の `harness-metrics.yml` の Job Summary と artifact を Agent が読む（必要なら `workflow_dispatch` で再実行）。
2. 前週との差分を見る: CI 初回 pass 率の低下、レビューループ数の多い PR、回数 2 以上の candidate、Evidence 欠落。
   CI 初回 pass 率は committer date からの推定値で誤分類があり得るため、確定値ではなく傾向として見る。
3. 新しい観測や回数の増加は、Evidence を添えて Learning ledger に追記する（事実の追記は Agent が行える）。
4. 回数 2 以上で Evidence の揃った candidate は、`promoted` への変更と対策（Guard の追加・規則の変更）を draft PR として起案する。規則・Guard の変更は人間が承認して merge する（「原則」「自律境界」に従う）。
5. 棚卸しの結果（見た run、追記・起案した PR）を PR 本文または Issue に記録する。

## Roadmap

1. **P1** — guidance drift validator、本書、Learning ledger（本PR）
2. **P2** — PreToolUse hookでBash経由のFrozen file書き込みを検出（実装済み）
3. **P3** — 指標の定期集計と週次棚卸し（実装済み。集計スクリプトのテスト `scripts/test_harness_metrics.py` は CI で実行。週次 workflow `harness-metrics.yml`（Job Summary と artifact に出力）。手順は「Measure」「週次棚卸し」。未決: 再発率を直接出すための ledger への日付列追加は、`harness_metrics.py` の解析と合わせて別途検討）
4. **P4（post-EXP-001）** — このハーネス自体をDATの実験として評価する（#21、#59 と関連）
