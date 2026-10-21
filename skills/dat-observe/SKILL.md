---
name: dat-observe
description: 1 回の作業単位（ウェーブ）の完了時に、実際の構成と結果を DAT の RunObservation として 1 件記録する。保存済み記録の集計（sum）もする。「ウェーブを記録して」「DAT の記録」「dat-observe」「記録を集計して」で使う。
---

# dat-observe

ウェーブ完了時（完了・中断・失敗のいずれでも）、会話や作業台帳が消える前に 1 件記録する。集計を頼まれたら「集計」だけを行う。

## 正本

項目・型・判定規則・秘匿規則はここに写さない。次を読む（パスはこの SKILL.md からの相対パス）。

- 設計: [docs/RUN_OBSERVATION_DESIGN.md](../../docs/RUN_OBSERVATION_DESIGN.md)（§5 項目と `topologyEquivalent` の判定、§6 秘匿）
- schema: [schemas/run-observation.schema.json](../../schemas/run-observation.schema.json)
- 値の取り方: [adapters/claude-code/RUN_OBSERVATION.md](../../adapters/claude-code/RUN_OBSERVATION.md)、[adapters/codex/RUN_OBSERVATION.md](../../adapters/codex/RUN_OBSERVATION.md)
- 記録例: [adapters/claude-code/examples/run-observation.yaml](../../adapters/claude-code/examples/run-observation.yaml)

## 記録

1. **値を集める**: このセッションで実際に行った委託・レビュー・手戻り・人の確認、PR の状態など、確認できる情報源だけを使う。
2. **YAML を書く**: 記録例の形で、作業中のリポジトリの外（一時ディレクトリ）に書く。
   - 分からない値は `unknown`。0・`[]`・`false` で補わない。レビューなしは `reviews: []`、手戻りなしは `rework.count: 0` と明記する
   - `metadata.project` は設定がなければ作業中のリポジトリのディレクトリ名（worktree なら親リポジトリ名）。private なら仮名（例: `project-a`）
   - `metadata.datVersion` はこのプラグインの版（`.claude-plugin/plugin.json` の `version`）
   - `topologyEquivalent` は設計 §5.2 の表を上から順に当てはめる。助言レビュー（`advisory`）と検証（`verifier`）を混ぜない
3. **秘匿を確かめる**（全文字列値が対象）: 秘密情報・トークン、private source、プロンプトや会話の本文、レビュー本文、個人環境の絶対パスを含めない。private な PR・ブランチ・リポジトリ名・個人名は仮名にする。`outcomeReason` は改行なしの 1 行。
4. **保存先を決める**: 既定はリポジトリの外（例: `~/.dat/observations`、または環境変数 `DAT_OBSERVATION_STORE`）。導入先の `.dat/state/observations/` に置くときは、`.gitignore` に `.dat/state/` があり、`git status --ignored --short .dat/state` が `!!` を示すことを確かめてから保存する。
5. **検証して保存する**:
   - Python 3 と `jsonschema`・`pyyaml` が使えるなら、DAT の CLI で検証と保存をする。`NG` なら直して再実行する。`OK` と一緒に出る `unknown` の項目に取れる値が残っていないか見直す

     ```bash
     python <DAT のパス>/scripts/run_observation.py save <記録.yaml> --store <保存先>
     ```

     `<DAT のパス>` はこの SKILL.md の 2 階層上（プラグインのルート）。
   - 使えないときは、schema の必須項目・enum と手順 3 の秘匿を目で確かめ、`<保存先>/<project>/<observationId>.yaml` に保存する。報告に「機械検証していない」と書く。
6. **報告**: 保存先のパス、`topologyEquivalent`、`unknown` の項目を短く示す。

## 集計（sum）

```bash
python <DAT のパス>/scripts/run_observation.py sum --store <保存先>
```

出力の表をそのまま示す。Python が使えないときは、保存先の YAML を数えて `topologyEquivalent`・`outcome` ごとの件数を表にし、`unknown` は分母から除いて件数を併記する。

## しないこと

- 記録や集計から構成の優劣を結論づけない。観察件数であり、比較実験ではないと添える
- 実際に行っていない作業の記録を作らない
- DAT リポジトリや導入先の追跡対象ファイルに記録を置かない
