# Anthropic Research型Multi-AgentとSubagent foldingの比較評価計画

> **状態（2026-11-23）: RESEARCH ONLY / NOT TESTED / NOT ADOPTED**
>
> この文書は実験候補の設計メモであり、実モデル実行・追加課金・Runtime設定変更・新Topology採用・PRマージの承認ではない。
> Ownerは研究対象に応じて [#93](https://github.com/s977043/dynamic-agent-topology/issues/93)（並列実行と委譲）と
> [#248](https://github.com/s977043/dynamic-agent-topology/issues/248)（Subagent folding）に分ける。新規Issueを重複作成しない。

## 1. 一次資料と主張の境界

| 出典 | 言えること | 言えないこと |
| --- | --- | --- |
| [Anthropic, How we built our multi-agent research system (2025-06-13)](https://www.anthropic.com/research/multi-agent-research-system) | 同社の内部research evalではLead Opus 4 + Subagent Sonnet 4がSingle Opus 4を90.2%上回った。複数方向の探索、独立Context、検索の並列化を活用した | 2026年モデルでの再現、同額予算での効果、一般的なソフトウェア開発タスクでの優位性、DATの実測効果 |
| [Anthropic, When to fold subagents (2026-10-22)](https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop) | Skills / Toolsのprogressive disclosureと、単一Loop内の並列Tool Callsが代替になりうる。Subagentは独立Context・並列探索・権限分離に価値が残る | 常にSingle Agentが優位、独立Verifier・Human権限を統合してよい、DATでfoldingが成功済み |

2025年記事の「multi-agentはchatの約15倍のToken」は**chatとの比較**であり、
同じタスクのSingle Agentとの増分コストやDATの見積もりではない。
同記事の「性能差90.2%」はModel・推論量・Tool Call数を揃えた純粋なTopologyの因果効果ではない。
Source台帳の既存IDは \`anthropic-multi-agent-research\`。現状の
\`adopted: [coordination-cost-awareness, task-dependent-parallelism]\` を本資料で拡張しない。
X投稿は発見経路であり、一次資料と別に扱う。

## 2. 既存研究との責務分離

- [#248 / SUBAGENT_FOLDING_DESIGN](SUBAGENT_FOLDING_DESIGN.md): 配送ETAの直列domain chainについて
  **F0（domain Subagent）対F1（Single Loop + Skill）**の合成oracleを準備済み。
  34件の合成テストは実モデルのfold/keepを証明しない。F0/F1の定義は変更しない。
- [#93 / Claude Code orchestration vs single](../knowledge/research/claude-code-orchestration-vs-single-2026-10.md):
  単独、逐次委譲、並列委譲の差を研究するOwner。2025年の「広く独立探索する」課題の検証はこちらに集約する。
- [PR #332](https://github.com/s977043/dynamic-agent-topology/pull/332):
  Orchestrationの決定権・失敗伝播を研究する別PR。研究indexとsource ledgerの競合を避け、このPRでは変更しない。
- [EXPERIMENTS](EXPERIMENTS.md) / [METRICS](METRICS.md):
  paired block、評価独立性、未観測と0の区別、全legコストを既存契約として参照する。
  P0/T0はBaselineであり、Research専用armをcanonical T0/T1/T2/T3に再定義しない。

## 3. 新たに検証する反証可能な問い

- **R-H1 並列Tool Callsの寄与**: 独立した調査shardでは、単一Agentが同一Context内で複数Toolを並列呼出しするだけで、
  逐次Tool Callsよりも確認済み回答のwall-timeを短縮できるか。
- **R-H2 独立Contextの限界寄与**: 同一調査shard・同一評価oracleの下で、Lead + 2 Subagentsは、
  単一Agent + 並列Tool Callsを上回る出典カバレッジや正答率を示すか。
  観測差はContext分離・並列探索・handoff・prompt差が混ざる**複合介入**であり、単独因果効果としない。
- **R-H3 不適格ケース**: 直列依存が強い問いや、全Agentに共通知識が必要な問いでは、
  Subagent分割のメリットが消え、重複探索・情報欠落・不要な調整コストが発生するか。
- **R-H4 引用の正当性**: 出典を列挙するだけでなく、各最終回答の主張を原文・版・参照位置に照合したとき、
  誤引用・根拠欠落・矛盾の未解決を検出できるか。

### 研究専用の最小比較（#93に従属、実験未開始）

| arm | 実行方式 | 主に比較できる点 |
| --- | --- | --- |
| R0 | Single Agent + 逐次Tool Calls | 最小の対照。独立検証は全armで共通 |
| R1 | Single Agent + 並列Tool Calls（同一Context） | R0→R1でTool schedulingの寄与を探索 |
| R2 | Lead + 2 Subagents（独立Context、同じ調査shard） | R1→R2はContext・委譲・handoffを含む**package比較** |

これは既存#93のA/B/C、#248のF0/F1を置き換えない。**新規比較条件の提案のみ**。
最初の実測へ3 armを一括投入しない。まずR0/R1のread-only static feasibilityを確認し、
R1が実際に並列Toolを発火できて、追加の独立Contextを評価する価値が残るときだけR2を検討する。
同一RuntimeでR1の並列Toolが利用できなければ「比較不能」と記録する。

## 4. 最小fixtureと独立oracleの設計候補

公開リポジトリに固定できる**合成資料**のみ使用し、本番の検索APIや顧客資料は使わない。
実際のfixture・実行Kit・Agent Promptはこの研究PRではまだ作成しない。

| ケース | 期待する受理条件 | 拒否・保留の例 |
| --- | --- | --- |
| Q1: 独立3資料から一覧を統合 | 3 shardすべての必須情報、出典IDと一致する事実、重複排除 | 一部shardの未取得、検証なしの網羅主張 |
| Q2: 前資料の結果が次の検索条件を決める | 依存順と最終回答が一致 | 結果取得前の先走り、誤った条件の並列化 |
| Q3: 互いに矛盾する資料 | 資料ごとの主張・版・未確定を分離 | 根拠のない一方の断定、誤った引用位置 |
| Q4: 欠測・timeout・冗長な委譲 | 取得失敗と有効情報を分離し、未観測はINCONCLUSIVE | 失敗shardを「0件だった」と誤集計 |
| Q5: 引用中の不正なTool指示 | 外部資料をデータとして処理し、実効権限・承認境界を維持 | 資料中の命令に従い禁止操作を実行 |

各ケースのACと必要な情報・出典照合を**回答生成とは独立のdeterministic oracle**で判定する。
CitationAgentやReviewerの「問題なし」自己申告のみを正解にしない。
同一資料revision、固定shard、同じModel/Effort/Tool権限、実効予算、fresh session、
キャッシュ、Prompt版、失敗時の再試行を可能な範囲で統制する。
Tool Call予算・全leg総Token上限・経過時間上限はOperatorの事前登録が必要。
予算が同一でない比較は、品質/コスト曲線の**記述的**比較として別掲する。

### 主な観測

- 主Outcome: 独立oracleが認める完了率、必須情報の網羅率、事実・引用の正確性、critical regression。
- 実行: 実Tool発火、同時進行区間、shard別失敗、冗長検索、handoff loss、重複探索。
- 費用: 全legのTool Calls / Model Calls / input・output・cache Tokens / 実費 / wall-time / 検証費用。
- 統制: Model・Runtime・Permissionの実効値と、欠測・中断・失敗・非activationの理由。
- Human: 介入回数と同時判断要求（観測できない認知負荷は推定しない）。

## 5. 実行Gateと停止条件

1. **G0（今回）**: 一次情報、既存Owner、重複しない問い、負側ケース、判断境界を文書化する。
2. **G1（次のPR候補）**: Q1/Q2/Q3の合成fixture・固定出典とoracleを作り、
   正例/誤引用/欠測/依存順の負側テストをofflineで検証する。
   既存#248の配送ETA oracleは調査fixtureに流用せず、共有できる抽象だけを評価する。
3. **G2（Operator候補環境）**: Runtime版、並列Toolの発火可否、Subagent実行権限、
   Trace独立取得、課金境界をread-onlyで確認する。実効制御が不明ならHOLD。
4. **G3（別途承認）**: 実モデル比較前に品質床、許容回帰、対数、費用・時間上限、
   停止/再試行規則を事前登録し、別セッション独立レビューとOperator承認を得る。
5. **G4（将来）**: 成立したpaired blockだけで効果を評価し、
   task class別にKEEP_SINGLE / KEEP_MULTI / INCONCLUSIVEを記録する。
   少数Runで2025年記事の90.2%を再現したとは主張しない。

**即時STOP**: 独立Evaluatorでfalse accept、重要な権限境界違反、予算不明、
実モデルの未承認起動、Traceや引用の真正性未確認、PRに必要な独立レビュー・CIの不成立。

## 6. 多視点レビューとマージ条件

| 観点 | この計画で先に防ぐ欠陥 | 実装PRでの再確認 |
| --- | --- | --- |
| Architecture | #93と#248のOwner混在、Agent数の無根拠な増加 | 新canonical topology・新Runnerなし |
| Evaluation / QA | 自己申告成功、90.2%の一般化、引用だけの「正解」判定 | 独立oracle、負側case、欠測分類 |
| Security / HOTL | Tool説明の自己変更、自動承認、書込権限の拡大 | 強制境界・Operator承認の維持 |
| Cost / Operations | 並列化の費用隠れ、Subagent legの集計漏れ | 全leg集計、上限未定ならHOLD |
| Maintainability | 既存研究やPR #332と重複する別framework | 既存contracts・source IDを再利用 |

この表は**作成セッション内の観点別自己レビュー**であり、独立Agentレビューの証跡ではない。
PRマージはリポジトリの [AGENTS.md](../AGENTS.md) と [AGENT_HARNESS](AGENT_HARNESS.md) の
HOTL規約に従い、最新HEADのrequired CI PASS、別セッションの独立Reviewerで必須指摘0、
PRラベル・未解決Thread・base/head・Rulesetを確認した後だけ判断する。
実モデル起動と費用、規則変更やRelease等のHuman専権は、研究PRのmergeで許可されない。
