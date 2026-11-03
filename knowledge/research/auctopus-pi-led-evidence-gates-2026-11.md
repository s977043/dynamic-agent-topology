# Auctopus: PI-ledの批判的判定ゲートと反証実験（調査・検証候補）

- 状態: **RESEARCH ONLY / NOT ADOPTED / NOT VALIDATED IN DAT**
- 調査日: 2026-11-03 JST
- 追跡: [Issue #295](https://github.com/s977043/dynamic-agent-topology/issues/295)
- DAT参照基準: main 95a4c8dad9564c1235108c0c1225ef（2026-11-03取得）
- 範囲: 外部論文と実装の出典固定・適用仮説・最小オフライン検証計画。現在のDATのTopology/Role/Policy/Schema/Runtime/Skillを変更しない。

## 1. 一次資料・固定条件

1. Mansouri, Kimura, Koga and Arai, *Collaborative AI agents for autonomous experimental research with solid-state quantum spins*（2026-10-29、arXiv:2610.40589v1、17頁5図、**査読前**）  
   https://arxiv.org/abs/2610.40589
2. E-zClap/auctopus、v1.0.0、MIT、commit bbb98e3711a8f18a6ca70d4d6787ecaadac9490f  
   https://github.com/E-zClap/auctopus/tree/bbb98e3711a8f18a6ca70d4d6787ecaadac9490f
3. 実装の[Workflow](https://github.com/E-zClap/auctopus/blob/bbb98e3711a8f18a6ca70d4d6787ecaadac9490f/docs/workflow.md)、[Safety](https://github.com/E-zClap/auctopus/blob/bbb98e3711a8f18a6ca70d4d6787ecaadac9490f/docs/safety.md)、[README](https://github.com/E-zClap/auctopus/blob/bbb98e3711a8f18a6ca70d4d6787ecaadac9490f/README.md)。

論文は著者の実験報告であり、DAT側での再現・第三者の査読・独立追試の代わりではない。公開リポジトリのdry-runはmockモデルによるオーケストレーションの確認で、論文の研究結果を再現しない。論文時のprompts/domain packは公開パッケージに同梱されず、実験データ・分析コードは著者に合理的な依頼をした場合の提供と記載されている。

## 2. Source Claim（論文・実装が報告すること）

- 六つの主役割: 複数の提案者、PI、計算研究者、実験担当、manager、独立査読者。別途safety agentと実験feasibility reviewを設け、文書交換と判定で段階を進める。
- 提案選定では約30時間に75件を却下した。managerが繰り返し却下された発想を探索除外リストに整理し、方向を変更した。
- ダイヤモンドNV中心の量子スピン集合を対象に、一定のパルス条件と「一つのパルス列の間でスピンごとの誤差が固定」という前提で、長さL以下のパルス列の応答を予測するには **L²+1の独立な校正設定が必要十分**と導出。L=3では10設定。10回のショットで済むという意味ではない。
- TSUBAME 4.0で計算検証。実機では4つのheld-out targetを使用し、予測されたcontrastと実測値が事前の許容範囲内で一致し、指定した補間ベースラインの予測と区別された。
- 初回実験は予測精度の条件を満たしていたが、独立のglobal-phase/reference controlsが失敗。照明点灯に同期する信号変化を含むdriftを見つけ、PIが結果を**inconclusive**と判定。既定の合否基準を緩めず測定方法を改訂し、再取得した。
- 人間は装置を構築・記述し最大電圧/出力などの安全制約を設定。論文著者貢献欄には研究構想、実験基盤の構築、データ解析、原稿執筆/改訂/監督も記載される。「人間の作業は電灯と組立だけ」という研究全体の描写は過度な要約。
- 公開AuctopusはPythonの研究オーケストレーターで、OpenAI/Anthropic API、SSH先のCodex/Claude Codeを想定。通常の実行方式には対話承認・sandbox回避設定がある。safety/human approval checkpointを持つが、モデルのsafety承認は装置の物理的安全を保証しない。

**外部研究が証明していないこと:** PI-led Multi-Agentが同一taskで単一Agent+Skillsより高品質・低コスト、他分野で同じ新規発見を繰り返せる、または論文の法則が全量子現象に一般化すること。

## 3. DAT解釈（実験候補・未採用）

成果の転用対象は「Agent人数」ではなく**反証可能な品質判定の境界**である。

| Auctopusで観測された仕組み | DATにおける検証する候補 | 既存契約と区別する点 |
| --- | --- | --- |
| PIが提案を棄却し探索方向を変える | 批判履歴に基づく次候補選択の有効性 | Routing Policyや権限を自動変更しない |
| 論理/計算を別Contextで確認 | 独立Verifier/Reviewerの増分価値 | Reviewer ≠ Verifier、独立会話 ≠ 強制隔離 |
| 事前固定の予測とcontrol | target PASSでもcontrol FAILなら保留 | Evidence ≠ Judgment、後出し採点を禁止 |
| 実機でdrift・再取得 | 失敗を隠さず方法を修正し再検証 | 再試行はOperator/既定Gateを迂回しない |
| 最終成果と判定履歴を保存 | Audit trailと完成フラグを区別 | Workflow done ≠ verified scientific success |

重複/所有権: #248はSubagent folding、#244はhard-task T0/T1、#293は手動handoff可否、#268はvNextの利用体験。#295は**evidence gateのfail-closed性とPI-ledの増分価値**に限定し、既存実験を実施済みとみなさない。

## 4. 最小検証（P1：無課金・failure first）

新しいruntime/Schema/Skillを先に作らず、現行DATのvalidator/比較・判断プロセスが次の決定を保持できるかを確認する。fixtureとoracleは結果閲覧前に固定する。下表は**候補の期待動作**であり、現在のcanonical enumや実行結果ではない。

| Case | 固定入力 | 期待する判定境界 |
| --- | --- | --- |
| C1 | target PASS、controls/事前固定/出典が有効 | 条件を満たす場合だけ成功候補 |
| C2 | target PASS、control FAIL | **ACCEPT禁止**、原因確認/保留 |
| C3 | target PASS、control未取得 | **ACCEPT禁止**、欠測と表示 |
| C4 | target FAIL、controls有効 | 結果不支持、成功扱い禁止 |
| C5 | drift発生・実験方法改訂 | 元Runは保留、新Runは別attemptとして扱う |
| C6 | target閲覧後に許容閾値を変更 | 事前登録違反、採用根拠から除外 |
| C7 | 査読者に必要なRaw Evidenceなし | 独立判定の限界を明示、保証した扱い禁止 |
| C8 | arm間でModel/Effort/Runtime/権限が不一致 | 因果比較はINCONCLUSIVE |

手順:
1. 現行DATのArtifact、validator、decision rule、independent oracleの担当範囲を読み、上表に対応できるものをマッピング。未サポートの項目はunknownとする。
2. 合成fixtureでpositive/negativeを1回ずつ監査し、実行コマンド・exit code・oracle版・修正前後の差・欠測を保存。Mock判定を実モデル品質と扱わない。
3. 新実装が必要なgapが再現した場合だけ、P1用の隔離Spikeで最小修正を提案。既存EXP-001凍結33blobを一切変更しない。
4. 結果は技術的な検出可否と、PI-led導入価値を分けて判定。P1だけでMulti-Agentを採用しない。

### 初回の静的契約マッピング・負の対照（2026-11-03 JST）

DAT mainの次の既存ファイルを参照した。これは現行契約の**静的確認とJSON Schema単体のローカルprobe**であり、Repo全validatorや実モデルの評価を実行したわけではない。

- schemas/evaluation.schema.json: verdictは pass/fail/inconclusive。evidenceにはrequiredGates、passedGates、completeness、任意のverifierFalseAcceptがある。**GateごとのID・時系列・provenanceは必須項目ではない**。
- schemas/execution-trace.schema.json: verify/evidence/reviewなどのeventと任意details/artifactがある。個別controlは記録できるが、記録内容とverdictの自動整合を表現するcanonical fieldではない。
- scripts/validate_experiments.py: acceptanceCriteriaPassed <= acceptanceCriteriaTotal、passedGates <= requiredGates、Trace/EvaluationのID・Runtime/Model/Effort・要約値整合、paired control一致を検査する。**passedGates < requiredGates と verdict=pass の組み合わせは、このスクリプトに直接の拒否条件がない**。
- scripts/compare_paired_blocks.py: arm間のRuntime/Model/Effort不一致と条件の重複・欠落をinvalid blockにする（C8を既存機構で扱える）。
- docs/EXPERIMENTS.md: evidence/実際の拒否/採用判断を区別し、必要なfail-closedはExperiment固有のDecision Ruleとindependent oracleで評価する方針。

ローカルprobe（実DAT JSON Schemaの2026-11-03 main blobを使用、Python jsonschema Draft202012Validator、mockのRunEvaluationを各ケースで変化させる。実行結果はいずれも同一schema入力で確認）:

| 入力差分 | スキーマ検証 | 読み取れること |
| --- | --- | --- |
| requiredGates=2、passedGates=2、taskSuccess=true、verdict=pass | PASS | 正常対照 |
| requiredGates=2、passedGates=1、taskSuccess=true、verdict=pass | PASS | control未通過をSchema単独では拒否しない |
| requiredGates=2、passedGates=0、taskSuccess=true、verdict=pass | PASS | control全欠測相当もSchema単独では拒否しない |
| requiredGates=2、passedGates=1、taskSuccess=true、verdict=inconclusive | PASS | VerdictとOutcomeの一貫性をSchemaだけで強制しない |
| verdict=approve（enum外） | FAIL | Schema検証が動作している負の対照 |

**判断:** schema-levelでの結果であり、実験固有oracleやOperator/Reviewer Gateを含む全体のfail-closed能力は未測定。DATはAgent Runtimeではないため、グローバルSchemaが常に判定を拒否するべきと即断しない。次のP1は「既存の実験Decision Ruleと独立oracleがC2/C3でfalse acceptを阻止できるか」を対象とし、Schemaやvalidatorの変更は**実際の再現gapが生じた場合のみ**提案する。

## 5. 後続の比較と事前登録ゲート

次の実測は別のOperator許可が得られた場合のみ。比較対象をT0+同じgate・oracleとPI-led候補に揃え、gate有無による改善とRole/Contextの改善を混ぜない。可能なら独立Verifierあり/なしも分け、必要なrole数は効果で判断する。

- task registry / difficulty / train-test-regression / sample size /判定閾値 /停止条件を結果閲覧前に固定。
- 同一task、AC、repo revision、Runtime、Model、Effort、Tool、permission、budgetと、arm別fresh workspace/sessionを管理。実効値・隔離が不明ならINCONCLUSIVE。
- 対照条件と順序をcounterbalanceし、独立oracleと負の対照を残す。
- Outcome: 独立verified success、重大false accept、regression、control不整合、安全違反。Cost: tokens/USD/latency、人間active attention、欠測/再試行/中断を記録。
- 有効性が同等でcoordination costが増えるなら**Keep T0**。差が不明なら**Defer**。局所的な改善がある場合もtask class限定の提案に留める。

## 6. Safety / Rejection / Freeze

- AuctopusをDATへ依存追加・コード取込み・Agent実行・外部設備接続しない。公開OSSのデフォルトのdangerous flagsを継承しない。
- 実API起動・追加課金と予算承認はOperator専権。human-only権限、モデル外の実際の拒否制御とAuditを維持。
- sourceが撤回/更新された場合は再評価。必要な独立Evidenceが欠ける、既存検証ですでに十分、費用対効果が不明なら採用を保留。
- EXP-001 Feature Freeze完了の歴史的スナップショットを不変とする。新しい研究で過去の決定を書き換えない。
- 本Research Noteを追加してもDATのcanonical contractやAuctopus採用を意味しない。

## 7. 次のアクション（Issue #295）

- [x] 論文とOSSの出典・限界・適用条件の調査記録
- [x] C1〜C8のうちSchema/validator/paired比較への初回静的マッピング（全経路の検証は未完了）
- [ ] P1 failure-first fixtureの安全な実施・機械検証
- [ ] 独立セッションレビュー（対象commitと実施範囲を記録）
- [ ] 課金・実モデル比較は事前登録とOperator承認後
