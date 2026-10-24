# RunObservation の計測の取り決め

日々の観測記録（RunObservation、[RUN_OBSERVATION_DESIGN.md](RUN_OBSERVATION_DESIGN.md)）を数えるときの規則。誰が数えても同じ件数になることを目的にする。項目の定義は [schemas/run-observation.schema.json](../schemas/run-observation.schema.json) と設計を正とし、ここには写さない。

## 1. 観測記録で言えること・言えないこと

- 観測記録は、どの構成で何件の作業が行われ、どう終わったかの観察件数である。構成の優劣の根拠にしない
- 記録の作業は難度・規模・担当がそろっておらず、T0 には確認役がいないので見落としを数えられない。件数や手戻り数を構成間で比べて「T1 が良い」などと結論づけない
- 構成の比較は、事前登録した実験（[EXPERIMENTS.md](EXPERIMENTS.md)）で行う。観測記録は、実験の仮説や候補を探す材料にとどめる

## 2. 集計対象

- 対象は store 直下の `<store>/<project>/<observationId>.yaml` だけ。それより深い・浅い位置の YAML は数えない。`run_observation.py sum` はそうしたファイルを `warning: not counted ...` として出す
- validator を通らない記録は数えない（`sum` は `skipped invalid` として出す）
- `observationId` は store 全体で一意とする。`run_observation.py save` は、同じ `observationId` のファイルが store のどこかにあれば保存を拒否する。既存の store に重複が残っている場合は、件数を出す前に解消する

## 3. 期間で数えるときの基準時刻

- 期間（「ある日時以降」など）は記録の `endedAt` で判定する。ファイルの更新時刻（mtime）は、コピーや再保存で変わり再現できないので使わない
- `endedAt: unknown` の記録は期間に入れられないので、「判定不能」として別に件数を出す（`sum` の `endedAt unknown` 行）。期間内に含めたり、除外して黙って捨てたりしない
- 時刻は記録の時差表記を保ったまま比較する（JST の区切りは `+09:00` で書く）

## 4. 除外条件

次に当たる記録は、集計に入れる前に除外し、除外した件数と理由を集計と一緒に示す。

- 動作確認・試験用に作った記録（実際の作業がない）
- 同じ作業を重複して記録したもの（同じ PR・同じウェーブ）
- validator を通らない記録

除外は記録ファイルを削除・書き換えずに、集計側の一覧で行う。

## 5. 記録単位の変化（2026-10-23）

2026-10-23 を境に、記録の単位が変わった。それより前は 1 件が複数の作業をまとめたウェーブを指すことがあり、以後は作業の区切り（PR の merge・close、Human 判断待ちなど）ごとに 1 件を記録する。前後で 1 件の重さが違うので、2026-10-23 をまたいで件数を合計・比較しない。またぐ場合は前後を別の表に分ける。

## 6. 集計時の正規化

- `reviews[].decision` は自由文字列のまま保存し、集計で次の正規値に寄せる。対応は `scripts/validate_run_observation.py` の `DECISION_ALIASES` を正とする

  | 正規値 | 受け付ける別名 |
  |---|---|
  | `approve` | `approve`、`approved`、`merge-ok` |
  | `changes-requested` | `changes-requested`、`changes-required`、`request-changes` |
  | `comment` | `comment`、`comments` |
  | `unknown` | `unknown` |

  これ以外の値は `other` に数え、validator が警告を出す。新しく書く記録は正規値を使う
- `topologyBasis.independentReview: 'yes'` は、`separate-session` / `separate-model` / `human` の `role: advisory` レビューが 1 件以上あるときだけ許す。`same-session` の助言だけの記録は `no` とする

## 7. 任意項目

次の項目は任意で、ない記録は「未記録」として数える（`unknown` とは区別しない）。比較に使う場合は、記録がある件数を分母と一緒に示す。

- `interruptionKind`: `outcome: interrupted` の中断の種類。`interrupted` で欠けていると validator が警告する（エラーにはしない）
- `rework.triggers`: 手戻りのきっかけ
- `taskDifficulty`: 作業の難度。構成を選ぶ前に記録する（結果を見てから付けない）
- `model[].effort`: モデルの Effort
- `usage.totalTokens` / `usage.costUsd`: token 数と費用。分からなければ `unknown`
