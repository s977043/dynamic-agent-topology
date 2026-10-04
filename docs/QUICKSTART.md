# Quick Start — 既存リポジトリへDATを導入する

この手順は、既存プロジェクトへDATを**非破壊・手動Adapter方式**で導入する最短経路です。

> 最初の目的はMulti-Agent化ではありません。  
> **プロジェクトのAgent実行を、構造化・検証可能・比較可能にすること**です。

## 1. .dat/ を作る

導入先リポジトリに以下を用意します。

```text
.dat/
├── project.yaml
├── evidence.yaml
├── policy.yaml       # A3以降
├── runtimes.yaml
├── dat.lock.yaml
├── generated/        # Git管理しない
└── state/            # Git管理しない
```

最初は [examples/brownfield/.dat](../examples/brownfield/.dat) をコピーして編集できます。

## 2. Project Bindingを設定する

`.dat/project.yaml` で利用可能なTopologyとRuntimeを宣言します。

最初は **T0 Single Agent** をdefaultにすることを推奨します。

## 3. Evidenceを接続する

`.dat/evidence.yaml` には既存のTest / Lint / Typecheck / Buildなどを宣言します。

重要: DATのvalidationはEvidence commandを実行しません。commandはuntrusted inputとして扱います。実行は既存CIまたは明示的に信頼したRunner側で行います。

## 4. Runtime Bindingを設定する

`.dat/runtimes.yaml` でDAT上のRuntime名と、既存プロジェクト側の設定ファイルを対応付けます。

v0.2.1では `mode: manual` を標準とします。

```yaml
bindings:
  - runtime: codex
    mode: manual
    configPath: AGENTS.md
```

DATはまだRuntime設定を自動生成・上書きしません。

## 5. DAT revisionを固定する

PoCでは `pinMode: floating` でも開始できますが、継続利用ではcommit SHAまたはtagへ固定してください。

```yaml
spec:
  dat:
    version: "0.2.1"
    apiVersion: dat/v1alpha1
    source: https://github.com/s977043/dynamic-agent-topology
    pinMode: pinned
    revision: "<commit-or-tag>"
```

## 6. 外部Project Validatorを実行する

DATリポジトリを別ディレクトリへcloneした状態で:

```bash
python -m pip install jsonschema pyyaml

python /path/to/dynamic-agent-topology/scripts/validate_project.py \
  --project /path/to/your-project \
  --dat-root /path/to/dynamic-agent-topology
```

PASSすれば、SchemaとDAT参照の整合が確認できています。`pinMode: pinned` の場合は、`dat.lock.yaml` のrevisionと実際のDAT checkout HEADも一致していることを検証します。

## 7. CIへ追加する

[examples/github-actions/dat-validate.yml](../examples/github-actions/dat-validate.yml) を参考に、DATを固定revisionでcheckoutしてvalidatorを実行します。

## 8. A0 → A3まで段階導入する

```text
A0 Assess
→ A1 Bind Evidence
→ A2 Observe
→ A3 Recommend
```

A4 Canary / A5 Dynamicへ進む必要はありません。

### 最初の推奨

- Runtime: 1つに絞る
- Topology: T0から開始
- Evidence: 既存CIを再利用
- Runtime設定: manual
- generated/state: Git管理しない
- Routing: A3まで不要

## 導入完了の最小条件

- `.dat/project.yaml` がvalid
- `.dat/runtimes.yaml` がProjectBindingと一致
- `.dat/dat.lock.yaml` がDAT versionと一致
- A1以降なら `.dat/evidence.yaml` がvalid
- A3以降ならRouting Policyがvalid
- External Project ValidatorがPASS


## Validatorが保証しないこと

Validatorは `.dat/` とDAT specificationの整合を確認しますが、Manual Adapterとして設定した `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` 等の内容が、宣言Topologyを実際に実装していることまでは証明しません。

A4 Canary以降ではExecutionTrace / Evidenceを使って実行時のTopology Adherenceを確認します。
