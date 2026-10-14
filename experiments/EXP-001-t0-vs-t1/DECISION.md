# EXP-001 Decision

**Status: PILOT COMPLETE — Keep T0（起案。独立 Reviewer の結果レビュー前）**

このファイルはEXP-001の最終判断記録です。

これは 18 Run（3 Scenario × 2 Condition × 3 rep）の **Pilot observation** であり、Benchmark claim ではありません（`pilot/FREEZE.md` Publication gate）。広い Task 分布・他 Runtime・他 Model へ一般化しません。

## 実行条件

- Runtime: codex（全 18 Run の `evaluation.yaml` `executionContext.runtime`。summarizer が混在なしを確認）
- Model: gpt-6.1-sol（同 `executionContext.model`）
- Effort: high（同 `executionContext.effort`）
- Runs per scenario / condition: 3（3 Scenario × T0/T1 × r01〜r03 = 18、counterbalanced-paired。`decisionPolicy.minimumRunsPerScenarioPerCondition: 3` を満たす）
- 実行環境: `EXP-001-train-normalize-name-r01` block だけが他と異なる（T0 = host 系で特定不能、T1 = one-time retry キット）。残り 16 Run は run-kit-g（PR #135 `8466ad5`、環境 Judgment #15 comment 6107822908 / 6107845799）。
- Feature Freeze: revision 3 のまま。集計時点で `validate_experiment_freeze.py` は 33 artifacts intact。

## 集計

数値はすべて凍結 `scripts/summarize_experiment.py`（freeze 対象）の出力 JSON、または Run Artifact の値からの転記です。token は `efficiency.inputTokens + efficiency.outputTokens`（cached input を含む最終 `total_token_usage`。T1 は Worker と Verifier の 2 session の合計）。判断の根拠は 18 件版、16 件版（train/normalize-name r01 block を除外）は感度分析です。

### Condition 別（凍結 summarizer）

| 指標（summarizer キー） | 18 件 T0 | 18 件 T1 | 16 件 T0 | 16 件 T1 |
|---|---|---|---|---|
| runs | 9 | 9 | 8 | 8 |
| taskSuccessRate | 1.0 | 1.0 | 1.0 | 1.0 |
| regressionRate | 0.0 | 0.0 | 0.0 | 0.0 |
| meanHumanInterventions | 0.0 | 0.0 | 0.0 | 0.0 |
| meanTotalTokens | 68022.0 | 150080.67 | 65642.125 | 145717.0 |
| meanWallClockMs | 44540.11 | 55777.78 | 40625.0 | 56375.0 |
| meanTopologyAdherence | 1.0 | 1.0 | 1.0 | 1.0 |
| meanEvidenceCompleteness | 1.0 | 1.0 | 1.0 | 1.0 |
| verifierFalseAcceptRate | null（N/A） | 0.0 | null（N/A） | 0.0 |

- token 比 T1/T0（meanTotalTokens）: 18 件 2.206（+120.6%）、16 件 2.220（+122.0%）。
- wall clock 比 T1/T0（meanWallClockMs）: 18 件 1.252、16 件 1.388。

項目別の要約:

- Task Success: T0 1.0 / T1 1.0（18 件・16 件とも）
- Regression: T0 0.0 / T1 0.0（同）
- Human Intervention: T0 0.0 / T1 0.0（同）
- Tokens: T0 68022.0 / T1 150080.67、T1/T0 = 2.206（18 件）。16 件では 2.220
- Latency: T0 44540.11 ms / T1 55777.78 ms、T1/T0 = 1.252（18 件）。16 件では 1.388
- Topology Adherence: T0 1.0 / T1 1.0
- Verifier False Accept: T1 0.0（T0 は N/A）

出典: 18 件 = `all-incl-r01.json`、16 件 = `all-excl-r01.json`（`conditions.T0|T1.<キー>`）。比は同 JSON の `meanTotalTokens` / `meanWallClockMs` から計算。

### Scenario 別（凍結 summarizer）

| Scenario（出力名） | runs T0/T1 | taskSuccessRate T0/T1 | regressionRate T0/T1 | meanHumanInterventions T0/T1 | meanTotalTokens T0 / T1（比） | meanWallClockMs T0 / T1 |
|---|---|---|---|---|---|---|
| train-normalize-name | 3/3 | 1.0/1.0 | 0.0/0.0 | 0.0/0.0 | 73979.0 / 160768.67（2.173） | 44620.33 / 51000.0 |
| train-normalize-name-excl-r01 | 2/2 | 1.0/1.0 | 0.0/0.0 | 0.0/0.0 | 67438.0 / 148658.0（2.204） | 29000.0 / 51000.0 |
| test-clamp-boundaries | 3/3 | 1.0/1.0 | 0.0/0.0 | 0.0/0.0 | 65053.0 / 140210.67（2.155） | 37000.0 / 45666.67 |
| regression-safe-divide | 3/3 | 1.0/1.0 | 0.0/0.0 | 0.0/0.0 | 65034.0 / 149262.67（2.295） | 52000.0 / 70666.67 |

全 Scenario で meanTopologyAdherence・meanEvidenceCompleteness は T0/T1 とも 1.0、T1 の verifierFalseAcceptRate は 0.0。

### Run 別（補助集計。Run Artifact から転記）

出典: `experiments/EXP-001-t0-vs-t1/runs/pilot-codex/<runId>/evaluation.yaml` のキー `outcome.taskSuccess`、`collaboration.boundaryViolations`、`collaboration.handoffFailures`、`efficiency.agentInvocations`、`efficiency.inputTokens`、`efficiency.outputTokens`、`efficiency.wallClockMs`。forkTurns は同 Run の `trace.yaml` の `forkTurns`。Verifier 初期 developer item は同 Run の `evaluation.yaml` `notes` と Issue #15 の受理コメント。全 18 Run で `outcome.regressionDetected: false`、`collaboration.humanInterventions: 0`、`collaboration.topologyAdherence: 1.0`、`evidence.completeness: 1.0`、T1 の `evidence.verifierFalseAccept: false`。

| runId | taskSuccess | boundaryViolations | handoffFailures | agentInvocations | inputTokens | outputTokens | wallClockMs | forkTurns | Verifier 初期 developer item | 受理（#15 comment / PR） |
|---|---|---|---|---|---|---|---|---|---|---|
| train-normalize-name-r01-T0 ※ | true | 0 | 0 | 1 | 86676 | 385 | 75861 | — | — | PR #54（Run acceptance 書式導入前。README Decision status 参照） |
| train-normalize-name-r01-T1 ※ | true | 0 | 0 | 2 | 183853 | 1137 | 51000 | none | 記録なし | 6106366753 / PR #130 |
| train-normalize-name-r02-T0 | true | 0 | 0 | 1 | 74477 | 335 | 29000 | — | — | 6108509132 / #142 |
| train-normalize-name-r02-T1 | true | 0 | 0 | 2 | 144552 | 903 | 47000 | none | 記録なし | 6108236361 / #140 |
| train-normalize-name-r03-T0 | true | 0 | 0 | 1 | 59669 | 395 | 29000 | — | — | 6110237869 / #143 |
| train-normalize-name-r03-T1 | true | 0 | 0 | 2 | 150982 | 879 | 55000 | all | 記録なし | 6110498856 / #144 |
| test-clamp-boundaries-r01-T0 | true | 0 | 0 | 1 | 74594 | 314 | 33000 | — | — | 6111292957 / #146 |
| test-clamp-boundaries-r01-T1 | true | 0 | 0 | 2 | 131173 | 901 | 47000 | all | 記録なし | 6110760953 / #145 |
| test-clamp-boundaries-r02-T0 | true | 0 | 0 | 1 | 59648 | 342 | 26000 | — | — | 6114012252 / #147 |
| test-clamp-boundaries-r02-T1 | true | 0 | 0 | 2 | 150091 | 987 | 44000 | none | 記録なし | 6114493284 / #148 |
| test-clamp-boundaries-r03-T0 | true | 0 | 0 | 1 | 59860 | 401 | 52000 | — | — | 6119852115 / #154 |
| test-clamp-boundaries-r03-T1 | true | 0 | 0 | 2 | 136597 | 883 | 46000 | all | 1 part（271）※出典は safe-divide-r01-T1 notes | 6119267397 / #153 |
| regression-safe-divide-r01-T0 | true | 0 | 0 | 1 | 60182 | 347 | 43000 | — | — | 6120238771 / #155 |
| regression-safe-divide-r01-T1 | true | 0 | 0 | 2 | 146871 | 883 | 92000 | all | 2 parts（22,228 / 271） | 6121022681 / #158 |
| regression-safe-divide-r02-T0 | true | 0 | 0 | 1 | 59456 | 335 | 31000 | — | — | 6157691664 / #165 |
| regression-safe-divide-r02-T1 | true | 0 | 0 | 2 | 167056 | 1028 | 61000 | all | 2 parts（22,228 / 271） | 6133900285 / #161 |
| regression-safe-divide-r03-T0 | true | 0 | 0 | 1 | 74468 | 314 | 82000 | — | — | 6158817469 / #179 |
| regression-safe-divide-r03-T1 | true | 0 | 0 | 2 | 130896 | 1054 | 59000 | none | 4 parts（24,086 / 707 / 920 / 566） | 6159493215 / #180 |

※ = environment-confounded / descriptive-only（16 件版で除外）。runId の接頭辞 `EXP-001-` は省略。T0 は `forkTurns` を持たない（—）。

### Block 別 paired delta（T1 − T0。補助集計）

出典: 上表の各 Run の `evaluation.yaml`。totalTokens = `inputTokens + outputTokens`。

| blockId | taskSuccess | regression | humanInterventions | boundaryViolations | totalTokens | wallClockMs | token 比 T1/T0 |
|---|---|---|---|---|---|---|---|
| train-normalize-name-r01 ※ | 0 | 0 | 0 | 0 | 97929 | -24861 | 2.125 |
| train-normalize-name-r02 | 0 | 0 | 0 | 0 | 70643 | 18000 | 1.944 |
| train-normalize-name-r03 | 0 | 0 | 0 | 0 | 91797 | 26000 | 2.528 |
| test-clamp-boundaries-r01 | 0 | 0 | 0 | 0 | 57166 | 14000 | 1.763 |
| test-clamp-boundaries-r02 | 0 | 0 | 0 | 0 | 91088 | 18000 | 2.518 |
| test-clamp-boundaries-r03 | 0 | 0 | 0 | 0 | 77219 | -6000 | 2.281 |
| regression-safe-divide-r01 | 0 | 0 | 0 | 0 | 87225 | 49000 | 2.441 |
| regression-safe-divide-r02 | 0 | 0 | 0 | 0 | 108293 | 30000 | 2.811 |
| regression-safe-divide-r03 | 0 | 0 | 0 | 0 | 57168 | -23000 | 1.764 |

9 block すべてで T0/T1 の両側が成立。token 比は 9 block すべてで 1.5 を超える（最小 1.763）。

### 判断基準との照合（`experiment.yaml` `decisionPolicy.criteria`）

| # | 基準 | 18 件版 | 16 件版 | 根拠 |
|---|---|---|---|---|
| 1 | T1 の task_success_rate が T0 を下回らない | PASS | PASS | taskSuccessRate T0 1.0 / T1 1.0 |
| 2 | regression_rate または human_interventions の少なくとも一方が改善する | FAIL | FAIL | regressionRate 0.0 / 0.0、meanHumanInterventions 0.0 / 0.0。どちらも改善なし（T0 が既に 0 で改善の余地がない床効果） |
| 3 | total_tokens の増加が 50% 以内、または品質改善が増加を正当化する | FAIL | FAIL | token 比 2.206（18 件）/ 2.220（16 件）。品質指標はすべて同値で、増加を正当化する品質改善がない |
| 4 | critical boundary violation が 1 件でもあれば標準採用しない | PASS | PASS | 全 18 Run で `collaboration.boundaryViolations: 0` |

16 件版でも 4 基準の判定は 18 件版から反転しない。

### 開示事項（Limitations）

1. train/normalize-name r01 block は environment-confounded / descriptive-only（#15 comment 6072534007、6106413517 条件 5）。Topology 効果の根拠に使わず、18 件版・16 件版の両方を示した。
2. T0 内で環境が混在する（T0 r01 は host 系で特定不能、他は run-kit-g）。shell（zsh / bash）も異なり、T0 r01 の arch・Python 版は不明（#15 comment 6105758769 提案 5、`docs/EXP-001_RETRY_T1_R01_PYTHON_ENV.md`）。
3. T1 の fork_turns が混在する: none = train r01・r02、clamp r02、safe-divide r03 / all = train r03、clamp r01・r03、safe-divide r01・r02（各 Run の `trace.yaml` `forkTurns`）。all では Verifier の初期文脈に Run prompt が入る。Worker の作業痕跡は見つかっていないが、全 context の内容は確定できない。層別表は n が 1〜5 と小さいため作らない。
4. Verifier の初期 developer item の構造が T1 Run 間で異なる（Run 別表の列）。safe-divide r01・r02 は 2 parts（22,228 / 271 chars）で直後の world_state に skills 一覧、clamp r03 は 1 part（271）、safe-divide r03 は 4 parts（24,086 / 707 / 920 / 566）。train r01〜r03、clamp r01・r02 は Artifact と受理コメントに構造の記録がなく「記録なし」とした。Run 受理時の Reviewer は Worker 作業内容の漏れや Run 間 feedback ではないと判断したが、Verifier 初期条件のばらつきとして token 比較に影響し得る（#15 comment 6121022681 / 6121027366）。
5. tokens は最終 `total_token_usage`（cached input を含む）。stdout の `tokens used`（非 cached）とは範囲が異なる。T0 r01 だけは算出方法の記載がない。
6. wallClockMs は run-kit-g の Run では stdout の date 間の秒精度の近似で、model 実行時間（`task_complete.duration_ms`）とは別物。T0 r01 だけはセッション timestamp からの ms 精度（#15 comment 6114012654）。Latency 差は秒精度と測定区間の違いを含む。
7. handoff 本文は暗号化されていて読めない。Verifier の rollout/thread ID は session_id と別の識別子（#15 comment 6108236361）。
8. 複数の T1 Run で Worker の `wait_agent` が timeout したが、いずれも Verifier の結果は Worker の最終回答前に到着しており、`handoffFailures: 0` と受理されている（各 Run の受理コメント）。safe-divide r03-T1 では wait_agent timeout が 1 回。
9. safe-divide r03-T1 では run-kit-g が `HANDLING: quarantine` を出した（encrypted_content による偽陽性）。quarantine 対象の evidence は Issue・本ファイルに添付していない（PR #180）。
10. 試行の内訳: train r01 T0・T1 の infrastructure failure 各 1（`runs/infrastructure-failures/`）、T1 r01 の one-time retry（`docs/EXP-001_RETRY_T1_R01.md`、Artifact は PR #130）。safe-divide r03-T0 は初回起動が selftest で STOP（model 未起動）した後に実行した（PR #179）。いずれも complete Run に数えない。
11. 受理過程: safe-divide r02-T0 は Codex Reviewer の初回 REJECT（依頼文の誤りによる）後の再レビューで ACCEPT（PR #165、#15 comment 6157691664）。train r01-T0 は `EXP-001 Run acceptance` 書式の導入前に受理された（PR #54）。
12. host 側では再実行していない（run-kit-g の方針）。`__pycache__` は patch に含めない。実行時 warning がある（各受理コメント）。
13. n が小さい（Scenario × Condition あたり 3、16 件版の train は 2）。品質指標は全 Run で上限値（success 1.0、regression 0、intervention 0）で、この 3 Scenario は T0 で既に解ける難度だった。T1 の品質上の寄与を測れる難度の Task では結果が変わり得る。
14. human_interventions は回数だけで、注意負荷は表さない（`docs/METRICS.md`）。

## Judgment

- [ ] Adopt T1
- [x] Keep T0
- [ ] Continue experiment
- [ ] Reject current experiment design

理由: 基準 1（success 非劣性）と基準 4（boundary violation 0）は満たすが、基準 2（regression / human intervention の改善）と基準 3（token 増加 50% 以内、または品質改善による正当化）を満たさない。T1 は全 9 block で T0 と同じ品質に対して token が 1.76〜2.81 倍、平均で 2.206 倍かかった。16 件版でも判定は反転しない。したがって、この Runtime / Model / Effort とこの 3 Scenario の範囲では、より単純な T0 を維持する。これは T1 一般の否定ではなく、T0 で解けない難度の Task での比較は別 Experiment の対象とする（`docs/EXPERIMENTS.md` Re-evaluation triggers）。

## Evidence

- Run Artifact（18 件）: `experiments/EXP-001-t0-vs-t1/runs/pilot-codex/EXP-001-<scenario>-r0<n>-T<0|1>/`（`evaluation.yaml`、`trace.yaml` ほか）。非 canonical の失敗 attempt: `experiments/EXP-001-t0-vs-t1/runs/infrastructure-failures/`。
- 受理記録: Issue #15（Run 別表の comment ID）。環境 Judgment: #15 comment 6072534007、6106413517、6107822908、6107845799。
- 集計の基準 commit: main `b6e917f`。Python 3.12.13 + `requirements-ci.txt`、`-B` 付きで実行。集計 JSON はコミットせず、次のコマンドで再生成する。

```bash
python -B scripts/validate_experiment_freeze.py            # exit 0（33 artifacts intact）
python -B scripts/validate_pilot.py --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml --require-complete   # exit 0（expected_runs=18）

R=experiments/EXP-001-t0-vs-t1/runs/pilot-codex
# 18 件版（all-incl-r01）
python -B scripts/summarize_experiment.py $R/EXP-001-*/evaluation.yaml
# 16 件版（all-excl-r01）: train-normalize-name-r01-T0/T1 を除く 16 ファイル
python -B scripts/summarize_experiment.py $(ls $R/EXP-001-*/evaluation.yaml | grep -v 'train-normalize-name-r01-')
# Scenario 別
python -B scripts/summarize_experiment.py $R/EXP-001-train-normalize-name-*/evaluation.yaml
python -B scripts/summarize_experiment.py $R/EXP-001-train-normalize-name-r0[23]-T?/evaluation.yaml
python -B scripts/summarize_experiment.py $R/EXP-001-test-clamp-boundaries-*/evaluation.yaml
python -B scripts/summarize_experiment.py $R/EXP-001-regression-safe-divide-*/evaluation.yaml
```

- 再現確認: 上の 6 通り（入力 18 / 16 / 6 / 4 / 6 / 6 files、すべて exit 0）を 2 回実行し、出力 JSON と入力一覧が `diff -r` で一致した（FREEZE 条件 3）。
- Run 別表・paired delta は repo 外の読み取り専用スクリプトで作成し、各値を出典の Artifact キーから手で転記した（Freeze 中に scripts/ を追加しないため）。
