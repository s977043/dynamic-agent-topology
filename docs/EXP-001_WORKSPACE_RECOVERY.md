# First T0 pre-execution workspace recovery — #48

The original fixture workspace was created on an ephemeral Actions runner. #25 and #32 committed only preparation metadata and prompt. #32 records revision-3 regeneration and empirical runs 0/18; #15 still records no empirical invocation. No model/runtime session was launched during this recovery.

Exception reviewed independently from bug/lifecycle and safety perspectives and merged in #49 (`4883e3dfc99248bbc2aaa55d202fbecfe44ff831`). No observed empirical, aborted or infrastructure-failed runtime session was retried.

- Run: `EXP-001-train-normalize-name-r01-T0`
- Original preparation commits: `095641192730d5325f6df251fb54d7ce7d34a299` (#25), `5b805650175a88685d54cefa9c267fe0cb1cf64f` (#32).
- Original #25 Actions run: `37220642557`; #32 PR records subsequent one-shot regeneration.
- Original workspaceId: `exp001-train-normalize-name-r01-t0-workspace`
- Recovered workspaceId: `exp001-train-normalize-name-r01-t0-recovered48-workspace`
- Original `run-meta.yaml` SHA-256: `d437cc596563de65bcd1e14008a062a07f1e7ce042867dd239f680d661f81de5`
- Original `prompt.md` SHA-256: `13159407859bc4486d9f7a7e042c62a51e8605bcc24e1f57ed89b76e5e3e36c8`
- Original directory preserved outside all DAT checkouts and the experimental workspace.
- Frozen revision-3 prepare script used unchanged on a fresh Operator-host workspace.
- Prompt byte comparison: identical.
- Parsed metadata comparison: identical except `spec.workspaceId`.
- Recovered workspace file set/content: identical to frozen train fixture.
- Feature Freeze validation: intact, 33 artifacts.

Recovery establishes fresh preparation only. Execution attestation, runtime measurements and results must come from the subsequent actual session. Recovery notes and archive are not supplied to that session.
