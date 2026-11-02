# 非公開の記録票 — 空テンプレート

**このファイルは未実測の雛形です。** Git外へコピーして使用し、回答・行動区間・個人IDを公開Repositoryへcommitしないでください。`null`は未取得です。0やPASSを初期値にしません。書式はこの手動練習専用で、DATのArtifact/Schemaではありません。

## 開始前

```yaml
record_status: not_started
package_revision: null  # この5ファイルを含むcommit SHA
block_id: null          # ローカル識別用。既存EXP-001のrunIdを使わない
performed_on: null      # 日付。個人の詳細な行動時刻は公開しない
participant_alias: null
consent_confirmed: null
viewer_and_device: null
order: null            # A_then_B または B_then_A。資料を開く前に記入
order_method: null
prior_exposure: null   # 既知のPR・教材・正解を列挙。不明はunknown
private_storage: null
raw_delete_on: null
quality_reviewer_ref: null
reviewer_authored_materials: null
```

## 条件ごとの実測

A/Bの開始からの相対秒数でintervalを記録します。回答は両条件が終わるまで見比べたり直したりしません。回答時刻はwall timeの終了anchorです。書式は任意のメモに置き換えられますが、欠測を隠さないでください。

```yaml
A:
  outcome: not_started  # completed / aborted / not_started
  measurement_mode: unavailable  # 実際に区間を取得できたときだけexplicit
  observation_complete: null
  wall_seconds: null
  active_intervals_s: null  # 例ではなく実測の [start,end] の配列
  wait_intervals_s: null
  measurement_intervals_s: null
  coordination_intervals_s: null  # activeの内訳
  active_seconds: null
  wait_seconds: null
  measurement_overhead_seconds: null
  coordination_seconds: null
  intervention_episode_ids: null
  intervention_count: null
  answer_1: null
  answer_2: null
  answer_3: null
  answer_4: null
  answer_5: null
  interruption_or_missing_reason: null
B:
  outcome: not_started
  measurement_mode: unavailable
  observation_complete: null
  wall_seconds: null
  active_intervals_s: null
  wait_intervals_s: null
  measurement_intervals_s: null
  coordination_intervals_s: null
  active_seconds: null
  wait_seconds: null
  measurement_overhead_seconds: null
  coordination_seconds: null
  intervention_episode_ids: null
  intervention_count: null
  answer_1: null
  answer_2: null
  answer_3: null
  answer_4: null
  answer_5: null
  interruption_or_missing_reason: null
```

同一人のactive intervalはunionを取ります。wait/measurementとactiveの重なり、負の時間、終了anchorを超えたintervalは修正根拠がなければ欠測です。coordination intervalはactiveの内側にあることを確認します。空配列は「観測して0件」の場合だけ使い、未観測は`null`を維持します。

介入はAIからのhandoff発生数の実測ではなく、今回の読解中に追加説明を要求した独立episodeの補助記録です。同じ依頼へのclick/commentを増分にせず、既存`humanInterventions`へ変換しません。

## 両回答固定後の品質確認

```yaml
quality:
  status: unavailable
  reviewer_ref: null
  independent_of_material_author: null
  checked_package_revision: null
  A_q1_to_q5: null       # 0/1を各問。未評価はnull
  B_q1_to_q5: null
  material_visibility_failures: null
  evidence_access_failures: null
  unsafe_authorization: null
  evidence_or_reason: null
feasibility:
  status: not_assessed   # measurable / revise / inconclusive
  delta_active_seconds_B_minus_A: null
  limitations: null
  next_action: null
```

実測前にqualityやfeasibilityを埋めません。準備側のレビューは回答採点ではありません。

## 公開用サマリー（Operatorが匿名化後に作成）

```text
#287 手順リハーサル
package revision / 対象block:
実施: A=?, B=?（中断・欠測も記載）
active秒: A=?, B=? / 計測overhead: A=?, B=?
品質確認: 担当の根拠参照、5問の取得可否、重大欠落・誤承認の有無
既知資料・順序・記憶効果・欠測の制約:
計測可能性: 計測可能 / 要修正 / 判定不能
次の一手:
効果の優位性・採用判断: 対象外
```
