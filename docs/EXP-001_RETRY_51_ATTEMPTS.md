# First T0 retry attempt accounting — #51

Policy: PR #53, merged commit `6ffe697` (docs/EXP-001_RETRY_51.md).

Original session `01a1095b-9caf-7691-a255-c0b434a5539a` remains one infrastructure failure: wallClockMs 90330; inputTokens 137613; cachedInputTokens 117248; outputTokens 538. No task command executed, no patch/evaluation.

Original workspaceId: `exp001-train-normalize-name-r01-t0-recovered48-workspace`.
New workspaceId: `exp001-train-normalize-name-r01-t0-retry51-workspace`.
Retry session: `01a10975-1997-7e33-bcb3-3d6c855b6471` (fresh exec; no resume/fork).
Current attempted sessions: 2; infrastructure failures: 1; complete matrix runs: 1/18.

Archive: `runs/infrastructure-failures/EXP-001-train-normalize-name-r01-T0/01a1095b-9caf-7691-a255-c0b434a5539a/`. All six files equal observation commit `d6d864e53ba149f36dc3efef97ac3e36583e6a78` byte-for-byte.

| File | SHA-256 |
| --- | --- |
| STOP-REPORT.md | `dc4f3c19bd626bce868bb9d0939da1b5942c5f5e6c510cdecba64e3c1249268c` |
| evidence.txt | `7f29a562e3ff9134f0041de798ddf340473d2c5268ba7bf7146f7adde64d85ce` |
| execution-attestation.yaml | `3933b7dcbd1597587a613d84ad709ff9d6dc101a582e5967ae96ce0d8c41fc44` |
| prompt.md | `13159407859bc4486d9f7a7e042c62a51e8605bcc24e1f57ed89b76e5e3e36c8` |
| run-meta.yaml | `95733298397bb7fa8346beca9899de0c815be6a1d19b3391c271464ea80b678f` |
| trace.yaml | `eaaeedf532b27229c735616f7b6e0f8b09dc9f42420f0147f2117835c6a9722b` |

Preparation checks: prompt bytes identical; parsed metadata equal except workspaceId; fresh external workspace matches the frozen fixture file set and bytes; 33 frozen artifacts unchanged. Initial deterministic tests: 2 run, 1 expected failure (ALICE != alice). At most one new invocation is permitted. Original stop instructions are historical; the reviewed #53 exception governs this attempt.

Non-model sandbox preflight: repository Python started; permitted inside write succeeded; outside write was denied with EROFS and created no file. Diagnostic profile is not used for the model run. Python bytecode writes are disabled.

Loop 2 independent reviews: contract and safety APPROVE, no blockers. Final fixture byte/file-set check PASS immediately before launch. The single retry allowance is consumed when the following CLI invocation starts; it cannot be used again after any outcome.

Retry observed result: PASS. Runtime wallClockMs 75861; inputTokens 86676; cachedInputTokens 67072; outputTokens 385. UTC start `2026-10-05T00:27:11.345383+00:00`, finish `2026-10-05T00:28:27.207199+00:00`. Model/effort independently read from actual persisted turn_context: gpt-6.1-sol / high. Worker changed only app.py and executed required unittest (2/2 PASS). Operator independently reran the tests after process completion (2/2 PASS); that recheck is not included in runtime wall-clock. The non-Git fixture caused a git-status inspection error (exit 1), retained in trace/evidence. No delegation or in-run human intervention occurred. No further retry is authorized by #53.

Post-capture gates: single-run semantic validation PASS; Feature Freeze 33/33 unchanged; pilot validator negative tests and Operator Kit tests PASS. Full `--require-complete` remains FAIL with 17 remaining runs (119 missing-file findings), as expected. T1 has not been prepared or invoked.
