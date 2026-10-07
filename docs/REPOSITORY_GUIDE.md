# Repository Guide — 仕様・Evidence・Issueの読み方

このガイドはDATの構成とIssueの関係を説明する入口です。実装契約は各Artifact、実行の最新判断は追跡Issue、公開versionはtag / Releaseを確認してください。

## 目的と利用の流れ

DATの問いは「どのAgent Topologyが、どの条件で、どれだけのコストに対して有効か」です。P0 Deterministic PipelineとT0 Single Agentを起点に、追加Roleや協調を比較実験で正当化します。詳細は [North Star](NORTH_STAR.md) と [Architecture](ARCHITECTURE.md) にあります。

既存プロジェクトのEvidenceを接続し、実行を観測して、候補構成とBaselineを比較します。静的validationのPASS、実Runtimeでの成功、Topologyの有効性には、それぞれ別のEvidenceが必要です。

## 構成と正本

| 関心 | 読む場所 | 確認すること |
|---|---|---|
| 構造・責務 | [topologies](../topologies/canonical/)、[roles](../roles/)、[baselines](../baselines/) | Node / Edge / RoleとP0の区別 |
| 選択・上限 | [policies](../policies/) | RoutingとEscalation。Topologyとは別契約 |
| Runtime対応 | [adapters](../adapters/) | [Capability status](../schemas/runtime-capability.schema.json) のnative / experimental / emulated / degraded / unsupported / unknown。宣言と権限強制の区別 |
| 契約の形・整合 | [schemas](../schemas/)、[scripts](../scripts/) | Schema検証とcross-file semantic validation |
| 外部導入 | [Quick Start](QUICKSTART.md)、[brownfield example](../examples/brownfield/) | Project / Evidence / Policy / Runtime Bindingとrevision pin |
| 観測・評価 | [experiments](../experiments/)、[Metrics](METRICS.md) | Trace、Attestation、Evaluation、比較判断 |
| Sourceと仮説 | [Knowledge Base](../knowledge/README.md)、[Research Notes](../knowledge/research/README.md) | Source claim、DAT解釈、採用状態 |
| 公開・運用 | [Public Repository Policy](PUBLIC_REPOSITORY_POLICY.md)、[Release Readiness](RELEASE_READINESS.md) | GitHub設定、candidate SHA、tag / Release |

現行 [harness](../harness/README.md) はArtifact検証・集計用です。外部導入では既存Runtime設定をManual Adapterで対応付け、Evidence commandの実行は信頼した既存CI / Runnerが担当します。DATはRuntime設定を自動compile/applyしたりAgentを起動したりしません。

### Harnessという語の範囲

`harness/` は実験Artifactのtoolingです。[PR #85](https://github.com/s977043/dynamic-agent-topology/pull/85) のAgent Development Harnessは、このリポジトリを開発するAgentのguidance・Guard・学習記録の運用です。mainへの採用状態はPRと対象revisionで確認します。[Issue #21](https://github.com/s977043/dynamic-agent-topology/issues/21) のExecutable Configuration evolutionは、EXP-001後に評価する構成改善の研究候補です。開発環境のGuard導入を、実験Runtimeの改善Evidenceやconfiguration promotionの採用と扱いません。

## Evidenceの到達点

[Issue #5](https://github.com/s977043/dynamic-agent-topology/issues/5) はManual Adoption Kit、[#7](https://github.com/s977043/dynamic-agent-topology/issues/7) は最初の外部dogfood、[#3](https://github.com/s977043/dynamic-agent-topology/issues/3) は比較実験基盤の履歴です。[Dogfooding Evidence](DOGFOODING.md) は一つのconsumerにおけるA2 / Codex / T0導入を支持します。T1の優位性や他Runtimeでの再現を証明する記録ではありません。

EXP-001は独立Verifier追加の限界効用を比較するPilotです。Experiment全体のRuntime候補と、Codexに固定したPilot条件を混同せず、[pilot.yaml](../experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml) と [run matrix](../experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml) を確認します。

## Issueの責務と依存関係

以下は2026-10-07にIssue本文を確認した責務マップです。進捗数、停止状態、次Run、CIは各Issue / PRで再確認します。

| Issue | 所有する問い・仕事 | 着手条件・最小の次アクション |
|---|---|---|
| [#15](https://github.com/s977043/dynamic-agent-topology/issues/15) | EXP-001実測・attempt disposition・Run acceptance | [Execution Handoff](EXP-001_EXECUTION.md) からFreeze、matrix、最新判断を照合 |
| [#31](https://github.com/s977043/dynamic-agent-topology/issues/31) | Git外の公開設定・ruleset・Release整合 | 既存auditで現在値を確認し、段階適用後に再監査。Releaseを実験成功と扱わない |
| [#21](https://github.com/s977043/dynamic-agent-topology/issues/21) | Executable Configurationの改善・評価・昇格 | EXP-001解除後、既存ablationで不足する観測済みfrictionを列挙 |
| [#42](https://github.com/s977043/dynamic-agent-topology/issues/42) | retry / stop / state / branch / recovery契約 | EXP-001解除後、既存Policyと小さい介入で解けないLoop / Graphの問題を特定 |
| [#57](https://github.com/s977043/dynamic-agent-topology/issues/57) | cross-artifact provenance検証の自動化 | EXP-001解除後、session / timestamp / token整合のnegative casesを評価。現在はmanual review |
| [#59](https://github.com/s977043/dynamic-agent-topology/issues/59) | Claude Code Modsの権限・監査機構 | EXP-001解除後、native controlで不足するRuntime固有のgapを確認 |
| [#63](https://github.com/s977043/dynamic-agent-topology/issues/63) | 永続・compiled Knowledgeのintegrity | EXP-001解除後、process successとsemantic correctnessのずれを検証 |
| [#82](https://github.com/s977043/dynamic-agent-topology/issues/82) | adversarial Judgmentと疎なchallenge gate | EXP-001解除後、既存Reviewer / Verifierで十分かを先に確認 |
| [#88](https://github.com/s977043/dynamic-agent-topology/issues/88) | model escalationとcompact handoff | EXP-001解除後、session / context / model効果を分けて比較 |
| [#93](https://github.com/s977043/dynamic-agent-topology/issues/93) | compound execution strategyと選択的multi-model orchestration | EXP-001解除後、CritiqueとCascadeを分け、既存Topology / Routingで不足するかを比較 |

#21はconfiguration promotion、#42はexecution control、#82はJudgment objective、#88はmodel / context handoff、#93はcompound execution strategyの独立性を扱います。実測した最小Work Unitごとに採用・棄却・延期を判断します。研究候補の文書化は、契約の採用や実装の許可を意味しません。

## EXP-001の状態を読む際の注意

[Issue #16](https://github.com/s977043/dynamic-agent-topology/issues/16) のcloseはFreeze導入作業の完了です。解除状態は [freeze.yaml](../experiments/EXP-001-t0-vs-t1/pilot/freeze.yaml) と [Freeze policy](../experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md) で確認します。

Issue #15本文はT1 r01をABORTED / not accepted / no retryと記録しています。[PR #86](https://github.com/s977043/dynamic-agent-topology/pull/86) は不完全attemptの保存であり、complete Runや成功Evidenceを追加するものではありません。canonical Artifactだけを読むstatus表示には、この外部保存attemptのdispositionが反映されません。

Issue本文の進行記載と、独立review record / Operator procedureのgateが整合するかを確認します。archive保存の承認だけでは次slotへ進めず、通常の前Run ACCEPT gateを満たさない場合はIssue #15で停止・整合確認します。

次slotへの進行許可とFreeze解除は別判断です。再試行しないslotがある場合、残りslotの終了だけで18/18 completeや最終validation PASSを主張できません。この到達可能性はIssue #15で明示的にレビューする必要があります。本ガイドは凍結契約の例外、Run数変更、validatorの迂回を認めるものではありません。

## 更新時の確認順

1. Issue本文の最新判断と、過去コメント・checkpointを区別する。矛盾が残る場合は正本を確認してから実行する。
2. 対象Artifact、validator、Freeze manifestを読み、変更が実験意味論に影響するか確認する。
3. Source claim、観測Evidence、解釈、判断を分けて記録する。UNKNOWNやabortedを成功へ変換しない。
4. [Contribution Guide](../CONTRIBUTING.md) とPR templateに従い、差分、根拠、検証結果を残す。
5. 実行進捗はIssueへ集約し、文書には手順・保証範囲・履歴へのリンクを残す。
