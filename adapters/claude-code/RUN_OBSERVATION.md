# Claude Code でのウェーブ観察記録

1 ウェーブの `RunObservation` を Claude Code で記録する手順です。項目・型・判定基準・秘匿規則の正本は [RUN_OBSERVATION_DESIGN.md](../../docs/RUN_OBSERVATION_DESIGN.md)、`schemas/run-observation.schema.json`、`scripts/validate_run_observation.py` で、この文書は値の取り方だけを書きます。項目や判定基準を追加・変更しません。

この文書の「未確認」は、リポジトリ内に根拠となる記述がない Claude Code の機能です。未確認の情報源に頼る項目は `unknown` にします。

## いつ記録するか

ウェーブ完了時（完了・中断・失敗のいずれでも）、作業台帳や会話が消える前に 1 件書きます。着手時に書いた値は完了時に見直します。

## 項目ごとの情報源

| 項目 | 情報源 | 取れないとき |
|---|---|---|
| `metadata.project` / `datVersion` | 導入先の `.dat/project.yaml` の `metadata.name`、`.dat/dat.lock.yaml` | 必須文字列。分からなければ記録しない |
| `startedAt` / `endedAt` / `wallClockMs` | 作業台帳・コミットや PR の時刻など、記録者が確認できる時刻。セッションから開始・終了時刻を取る機能は未確認 | `unknown`。`wallClockMs` は両時刻が分かるときだけ |
| `goalRecorded` | ウェーブ開始前に目的を書いた記録（台帳・Issue）があるか | `unknown` |
| `outcome` / `outcomeReason` | 完了時の状態。理由は 1 行の要約 | `unknown` |
| `runtime` | Organizer と Worker が Claude Code なら `name: claude-code`。版の取得方法は未確認 | `version` を省略。全体が分からなければ `unknown` |
| `model` | Organizer とサブエージェントのモデル ID・effort。セッション・サブエージェントから取る方法は未確認 | `unknown` |
| `tasks` / `agentInvocations` | 台帳のタスク一覧と、サブエージェントへの委託の記録。サブエージェントは独立したコンテキストで動き（`capabilities.yaml` の `isolated_context`）、並列起動もできる（`parallel_subagents`）。起動回数を自動集計する機能は未確認なので、委託・再委託を記録者が数える | `unknown` |
| `artifacts` | 作成・merge した PR（仮名 `pr-1` など） | 空配列ではなく、状態が分からない要素だけ `state: unknown` |
| `reviews` | 独立レビューの判定と指摘件数。別セッション・別モデル・人の区別を `reviewerKind` に、助言か受け入れ判断かを `role` に書く。本文は書かない | 一部も追えないときは `unknown`。レビューなしは `[]` |
| `rework.count` | 修正のための再委託・再レビューの回数 | `unknown`。なかったときは `0` |
| `humanInterventions` | 承認・方針の回答など人の介入の種別ごとの件数 | `unknown` |
| `topologyEquivalent` / `topologyBasis` | 上の記録から設計 §5.2 の順で判定する | 設計の規則どおり `unknown` |

`runtime_hooks`（`capabilities.yaml`）で値を自動取得する手順は DAT 側では定めません（設計 §9）。

## 保存先と手順

保存と集計には DAT の CLI `scripts/run_observation.py` を使います。保存先は `--store` か環境変数 `DAT_OBSERVATION_STORE` で指定し、DAT リポジトリの中は拒否されます。推奨はリポジトリ外のディレクトリです。導入先の `.dat/state/observations/` に置く場合は、導入先の `.gitignore` に `.dat/state/` を追加し（例: `examples/brownfield/.gitignore`）、`git status --ignored --short .dat/state` で `!!` と表示される（除外されている）ことを確認してから保存します。

1. 記録を一時ファイルに 1 ウェーブ 1 件で書く
2. `save` で保存する。validator を通った記録だけが `<保存先>/<metadata.project>/<metadata.observationId>.yaml` にコピーされ、既存の ID は拒否される。`metadata.project` と `observationId` は英数字で始まり英数字・`.`・`_`・`-` だけからなる値にする（ファイル名に使うため）。保存先の外を指す値や symlink は拒否される。`OK` と一緒に値が `unknown` の項目が表示されるので、取れる値が残っていないか見直す。`NG` のときはエラーを直して再実行する

   ```bash
   python <DAT のパス>/scripts/run_observation.py save <記録.yaml> --store .dat/state/observations
   ```

3. 集計は `sum` で Markdown の表として出す。不正なファイルは表示して数えない。終了コードは、すべて数えたとき 0、不正なファイルを飛ばしたとき 1（表は出る）、保存先がないとき 2。集計は観察件数であり、構成の優劣の根拠ではない

   ```bash
   python <DAT のパス>/scripts/run_observation.py sum --store .dat/state/observations
   ```

4. 合成値の記録例: [examples/run-observation.yaml](examples/run-observation.yaml)

## 秘匿

設計 §6 をすべての文字列値に適用します。秘密情報、private source、プロンプト・会話本文、レビュー本文、個人環境の絶対パスを書きません。private な導入先の PR・ブランチ・リポジトリ名・個人名は仮名にします。validator の検査は簡易なもので、人の差分確認を置き換えません。
