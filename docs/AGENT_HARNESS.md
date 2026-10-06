# Agent Development Harness

このRepositoryを開発するCoding Agent（Claude Code / Codex など）が、自分の失敗やレビュー指摘から学び、再発防止を仕組みに変えていくための開発ハーネスです。

これはDATの仕様（Topology / Role / Runtime Mapping / Evaluation）ではなく、DATを開発する作業環境の運用です。EXP-001のFrozen artifactや評価semanticsは変更せず、EXP-001 Runにも影響しません（Runは外部のfresh workspaceで実行されます）。

## 原則

- **人間がmergeを持つ。** Agentは記録と提案までを自律的に行い、mergeは人間が判断します。
- **ハーネス自身の変更は人間レビュー必須。** `AGENTS.md`、`CLAUDE.md`、`.claude/`、`.codex/`、本書、`scripts/validate_agent_guidance.py` をAgentが自分の判断だけで緩めません。
- **Evidenceのない学びは昇格しない。** PR / commit / CI run / Issueへのリンクがない記録は候補のままです。
- **Proseより機械的なGuardを優先する。** 昇格先は CI・validator → hook → permission設定 → `AGENTS.md` の文章 → skill の順に検討します。

## ループ

| 段階    | 内容                                                                    | 担い手                   |
| ------- | ----------------------------------------------------------------------- | ------------------------ |
| Observe | CI失敗、レビュー指摘、validator失敗、permission拒否、ユーザー訂正を拾う | Agent                    |
| Learn   | 下の Learning ledger に、Evidence・発生回数・状態を追記する             | Agent                    |
| Promote | 同種が2回以上でEvidenceが揃ったら、改善PRを出す                         | Agentが提案、人間がmerge |
| Enforce | 採用した対策をCI / hook / 設定として常時有効にする                      | Harness                  |
| Measure | 再発率、CI初回pass率、レビューループ数、permission prompt数を見る       | 定期棚卸し               |

## 自律境界

| Agentが自律的に行ってよい | 人間の承認が必要                             |
| ------------------------- | -------------------------------------------- |
| Learning ledgerへの追記   | merge、release、tag                          |
| 改善PRのdraft作成         | Guard（hook・permission・`AGENTS.md`）の変更 |
| validator / testの実行    | Feature Freezeの改訂、Frozen artifactの変更  |
| 自分のbranchへのpush      | 他Agentが担当するbranchへのpush、force push  |

1 branchは1 Agentが担当します。同じbranchに別Agentがpushしている場合は、上書きせず最新のheadに積み直し、pushは `--force-with-lease` に限ります。

## Guard

| Guard                                      | 状態       | 検出するもの                                                                                                                |
| ------------------------------------------ | ---------- | --------------------------------------------------------------------------------------------------------------------------- |
| `scripts/validate_agent_guidance.py`（CI） | 有効       | `AGENTS.md` / `CLAUDE.md` が参照する存在しないpath、`freeze.yaml` と `.claude/settings.json` のask ruleのずれ（漏れ・過剰） |
| `.claude/settings.json` ask rule           | 有効       | Claude CodeのEdit/WriteによるFrozen fileの変更                                                                              |
| `PYTHONDONTWRITEBYTECODE=1`                | 有効       | Frozen fixture内への `__pycache__` 生成                                                                                     |
| PreToolUse hook                            | 予定（P2） | Bash経由のFrozen fileへの書き込み                                                                                           |

## Learning ledger

| ID    | 観測                                                                                                           | Evidence                      | 回数 | 状態      | 対策                         |
| ----- | -------------------------------------------------------------------------------------------------------------- | ----------------------------- | ---- | --------- | ---------------------------- |
| L-001 | Agent guidanceの記述がRepositoryの実態とずれる（fixturesの説明、schema適用範囲、freeze範囲、permissionの効果） | PR #84 / #85 のレビューループ | 4    | promoted  | `validate_agent_guidance.py` |
| L-002 | ask ruleがBash経由の書き込みを検出しない                                                                       | PR #85 review                 | 1    | candidate | P2 hook                      |
| L-003 | 複数Agentが同じbranchへ同時にpushする                                                                          | PR #85 commit `792102d`       | 1    | candidate | 本書の1 branch 1 Agent rule  |
| L-004 | Frozen fixtureでtest実行時に `__pycache__` が生成される                                                        | PR #85 作業時のlocal観測      | 1    | promoted  | `PYTHONDONTWRITEBYTECODE=1`  |

状態は `candidate` / `promoted` / `rejected` のいずれかです。回数1件でも、Frozen artifactやEvidenceの完全性に関わるものは先行して対策してかまいません（L-004）。

## Roadmap

1. **P1** — guidance drift validator、本書、Learning ledger（本PR）
2. **P2** — PreToolUse hookでBash経由のFrozen file書き込みを検出
3. **P3** — 指標の定期集計と週次棚卸し
4. **P4（post-EXP-001）** — このハーネス自体をDATの実験として評価する（#21、#59 と関連）
