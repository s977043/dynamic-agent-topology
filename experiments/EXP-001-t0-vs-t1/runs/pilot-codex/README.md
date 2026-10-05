# Pilot Run Artifacts

EXP-001 Codex Pilotの実Run Artifactを保存する場所です。

各runは `<runId>/run-meta.yaml`, `trace.yaml`, `evaluation.yaml`, `patch.diff`, `evidence.txt` を持ちます。`run-meta.yaml` の sessionId / workspaceId は秘密情報ではなくPilot用の一意なopaque IDを記録します。

最初のT0実測Runは結果Artifactとsingle-run検証の対象になっています。18件のPilot完了やT0/T1比較を意味しません。元のinfrastructure failureは隣接する`../infrastructure-failures/`へ原本を保存し、[attempt accounting](../../../../docs/EXP-001_RETRY_51_ATTEMPTS.md)に両sessionを記録しています。Runbookは [../../pilot/RUNBOOK.md](../../pilot/RUNBOOK.md) を参照してください。
