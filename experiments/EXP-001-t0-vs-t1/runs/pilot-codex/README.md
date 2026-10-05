# Pilot Run Artifacts

EXP-001 Codex Pilotの実Run Artifactを保存する場所です。

各canonical run directoryは、prepare時に:

- `run-meta.yaml` — run / block / scenario / condition、repetition、executionOrder、`workspaceId`、Prompt hash
- `prompt.md` — そのRunへ渡す固定Prompt

を持ちます。

実行後は、観測できた事実に基づいて:

- `execution-attestation.yaml` — actual `sessionId`、fresh-session / cross-run-feedback、Runtime / Model / Effort、start / finish
- `trace.yaml` — 実行Trace
- `evaluation.yaml` — RunEvaluation
- `patch.diff` — 実装差分
- `evidence.txt` — deterministic Evidence

を保存します。`sessionId` は `run-meta.yaml` ではなく post-run の `execution-attestation.yaml` に記録します。`workspaceId` と `sessionId` は秘密値を入れないopaque IDです。

## Checkpoint after PR #54

PR #54（merge commit `a718293`）で `EXP-001-train-normalize-name-r01-T0` がsingle-run validationを通り、checkpoint時点のcomplete empirical runsは **1 / 18** です。次のmatrix itemは `EXP-001-train-normalize-name-r01-T1` ですが、実workspaceの作成とfresh Codex session実行はOperator hostで行います。GitHub上のArtifactだけを先に捏造しません。

最初のT0には、canonical complete Runとは別にinfrastructure failureが1 attemptあります。原本は隣接する `../infrastructure-failures/` に保存し、[attempt accounting](../../../../docs/EXP-001_RETRY_51_ATTEMPTS.md) に両sessionを記録しています。

これはhistorical checkpointであり、T0/T1比較やPilot完了を意味しません。Live progressと次アクションはIssue #15を正本とします。

Runbookは [../../pilot/RUNBOOK.md](../../pilot/RUNBOOK.md) を参照してください。
