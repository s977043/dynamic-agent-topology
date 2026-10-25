# Documentation

`docs/` は、Dynamic Agent Topology (DAT) の設計意図、導入手順、評価方法、実験運用、リポジトリ運用方針を説明する人間向けドキュメントです。

> Machine-readable な契約の正本は `schemas/`、`topologies/`、`roles/`、`policies/`、`experiments/` などの各Artifactです。ドキュメントと実装が矛盾する場合は、各文書で明示された Source of Truth を優先してください。

## Reading paths

### まず全体像を理解する

[Repository Guide](REPOSITORY_GUIDE.md) で構成・Evidenceの到達点・Issue間の依存関係を確認してから、以下を読みます。

1. [NORTH_STAR.md](NORTH_STAR.md) — 何を解きたいか、何を最適化しないか
2. [PRACTICE_EVOLUTION.md](PRACTICE_EVOLUTION.md) — アジャイルの価値観と、DAT自体の開発・運用の進化
3. [ARCHITECTURE.md](ARCHITECTURE.md) — Topology / Policy / Runtime / Trace / Evaluation の責務分離
4. [GLOSSARY.md](GLOSSARY.md) — DATで使う主要用語
5. [ENGINEERING_LAYERS.md](ENGINEERING_LAYERS.md) — 失敗箇所をPrompt / Context / Harness / Loop / Graph / Evaluationで診断する補助レンズ

### 既存リポジトリへ導入する

1. [QUICKSTART.md](QUICKSTART.md) — 非破壊・Manual Adapter方式での最短導入
2. [ADOPTION.md](ADOPTION.md) — A0〜A5の段階導入とArtifact契約
3. [DOGFOODING.md](DOGFOODING.md) — 実リポジトリで確認済みの範囲と、まだ証明していない範囲

### 評価・実験を理解する

1. [EXPERIMENTS.md](EXPERIMENTS.md) — 比較実験、paired comparison、ablationの原則
2. [METRICS.md](METRICS.md) — Outcome / Quality / Cost / Collaboration をどう測るか
3. [EXP-001_EXECUTION.md](EXP-001_EXECUTION.md) — EXP-001実行時のナビゲーション
4. [EXP-001_ARTIFACT_CAPTURE.md](EXP-001_ARTIFACT_CAPTURE.md) — 実Run後のArtifact記録方法

### Research / Evidence Baseを確認する

1. [Knowledge Base](../knowledge/README.md) — Source Claim / Research candidate / adopted principleの境界
2. [Source ledger](../knowledge/sources.yaml) — 参照Sourceと`adopted`状態
3. [Research notes](../knowledge/research/README.md) — 調査・仮説・追跡Issue・post-freeze評価候補

### 公開リポジトリ運用を確認する

1. [PUBLIC_REPOSITORY_POLICY.md](PUBLIC_REPOSITORY_POLICY.md) — Git外にあるGitHub設定の意図と監査方針
2. [RELEASE_READINESS.md](RELEASE_READINESS.md) — release candidateの選定からtag / GitHub Release公開までのゲート
3. [AGENT_HARNESS.md](AGENT_HARNESS.md) — このRepositoryを開発するAgentの学習ループ、自律境界、Guard
4. [ENVIRONMENT_USAGE.md](ENVIRONMENT_USAGE.md) — クラウド・Mac・ThinkPadの環境差分、用途別の利点と制約、検証順序（非規範的な検討記録）
5. [KNOWLEDGE_OWNERSHIP.md](KNOWLEDGE_OWNERSHIP.md) — 共有するプロジェクト知識と環境メモリの保存先、再確認と引き継ぎ
6. [MAINTENANCE_COST_REVIEW.md](MAINTENANCE_COST_REVIEW.md) — 保守コスト削減候補、Evidenceの限界、実行順序とHuman境界（非規範的）

## Document roles

| Document | 主な責務 | 規範性 |
|---|---|---|
| `REPOSITORY_GUIDE.md` | 構成・Evidence・Issueの責務と更新順 | ナビゲーション |
| `NORTH_STAR.md` | 目的・原則・非目標 | 設計原則 |
| `PRACTICE_EVOLUTION.md` | DATの開発・知識採用・改善の基本姿勢（Gateを増やさない） | Livingな判断ガイド |
| `ARCHITECTURE.md` | 責務境界・Plane分離 | 設計原則 |
| `GLOSSARY.md` | 用語定義 | 用語上の基準 |
| `ENGINEERING_LAYERS.md` | 障害診断の補助レンズ | 診断ガイド |
| `ADOPTION.md` | 段階導入の契約 | 導入ガイド |
| `QUICKSTART.md` | 最短の導入手順 | 実行ガイド |
| `DOGFOODING.md` | 観測済みEvidenceと非主張 | Evidence記録 |
| `EXPERIMENTS.md` | 実験設計原則 | 実験ガイド |
| `METRICS.md` | 評価指標の意味 | 評価ガイド |
| `EXP-001_*` | EXP-001の実行・記録補助 | ナビゲーション / 運用ガイド |
| `PROVENANCE_AUDIT_DESIGN.md` | Attestation / Trace / Evaluation間provenance監査の再現と設計案（#57） | 非規範的な設計案（未採用） |
| `POST_EXP001_EVALUATION_DESIGN.md` | post-EXP-001のescalation / stronger model評価の設計案（#93 / #88） | 非規範的な設計案（未採用） |
| [EXP_TIME_SIGNAL_DESIGN.md](EXP_TIME_SIGNAL_DESIGN.md) | 経過時間シグナル（elapsed / budget）の paired 評価設計案（#201） | 非規範的な設計案（未採用） |
| [MODEL_ROLE_SPLIT_DESIGN.md](MODEL_ROLE_SPLIT_DESIGN.md) | 同一T0でメインモデルだけを変えるモデル役割分担の paired 評価設計案（#220） | 非規範的な設計案（未採用） |
| [MODEL_ROLE_SPLIT_RUNBOOK.md](MODEL_ROLE_SPLIT_RUNBOOK.md) | 上記設計案の比較条件・測定項目・記録先・停止条件と、Operator / Agent / Reviewer の手順（#220） | 非規範的な実行手順書（未採用） |
| [MODEL_ROLE_SPLIT_PREREGISTRATION.md](MODEL_ROLE_SPLIT_PREREGISTRATION.md) | 上記設計案のU1〜U6の確定値と事前登録の本文（#220） | U1〜U6確定版（事前登録はblob hashのIssue記録で成立） |
| [model-role-split/CANDIDATES.yaml](model-role-split/CANDIDATES.yaml) | 上記事前登録 §2（U1）の手順で集めた18 Task の候補表（易9・複数ファイル9、既知欠陥3、SHA-256順。#220） | 第1版（事前登録と同じPRで固定） |
| [../fixtures/model-role-split/README.md](../fixtures/model-role-split/README.md) | 上記候補表の18 Task の fixture（Task 定義・取得/検証スクリプト・negative oracle、#220） | 予備検証・本 Run の入力（Run 前） |
| [model-role-split/PILOT_RUNBOOK.md](model-role-split/PILOT_RUNBOOK.md) | 上記事前登録の予備検証 2 Run（order 2 を arm A / B で 1 回ずつ）を Operator が実行する手順と、実行・集計キット `scripts/model_role_split_pilot.py`（#220） | 起案（未実行。隔離の一部と上限は未確定） |
| [HARD_TASK_T0_T1_DESIGN.md](HARD_TASK_T0_T1_DESIGN.md) | T0の成功率が低いTaskでRuntime・Model・Effortを固定しT0/T1を比べる paired 評価設計案（EXP-001 床効果） | 非規範的な設計案（未採用） |
| [HARD_TASK_T0_T1_PREREGISTRATION.md](HARD_TASK_T0_T1_PREREGISTRATION.md) | 上記設計案のU1〜U7の確定値と、実験開始前に残る手順 | U1〜U7確定版（事前登録はblob hashのIssue記録で成立） |
| [hard-task/CANDIDATES.yaml](hard-task/CANDIDATES.yaml) | 上記事前登録 §3 の手順で集めた候補表（初回44件・予備44件、SHA-256順。[#244](https://github.com/s977043/dynamic-agent-topology/issues/244)） | 第2版（§9手順3の固定は未実施） |
| [hard-task/CALIBRATION_RUNBOOK.md](hard-task/CALIBRATION_RUNBOOK.md) | 上記事前登録 §9 手順 6 の最初の較正 25 Run（5候補×5回）を Operator が実行する手順と、実行・集計キット `scripts/hard_task_calibrate.py` | 起案（未実行。prompt と上限は未確定） |
| [RUN_OBSERVATION_DESIGN.md](RUN_OBSERVATION_DESIGN.md) | 日常開発のウェーブ観察記録（RunObservation）の設計案（#223） | 非規範的な設計案（未採用） |
| [OBSERVATION_MEASUREMENT.md](OBSERVATION_MEASUREMENT.md) | RunObservation の集計対象・期間の基準時刻・除外条件・記録単位の変化 | 計測の取り決め（構成の優劣の根拠にはしない） |
| `PUBLIC_REPOSITORY_POLICY.md` | GitHub設定の目標状態 | 運用ポリシー |
| `ENVIRONMENT_USAGE.md` | 環境の観測台帳、用途比較、後続検証案 | 非規範的な検討記録 |
| [CLOUD_VERIFICATION_PLAN.md](CLOUD_VERIFICATION_PLAN.md) | Cloudで実行する知識整合性probeの事前計画とoracle | 非規範的な検証計画（#63） |
| [KNOWLEDGE_INTEGRITY_CLOUD_RESULTS.md](KNOWLEDGE_INTEGRITY_CLOUD_RESULTS.md) | 実PDF抽出・故障注入・鮮度/接続を分けたCloud実測と再現手順 | 合成corpusの限定検証（未採用） |
| `KNOWLEDGE_OWNERSHIP.md` | repo知識と環境memoryの分担、引き継ぎ | 運用ガイド（権限・実験条件を変更しない） |
| `RELEASE_READINESS.md` | Release candidateのEvidence / metadata / publication gate | Release運用チェックリスト |

## Writing conventions

- 説明文は日本語を基本とし、Schema field、Artifact kind、Runtime名、Metric IDなどの識別子は実装上の表記を維持します。
- `Evidence`, `Verifier`, `Topology`, `Runtime` など意味を持つDAT用語は、一般語として曖昧に言い換えず [GLOSSARY.md](GLOSSARY.md) の定義に合わせます。
- 「検証できたこと」と「まだ証明していないこと」を分離します。単一dogfoodや単一Runから一般化しません。
- 手順文書では、前提、入力、実行、期待結果、保証しない範囲を可能な限り分けて記述します。
- 実験文書では、観測値と推測値を混在させません。取得できない値は0で補完しません。

## Change discipline

ドキュメント変更でも、実験条件・評価意味論・凍結Artifactの解釈を変える場合は、通常の文言修正として扱いません。EXP-001のFreeze対象と衝突しないことを確認し、必要なら実験側の変更手続きを優先してください。
