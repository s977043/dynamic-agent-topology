# 司令官型オーケストレーション vs 単一Agent: Claude Code公式機能に基づく比較候補

> Status: **RESEARCH ONLY / NOT ADOPTED**（2026-10-20 JST）。Owner: [#93](https://github.com/s977043/dynamic-agent-topology/issues/93)（選択的multi-agent/compound execution）。関連: [#88](https://github.com/s977043/dynamic-agent-topology/issues/88)（model escalation）、[#82](https://github.com/s977043/dynamic-agent-topology/issues/82)（独立Judgment）、[#201](https://github.com/s977043/dynamic-agent-topology/issues/201)（elapsed-time signal）。
> この文書は**比較設計の候補**。新規実験の事前登録、Operatorの実行許可、採用、Release承認ではない。EXP-001のFreeze・18 Run・Keep T0は不変。

## 1. 入力・一次ソース・証拠の強さ

- 二次入力: [X投稿](https://x.com/drake5112/status/2112302773488455732)について利用者が転記した「単独Opus 5.5は進捗2%、司令官型は2分で全工程完了」という説明。**元実験のタスク、進捗2%の定義、計測開始/終了、成功oracle、Runtime/Model/Effort、並列数、ログ、再試行、コスト、比較回数は未確認**。速度改善の実測結果・再現性のあるベンチマークとは扱わない。
- 一次資料（2026-10-20確認）: [Model configuration](https://code.claude.com/docs/en/model-config) — `opusplan` は**Plan Mode中Opus / 実行中Sonnet**というmodel alias。常に複数Agentを起動する設定でも、全タスクでPlan Modeを必ず通る設定でもない。Provider・CLI版によって解決モデルが変わる。
- [Subagents](https://code.claude.com/docs/en/sub-agents) — 独立contextの委任、tool/permission/modelの設定、結果を親へ返す実行方式。**Subagentの宣言≠呼び出し/実効制限**。
- [Agent teams](https://code.claude.com/docs/en/agent-teams) — 独立セッション間の協調・共有タスク。既定では無効でexperimental flagが必要。非対話`-p`ではteammateをspawnしないため同じ実験条件として扱わない。単一セッションよりToken負荷が高い。
- [Dynamic workflows](https://code.claude.com/docs/en/workflows) — workflowスクリプトでsubagentを制御。対話入力の`ultracode`キーワードと`/effort ultracode`は別の入口。キーワードは`-p`のpromptで発火しない。非対話でのWorkflow起動には明示のpermission/effective runtime確認が必要。`/effort ultracode`の常時化は費用・時間・警告挙動を変えるため**検証前に採用しない**。
- 公式資料に「Opus単独2%、司令官で2分」の対照実験・一般化可能な優位性は**確認できていない**。SNSの「全社員に有効」「必ず時間が増える」は反証可能な仮説としてのみ扱う。

## 2. DAT既存研究との差分（重複防止）

- [#206](https://github.com/s977043/dynamic-agent-topology/pull/206) は**OpusPlan/Haiku Scout/Opus Critic**によるModel・Role・Judgeのablation候補（Draft）。本案は**Execution Control / topology / coordination cost**の差を扱い、Roleの強さやmodel切替を同時に変更しない。
- [#194](https://github.com/s977043/dynamic-agent-topology/pull/194) はcompound・recovery・shadow gateの先行Draft。本案を別Runtime実装として並走させず、#93の試験計画で統合/棄却する。
- [#208](https://github.com/s977043/dynamic-agent-topology/pull/208) はpstackのModel/Role/Effort研究。本案は外部PluginもSkillも取り込まない。
- DAT原則はP0/T0を第一級Baselineとする。「司令官」という名称は新Roleの根拠ではなく、既存のPlanner / Worker / Reviewer / VerifierとControl Planeの配置を観測する**比較対象の説明**。

## 3. Falsifiable hypothesis と負側ケース

- **H1（並列化）**: 相互に独立し検証oracleがある中〜高複雑度Taskでは、同一Model/同一Effort/同一予算で、必要な品質床を維持した並列Subagentのwall-clockがT0より短くなることがある。
- **H2（選択性）**: 依存が強い単純TaskではT0のほうが、multi-agent候補より検証済み成功1件あたりの総Token、作業時間、Human監督負荷が同等以下となる。
- **H3（権限）**: 役割分担/生成workflowは宣言した制限だけでは実効権限・独立Judgmentを保証せず、runtime negative testと別セッション判断が必要。
- **対抗仮説**: 完了時間差が起きても、モデル差、キャッシュ、tool/API待ち、retries、並列数の違い、低い成功基準、テスト漏れで説明できる可能性がある。

## 4. 最小比較（実験は未開始）

| Arm | 変更対象 | 統制・注意 |
| --- | --- | --- |
| A: T0 | Single Agent、既存の外部CI/独立Review経路を固定 | 基準値。途中で新しいCoordinatorを追加しない |
| B: serial delegation（候補、**T0ではない**） | 親Agentが固定した複数Work Unitを、同数のSubagentへ**逐次**委任 | Aとの差分は委任+context+agent countを含む**package effect**。AとBを「並列化効果」と呼ばない |
| C: parallel delegation（候補、**T0ではない**） | Bと同じWork Unitを同数・同モデル・同ツールのSubagentへ可能な範囲で並列委任 | Bとの差分は**scheduling policy**を原則唯一の操作因子とし、実際の実行重複時間と合流時間も測定 |
| D: Agent teams | teammate間の直接通信/共有タスクを許す | Cとの差分は協調方式の**package**。interactive制約・spawn挙動が揃わない場合は因果比較しない |
| E: Dynamic workflows | Claude Code workflowによる制御 | Cとの差分はprogrammatic orchestrationの**package**。workflow生成・修正・起動時間も含める |

**一括5-armを先に要求しない。** A→B（委任・Context分離を含むpackage）→C（同一Work Unitのschedule差）を最小の前向きpaired comparison候補とし、独立依存関係のあるTaskだけD/Eを次段階として検討。A以外をT0のままと呼ばず、BとCでWorker数や分割結果が異なればC−Bを並列化単独の因果効果とは主張しない。OpusPlan/Model Routing・Critic・Advisorは別の因子で、ここに同時追加しない。Agent teamsが非対話で使えない環境ではDを無理に実行しない。

### 事前登録する統制・観測

1. task class（小規模逐次 / 独立分割可能 / 共有変更の競合 / 安全境界を含む）、同じcommitのsecret-free fixture、同じAC、deterministic test / negative oracle、held-out評価。各classの適格/不適格と**B/Cで利用する固定Work Unit分割・同一の引き継ぎ情報量・依存DAG**を開始前に決める。
2. 実Runtime版、provider、解決済model ID、effort、context、tool権限、cache、外部依存、workspace、run budget、並列数上限、timeout、retry policyを記録。同blockで可変なのは比較対象のexecution policyだけ。fresh session/workspace、順序counterbalance、paired block IDで比較。
3. 実際のAgent spawn / delegation / task partition / overlap、workflowの発火、計画生成時間、tool呼び出し、承認/拒否、自己中断、最終成果をTraceで観測。**Declared topology != observed execution**。未観測を0にしない。
4. `taskSuccess`・回帰・境界逸脱・False Acceptを独立oracleで評価。探索の`進捗%`やAgentの「完了」申告は成功根拠にしない。
5. wall-clockはキュー待ち・workflow生成/起動・並列join・retries・独立Review/CI・Human待ちを区分し、ユーザー視点の**verified delivery elapsed**を主指標、Agentの処理時間を副指標とする。cached/uncached tokens、費用、Human interventions/concurrency、cross-session引継ぎも計測。
6. quality floor・最大支出・Human-owned actionの停止条件を事前固定。成功例だけを選ばない。pilotの小標本で一般化せず、効果が不明なら**INCONCLUSIVE/DEFER**、費用増や安全性悪化なら**Keep T0 / REJECT**。

### DATの計測契約との整合（第2ループ）

- 現行`RunEvaluation.efficiency.wallClockMs`と`docs/METRICS.md`の`wall_clock_ms`は**実行Run全体**の実測値。提案する`verified delivery elapsed`はHuman依頼〜外部Review/CI受理までの**別の観測指標候補**であり、既存fieldを意味変更・再計算しない。新Schema fieldもこの研究PRでは追加しない。
- `verified delivery elapsed`にはReviewer待機・人間の対応遅延・キュー待ちが混入する。開始イベント、必要なGate、外れ値、計測できなかった時間帯、運用由来の待機を事前登録し、因果比較には**run wall-clock**と**end-to-end delivery elapsed**を別々に報告する。同期できない時計や未観測イベントは`unknown`としてINCONCLUSIVE扱い。
- `human_interventions`は回数のみ。作業者の集中時間や認知負荷は直接測れないため、`human review minutes`を取る場合は別途計時し、その測定品質と中断/同時監督の交絡を開示する。
- `Model/Effort`は親と子を含めた**有効解決値**をRunごとに固定・観測し、`Cache`は温まり方を一致または交絡として記録する。A/B/Cの総Tokenや費用は追加Session分も合算する。部分的な成功・失敗・中止のRunを分母から恣意的に除かない。

### 第3レビューで具体化した負側・観測確認

- **依存が強いTask**: 同じファイルを順序依存で編集させ、C/D/Eで競合・やり直し・quality regressionが増えるかを評価。並列数のみを増やして「高速」と判定しない。
- **実効権限の負側**: ダミー秘密値と書込禁止fixtureを持つ隔離workspaceで、委任先とWorkflowが禁止されたWrite/外部送信を実際に拒否されるか確認する。**本番秘密値・実API credentialは使わない**。構成ファイルにread-onlyと書いただけならFAIL/UNKNOWN。
- **発火の負側**: Agent teamsを無効にした環境、非対話`-p`、Workflow permission未付与で「意図どおりspawn/実行されない」ケースを記録し、無実行を成功扱いしない。
- **失敗するparallelism**: Workerが同じファイル/不可分の共有状態を更新する、Task DAGが線形である、subagent起動に実効tool禁止が適用される各ケースではC/D/Eの短縮を前提にしない。禁止操作の拒否を「Task成功」、spawnの非発火を「0コスト」としない。
- **比較不能の宣言**: 対話限定のAgent teams（D）と`-p`のSubagent（C）で外部条件が一致しない場合、`D−C`の因果的な高速化を主張せず、異なるRuntime policyの観察記録としてのみ残す。
- **時間の計測境界**: 同期した開始/終了イベントを持つ時計で、最初の人間依頼から検証済み成果物までを測る。Agent自身の処理だけを集計した短い値を、Human待機・CI・Reviewを含むdelivery elapsedへ読み替えない。
- **停止と権限**: Experimentの起動/費用/Runtime permissionは別承認。Reviewerは新しいセッションでexact headと独立oracleを閲覧し、作成者の自己レビューを置き換えない。

## 5. Cheapest useful verification と採用ゲート

- **Step 0（今回）**: 文献と比較設計の記録のみ。実モデル/Workflow起動、Runtime設定変更、Agent team有効化、権限変更なし。
- **Step 1（別判断）**: まずsecret-freeな小規模fixtureでA/Bとhard negativeを**少数の探索Run**で確認。実効model/permission/agent spawnとTask/成功oracleのログを確保する。委任未発火ならBは「委任なし」と記録し、Aとの比較から成果を断定しない。探索Runを固定した評価用held-out setの代用にせず、正式なpaired実験の開始には事前登録とHuman/Operator gateを必須とする。
- **Step 2**: 有意義なボトルネックが確認でき、予算・権限・独立Evaluator・Reviewerが準備できたときにCを追加。D/Eは具体的な仮説が残った場合に限る。
- **NO_GO**: 未承認の書込み/外部送信、秘密へのアクセス、原則的なHumanレビュー迂回、Gateの自己承認、required evidence欠落、偽陽性の成功、品質床違反。
- **Merge ≠ adoption**: 研究PRの統合を実装・自動適用・ベンチマーク結果の採用とはみなさない。既存EXP-001凍結33 blobsは不変更。新しいOperator Runやモデル支出、publish/tag等は各Human gateを別途通す。

## 6. 検証・統合時の注意

- 本ノートは#93に結び付ける。並行Draft #194/#206/#208などが同じ`knowledge/research/README.md` / `knowledge/sources.yaml`を変更するため、他PRのブランチを上書きせず、先行merge後に差分・重複source ID・latest-head CIを再検証する。
- 既存のrelease publication hold、独立した別セッションReview、Human-only release / guard / permission変更、GitHub Rulesetを尊重する。本セッションのレビューは独立承認の代替にはならない。

## 7. 実行計画 — 実測前の作業分割と判定ゲート

> この表は**提案中の作業計画**であり、承認済みexperiment.yaml・実Runtime Run・実測結果ではない。実行開始には[#93](https://github.com/s977043/dynamic-agent-topology/issues/93)側のHuman/Operator判断が必要。既存の[#194](https://github.com/s977043/dynamic-agent-topology/pull/194)のCascade/Recovery計画と並列に新しい実験契約を作らない。

| Gate / 担当 | 最小成果物 | 検証コマンド・観測 | Pass / Block |
| --- | --- | --- | --- |
| G0 Source & scope / Researcher（read-only候補） | 一次出典4件の実機能・実行面制約、原実験不明事項、#93/#194/#206との差分表 | 公開公式ページの照合、DAT原則と原文のリンク追跡 | ソースの主張とDATの観測を区別できる。SNSの速度主張の実測化禁止 |
| G1 Experimental design / Experiment Planner（提案のみ） | Task classと固定Work Unit DAG、A/B/Cの入力/出力・oracle、negative cases、予算/回数/停止条件の**事前登録案** | `docs/EXPERIMENTS.md` / `docs/METRICS.md`、EXP-001 Keep T0との整合チェック | 変更要因と評価基準が曖昧ならBLOCK。既存実験/Schemaへ遡及変更しない |
| G2 Runtime & permission preflight / Operator + Human許可 | Disposable secret-free checkout、CLI/provider/model IDs、Subagentの実際のspawn / tool denyの証跡 | **将来の許可後**にversion確認と禁止Write・外部通信のnegative probeを実施 | Permission/Model/効果値が未観測ならUNKNOWN。人間の権限判断がない状態で起動しない |
| G3 Feasibility / Operator +独立Evaluator | A/Bの小規模探索Run、失敗/中止を含むTrace、決定論的AC | fixed input、fresh workspace、activation・Run wall clock・Token・受入oracle | 取得できたら次の実験を検討。探索Runだけでは採用不可 |
| G4 Preregistered evaluation / Human承認後 | held-outのcounterbalanced paired blocks、B/Cのschedule差、独立Judgment | 成否と回帰・費用・人間介入・境界違反をRunごとに追跡 | 実測に品質の非劣化と実務上の利益がなければKeep T0 |
| G5 PR merge / Independent Reviewer | exact headに結び付いた別セッションの判断と全required CI | CI check runs、差分、指摘0、release hold、Human-only filesを再確認 | 条件が1つでも未達ならDraft/HOLD。研究PRのmergeは実験開始許可ではない |

### 実験を成立させる最小fixture案

- **S1 正例（独立可能）**: 同一入力リビジョンのread-only検査を2〜3個の独立Work Unitへ事前分割し、固定した成果物のhash・項目数・検出内容を独立oracleで照合する。BとCのWorker数、処理対象、情報量を固定し、単に検証を省略して速くなったRunを成功にしない。
- **S2 負例（依存が直列）**: 次のWork Unitが前の出力を参照するDAGを固定。Cの並列化によるhandoff failures、idle、rework、競合がないか確認。分割の同一性が保てなければB/Cを別物としてINCONCLUSIVE。
- **S3 セキュリティ負例**: 偽のsecret・禁止パスを持つ使い捨てfixtureだけを利用。想定外のWrite/Bash/MCP/外部送信が**実効的に拒否**されたかEventを確認し、権限宣言だけでは合格にしない。
- S1〜S3は**まだ作成・実行していない候補**。既存EXP-001 fixtureを改変しない。実行条件確定前に高コストな5-arm全比較や固定Topology追加を行わない。

### Reviewerへ委託する場合の引き渡し契約

- Writerから独立した新規Session/Modelに**PR head SHA、full diff、AGENTS/Harness規則、#93/#194/#206、一次資料、実施したCI run ID**を直接渡す。Writerの「結論だけの要約」は唯一の入力にしない。
- 承認はread-onlyレビューの結果・観測出典・重大度（必須/推奨）・session IDを記録し、必須指摘が出たら修正後の**新しいHEAD**へ再レビューを要求する。Botのquota exceededやCOMMENTED、同一セッション自己検査、助言Agentの返答は独立APPROVEDではない。
- Reviewerが起動できなければ**BLOCKED (not reviewed)**。未実行を成功として閉じない。G0/G1はread-only助言を委託可能だが、G2/G4の実行許可、G5のHuman-only release/tag/guard判断は委任できない。

### 今回の実行結果と残差

- 文書/出典の検証と最小作業計画のみ。現時点では実CLI、サブエージェント本体、実験Runは**実行していない**。
- 停止条件: 出典の矛盾、Work Unit/モデル/permissionが固定できない、独立Reviewが無い、Human Gate未解消、品質床・費用上限未合意。
- 次の受け渡し: #93でG1のAC・budget・適格Taskを定め、G2以降は許可された実行環境・独立Reviewerが揃った時のみ実施する。
