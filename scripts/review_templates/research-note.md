PR #{{PR}} は研究ノート（`knowledge/research/`）を追加する docs-only の変更です。

1. **Feature Freeze**: 差分が EXP-001 の凍結対象（checkout 内の `experiments/EXP-001-t0-vs-t1/pilot/freeze.yaml` と `AGENTS.md` / `docs/AGENT_HARNESS.md` の Freeze 規定）に触れていないか。実験条件・schema・role・topology・評価方法を変えていないか。
2. **Research-only の境界**: ノートが「採用済み」「実証済み」と読める書き方をしていないか。出典の主張と DAT の evidence を区別しているか。外部のコード・CLI・SDK・Skill の導入や実機起動を許可しているように読める記述がないか。
3. **索引と台帳の整合**: `knowledge/research/README.md` の規則（採用状態は `knowledge/sources.yaml` に記録する等）と、追加した行・リンク・Issue 番号が一致しているか。リンク先のファイルが checkout に存在するか。
4. **安全**: 秘密値、破壊的操作を許可する記述、承認ゲートの迂回を勧める記述がないか。
