# provenance-audit fixtures（#57）

Issue #57 の設計用に作った**合成 fixture**です。実 Run ではなく、EXP-001 の Evidence として数えてはいけません。凍結済みの `fixtures/exp-001/` と EXP-001 の Run Artifact は使っていません。

各ケースは `pilot.yaml`（EXP-001 の `pilot.yaml` から `artifactRoot` と `notes` だけを変えたもの）と、`runs/EXP-001-train-normalize-name-r01-T0/` の 7 ファイルで構成されます。ケースごとに Attestation / Trace / Evaluation の関係を 1 つだけ壊しています。

## 再現コマンド

repo root で、ケースごとに既存の `scripts/validate_pilot.py` を single-run モードで実行します。

```bash
python scripts/validate_pilot.py \
  --pilot fixtures/provenance-audit/<case>/pilot.yaml \
  --matrix experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml \
  --run-id EXP-001-train-normalize-name-r01-T0
```

## ケースと観測結果（2026-10-14、Python 3.12、main 24fa06b）

| ケース | 壊した関係 | 現行 validator の exit | 監査で期待する判定 |
|---|---|---|---|
| `baseline-consistent` | なし（対照） | 0 | PASS |
| `ctl-trace-model-mismatch` | Trace `model.id` ≠ pilot / Attestation（既存の検査対象。fixture が validator に届いていることの対照） | 1 | FAIL |
| `neg-session-id-mismatch` | Trace start `details.sessionId` ≠ Attestation `spec.sessionId` | 0 | FAIL |
| `neg-fresh-session-mismatch` | Trace start `freshSession: false` / `crossRunFeedbackUsed: true`、Attestation は true / false | 0 | FAIL |
| `neg-timestamp-mismatch` | Trace start / finish の時刻が Attestation の `startedAt` / `finishedAt` と 1 時間以上ずれる | 0 | FAIL |
| `neg-token-mismatch` | Evaluation `efficiency.inputTokens` / `outputTokens` ≠ Trace `summary` | 0 | FAIL |
| `neg-summary-field-missing` | Trace `summary` に `wallClockMs` / `inputTokens` がなく、Evaluation 側だけに値がある | 0 | UNKNOWN |
| `neg-trace-session-unknown` | Trace start の `details` が空で、session 情報を観測できない | 0 | UNKNOWN |

exit 0 の負側ケース（`neg-*`）が、現行の検査の穴です。判定の意味と監査案の比較は [docs/PROVENANCE_AUDIT_DESIGN.md](../../docs/PROVENANCE_AUDIT_DESIGN.md) を参照してください。
