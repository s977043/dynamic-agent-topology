# EXP-001 Execution Handoff

この文書は、EXP-001の実行を開始するための**ナビゲーション専用**です。実験条件や評価意味論を定義する文書ではありません。

> **この文書は実験条件のSource of Truthではありません。**

正本は次です。

1. Feature Freeze: `experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md`
2. Pilot condition: `experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml`
3. Run order: `experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml`
4. Operator procedure: `experiments/EXP-001-t0-vs-t1/pilot/OPERATOR.md`
5. Runbook: `experiments/EXP-001-t0-vs-t1/pilot/RUNBOOK.md`
6. Live progress: GitHub Issue #15

内容が矛盾した場合は、上記の正本を優先します。この文書の役割は、正本へ安全に到達し、実Run開始前後の操作順を迷わないようにすることです。

## Current boundary

DATはCodex Runtimeを自動起動しません。

DATが担当するのは:

- Run順序の固定
- fresh workspaceの準備
- Prompt / provenanceの固定
- Artifact validation
- completeness / summary / decisionの検証

実際のCodex sessionはOperatorが外部で起動します。

## Preflight

実Run開始前にFreezeがintactであることを確認します。

```bash
python scripts/validate_experiment_freeze.py
```

次に現在のRun状態を確認します。

```bash
python scripts/pilot_status.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml
```

Preflightが失敗した場合はRunを開始せず、Issue #15を停止して原因を確認します。

## Runtime boundary

このRepositoryとOperator Kitは、Codex sessionを起動・代替しません。

実測Runとして認めるには、Pilotで固定されたRuntime / Model / Effortを満たす**実際のCodex session**が必要です。GitHub CIやArtifact生成だけではempirical runになりません。

## Handoff checkpoint after PR #54

PR #54（merge commit `a718293`）で最初のT0 `EXP-001-train-normalize-name-r01-T0` はsingle-run validationを通過し、独立レビューで受理されています。checkpoint時点のcomplete empirical runsは **1 / 18** です。最初のinfrastructure failureはcanonical Runとは分離して保存され、retry accountingも記録済みです。

このcheckpointはhistorical recordであり、この文書はlive trackerではありません。**現在の次Run・停止条件・attempt countはIssue #15を正本**としてください。#54時点の次matrix itemは `EXP-001-train-normalize-name-r01-T1` です。

実workspaceを作っていない状態で `run-meta.yaml` や結果ArtifactだけをGitHub上に先行生成しません。prepareはOperator hostでfresh workspaceを実際に作る操作と一体です。

## First blockのdispositionと進行判断

最初のblock `EXP-001-train-normalize-name-r01` は履歴として参照します。

- T0はPR #54でvalidation PASS・独立レビューACCEPTとなりました。同じrunIdを再prepare / 再実行しません。
- T1のpreparationはPR #81、不完全attemptの保存は [PR #86](https://github.com/s977043/dynamic-agent-topology/pull/86) にあります。
- 2026-10-07の [Issue #15本文](https://github.com/s977043/dynamic-agent-topology/issues/15) はT1 r01を **ABORTED / not accepted / no retry** と記録し、次の固定slot r02-T1への進行を示しています。これはcomplete Run受理やT1再試行の許可ではありません。

実行直前にIssue #15の最新disposition、独立review record、固定matrix、Operator procedureの進行gateを照合します。Issue本文の進行記載だけで、前RunのReviewer `ACCEPT` を必要とする通常gateを置き換えません。archive保存のレビューと次slotへの進行判断も別です。通常gateを満たさない場合や、review recordと契約に不明点・矛盾がある場合は、Issue #15に停止理由を残し、整合が確認されるまでprepare / 実行を開始しません。過去のprepare例や古いcheckpointを現在の実行指示として使いません。

`pilot_status.py` はcanonical directoryのArtifact有無を表示します。外部保存の不完全attemptとno-retry判断を扱うlive trackerはIssue #15です。`prepared` 表示だけを根拠に同じrunIdを再実行しません。

## T1 r01 reviewed retry exception

T1 r01のarchive保存（PR #86）だけではRun acceptanceやretry許可になりません。

Issue #97で検討した [T1 r01 one-time infrastructure retry](EXP-001_RETRY_T1_R01.md) は、このprocedureを含むPRがレビュー・mergeされた後に限り、`python -m unittest ...` がRuntime内で起動できず、T1 Verifier phaseも未完了だった不完全attemptに対する**Run固有の一度限り例外**です。

この例外を適用する場合も:

- 元attemptを削除・上書きしない
- retry前にnormal experimental sandboxで凍結Evidence commandの起動性を非model確認する
- Prompt / Fixture / Runtime / Model / Effort / T1 Role Contractを変更しない
- fresh workspace / fresh sessionを使う
- retry allowanceはmodel invocation開始時に消費する
- complete fail / inconclusiveも結果として保持し再retryしない
- retry後もsingle-run validation + manual consistency review + Reviewer `ACCEPT` まで次slotへ進まない

というgateを維持します。

## 次slotの操作前に確認するgate

1. Freeze preflightとstatus表示を確認する。
2. 前RunのReviewer `ACCEPT` と固定matrix順の整合を確認する。ABORTEDなどで通常gateを満たさない場合は停止し、Issue #15のdispositionと契約の整合を独立レビューで確認する。本文の「進行可能」だけでprepareしない。
3. [Operator procedure](../experiments/EXP-001-t0-vs-t1/pilot/OPERATOR.md) に従い、未使用のfresh external workspaceとunique workspaceIdでprepareする。既存runIdのpreparationを置き換えない。
4. 初期fixtureとexpected initial Evidence FAILを確認する。ここでのFAILは、指定Evidence commandが実行され、fixtureの不具合による想定されたテスト失敗を観測した状態。`python`不在のexit 127やsandbox起動失敗は、テスト未実行の環境障害として区別し、停止理由を記録する。
5. Operatorが固定Runtime / Model / Effort、fresh session、当該promptだけで実行する。
6. [Artifact Capture Guide](EXP-001_ARTIFACT_CAPTURE.md) に従い観測Artifactを保存し、single-run validationとmanual cross-artifact reviewを行う。
7. 結果PRのreview commentに `EXP-001 Run acceptance: ACCEPT | BLOCK` を記録する。次のmatrix itemはACCEPT後に進める。不完全attemptのdispositionを記録しても、ACCEPTや契約に整合した進行判断の代わりにはならない。

Blocking defectが見つかった場合は、次Runへ進まずIssue #15を停止し、Feature Freezeの例外手続きに従います。

指定Evidence commandはScenarioの正本を使います。Repositoryの静的validatorを`python3`で実行できても、凍結されたRun commandの置換やRuntime内での実行成功を意味しません。

## 最終完了との区別

残りslotへの進行は、Freeze解除やT0/T1の比較判断を意味しません。Run途中のPrompt / Role / Topology / Scenario / Fixture / Model / Effort / Evaluation semantics改善は禁止されたままです。

T1 r01を再試行しない判断と、Freezeの18/18 complete・最終completeness PASSという条件の整合は、Issue #15で解決すべき完了ゲートです。残りslotを終えてもaborted slotをcompleteとして数えず、欠けたpaired blockを比較結果へ含めません。凍結契約を変更する必要があるかも含めてレビューし、文書だけで解除条件を緩めません。

## Status check

```bash
python scripts/pilot_status.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml
```

`artifacts-present` はsemantic completionではありません。

18 / 18 Run完了後の最終判定は:

```bash
python scripts/validate_pilot.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml \
  --require-complete
```

です。

## Do not do

- この文書を根拠に凍結Artifactを変更しない
- Run結果を見てPromptやTopologyを改善しない
- 実Runtime未実行のArtifactを生成・推測しない
- 不足値を0で埋めない
- 他RunのArtifactをfresh sessionへ持ち込まない

Live progressと次アクションはIssue #15で管理します。


## Result capture

実Codex Run終了後のArtifact記録は [EXP-001 Artifact Capture Guide](EXP-001_ARTIFACT_CAPTURE.md) を参照してください。
