# Uber Software Factoryの成果単位コスト・品質評価 — research note

## Status / authority boundary

**Research-only / 未採用、未実測。** DATの既存評価基盤に適用できるかを調べるための候補であり、Runtime、Routing、Schema、Experiment、モデル設定、認可、CI、既存EXP-001の結論を変更しない。

関連Issue: [#162 Workflowモデル切替の総コスト再検証](https://github.com/s977043/dynamic-agent-topology/issues/162)、[#93 compound execution strategy](https://github.com/s977043/dynamic-agent-topology/issues/93)、[#88 model escalation](https://github.com/s977043/dynamic-agent-topology/issues/88)。それぞれの所有範囲に接続し、新しい評価エンジンは作らない。

## Primary source / provenance

- Uday Kiran Medisetty, Uber Engineering, [Running a Software Factory Efficiently at Uber Scale](https://www.uber.com/us/en/blog/efficient-software-factory/), **2026-08-27**（Uberによる一次報告）。
- この記事はUberの内部環境・期間における観測と方針であり、DATでの改善を証明しない。コスト・品質の公開集計は全条件での再現性や因果効果の保証ではない。

### Source claims (Uber observed / stated)

1. **2026年2〜8月の週次利用者が7倍、週次Agentリクエストが9.4倍**。4月以降のAI総支出は比較的安定したと報告するが、絶対額は公開されない。
2. **モデルを固定した比較**で、1,000リクエストあたりのコストはピーク比約34%減、セッションあたりは6月ピーク比52%減。後者の観測は5月末からであり、2月始点の削減率ではない。
3. Layer 1 Raw Sessions / Layer 2 Sessions with Skills / Layer 3 General Agents / Layer 4 Specialized Agentsを区別。Managed agentでは **cost per merged PR / review / alert / cleanup** と、revert率・F1・MTTRなどの品質信号を組み合わせる。
4. 実PRの既知バグを使ってReviewerのprecision / recall / F1、cost / review、latency、timeout、noiseを比較し、タスクごとのPareto効率でモデルを選ぶ。
5. コンテキスト圧縮、Medium effort、prompt cache、CLIによる動的ツール解決、code-mode、グラフによる文脈接地などを最適化候補として挙げる。**400K tokenの圧縮閾値、cache TTL、モデル既定値をDATへ一律転用しない。**
6. SQLクエリ5例のcode-mode比較およびContext Graph利用有無による38秒対20分9秒の比較は、**対象限定の事例**。一般的な削減率・品質改善率としてDATに流用しない。

## DAT interpretation (unverified)

- **成果を分母にする**: 「生成したPR数」だけでは価値を示さない。事前合意の品質基準を満たした **verified task**、判定済みreview、重大エラー検出などを評価単位の候補にする。
- **品質をハード制約にする**: Task成功、意味的正確性、critical regression、境界違反を先に評価し、品質を下回る候補は安さで正当化しない。
- **全費用を把握する**: モデル費用のほか、retry、tool calls、validation、human correction、レビュー待ち、再評価、移行工数を別々に記録する。金銭換算不可の項目を推定0へ倒さない。
- **比較を交絡させない**: Topology、Model、Effort、Cache、Context、Tool accessを同時変更した試行から、単一要因の効果を断定しない。
- **実行効率と権限は別**: Code-modeでの呼び出し集約は、権限・データ保護・監査・Human approvalの代替ではない。

## Existing contracts / responsibility mapping

| Concern | Existing owner / boundary | Proposed connection |
|---|---|---|
| Paired Runの品質・経過時間・token・Human介入 | DAT `docs/METRICS.md` / `schemas/evaluation.schema.json` / experiment artifacts | 既存fieldが取得可能か棚卸し。既定の集計意味論は変更しない |
| Model migration / workflow revalidation | DAT [#162](https://github.com/s977043/dynamic-agent-topology/issues/162) | 費用・品質のpaired decision候補として評価 |
| Topology / Role / Routing | DAT [#93](https://github.com/s977043/dynamic-agent-topology/issues/93) / [#88](https://github.com/s977043/dynamic-agent-topology/issues/88) | 最適構成は実験結果が出てから決定 |
| Runtime execution / PBI / approval | [PlanGate #1576](https://github.com/s977043/PlanGate/issues/1576) | Human-owned C-3/C-4はDATの比較結果から生成しない |
| PRレビュー・実バグの正解セット | [River Review #2701](https://github.com/s977043/river-review/issues/2701) | Ground truthとfalse positiveを独立管理 |
| Skill / session utilization | [ai-agent-template #127](https://github.com/s977043/ai-agent-template/issues/127) | トークン観測と検証済み成果を混同しない |
| Provider / cache cost | [hermes-agent-ops #225](https://github.com/s977043/hermes-agent-ops/issues/225) | Provider固有TTLやcache localityを実測する |

## Read-only contract audit (2026-10-17 / main `35b1c943`)

現行実装をread-onlyで確認した結果（計測結果ではなく、**取得可能なフィールドの監査**）:

| 現行artifact | 取得できる値 | まだ取得・集計できない値 |
|---|---|---|
| `schemas/evaluation.schema.json` | `taskSuccess`, `regressionDetected`, Acceptance Criteria件数、`humanInterventions`、`agentInvocations`、`coordinationTransitions`、`wallClockMs`、任意の`inputTokens/outputTokens`、`verifierFalseAccept` | Provider請求額、cache read/write token、retry費、Human実作業時間、評価者によるsemantic ground truth |
| `schemas/execution-trace.schema.json` | `runId`, `blockId`、Runtime/Model/Effort、Event、起動・遷移・介入・token・経過時間のsummary | 費用明細、料金条件、cache TTL、credential pool、failed attemptの独立課金区分 |
| `scripts/summarize_experiment.py` | 同一Runtime/Model/Effort内で条件ごとの成功・回帰・平均tokens・平均wall clock・介入回数などを集計 | 成果単位の通貨コスト、retryを含む分母・分子、モデル間cross-context比較、Human時間と品質調整済み費用 |

- evaluation/traceの主要オブジェクトには `additionalProperties: false` がある。**既存YAMLへコストやcacheのフィールドを勝手に追加するとSchema互換性を壊す**。観測の不足はまず別の分析メモとして保持し、必要性が実証されるまでSchemaを変更しない。
- 現行`summarize_experiment.py`は、同一Experiment内に複数Runtime/Model/Effortが混在した入力を拒否する。モデル間比較は現行summarizerに投入せず、既存のpaired実験契約に従って別に比較する。
- `humanInterventions`は回数であり、人時ではない。`taskSuccess`や`passedGates`は独立したHuman確認済みsemantic correctnessを自動的に意味しない。
- 生のprovider/請求/実行ログは取得していない。**現時点で実測cost/verified taskは算出不能**。

## Falsifiable hypotheses

- **H1**: 匿名化した代表的workflowのpaired comparisonでは、token単価で最安の構成が「品質条件を満たすverified taskあたり総コスト」では最安でないケースが少なくとも1つ存在する可能性がある。見つからなければその範囲で棄却する。
- **H2**: モデル単体費用が同程度でも、subagent回数・失敗retry・コンテキスト肥大化が多いArmは、要求/成果物あたりの総使用量とwall-clockが増える可能性がある。
- **H3**: コストを計測してもsemantic correctnessを独立評価しなければ、表面的な成功率の改善が品質劣化を隠すことがある。負例で検出できなければ評価プロセスを再設計する。

## Cheapest useful verification (no live change authorized)

1. **Gap audit (read-only)**: 現行 `docs/METRICS.md`、evaluation schema、traceとsummarizerを確認。取得できる費用、欠測、observability limits、Human時間とレビュー品質の参照先を一覧化。既存fieldを優先。
2. **Case selection**: 匿名化済みの成功例・失敗例・clean negativeを含む最小5件を候補にする。Ownerが品質下限、critical失敗、評価者、費用上限、停止条件を **実行前** に決める。5件の合格は本番品質を保証しない。
3. **Paired replay**: 同一workflow、case、固定code snapshot・prompt/skills、tool permissions、budget条件で単一の変数を変更。交互順序とfresh sessionを採用し、評価者とGround Truthを事前に独立確定する。実行には別途Operatorの許可が必要。
4. **Record evidence**: `case_id`, `run_id`, `block_id`, baseline/candidate、version/effort/runtime、quality verdict、critical regression、tokens/input/output/cache、retries、human active correction time、validation費、料金前提・通貨・timestamp、missing理由を記録。未計測・N/A・0を分ける。
5. **Decision**: 品質下限を満たしたrunの中だけで、task単位の総コスト・latency・Human介入を比較。失敗/abort/timeoutの扱い、分母、sample sizeを明示。測定不足なら `INCONCLUSIVE` とし、Ownerのみが採用・rollbackを判断する。

### Proposed outcome metric (not implemented)

`cost_per_verified_task = attributable_observed_total_cost / count(verified_accepted_tasks)`

- 分母が0または未観測、分子の必要な費用要素が欠測なら **undefined / INCONCLUSIVE**。Infinityや0で埋めない。
- `merged PR`、`posted review`、`verified task` は異なる成果単位であり、同一の分母として集計しない。
- API従量課金、定額契約の配賦、人間労力は同一の「実測金額」とみなさず、測定種別・配賦仮定を付記する。
- workflow当たりの費用比較では、移行/再検証の一時費用とランニング費用を分け、観測期間も固定する。

## Review / rejection gates

| Lens | Stop / rejection condition |
|---|---|
| Scientific | 同時変更要因が多い、正負例が偏る、paired evidence・independent Ground Truthがない |
| Quality | Critical不具合の見逃し、semantic誤判定、品質下限の事後変更 |
| Cost | Missing料金を0扱い、subscription配賦と従量課金を混合、低品質な成果を分母へ含める |
| Security | 生traceやsecretを外部に送る、shellバッチでtool permission/approvalを迂回 |
| Governance | EvidenceがHuman承認に昇格、既存freezeを変更、未承認実験を開始 |
| Simplicity | 既存artifactで十分なのに、新しいschema/runner/routerを先に作る |

**Adoption remains deferred** until #162/#93 owners approve a narrowly scoped experiment, independent review and real paired evidence exist. This note does not alter any current DAT adoption state.
