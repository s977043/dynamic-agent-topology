# Brownfield reference project

このディレクトリは、別リポジトリへDATを導入するための最小Reference Exampleです。

```text
.dat/
├── project.yaml
├── evidence.yaml
├── policy.yaml
├── runtimes.yaml
└── dat.lock.yaml
```

現在のexampleは `A3-recommend` を想定しています。

`runtimes.yaml` のRuntime設定ファイルは説明用のため、実ファイルが存在しない場合validatorはwarningを出します。外部Projectでは実際の設定ファイルへ置き換えてください。

`dat.lock.yaml` はexampleの追従性を優先して `floating` ですが、実ProjectのCIではcommit SHAまたはtagへのpinを推奨します。
