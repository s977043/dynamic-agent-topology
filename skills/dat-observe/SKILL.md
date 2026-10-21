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
   - `metadata.datVersion` は記録時に参照した DAT 仕様（リポジトリ）の版で、プラグインのルートにある `CITATION.cff` の `version`。plugin manifest の `version` も同じ値に揃えてある
   - `topologyEquivalent` は設計 §5.2 の表を上から順に当てはめる。助言レビュー（`advisory`）と検証（`verifier`）を混ぜない
3. **秘匿を確かめる**（全文字列値が対象）: 秘密情報・トークン、private source、プロンプトや会話の本文、レビュー本文、個人環境の絶対パスを含めない。private な PR・ブランチ・リポジトリ名・個人名は仮名にする。`outcomeReason` は改行なしの 1 行。
4. **保存先**: リポジトリの外の 1 か所。`--store` か環境変数 `DAT_OBSERVATION_STORE` で指定し、指定がなければ `~/.dat/observations` を案内する。
5. **検証して保存する**: 保存には Python 3・`jsonschema`・`pyyaml` と DAT の CLI が必須。validator を通った記録だけを保存する。`NG` なら直して再実行し、`OK` と一緒に出る `unknown` の項目に取れる値が残っていないか見直す。

   ```bash
   python <DAT のパス>/scripts/run_observation.py save <記録.yaml> --store ~/.dat/observations
   ```

   `<DAT のパス>` はこの SKILL.md の 2 階層上（プラグインのルート）。Python や依存が使えないときは保存しない。記録 YAML を表示し、「未保存（validator 未実行）」と報告する。
6. **報告**: 保存先のパス（または未保存）、`topologyEquivalent`、`unknown` の項目を短く示す。

## 集計（sum）

```bash
python <DAT のパス>/scripts/run_observation.py sum --store ~/.dat/observations
```

出力の表をそのまま示す。Python が使えないときは集計できないと報告する。

## しないこと

- 記録や集計から構成の優劣を結論づけない。観察件数であり、比較実験ではないと添える
- 実際に行っていない作業の記録を作らない
- DAT リポジトリや導入先の追跡対象ファイルに記録を置かない
