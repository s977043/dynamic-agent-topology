# Knowledge Base

`knowledge/` は、DATが参照した研究・公式知見と、そこから得た設計判断を分離して管理するための領域です。

外部SourceがRepositoryに存在することと、DATへ設計として採用されたことは同義ではありません。

## Navigation and status

- [`sources.yaml`](sources.yaml) — 参照Sourceと、そのSourceから明示的に採用した項目のledger
- [`principles/`](principles/) — 主要な設計原則を説明する短いprinciple note。採用状態の完全なledgerではない
- [`research/`](research/) — 調査・解釈・仮説・将来評価候補。存在するだけでは採用を意味しない

`sources.yaml` の `adopted` が空の場合、そのSourceは**参照済みだが、現在のDAT契約へは未採用**です。

```yaml
adopted: []
```

Research Note内にcandidate schema、lifecycle、metric、role、runtime mechanismなどが記載されていても、明示的な採用判断と対応するcanonical artifact変更がない限り、DATの現在仕様ではありません。

## Evidence discipline

外部知見は次の順で扱います。

```text
Source
  ↓
Source Claim
  ↓
DAT Interpretation
  ↓
Hypothesis / Candidate
  ↓
Controlled or observable Evidence
  ↓
Adopt / Reject / Defer
```

特に次を区別します。

- **Source Claim != DAT benchmark result**
- **Research candidate != adopted contract**
- **Generated summary != source evidence**
- **Observed success != semantic correctness**
- **Adoption != permanent commitment**

Evidenceが追加コストを正当化しなくなった場合、既存の採用判断もablation / re-evaluationの対象です。

## Research notes

現在のResearch Note一覧、追跡Issue、想定構造、Research Proposalの入口は [Research Notes](research/README.md) を参照してください。

### EXP-001 Feature Freeze中の扱い

EXP-001のFreeze中に追加するResearch Noteは、原則として**調査結果とpost-freeze hypothesisの保存**に留めます。

Research Note追加だけを根拠に、凍結中のPrompt / Topology / Role / Scenario / Fixture / Schema / validator / Runtime behavior / evaluation semanticsを変更しません。Blocking defectの場合は、EXP-001のFreeze手続きに従います。

現在の実行状況とFreeze境界は [Issue #15](https://github.com/s977043/dynamic-agent-topology/issues/15) を参照してください。

## Adding or revising knowledge

新しいSourceを追加するときは、Sourceの種類と一次Source URLを `sources.yaml` に記録し、採用していない場合は `adopted: []` を維持します。

設計へ取り込む場合は、Sourceの存在ではなくDAT側のEvidenceと判断理由を示し、必要なcanonical artifact / documentation / validationを同じ変更で更新します。

Sourceの主張が後から更新・撤回・反証された場合は、既存の採用判断も再評価します。
