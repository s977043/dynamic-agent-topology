1. **Feature Freeze**: 差分が EXP-001 の凍結対象（checkout 内の `experiments/EXP-001-t0-vs-t1/pilot/freeze.yaml` と `AGENTS.md` / `docs/AGENT_HARNESS.md` の Freeze 規定）に触れていないか。実験条件・schema・role・topology・評価方法を変えていないか。
2. **自律境界**: `docs/AGENT_HARNESS.md` の「自律境界」の規則変更 PR の対象（`AGENTS.md`、`CLAUDE.md`、`.claude/`、`.codex/`、`docs/AGENT_HARNESS.md` の規則、`scripts/validate_agent_guidance.py`、Guard の hook や検査スクリプト。merge は Human）、別モデルの独立レビューが必須の依存の追加、その他の Human 専権の操作を含むか。含む場合、PR 本文がそれを明記しているか。検査を弱める変更（validator・Guard の判定を緩める、必須チェックを外す）なら、その旨が PR 本文に書かれているか。
3. **正しさ**: PR 本文の Summary・Scope と差分が一致しているか。変更したコードに、テストや CI（`.github/workflows/spec-lint.yml`）で確かめられていない動作がないか。
4. **安全**: 秘密値、破壊的操作を許可する記述、承認ゲートの迂回を勧める記述がないか。
