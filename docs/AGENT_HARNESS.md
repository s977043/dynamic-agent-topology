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
| Measure | 再発率、CI初回pass率、レビューループ数、permission prompt数を見る       | 定期棚卸し               |

## Fast Feedback と相談エージェント

[Fast Feedback workflow](FAST_FEEDBACK_WORKFLOW.md) は **開発・Operator作業を小さく検証するための任意の助言フロー**です。EXP-001のFrozen実験条件や本書の自律境界、Run acceptanceは変更しません。必須の安全・権限検査が不合格/不明なら停止します。

- **Agile Coach**（`.claude/agents/agile-coach.md` / `.codex/agents/agile-coach.toml`）: 実測の学習目標、最小の安全な確認、準備の肥大化を見直す。
- **Scrum Master**（`.claude/agents/scrum-master.md` / `.codex/agents/scrum-master.toml`）: impediment、判断待ち、次の一手を可視化する。
- 両ロールともread-onlyの**助言**専用。独立Reviewer、Verifier、Humanの承認権限を持たない。どちらか一方または両方を必要な時だけ呼び、全Run必須の新Gateを作らない。
- 実験用のfresh Codex sessionへ過去Runの出力や相談記録を入力しない。現在のRun実行権限はIssue #15と承認済み手順で判断する。

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

状態は `candidate` / `promoted` / `rejected` のいずれかです。回数1件でも、Frozen artifactやEvidenceの完全性に関わるものは先行して対策してかまいません（L-002、L-004、L-006。L-006 は検証結果の報告が実態とずれたEvidence完全性の問題）。昇格には原則2回以上の観測が必要で、これらはその例外です。

## Roadmap

1. **P1** — guidance drift validator、本書、Learning ledger（本PR）
2. **P2** — PreToolUse hookでBash経由のFrozen file書き込みを検出（実装済み）
3. **P3** — 指標の定期集計と週次棚卸し
4. **P4（post-EXP-001）** — このハーネス自体をDATの実験として評価する（#21、#59 と関連）
