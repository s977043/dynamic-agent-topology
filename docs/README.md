# Documentation

`docs/` は、Dynamic Agent Topology (DAT) の設計意図、導入手順、評価方法、実験運用、リポジトリ運用方針を説明する人間向けドキュメントです。

> Machine-readable な契約の正本は `schemas/`、`topologies/`、`roles/`、`policies/`、`experiments/` などの各Artifactです。ドキュメントと実装が矛盾する場合は、各文書で明示された Source of Truth を優先してください。

## Reading paths

### まず全体像を理解する

1. [NORTH_STAR.md](NORTH_STAR.md) — 何を解きたいか、何を最適化しないか
2. [ARCHITECTURE.md](ARCHITECTURE.md) — Topology / Policy / Runtime / Trace / Evaluation の責務分離
3. [GLOSSARY.md](GLOSSARY.md) — DATで使う主要用語
4. [ENGINEERING_LAYERS.md](ENGINEERING_LAYERS.md) — 失敗箇所をPrompt / Context / Harness / Loop / Graph / Evaluationで診断する補助レンズ

### 既存リポジトリへ導入する

1. [QUICKSTART.md](QUICKSTART.md) — 非破壊・Manual Adapter方式での最短導入
2. [ADOPTION.md](ADOPTION.md) — A0〜A5の段階導入とArtifact契約
3. [DOGFOODING.md](DOGFOODING.md) — 実リポジトリで確認済みの範囲と、まだ証明していない範囲

### 評価・実験を理解する

1. [EXPERIMENTS.md](EXPERIMENTS.md) — 比較実験、paired comparison、ablationの原則
2. [METRICS.md](METRICS.md) — Outcome / Quality / Cost / Collaboration をどう測るか
3. [EXP-001_EXECUTION.md](EXP-001_EXECUTION.md) — EXP-001実行時のナビゲーション
4. [EXP-001_ARTIFACT_CAPTURE.md](EXP-001_ARTIFACT_CAPTURE.md) — 実Run後のArtifact記録方法

### 公開リポジトリ運用を確認する

1. [PUBLIC_REPOSITORY_POLICY.md](PUBLIC_REPOSITORY_POLICY.md) — Git外にあるGitHub設定の意図と監査方針
2. [RELEASE_READINESS.md](RELEASE_READINESS.md) — release candidateの選定からtag / GitHub Release公開までのゲート

## Document roles

| Document | 主な責務 | 規範性 |
|---|---|---|
| `NORTH_STAR.md` | 目的・原則・非目標 | 設計原則 |
| `ARCHITECTURE.md` | 責務境界・Plane分離 | 設計原則 |
| `GLOSSARY.md` | 用語定義 | 用語上の基準 |
| `ENGINEERING_LAYERS.md` | 障害診断の補助レンズ | 診断ガイド |
| `ADOPTION.md` | 段階導入の契約 | 導入ガイド |
| `QUICKSTART.md` | 最短の導入手順 | 実行ガイド |
| `DOGFOODING.md` | 観測済みEvidenceと非主張 | Evidence記録 |
| `EXPERIMENTS.md` | 実験設計原則 | 実験ガイド |
| `METRICS.md` | 評価指標の意味 | 評価ガイド |
| `EXP-001_*` | EXP-001の実行・記録補助 | ナビゲーション / 運用ガイド |
| `PUBLIC_REPOSITORY_POLICY.md` | GitHub設定の目標状態 | 運用ポリシー |
| `RELEASE_READINESS.md` | Release candidateのEvidence / metadata / publication gate | Release運用チェックリスト |

## Writing conventions

- 説明文は日本語を基本とし、Schema field、Artifact kind、Runtime名、Metric IDなどの識別子は実装上の表記を維持します。
- `Evidence`, `Verifier`, `Topology`, `Runtime` など意味を持つDAT用語は、一般語として曖昧に言い換えず [GLOSSARY.md](GLOSSARY.md) の定義に合わせます。
- 「検証できたこと」と「まだ証明していないこと」を分離します。単一dogfoodや単一Runから一般化しません。
- 手順文書では、前提、入力、実行、期待結果、保証しない範囲を可能な限り分けて記述します。
- 実験文書では、観測値と推測値を混在させません。取得できない値は0で補完しません。

## Change discipline

ドキュメント変更でも、実験条件・評価意味論・凍結Artifactの解釈を変える場合は、通常の文言修正として扱いません。EXP-001のFreeze対象と衝突しないことを確認し、必要なら実験側の変更手続きを優先してください。
