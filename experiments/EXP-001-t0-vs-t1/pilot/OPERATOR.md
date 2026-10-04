# EXP-001 Operator Kit

Operator KitはCodexを自動実行しません。18 Runの**準備・順序・provenance・進捗**をDAT側で統制します。

## 1. 次Runを確認

```bash
python scripts/pilot_status.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml
```

`executionOrder` はpaired block内の先行条件です。matrixの順序を変更しません。

## 2. Runを準備

例:

```bash
python scripts/prepare_pilot_run.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml \
  --run-id EXP-001-train-normalize-name-r01-T0 \
  --workspace /tmp/dat-exp001-r01-t0 \
  --session-id exp001-r01-t0-session \
  --workspace-id exp001-r01-t0-workspace
```

条件:

- `--workspace` は存在していてはいけません。
- `--workspace` はDAT repositoryの外側に置きます。これによりCodex sessionから他Run Artifactへ親ディレクトリ経由で到達しにくくします。
- session/workspace IDはPilot内で一意な**非秘密のopaque ID**にします。
- providerのtoken、API key、private path等をIDへ入れません。
- 同じrunIdを再prepareしません。再試行が必要ならRunを失敗として保存してから、実験計画を明示的に改訂します。
- `prompt.md` のSHA-256を `run-meta.yaml` に保存し、完了検証時にPrompt改変を検出します。

生成物:

```text
workspace/
└── fixtureのfresh copy

runs/pilot-codex/<runId>/
├── run-meta.yaml
└── prompt.md
```

ここでは結果Artifactを生成しません。

## 3. Codexを実行

1. fresh workspaceでScenarioの初期deterministic Evidenceが失敗することを確認する。初期状態でPASSする場合はRunを開始せず、#15で停止理由を記録する。
2. 新しいCodex session/contextを開始する。
3. 対象Runの `prompt.md` だけを入力として使う。
4. Run開始時点を記録し、終了時点との差分から `wallClockMs` を実測する。
5. 他RunのArtifact/結果を参照しない。
6. T0/T1のRole Contractを変更しない。
7. Run終了後、Trace / Evaluation / patch / Evidenceを保存する。

## 4. 進捗状態

`pilot_status.py` は次だけを表示します。

- `planned`: 未準備
- `prepared`: run-meta + promptのみ
- `in-progress`: 結果Artifactが一部存在
- `artifacts-present`: 必要ファイルは存在しnon-empty
- `invalid`: preparation/result file setが不正

**artifacts-present ≠ complete** です。

各Run終了後は、そのRunだけをsemantic validationします。

```bash
python scripts/validate_pilot.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml \
  --run-id <runId>
```

このsingle-run validationがPASSするまで、paired blockの次Runへ進みません。

18 Runすべての最終completionは:

```bash
python scripts/validate_pilot.py \
  --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml \
  --require-complete
```

で判定します。
