1. **Feature Freeze**: 差分が EXP-001 の凍結対象（checkout 内の `experiments/EXP-001-t0-vs-t1/pilot/freeze.yaml` と `AGENTS.md` / `docs/AGENT_HARNESS.md` の Freeze 規定）に触れていないか。実験条件・schema・role・topology・評価方法を変えていないか。
2. **自律境界**: `docs/AGENT_HARNESS.md` の「自律境界」で人間の承認が要る変更（`AGENTS.md`、`CLAUDE.md`、`.claude/`、`.codex/`、ハーネスの規則・Guard、`scripts/validate_agent_guidance.py`）を含むか。含む場合、PR 本文がそれを明記しているか。
3. **正しさ**: PR 本文の Summary・Scope と差分が一致しているか。変更したコードに、テストや CI（`.github/workflows/spec-lint.yml`）で確かめられていない動作がないか。
4. **安全**: 秘密値、破壊的操作を許可する記述、承認ゲートの迂回を勧める記述がないか。
