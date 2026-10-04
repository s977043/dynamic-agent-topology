# Dogfooding Evidence

DATのdogfoodingでは、「導入できた」ことと「Topologyが優れている」ことを分離して記録します。

## ADOPT-001 — notionnext-blog

**Date:** 2026-10-04  
**Consumer:** https://github.com/s977043/notionnext-blog  
**Consumer Issue:** https://github.com/s977043/notionnext-blog/issues/615  
**Consumer PR:** https://github.com/s977043/notionnext-blog/pull/616  
**DAT Revision:** `717a03fa389fb77a47694b9cf8a0c6e97ac0888b`

### Adoption configuration

- rollout stage: **A2 Observe**
- runtime: **Codex**
- topology: **T0 Single Agent**
- adapter mode: **manual**
- runtime config: `AGENTS.md`
- evidence binding: `pnpm test`
- lock mode: **pinned**

### Observed result

Consumer PR #616 で次を確認しました。

- DAT External Project Validator: **PASS**
- `--require-pinned`: **PASS**
- consumer `content-ci` / `pnpm test`: **PASS**
- spec-sync-check: **PASS**
- readme-sync-check: **PASS**
- article-risk-gate-check: **PASS**
- unresolved review thread: **0**
- merge後mainの DAT Validate: **PASS**

### What this evidence supports

このdogfoodは、次を支持します。

1. 完全な `.dat/` Reference Layoutを既存Repoへ追加できる。
2. DAT本体をcommit SHAでpinし、consumer CIからExternal Project Validatorを実行できる。
3. A2 Observe / T0 / Manual Adapterを、既存Agent設定や既存品質ゲートを変更せず導入できる。
4. `ProjectBinding / EvidenceProfile / ProjectPolicy / RuntimeBinding / DatLock` の参照整合を外部Repoで検証できる。
5. DAT導入と既存Repoのspec / test / review governanceを共存させられる。

### What this evidence does NOT support

このdogfoodだけでは、次を証明しません。

- T0がT1/T2より優れていること
- Multi-AgentがSingle Agentより優れていること
- Runtimeの実行が宣言Topologyへ完全にAdhereしていること
- Claude Code / Gemini CLI / Antigravityでも同じ導入結果になること
- Runtime Adapterの自動compile/applyが成立すること
- DATが任意のRepositoryへ無変更で導入できること
- 独立した第三者maintainerでも同じ導入体験になること（今回のconsumerはDATと同一GitHub owner配下）

### Friction observed

今回のA2導入では、DAT specification / validator側にBlockingとなる不足は見つかりませんでした。

Consumer側では、既存のTask/Spec/CI governanceへDAT Artifactを追加する作業が必要でしたが、既存Agent設定や開発フロー自体の変更は不要でした。

### Judgment

**Manual adoption path: PASS for one existing consumer repository with established CI/governance.**

これはv0.2.1のManual adoption contractに対する最初の外部dogfood Evidenceです。一般化には、別構成のRepository・別Runtime・可能なら独立maintainerによる追加dogfoodが必要です。
