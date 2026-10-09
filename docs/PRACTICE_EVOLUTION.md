# Practice Evolution — アジャイルの価値観と実践を進化させる判断指針

> **Status**: Living proposal v0.1 — 実際の開発・運用で検証し改訂する
> **Scope**: DATの開発、OSS運営、知識採用、開発プロセス改善
> **Nature**: 価値観と判断のガイド。新しいGate、実験契約、承認権限ではない

## 目的

DATは、AI Agent Teamの構造を仮説として比較する**仕様・実験基盤**である。この文書は、そのDAT自体を**どう育てるか**の判断指針を扱う。

[アジャイルソフトウェア開発宣言（公式日本語版）](https://agilemanifesto.org/iso/ja/manifesto.html)の4つの価値、および[背後にある原則](https://agilemanifesto.org/iso/ja/principles.html)を尊重する。以下は**DATへの適用解釈**であり、宣言原文やScrumの規定そのものではない。

| 価値 | DATでの適用解釈 |
| --- | --- |
| 個人と対話 | Agentやツール、記録様式の都合より、共同開発者・利用者との対話と意図の理解を重視する |
| 動くソフトウェア | 設計文書だけで前進とみなさず、実行できる小さな変更・validな実測・検証可能な結果を重視する |
| 顧客との協調 | OSS利用者・Contributors・実験Operatorのフィードバックと、真に解きたい問題を確認する |
| 変化への対応 | 計画や既存の定石を仮説として見直す。ただし実験条件や承認境界を独断で変更しない |

**完璧な準備そのものを成果としない。** 安全に得られる最小の有効なフィードバックを早く得て、必要なら修正・回復する。一方、失敗を隠すこと、証拠を作り替えること、不可逆な危害を「Fast Fail」で正当化することはしない。

## 変わらない価値、守る境界、進化する実践

| 層 | DATでの位置づけ | 変更に対する扱い |
| --- | --- | --- |
| **Values / Principles** | 対話、価値、協調、適応、技術的卓越性、誠実な検証 | 短期的な便宜で軽視しない。現実とのずれがあれば解釈を問い直す |
| **Safety / Authority / Experimental integrity** | 秘密情報保護、実効権限、Human-ownedの承認、EvidenceとJudgmentの分離、Feature Freeze、比較可能性 | 実行Agentが勝手に緩和しない。変更には既存の正本と責任者の判断が必要 |
| **Contracts / Decisions** | Schema、Role/Permission境界、実験Control、凍結条件、現行の運用合意 | 所管する正本をEvidence・Review・必要な承認とともに変更する |
| **Practices / Tools** | バッチサイズ、Agentの使い分け、レビュー、preflightの進め方、開発ツール | 小さく試し、効果・負担・副作用でKeep / Adapt / Revert / Deferを選ぶ |
| **Evidence / History** | 実測Run、STOP理由、Trace、CI、Issue/PR、外部研究、当時の判断 | 改ざん・後付けの成功扱いをしない。後続の判断は履歴を残して追記する |

「境界を守る」は現行契約の無断変更を禁じる意味であり、正当なHuman-ownedの方針変更まで永久に禁止する意味ではない。具体的な実行・権限・実験条件は、各責務の正本である[AGENT_HARNESS.md](AGENT_HARNESS.md)、[AGENTS.md](../AGENTS.md)、[EXPERIMENTS.md](EXPERIMENTS.md)、各Experimentの正式Artifactに従う。

## Local Evidence × External Knowledge

**現場経験だけに固執せず、外部の標準・研究・他OSSも盲信しない。**

- **Local Evidence**: DATの現在の実装、CI、実Run、Issue、PR、利用者からの報告。観測済みの事実、経験則、未確認の推論を区別する。
- **External Knowledge**: 公式仕様、アジャイル・リーンの知見、研究、OSS事例。出典、実証範囲、再現性、新しさ、DATの条件との違いを確認する。
- **重み付け**: 双方を検討することは、同じ確からしさを与えることではない。測定条件、一次性、反証可能性、適用条件、リスクで判断する。
- **研究の扱い**: [Knowledge Base](../knowledge/README.md)のSource Claim / Research Candidate / Adopted Principleの区別を維持する。外部記事への賛同だけで実験の採用判断にしない。

重要な変更では、次のうち必要な問いだけを使う。新しい必須提出物は増やさない。

1. **Problem / Outcome**: 何を改善したいか。完了した手順でなく、どの利用価値・実測結果を変えるか。
2. **Facts / Unknowns**: 現行実装・失敗・停止理由から何が確認済みで、何が未確認か。
3. **External insight / Fit**: 外部知見は、どの条件で成立し、DATと何が異なるか。
4. **Smallest safe test**: 最初の有効なSignalを得る、安価で可逆な試行は何か。
5. **Evidence → Judgment**: 実測と評価を分け、必要な判断者が採否・修正・撤回・保留を選ぶ。

### 知識の取り込みを4択で考える

| 選択 | 判断の意味 | DATでの例 |
| --- | --- | --- |
| **Adopt** | DATの条件に合う実績ある方法を、そのまま使う | GitHubの既存機能や既存の標準ツールを使う |
| **Adapt** | 有効な原則を、DATの実験・権限境界に合わせて調整する | Fast Feedbackを凍結実験とは別の開発ループに適用する |
| **Transform** | DAT側の前提、成果指標、進め方そのものを問い直す | 準備項目の充足でなく、validな実測と次の判断を進捗とする |
| **Defer / Reject** | 必要性や適合性が不十分、あるいはリスクが高いので見送る | 効果未検証のAgent常時追加・新Gateの強制をしない |

採用自体も変革自体も目的ではない。何もしない合理性も含め、Evidenceと副作用を見て再評価する。

## 2つのループを混同しない

### A. Repository Development / Practice Evolution（変えられるループ）

```text
Observe → Hypothesize → Small safe change → Verify → Inspect / Adapt
    ↑                                                  |
    └──────────────────────────────────────────────────┘
```

開発作業、Operator手順、情報共有、Issue対応、ツールの使い方を改善する。必要な安全チェックは省略せず、不要な準備や文書の肥大化は減らす。失敗・BLOCK・UNKNOWNは成功扱いにせず、原因・責任者・最小の回復策を見えるようにする。

関連する任意の実践案は[PR #124](https://github.com/s977043/dynamic-agent-topology/pull/124)（Fast Feedbackと助言Agent、**本書作成時点ではDraft提案**）にある。採否は独立して判断し、この原則をもってPR #124を承認済みとは扱わない。

### B. Empirical Experiment / Topology Evaluation（条件を守るループ）

```text
Predeclared controls → Authorized run → Immutable observation
                                      → Independent evaluation → Decision
```

[Experiment Protocol](EXPERIMENTS.md)と各ExperimentのControlが正本。比較中の変更、Cross-arm / Cross-run contamination、事後の基準変更は、学習を速める目的であっても認められない。**実験を途中で変えたい場合は、既存の例外・新Experiment・post-freeze提案として扱う。**

本書作成時点（2026-10-10）のEXP-001はFeature Freeze中である。本書はFrozen artifact、Run prompt、T0/T1条件、検証基準、Retry allowance、Run acceptance、Reviewer判断を変更しない。実Runの開始・再開許可を新たに与えることもない。正本は[EXP-001 Execution](EXP-001_EXECUTION.md)と[Freeze policy](../experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md)。

**Process improvementで得た知見を、凍結中のTreatmentに流し込まない。** 改善できる運用の範囲は、実験条件を変えない箇所に限る。停止時は必須Guardを維持し、勝手に再試行しない。

## 軽量な判断記録と再訪

影響のある知識採用・運用変更では、既存IssueやPRに短く残す。すべての軽微な変更へテンプレート提出を強制しない。

```text
Problem / observed evidence / unknowns:
External insight / fit / limitations:
Option (Adopt / Adapt / Transform / Defer) and why:
Small safe verification / success and stop signal:
Decision / authority / rollback:
Revisit trigger:
```

- **別視点から問い直す**: 標準の無批判な導入、過度な独自化、実験の汚染、安全・承認境界の弱体化、運用負荷の増加を確認する。リスクに応じて既存レビュー手続を選ぶ。形式的に新しい審査を必須化しない。
- **結果で評価する**: 変更後の初回Signalまでの時間、実際に解消したBlocker、回復に要した作業、品質・安全上の副作用などを可能な範囲で観測する。測っていない改善を実証済みと主張しない。
- **再訪する**: 前提の変化、新しい実Run、利用者Feedback、失敗の再発、運用コストの増大、より強い外部Evidenceが生じたときに見直す。
- **History ≠ Current policy**: 過去の失敗や決定を消さず、現行の正本へ必要な修正を行う。効果がない文書・手順は削除や統合も選べる。

## 既存の正本・適用範囲

- [NORTH_STAR.md](NORTH_STAR.md): **何を研究するか**。本書は**DATをどう開発・改善するか**。
- [ARCHITECTURE.md](ARCHITECTURE.md) / [EXPERIMENTS.md](EXPERIMENTS.md): Topology、Control、観測と評価の正式な境界。本書は代替しない。
- [AGENT_HARNESS.md](AGENT_HARNESS.md) / [AGENTS.md](../AGENTS.md): Coding Agentの実行・承認・Guardの現行契約。本書は権限を追加しない。
- [Knowledge Base](../knowledge/README.md): 出典の記録と採用状態。本書はソース台帳を複製しない。

**Non-goals**: 新しいスキーマ、実験Treatment、Agent Runtime、新たな定例・Gate・組織制度、義務的なKPI台帳を作ること。

### 改訂履歴

| Date | Change | To validate |
| --- | --- | --- |
| 2026-10-10 | アジャイルの価値、Evidenceに基づく実践進化、実験との分離をDAT向けに文書化 | 現実の判断が速くなり、証拠品質と承認境界を維持できるか |
