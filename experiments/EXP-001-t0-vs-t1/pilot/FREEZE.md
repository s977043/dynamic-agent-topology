# EXP-001 Feature Freeze

**Status: ACTIVE**  
**Execution issue: #15**  
**Freeze issue: #16**

EXP-001は設計フェーズを終了し、一次データ取得フェーズへ移行しています。

この期間の原則は次です。

> **Evidenceが次の設計変更を決める。Evidenceを取る前に設計を増やさない。**

## Freeze期間

Feature Freezeは、最初のempirical run開始前から次を満たすまで継続します。

1. 18 / 18 Runの実測Artifactが存在する
2. `validate_pilot.py --require-complete` がPASSする
3. 集計結果が再生成可能である
4. `DECISION.md` がEvidence参照付きで更新される
5. 結果レビューPRがmergeされる

## 凍結対象

凍結対象は [freeze.yaml](freeze.yaml) を正本とします。

主に次を含みます。

- EXP-001のQuestion / Hypothesis / Decision Policy
- Pilot Runtime / Model / Effort / Repetition
- Run Matrix / Counterbalancing
- BASE / T0 / T1 Prompt Contract
- Scenario Set / Fixture
- T0 / T1 Topology / Worker / Verifier Role
- Trace / Evaluation / Pilot Schema
- Matrix生成 / Pilot validation / Experiment summary logic

CIは各ArtifactのGit blob identityを検証し、意図しない変更を拒否します。

## Freeze中に変更しないもの

- Prompt Contract
- T0 / T1 Topology
- Worker / Verifier Role Contract
- Scenario / Fixture
- Model / Effort / Runtime
- Repetition数
- Run順序
- Metric / Decision criteria
- Evaluation semantics
- Summary calculation

18 Runの途中結果を見て改善してはいけません。

## Freeze中に許可するもの

実験条件や評価意味論を変えない変更のみ許可します。

例:

- 誤字修正など、実験意味論に影響しない文書変更
- EXP-001と無関係なsecurity fix
- CI infrastructure fixで、凍結Artifactを変更しないもの
- #15の進捗更新

## Blocking defect

凍結ArtifactにBlocking defectが見つかった場合、結果を補正・推測して継続しません。

1. #15の実行を停止する
2. defect Issueを作成する
3. defectが実行・評価意味論へ与える影響をレビューする
4. 凍結Artifactを変更する場合は `freeze.yaml` を更新する
5. **empirical run開始後に凍結Artifactを変更した場合、原則として収集済みRunを無効化し0 / 18から再開する**
6. 例外判断をする場合は、変更が実行条件・評価結果へ影響しないことを独立レビューで明示する

「せっかく取ったデータを残したい」は例外理由にしません。

## Deferred

EXP-001完了まで次を実装しません。

- 新しいCanonical Topology
- EXP-002以降
- Dynamic Routing / Recompositionの拡張
- Runtime auto compile/apply
- Research Profile / Production Profileの新設計
- EXP-001結果を前提にした最適化

Research / Productionの二面性は重要なテーマですが、EXP-001で実際のfrictionを観測してから設計します。

## Publication gate

EXP-001について結果記事・Benchmark claimを出すのは、次の後です。

- 18 / 18 Run完了
- completeness validation PASS
- 集計再現可能
- `DECISION.md` 更新
- review merge

最初の結果は一般化されたBenchmarkではなく、**Pilot observation** として扱います。
