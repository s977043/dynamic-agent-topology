# Quick Start — 既存リポジトリへDATを導入する

この手順は、既存プロジェクトへDATを**非破壊・Manual Adapter方式**で導入する最短経路です。

> 最初の目的はMulti-Agent化ではありません。  
> **プロジェクトのAgent実行を、構造化・検証可能・比較可能にすること**です。

## Before you start

- 導入先Repositoryの既存CI / Test / Agent設定を把握していること
- DATを別checkoutとして参照できること
- External Project Validatorを実行できるPython環境があること
- Runtime-native設定をDATが自動上書きしない前提を理解していること

最初はA0〜A2で、既存Workflowを変更しない導入を推奨します。

## 1. `.dat/` を作る

導入先Repositoryに以下を用意します。

```text
.dat/
├── project.yaml
├── evidence.yaml      # A1以降
├── policy.yaml        # A3以降。A0〜A2でも明示stage用に置ける
├── runtimes.yaml
├── dat.lock.yaml
├── generated/         # Git管理しない
└── state/             # Git管理しない
```

最初は [examples/brownfield/.dat](../examples/brownfield/.dat) をコピーして編集できます。

```bash
git clone https://github.com/s977043/dynamic-agent-topology.git /tmp/dynamic-agent-topology
cp -R /tmp/dynamic-agent-topology/examples/brownfield/.dat ./.dat
```

コピー後は、Project名、Runtime、Evidence command、DAT revisionを必ず自分のRepositoryに合わせて変更してください。

## 2. Project Bindingを設定する

`.dat/project.yaml` で利用可能なTopologyとRuntimeを宣言します。

最初は **T0 Single Agent** を`defaultTopology`にすることを推奨します。Multi-Agent化は導入完了条件ではありません。

## 3. Evidenceを接続する

`.dat/evidence.yaml` には既存のTest / Lint / Typecheck / Buildなどを宣言します。

重要: DATのvalidationはEvidence commandを実行しません。commandはuntrusted inputとして扱います。実行は既存CIまたは明示的に信頼したRunner側で行います。

Evidence commandは「DAT導入のために新設する」より、まず既存品質ゲートを再利用してください。

## 4. Runtime Bindingを設定する

`.dat/runtimes.yaml` でDAT上のRuntime名と、既存Project側の設定ファイルを対応付けます。

現行の標準は`mode: manual`です。

```yaml
bindings:
  - runtime: codex
    mode: manual
    configPath: AGENTS.md
```

DATはManual AdapterではRuntime設定を自動生成・上書きしません。

## 5. DAT revisionを固定する

PoCでは`pinMode: floating`でも開始できますが、継続利用やCIではcommit SHAまたは実在するimmutable tagへ固定してください。validatorを実行するDAT checkoutも、`dat.lock.yaml` と同じrevisionへcheckoutします。

`main` はUnreleased変更を含む場合があります。`version`文字列だけからGit tag / GitHub Releaseの存在を推測せず、Repository rootの`CHANGELOG.md`、tag、Releaseを確認してください。

```yaml
spec:
  dat:
    version: "0.2.1"
    apiVersion: dat/v1alpha1
    source: https://github.com/s977043/dynamic-agent-topology
    pinMode: pinned
    revision: "<commit-or-tag>"
```

```bash
git -C /tmp/dynamic-agent-topology checkout "<commit-or-tag>"
```

Version文字列だけでなく、実際に検証へ使うcheckout revisionも一致させることが重要です。historical content pointを使う場合も、Release名ではなく対象commitを明示的にpinできます。

## 6. External Project Validatorを実行する

DAT Repositoryを別ディレクトリへcloneした状態で:

```bash
python -m pip install jsonschema pyyaml

python /path/to/dynamic-agent-topology/scripts/validate_project.py \
  --project /path/to/your-project \
  --dat-root /path/to/dynamic-agent-topology
```

PASSすれば、SchemaとDAT参照の静的整合が確認できています。`pinMode: pinned` の場合は、`dat.lock.yaml` のrevisionと実際のDAT checkout HEADの一致も検証されます。

CIではさらに`--require-pinned`を付け、floating revisionを拒否することを推奨します。

## 7. CIへ追加する

[examples/github-actions/dat-validate.yml](../examples/github-actions/dat-validate.yml) を参考に、DATを固定revisionでcheckoutしてvalidatorを実行します。

Actionsの`ref`と`dat.lock.yaml.spec.dat.revision`は同じcommit SHAまたはtagを指定してください。

## 8. A0 → A3を段階導入する

```text
A0 Assess
→ A1 Bind Evidence
→ A2 Observe
→ A3 Recommend
```

A4 Canary / A5 Dynamicへ進む必要はありません。

### 最初の推奨構成

- Runtime: 1つに絞る
- Topology: T0から開始
- Evidence: 既存CIを再利用
- Runtime設定: Manual Adapter
- `generated/` / `state/`: Git管理しない
- Routing: A2までは不要。A3から必要

## Minimal completion criteria

- `.dat/project.yaml` がvalid
- `.dat/runtimes.yaml` がProject Bindingと一致
- `.dat/dat.lock.yaml` がDAT version/source/revisionと整合
- A1以降なら `.dat/evidence.yaml` がvalid
- A3以降なら `policy.yaml` とRouting Policyがvalid
- External Project ValidatorがPASS

この時点で確認できるのは**導入契約の整合**です。Topologyの有効性やRuntime enforcementまで確認できたことにはなりません。

## What the validator does not guarantee

Validatorは`.dat/`とDAT specificationの整合を確認しますが、Manual Adapterとして設定した`AGENTS.md` / `CLAUDE.md` / `GEMINI.md`等の内容が、宣言Topologyを実際に実装・強制していることまでは証明しません。

A4 Canary以降では`ExecutionTrace` / Evidenceを使い、実行時のTopology AdherenceやBoundary Violationを確認します。

## Observed adoption evidence

Quick Start相当のManual Adoptionは、`s977043/notionnext-blog` でA2 Observeとしてdogfood済みです。

導入条件、確認できた結果、まだ一般化できない範囲は [DOGFOODING.md](DOGFOODING.md) を参照してください。
