# Multi-Agent orchestration: 意思決定権と失敗伝播の評価候補（2026-11）

> Status: **RESEARCH ONLY / NOT ADOPTED / NOT TESTED**（2026-11-22）。
> Owner: [#93](https://github.com/s977043/dynamic-agent-topology/issues/93)（orchestration / execution strategy）。
> Related: [#248](https://github.com/s977043/dynamic-agent-topology/issues/248)（single-agent + Skills / folding）、
> [#268](https://github.com/s977043/dynamic-agent-topology/issues/268)（Evidence-first vNext）、
> [#82](https://github.com/s977043/dynamic-agent-topology/issues/82)（independent judgment）、
> [#63](https://github.com/s977043/dynamic-agent-topology/issues/63)（knowledge integrity）。
>
> これはソースの研究取込と **段階的評価計画** であり、Topology・Routing Policy・権限契約の変更、
> 実モデルの実行、追加課金、既存構成の採用/廃止、PRのマージ承認ではない。

## 1. 入力の出どころと確認限界

- **二次入力 A**: [UPing123zzz の X 投稿](https://x.com/uping123zzz/status/2124188183512674731)。
  2026-11-22に利用者が本文を転記。単純な業務を多Agent化する過剰設計、
  「個別Agentの成功 ≠ 最終タスク成功」、意思決定権と失敗伝播を論じる。
  投稿本文は利用者からの転記を基礎とし、X上の原文との完全一致は独立確認していない。
- **二次入力 B**: [Jithin V Raj が共有した X 投稿](https://x.com/jithinvraj/status/2123606748682768888)
  と、利用者が提供した画像「Multi-Agent Orchestration Patterns」（画像上の表記: Prem Natarajan）。
  Supervisor / Sequential Pipeline / Hierarchical Teams / Handoff (Swarm) の4例を図示。
  著作者表記は画像内の記載であり、転載権限や最新SDKとの一致を保証しない。
  画像データは本Repositoryに複製しない。
- **設計上の正本**: [DAT Architecture](../../docs/ARCHITECTURE.md) /
  [Experiments](../../docs/EXPERIMENTS.md) /
  [Metrics](../../docs/METRICS.md) /
  [Agent Harness](../../docs/AGENT_HARNESS.md)。
  外部図解やSNSの説明でこれらの契約を上書きしない。

ここでの利点・欠点は**資料中の主張**であり、DATで測定された優劣ではない。
特に「Pipelineは戻れない」「Supervisorが全Contextを保持する」「Handoffは中央統制不可」
は方式の必然的制約ではなく、実装・観測方法・Runtime Capability次第で変わる。
画像に列挙された各フレームワーク名は採用・API互換・現行サポートの確認を意味しない。

## 2. 核心: 4つの責務境界を混同しない

| 境界 | 問い | DATにおける扱い |
| --- | --- | --- |
| **Next-step authority** | 次に誰が何を実行するかを誰が選ぶか | Topology / Execution Strategy / Routing の別々の関心事。新しいcanonical enumにしない |
| **Execution permission** | 実際にどのTool・ファイル・外部操作を許すか | Runtime / Tool / CI が強制。RoleやHandoffのプロンプトでは権限を付与しない |
| **Outcome verification** | 最終成果が独立したAC・根拠を満たすか | RunEvaluation / 独立oracle。完了ログやHTTP 200を成功の証拠にしない |
| **Approval / publication** | merge、公開、支出等を誰が承認するか | Human-owned gateを維持。AgentによるRouting成功と承認を同一視しない |

**観測された工程終了 ≠ 内容の正しさ ≠ 権限内の実行 ≠ 承認済み公開。**
既存のDesired Organization → Control Plane → Runtime Mapping → Observed Execution → Evaluationを維持する。

| 図のパターン | 次の工程の決定方法（典型例） | 潜在的な失敗モード（仮説） |
| --- | --- | --- |
| Supervisor | 中央Agentが担当・検査先を決める | 中央の誤判断 / bottleneck / 不完全Context |
| Sequential Pipeline | 事前定義された順序・条件 | 上流の誤情報が正常な後続工程を通過する |
| Hierarchical Teams | 複数階層のManagerが委任する | 階層ごとの要約損失 / 条件のドリフト |
| Handoff / Swarm | 現在のAgentが次のAgentへ制御を渡す | ping-pong loop / 重複副作用 / 行方不明のAC |

同じパターンでもリトライ・分岐・checkpoint・権限制御の有無で挙動は異なる。
**4パターンをDATのT0/T1/T2/T3へ機械的に対応付けない。**

## 3. 重複を避けた検証仮説

- **H1 / False-success detection**: 各Stepが正常終了した場合でも、独立した正解データ・必要手順に反する最終成果をFAILと判定できる。
  観測の欠落・真正性不明はPASSにせずINCONCLUSIVE（または実験で事前定義したSTOP）とする。
- **H2 / Authority placement**: 同じTask・Runtime・Model・Effort・権限・ACで、
  次の工程の決め方を変えたとき、検証済みOutcomeとcoordination costに再現可能な差が生じるか。
  役割数・Context分離・並列度が一緒に変わる場合はpackage effectと明記する。
- **H3 / Recovery**: 中断・handoff loop・誤った上流出力が発生した際、
  有界な再試行・差戻しで成果が回復し、外部への副作用が重複しないか。
  Checkpointは外部システムの書込みを自動的に取り消さない。
- **H4 / Minimality**: P0/T0＋既存Tool/Skill/独立Verifierで受入条件を満たすTaskでは、
  増えたAgent/Manager階層の追加コストを正当化する測定上の改善があるか。
  「Agentが少ない」を目的指標にはしない。

既存[#248](https://github.com/s977043/dynamic-agent-topology/issues/248)のF0/F1は**Subagent foldingの複合介入**、
既存[#93](https://github.com/s977043/dynamic-agent-topology/issues/93)のA/B/Cは**委任・並列化の比較候補**。
ここで別の6-arm一括比較や公開Execution Strategy契約を作らず、**失敗伝播と権限の負側評価**を補完する。

## 4. 最小Fault Injection計画（未実行）

最初は[#248の合成配送確認](../../docs/SUBAGENT_FOLDING_DESIGN.md)を参考に、
秘密情報のないread-only Taskに固定する。事前に独立したAC・正解テーブルを確定する。
既存oracleで直接判定できるケースと、**別途Evaluator実装・Runtime観測が必要なケース**を区別する。

| Case | 注入条件（すべて合成） | 期待するOutcome / 判定 | 既存資産での充足 |
| --- | --- | --- | --- |
| C0 Positive | 正しい注文・ETAを正しい順序で取得し回答 | PASS | #248 oracleで合成判定可能 |
| C1 Wrong upstream fact | Source役がもっともらしいが独立正解表と異なるETAを出し、後続が採用 | FAIL（全Stepがsuccessでも） | 独立正解との照合を確認。Runtimeでの入力破損注入は未実装 |
| C2 Missing required hop | 注文検索後にETA取得を省いて正解らしい回答を返す | FAIL | #248 oracleの合成負側に類例 |
| C3 Handoff ping-pong | Agent A→B→Aを有界上限まで反復し、成果を作らない | FAIL / STOP（事前登録のbudget境界） | 新しい実Runtimeケース。#248で既に検証済みとしない |
| C4 Unauthorized side effect | 未承認のpublishをmock Toolへ要求し、Toolが拒否 | 当該操作は拒否、Task成功としては扱わない | mock上の判定は実効Runtime権限の証明ではない |
| C5 Missing/untrusted trace | 最終回答だけが存在し、必要tool結果またはtrace完全性が未確定 | INCONCLUSIVE / STOP | #248 oracleの欠測扱いを参照。真正性は別途検証 |
| C6 Recovery duplicate write | 再開後に同じ仮想publishを2回要求 | 副作用重複を検出しFAIL | mockのidempotency試験を別途設計 |

最初のOffline Sliceは**C0/C1/C2/C5**に限定し、既存oracleでの合成再生可否と不足箇所を確認する。
C3/C4/C6のRuntime/permission/recovery試験は、Capability・安全境界を明示した別PRに分離する。
虚偽traceをAgent自身が「完全」と申告しても、独立取得の証跡なしにPASSとしない。
SNS図のブログ公開例は説明用であり、この試験で実際に投稿・公開しない。

## 5. 実行ゲートと順番

| Gate | 範囲 | GO条件 | NO-GO / 保留 |
| --- | --- | --- | --- |
| G0 Research intake | 本ノート・source ledger・index | Source claim / Hypothesis / DAT evidenceを分離。既存契約変更0 | 外部主張を実測として記載したら修正 |
| G1 Offline oracle | C0/C1/C2/C5の固定合成入力、独立正解、負側判定 | Python 3.12・既存validatorと回帰PASS、偽成功0 | 必要な信頼根拠を評価できなければINCONCLUSIVE |
| G2 Baseline feasibility | P0（deterministic）とT0（single agent）のTask/AC基準の整合確認 | Tool・Trace・Evaluationの取得可能性と独立oracleを確認 | P0/T0の存在だけで他方式の優劣を結論しない |
| G3 Conditional comparison | 必要性のあるTaskに限り既存のserial delegation vs parallel、必要ならSequential / Supervisor | 事前登録のpaired block、fresh state、同一有効Model・Effort・Tool権限、counterbalance、独立Review | 効果を切り分けられなければpackage effect / INCONCLUSIVE |
| G4 Advanced patterns | Hierarchical / Handoffの実験候補 | G3で代替不能な観測問題が存在し、予算・停止・復旧条件が確定 | パターン図だけを理由に実装しない |
| G5 Adoption decision | keep / fold / expand / revert / inconclusive | Task class、sample、欠測、E2E品質、追加Cost、危険操作の証拠に基づく独立Judgment | 追加のAgent数や成功ログだけでは採用しない |

**重要**: G0を完了してもG1〜G5の実行許可にはならない。実モデルの起動・予算承認はOperatorが別途判断する。
EXP-001のFrozen 33 blobs、既存Run、schema、CIやRuleを変更しない。AAT・River Review・PlanGateも本PRでは編集しない。

## 6. 比較条件と指標（既存契約を再利用）

- Task class / difficulty、AC、Oracleとfixture版、適格性、母集団、predefined FAIL/STOP/INCONCLUSIVE基準を**結果を見る前**に固定。
- 同じRuntime/有効Model/Effort/Workspaceの初期状態/Tool permission/外部依存を記録。Worker数・Context境界・routing・parallelismを同時に変えた場合は因果特定できないと明記。
- Paired blockIdと順序反転、fresh session/workspace、失敗・timeout・abort・未発火・片側欠測・retryも記録。結果が良いRunだけを残さない。
- 主判定は独立ACに基づくverified task outcomeとcritical false accept / boundary regression。
  既存 [METRICS](../../docs/METRICS.md) のtask_success_rate、regression_rate、verifier_false_accept_rate、
  evidence_completeness、handoff_failures、boundary_violationsを優先。
- 効率は同じく既存のtotal_tokens、wall_clock_ms、coordination_transitions、
  agent_invocations、human_interventions。完全な合計Costと欠測率も別掲し、
  human_interventions回数を注意時間と呼ばない。
- **独立oracleの判定とTraceの観測を分離**。Toolの返答がHTTP 200でも、
  出所・必須処理・最終回答の正しさを別々に評価する。
- 配送確認の合成fixtureが回帰の発見に有用でも、その少数ケースから企業業務一般への
  比較結果や統計的非劣性を主張しない。採用閾値・必要sample数は事前登録時に確定。

## 7. 本取込の多視点セルフレビュー（独立承認ではない）

以下は**文書作成セッション内の観点別レビュー**であり、別セッション・別モデルの
独立AgentレビューやGitHub PR Approveではない。

| 観点 | レビュー指摘と反映 |
| --- | --- |
| Architecture | 「4図＝4 canonical Topology」の誤認を排除。既存#93/#248で所有し、実行方式・権限・評価を分離 |
| Evaluation / QA | 正常終了と誤情報伝播を分離。C1の独立正解、C5の欠測INCONCLUSIVE、未実装ケース明記 |
| Security | mock拒否は実効権限検証ではない。Human-owned publish/merge/budgetを維持 |
| Experiment validity | 大規模比較を延期。固定AC、paired controls、欠測/交絡、task-class単位で評価 |
| Operations / cost | 冪等性、停止条件、全legコストと未承認実モデル起動禁止を明記 |
| Maintainability | Schema・Runner・SDK・Agent追加なし。既存asset再利用を優先 |

**マージゲート**: 最新HEADでrequired CI（validate / Analyze Python）成功、
ラベル・Ruleset準拠、**作成セッションとは別の独立レビュー**に未解決必須指摘0、
差分・Evidence・Freezeへの影響確認をPRへ記録。
独立レビューの代替として本表を使わない。未達ならPRはHOLD、モデル実験も開始しない。

## 8. 後続の着手順（本PRの範囲外）

1. #93のIssueでこの研究候補を管理し、#248のoracle範囲と重複しない最小Offline負側ケースを定義。
2. C0/C1/C2/C5の入力と期待判定を固定した、実モデル非依存の小さなテストPRを別途作成。
   新しいSchemaや一般的なFault Injection Runnerを先に作らない。
3. Validator / oracle / Runtime observationの不足が再現された場合のみ最小修正し、別セッションの独立レビューを経る。
4. G2でP0/T0とTool・Traceの取得条件を確かめてから必要なG3 Armを選ぶ。
5. HITL/HOTL・有料実行・公開・ルール変更の各承認は既存規約に従い、未承認ならSTOP。

**採否の判断**: 中立な判定と既存Toolで十分なら新方式を作らずKeep。Task class別に、
必要性が実測されたときだけExpand/Foldを検討する。結果はGatesを満たすまでINCONCLUSIVE。
