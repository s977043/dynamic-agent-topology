# RFC: DAT vNext — Evidence-first redesign

- Status: **DRAFT / NOT ADOPTED**
- Tracking: [Issue #268](https://github.com/s977043/dynamic-agent-topology/issues/268)
- Baseline: `main` `4475b3004ecd07ae5da313121543067119a59479` (2026-10-29)
- Scope: 新設計の仮説、代替案、検証条件、移行判断。**実装・実モデル起動・規則変更の承認ではない**
- Companion: [Baseline inventory](DAT_VNEXT_BASELINE.md) / [Review runbook](DAT_VNEXT_REVIEW_RUNBOOK.md)

## 1. Problem / Desired Outcome

DATのNorth Star「**Which agent topology works, under what conditions, and at what cost?**」は維持する。現在の課題はTopology表現能力の欠如ではなく、利用者が **Assess → Select → Observe → Compare → Decide** を安全・再現可能・少ない操作で行えるかという未検証の利用体験にある。

### 検証する問い

1. 現行の2 Skills・Manual Adapter・既存Harnessで、一連の判断をすでに十分低負荷で完遂できるのか。
2. 新しいInterface / 責務境界はユーザー操作と保守変更時間を減らせるか。
3. Single-Agent-firstを**実行候補**として優先しつつ、評価器のTopology中立性を維持できるか。
4. Multi-Agentの追加だけでなくFold / Keep / Escalate / Revertを、別々のEvidenceから判断できるか。
5. 新しい抽象化や互換レイヤーのコストが便益を上回らないか。

**Success is an independently reproducible decision, not fewer files or agents.**

## 2. Current facts vs unknowns

### Observed (source-of-truth files are linked in baseline)

- DATはAgent Runtimeではなく仕様・実験・評価基盤。Runtime構成の自動適用はしない。
- `dat-select`はRouting/Escalation Policyに基づく**提案**のみ。不明入力では選択保留。
- `dat-observe`は日常のRunObservationを検証しGit外へ保存。これは構成間の因果比較ではない。
- EXP-001: 18/18 accepted、9/9 paired blocks、対象3 ScenarioでT0/T1成功率100%。T1の平均TokenはT0の約2.21倍。**Pilot条件ではKeep T0**。床効果・交絡のため一般化しない。
- 2026-10-29時点の公開境界はv0.4.1。既存Schema、CLI、Skills、Plugin packagingは互換性の対象。

### Unknown — must not be silently filled

- 初回利用者の設定時間、操作回数、選択保留率、導入失敗率。
- 同等の機能変更時に必要なエンジニア時間・レビュー時間・CI負担。
- 実際のTopologiesにおける独立Verifier/Contextの限界価値（難タスクでの実証は未完）。
- 外部利用者の入力互換要件、必要な移行期間。
- vNextが現行Aより良いという実測Evidence。

## 3. Alternatives (review independently, do not preselect)

| Option | Description | Reasons to choose | Stop conditions |
| --- | --- | --- | --- |
| A — Incremental | 現行DATと公開契約を維持、観測されたボトルネックだけ修正 | 既存導線が実務上十分なら最少リスク | 実証済みの責務競合により局所改善不能 |
| B — Evidence-first vNext | 利用体験・責務をゼロベースで再設計、比較可能な最小vertical sliceを隔離実装。既存Domain/評価を必要に応じて再利用 | 利用負担や変更コストの実測改善が見込める | 新規抽象化が増えても改善せず、移行負担を回収できない |
| C — Full rebuild | Domain・Schema・Adapter・実験基盤を再構築 | 既存契約が検証可能な阻害要因で、Bで回避不可能 | 履歴/互換性/安全性の再構築コストが便益超過 |

初期検証優先は**B vs A**。Cは比較する設計代替案として記録するが、着工には「Bでは解決できない再現可能な構造的障害」と新規判断が必要。

## 4. Architecture: Topology-neutral core

```text
                 Human-approved boundaries
          budget / write permission / secrets / publish
                              |
Task + acceptance criteria + fixed experiment controls
                              |
Assessment -> Candidate recommendation (no auto apply)
                              |
          External Runtime (Claude Code/Codex/etc)
          ├── P0: deterministic pipeline
          ├── T0: single agent + tools/skills
          ├── T1/T2/T3: multi-agent variants
          └── optional hybrid (research arm, not default)
                              |
Observed Trace + verified Evidence + missingness
                              |
Independent Evaluation / paired blocks / regression
                              |
Decision: keep / fold / expand / revert / inconclusive
```

**Hard boundaries:** Topology ≠ Routing Policy; Role ≠ Permission; Role ≠ Model; Runtime ≠ Model Provider; Selection ≠ Permission; Observed Execution ≠ Attestation ≠ independent verification; Evidence ≠ Judgment.

**Single-Agent-first**は新規Taskの低coordination-cost初期候補というPolicy仮説。DAT全体がSingle Agentに偏って評価する根拠ではない。独立Context、並列性、独立Verificationなどの限界価値は、task classごとのablationで判定する。

## 5. Vertical slice / User journey

**MVP: 一つのタスクについて「候補→観測→比較→判定」を再現できること。Agentの実行は既存Runtimeに委ねる。**

1. TaskとAC、制約、未知、現行runtimeを入力。
2. 現行Policy（または新候補）からTopologyの提案・選択保留理由・代替案を示す。自動実行しない。
3. 合成fixtureまたは既存の信頼できるRun Artifactを取得し、schema/semantic validationを通す。**合成fixtureを実測と混同しない**。
4. 同条件のbaseline / candidate Runをpairedで評価。差分、欠測、n、不一致、回帰を出す。
5. Reviewer/Operatorが実測範囲に限定してAdopt / Reject / Inconclusiveの判断を記録し、根拠リンクとrevisit triggerを残す。

初期利用者体験は既存`dat-select` / `dat-observe`で再現できることが前提。**第三のSkillや新CLIを先に作らない。** 発見したgapを示してから最小変更する。

## 6. Scope / Non-goals

### In scope (design or offline spike only)
- 現行公開契約と導線のInventory/measurement。
- A/B/C案のADR、6視点レビュー、反証可能な仮説。
- 一つのRuntime・一つのTaskでの非破壊的なoffline vertical slice。
- 既存Schema / validators / skills の再利用可能性と変更負荷の評価。
- Compatibility・Migration・Rollback計画。

### Out of scope until separately authorized
- 自作Agent Runtime / 強制的なSingle-Agent移行 / 新規Topologyの標準採用。
- 既存SchemaやCLIの破壊的変更、Skill名変更、Plugin配送経路変更。
- EXP-001 frozen artifacts / result / decisionの修正・再実行。
- 有料モデル起動、追加課金、Runtime権限昇格、実ユーザー秘密・本番変更。
- #248 folding試験、#244 hard-task試験、#93 selector/#88 escalation/#220 model splitを本RFCの設計実験へ混合すること。

## 7. Validation protocol / Falsification

### H1: User friction
同一代表タスクをAとBで実施し、操作数、経過時間（active vs wall timeを区別）、設定ファイル編集、失敗・リトライを同じ手順で記録する。改善が一回限りか判断できない少数標本は feasibility-only。**未測定の「30%短縮」を達成済みと主張しない**。

### H2: Decision fidelity
提案結果が「Policy根拠」「未確定入力」「選択と効果証拠の区別」を明示できること。Unknown task・境界条件を含む。実装の出力が正確でもTopology優位性は証明しない。

### H3: Reproducible comparison
同じTask/AC/Runtime/Model/Effort/workspace/Verification/budgetに対するpaired比較を、`blockId`とArtifactで再現できる。input contextが混在、独立oracleなし、片側欠測、条件不一致、採用基準の後出しのいずれかは **INCONCLUSIVE/STOP**。

### H4: Safety and compatibility
Permissionsは既存Runtime/Tool/CIで強制。拒否すべき操作が実際に拒否されるnegative fixture、権限範囲内のpositive fixtureを用意する。既存のschema/CLI/Skillやimmutable historyを変更しない。Critical boundary violationでNo-Go。

### H5: Maintainability
同じ小変更要求をAとBへ適用する作業を比較し、レビュー含む実作業時間と契約影響面積を記録する。ファイル数減・コード行減のみを採用理由にしない。

**Preregistration:** operator・reviewerがsample size / case registry / thresholds / failure budget / missingness policy / counterbalancing / scopeを結果閲覧前に固定。Offline SpikeのPASSは実モデルの有効性を意味しない。

## 8. Acceptance gates

| Gate | Exit signal | On failure |
| --- | --- | --- |
| G0 Baseline | Consumer journeyを現行mainで再現。静的観測と実測を分離。公開契約表あり | Bの実装開始を保留 |
| G1 RFC | Architecture/Evaluation/Security/DX/Maintainability/OSSの6視点からcritical 0、独立レビュー証跡が必要 | RFC修正 |
| G2 Offline | 既存validator通過、positive/negative fixture、変更対象外の差分0 | Revert spike |
| G3 Compare | A/Bの同条件比較、n/欠測/限界・回帰・操作コストを明記 | Inconclusive or prefer A |
| G4 Adoption | Bに実測優位・移行可能性・運用責任者の許可あり | Aの局所改善に戻る |

判定候補は **A / B / C / INCONCLUSIVE**。Cは独立した承認なしに着工しない。重要な互換変更・HOTL規則変更・公開Releaseは各正本のHuman-owned境界に従う。

## 9. Compatibility / Migration / Rollback

公開契約の正本は [Release readiness](../RELEASE_READINESS.md) のCompatibility boundary：
- `schemas/`とvalidators/CLIの入力・出力・exit code
- `topologies/`, `roles/`, `policies/`, `baselines/`, `docs/RUN_OBSERVATION_DESIGN.md` の意味論
- `skills/`および`.claude-plugin/`, `.codex-plugin/` 配布
- RunObservationのGit外store、version pinning

Bは最初**既存公開API/Skillの変更を伴わない分離Spike**に限定する。新規Interfaceの導入時は既存呼び出しを保ち、適用対象ごとにcompatibility testsを記録。旧コード削除は観測された利用状況と移行完了後に別Issue/PRで判断。RollbackはSpike差分をrevert（Frozen原本には触れない）。

## 10. Work plan / Owners

1. [P0 baseline](DAT_VNEXT_BASELINE.md)の未測定欄を、実際のworkflow計測で埋める（read-only）。
2. 本RFCを6視点で独立レビューし、[review runbook](DAT_VNEXT_REVIEW_RUNBOOK.md)のフォーマットで findings / reviewed SHA / independence / blockersを記録。単一セッションの架空エージェント合議は不可。
3. RFCに対してADRを作成してA/B/CのSpike可否を決定。現時点で採用は未確定。
4. Spikeの実装は**別PR**で小さく行い、main/consumer/experiment contractsを変えない。
5. #248/#244等の実モデル実験はそれぞれの既存承認Gateを通す。

## Related work

- [#268](https://github.com/s977043/dynamic-agent-topology/issues/268) vNext RFC parent
- [#248](https://github.com/s977043/dynamic-agent-topology/issues/248) folding paired-E2E study
- [#244](https://github.com/s977043/dynamic-agent-topology/issues/244) hard-task T0/T1 experiment
- [#223](https://github.com/s977043/dynamic-agent-topology/issues/223) RunObservation & skills
- [#93](https://github.com/s977043/dynamic-agent-topology/issues/93), [#88](https://github.com/s977043/dynamic-agent-topology/issues/88), [#220](https://github.com/s977043/dynamic-agent-topology/issues/220) orthogonal model/routing studies
- [Anthropic single-agent-loop-kit](https://github.com/anthropics/single-agent-loop-kit) reference only; maintenance and example generalization are limited

**Open decision at RFC draft time:** Is redesign B measurably better than the smallest safe improvement A? **UNKNOWN**.
