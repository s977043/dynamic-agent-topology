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

## First paired block

最初に実行するblockは:

`EXP-001-train-normalize-name-r01`

run-matrix上の順序は固定です。

### 1. T0 — executionOrder 1

`EXP-001-train-normalize-name-r01-T0`

準備:

```bash
python scripts/prepare_pilot_run.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml \
  --run-id EXP-001-train-normalize-name-r01-T0 \
  --workspace /tmp/dat-exp001-train-normalize-name-r01-t0 \
  --workspace-id exp001-train-normalize-name-r01-t0-workspace
```

次に、生成された `prompt.md` をfresh Codex sessionへ渡します。

Run終了後、まず実行事実を `scripts/attest_pilot_run.py` で `execution-attestation.yaml` に記録します。その後、次を保存します。

- `execution-attestation.yaml`
- `trace.yaml`
- `evaluation.yaml`
- `patch.diff`
- `evidence.txt`

T0 Runだけを検証:

```bash
python scripts/validate_pilot.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml \
  --run-id EXP-001-train-normalize-name-r01-T0
```

この検証がPASSするまでT1をprepareしません。

Gitにprepare済みArtifactがあっても、Operator hostの実workspaceが利用可能かは別途確認します。最初のT0で一時runnerのworkspaceが失われている場合は、[Operator Kitの #48 復旧例外](../experiments/EXP-001-t0-vs-t1/pilot/OPERATOR.md)に従います。例外の独立レビュー・merge前に同じrunIdを再prepareしません。

### 2. T1 — executionOrder 2

`EXP-001-train-normalize-name-r01-T1`

T0がsingle-run validationを通った後に同じ手順でprepareします。

```bash
python scripts/prepare_pilot_run.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml \
  --run-id EXP-001-train-normalize-name-r01-T1 \
  --workspace /tmp/dat-exp001-train-normalize-name-r01-t1 \
  --workspace-id exp001-train-normalize-name-r01-t1-workspace
```

T1もfresh Codex sessionで実行し、execution attestationを含む結果Artifactを保存してsingle-run validationを行います。

## After the first pair

最初の2 Runが完了しても、結果を見て次を変更しません。

- Prompt
- Role Contract
- Topology
- Scenario / Fixture
- Model / Effort
- Evaluation semantics

確認してよいのは、**実行パイプラインが成立したか**だけです。

Blocking defectが見つかった場合は、次Runへ進まずIssue #15を停止し、Feature Freezeの例外手続きに従います。

問題がなければrun-matrix順に残り16 Runを継続します。

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
