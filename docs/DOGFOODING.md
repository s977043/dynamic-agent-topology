# Dogfooding Evidence

DATのdogfoodingでは、**「導入できた」こと**と**「Topologyが優れている」こと**を分離して記録します。

## ADOPT-001 — notionnext-blog

| Field | Value |
|---|---|
| Date | 2026-10-04 |
| Consumer | `s977043/notionnext-blog` |
| Consumer Issue | `#615` |
| Consumer PR | `#616` |
| DAT Revision | `717a03fa389fb77a47694b9cf8a0c6e97ac0888b` |

Consumer links:

- Issue: https://github.com/s977043/notionnext-blog/issues/615
- PR: https://github.com/s977043/notionnext-blog/pull/616

### Adoption configuration

- rollout stage: **A2 Observe**
- runtime: **Codex**
- topology: **T0 Single Agent**
- adapter mode: **manual**
- runtime config: `AGENTS.md`
- evidence binding: `pnpm test`
- lock mode: **pinned**

### Observed result

Consumer PR #616とmerge後mainで次を確認しました。

- DAT External Project Validator: **PASS**
- `--require-pinned`: **PASS**
- consumer `content-ci` / `pnpm test`: **PASS**
- `spec-sync-check`: **PASS**
- `readme-sync-check`: **PASS**
- `article-risk-gate-check`: **PASS**
- unresolved review thread: **0**
- merge後mainの DAT Validate: **PASS**

PR headでは上記5つの品質・整合Workflowがsuccessし、merge commit `f7a5b2721e0c784ea054734e4aaa2f3211f00cea` に対するmainのDAT Validateもsuccessしました。

### Evidence provenance

この記録は、consumer Issue / PR、GitHub Actions結果、merge後main、pinされたDAT revisionをmaintainer側で照合したdogfood Evidenceです。

ただし、**maintainer-operated dogfoodは独立した第三者再現ではありません。** 外部読者が同じconsumer Evidenceへ常にアクセスできるとも限らないため、この記録だけをpublic benchmarkや第三者再現性の証拠として扱いません。

### What this evidence supports

このdogfoodは、次を支持します。

1. 完全な`.dat/` Reference Layoutを既存Repositoryへ追加できる。
2. DAT本体をcommit SHAでpinし、consumer CIからExternal Project Validatorを実行できる。
3. A2 Observe / T0 / Manual Adapterを、既存Agent設定や既存品質ゲートを変更せず導入できる。
4. `ProjectBinding / EvidenceProfile / ProjectPolicy / RuntimeBinding / DatLock` の参照整合を外部Repositoryで検証できる。
5. DAT導入と既存Repositoryのspec / test / review governanceを共存させられる。

### What this evidence does NOT support

このdogfoodだけでは、次を証明しません。

- T0がT1/T2より優れていること
- Multi-AgentがSingle Agentより優れていること
- Runtimeの実行が宣言Topologyへ完全にAdhereしていること
- Claude Code / Gemini CLI / Antigravityでも同じ導入結果になること
- Runtime Adapterの自動compile/applyが成立すること
- DATが任意のRepositoryへ無変更で導入できること
- 独立した第三者maintainerでも同じ導入体験になること
- public benchmarkとして一般化できること

### Friction observed

今回のA2導入では、DAT specification / validator側にBlockingとなる不足は見つかりませんでした。

Consumer側では、既存のTask / Spec / CI governanceへDAT Artifactを追加する作業が必要でしたが、既存Agent設定や開発フロー自体の変更は不要でした。

### Judgment

**Manual adoption path: PASS for one existing consumer repository with established CI/governance.**

これは現行Manual adoption contractに対する最初の外部dogfood Evidenceです。一般化には、別構成のRepository、別Runtime、可能なら独立maintainerによる追加dogfoodが必要です。

## OBS-H1 — RunObservation の取得率（H1）

| Field | Value |
|---|---|
| 測定日時 | 2026-10-23 12:01 JST |
| 対象 | 段階 4 の dogfooding で保存先に保存された `RunObservation` 全件 |
| 記録件数 | 21 件 |
| リポジトリ数 | 6 |
| 判定規則の出典 | [RUN_OBSERVATION_DESIGN.md](RUN_OBSERVATION_DESIGN.md) §2 H1、§8 段階 4 |

### 取得率

「取得」は値が `unknown` でないこと（`0` や `[]` は取得に数える）。分母は全記録 21 件で固定し、`unknown` は分母に残す（§2）。`reviews` の指摘数は、`reviews` が `unknown` でなく、各要素の `findings.blocking` と `findings.nonBlocking` がともに `unknown` でない記録を取得とした。`rework` は `rework.count` で数えた。

| 項目 | 取得 / 全件 | 取得率 | 既存台帳の値 |
|---|---|---|---|
| `outcome` | 21 / 21 | 100% | 11% |
| `endedAt` | 13 / 21 | 61.9% | 0% |
| `reviews` の指摘数 | 21 / 21 | 100% | 25% |
| `rework` | 21 / 21 | 100% | 14〜22% |
| `runtime` | 21 / 21 | 100% | 0% |
| `model` | 20 / 21 | 95.2% | 0% |

### Judgment

**H1: INCONCLUSIVE（中間）。**

§2 の順に当てはめた。記録は 20 件以上・2 リポジトリ以上で前提不足には当たらない。50% 未満の項目はなく棄却に当たらない。`endedAt` が 80% 未満のため支持に当たらない。INCONCLUSIVE は採否の根拠にしない。

### 補足

- 記録の単位: 2026-10-23 以降の記録は作業の区切り単位、それ以前はウェーブ単位で、両者が混在している。H1 は記録単位の取得率なので、この混在は判定に影響しない
- 未取得の主因の見立て（推測・未確認）: 未取得 9 件のうち 8 件が `endedAt` の `unknown` で、記録時に終了時刻を確かめる情報源がなかった可能性がある
- 次の手順の候補（決定ではない）: dat-observe の記録手順で `endedAt` に記録時刻を入れる。手順を変えた場合は、変更後の新しい記録で H1 を判定し直す
- H2（`topologyEquivalent` の再現性）は未判定
