# Grok Bot のチーム運用パターン：DATへの適合性評価（2026-10-12）

## 状態・境界

**Research candidate / Not adopted / Post-EXP-001 only.** このノートは評価候補の記録であり、DAT の実験結果でも契約変更でもない。EXP-001 Feature Freeze 中は `experiments/`、`schemas/`、`roles/`、`topologies/`、pilot 関連ファイルを変更しない。進捗の正本は [#15](https://github.com/s977043/dynamic-agent-topology/issues/15) とする。

関連候補: [#42](https://github.com/s977043/dynamic-agent-topology/issues/42)（実行制御）、[#63](https://github.com/s977043/dynamic-agent-topology/issues/63)（永続知識）、[#88](https://github.com/s977043/dynamic-agent-topology/issues/88)（委譲・引継ぎ）、[#93](https://github.com/s977043/dynamic-agent-topology/issues/93)（複合実行）。

## 出典と確認範囲

- [Grok Bot Tokyo Hackathon スライド](https://speakerdeck.com/taigakono/grok-bot-tokyo-hackathon)（着想元。今回のレビューでは公開ページ本体の直接取得はできず、スライド固有の説明を一次確認済みとは扱わない）
- [xAI公式: Create and manage Bots](https://docs.x.ai/grok-bot/bots)（2026-10-06更新。各Botの固有職務・承認境界・最小人数・共有PC）
- [xAI公式: Skills and routines](https://docs.x.ai/grok-bot/skills-routines-and-automations)（2026-10-06更新。単発タスク→検証→Skill→Routine、トリガー、例外）
- [xAI公式: Approvals, security, and privacy](https://docs.x.ai/grok-bot/approvals-security-and-privacy)（2026-10-06更新。モデルベースAuto Review、共有権限境界）

**Source claim ≠ DAT evidence.** 公式ドキュメントは製品の設計方針を説明するが、複数Agentの成果品質、費用削減、承認強制の完全性を実証しない。

## 既存DATとの照合

| 観点 | 情報源にあるパターン | DAT側の扱い |
| --- | --- | --- |
| 専門Bot | 特定のGoal/Tools/Approvalを持たせ、必要な時だけ増員 | `Role != Model != Permission` を維持。T0/P0と比較する仮説にとどめる |
| 引継ぎ | メッセージ・共有ファイルでコンテキストを渡す | 既存のExecutionRef/Evidenceに沿って入力・出力・状態を記録する候補 |
| Skill→Routine | 単発で成功し検証後に繰り返す | Skillの有効性とRoutine発火の安全性を別々に評価 |
| Memory | 安定情報を記憶、変化する事実は元システムで再確認 | source freshness・provenance・promotion判断を分離 |
| 共有PC | Botごとにファイル・認証情報が隔離されない | roleの分離を権限分離と誤認しない。境界はsandbox/OS/tool権限で強制 |
| Auto Review | 実行前にモデルベースで危険を検査 | 判定補助であり権限強制の証明には使わない |

## 反証可能な仮説（EXP-001終了後）

H1: 同一シナリオ・Model・Effort・予算・入力・制限の下で、専門Agentへの委譲はT0より成功率または完了品質を改善する。追加レイテンシ・費用・引継ぎ失敗は副作用として測定する。**改善なし・信頼区間不明・サンプル不足なら不採用/INCONCLUSIVE**。

H2: 明示的な `Goal / Non-goals / Allowed / Forbidden / Evidence / Escalation` を持つ委譲では、曖昧な委譲より責務逸脱が減る。権限自体はプロンプトに依存せず機械層で制限する。

H3: Memoryの共有状態を固定または初期化しない比較実験は、引継ぎ効果と記憶汚染を交絡させる。実験条件として共有状態の初期化・観測を必須にすることが有効か検証する。

## Cheapest useful verification（凍結解除後のみ）

1. #15の完了判断とFreeze解除を確認する。未解除なら実行禁止。
2. #42 / #88 / #93 の未解決要求と照合し、**新しいroleやcontractを作らず**既存比較へ載せられるか確認。
3. まず既存T0/T1の証跡から、委譲失敗・共有状態・権限逸脱の測定可能性を確認。欠損はUNKNOWNとする。
4. 必要な場合だけ別Issueで対照条件・評価尺度・停止予算・汚染防止を事前登録して実験する。
5. 評価完了後、`knowledge/sources.yaml`・正本・schema・validator等の変更要否を**別レビュー**で判断する。

## 棄却・保留条件

- EXP-001凍結中、未承認の実機起動、信頼境界の緩和、追加ランタイム/SDK導入、Grok Botとの直接連携は行わない。
- 既存Verifier/Reviewer、Skill設計、Routingで十分なら新機構を作らない。
- 他社のSkill本文・コード・配布素材は複製しない。着想のみ利用する。
