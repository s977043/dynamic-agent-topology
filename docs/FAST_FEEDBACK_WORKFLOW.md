# Fast Feedback — DAT開発・EXP-001 Operator運用

> 状態: 開発Harness運用の提案。**EXP-001の実験条件・Runtime Adapter・Run受理基準・Permissionを追加または変更するものではない。**
>
> 正本: Agentの自律・承認境界は [Agent Development Harness](AGENT_HARNESS.md)、Runの最新状況は [Issue #15](https://github.com/s977043/dynamic-agent-topology/issues/15)、実測手順は [Feature Freeze](../experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md) と [Operator procedure](../experiments/EXP-001-t0-vs-t1/pilot/OPERATOR.md)。

## 目的と守る境界

**Outcome:** 障害の発見から、次の**有効な実測Evidence**を得るまでの時間を縮める。準備チェックの完了を実験進捗の代わりにしない。

- **厳格に守るもの:** 認証情報、実効Permission、Frozen inputs、決定論的Evidence、実Runtimeのattestation、1回限りのretry allowance、独立Run acceptanceの承認境界。
- **高速化するもの:** 重複した目視確認、際限のない追加調査、大きすぎる変更、不要な引き継ぎ、レビュー待ち。既存Gateが許可する場合にのみ不変の検証証跡を再利用し、実行時に最新状態の確認が必要なSecurity/Runtime条件は再検証する。

**開発用ループと実験用ループは別物。**

| ループ | 現在改善できるもの | 禁止事項 |
| --- | --- | --- |
| Repository Development | 小さな文書・Guard・ツール変更、局所検証、Review、学びを次のPRに反映（既存の承認規約内） | Frozen fileの無断変更、自己承認、Human専権のHarness変更を自動merge |
| EXP-001 empirical | 承認された固定matrixを1 Runずつ進め、結果Artifactを速やかに検証、Operatorの障害を実験Context外で記録 | Prompt / Topology / Role / Fixture / Evaluation / matrix / 固定Model・Effortの変更、先行Run結果に基づく後続条件の変更 |

**Cross-run feedbackは禁止。** Repository開発で得た助言や過去Runの成果を、後続のfresh Codex実験セッションへ注入しない。相談AgentはT0/T1構成の一部ではなく、Operatorが既存Runbookにない手段へ切り替える許可も与えない。

## 最小の安全なフィードバックループ

1. **次の観測可能な成果を1つ定める。** 例: 「現行の必須PreflightとReviewer条件を満たした状態で、承認済みT1 r01 retryを開始できる」。`あり得る懸念をすべて事前に潰す` は成果ではない。
2. **失敗を分類する。** `SECURITY/BOUNDARY`、`INFRASTRUCTURE`、`EXPERIMENT-CONTRACT`、`TASK/IMPLEMENTATION`、`UNKNOWN`。最初の観測事実と最小のBroken Work Unitを記録する。
3. **最も安価で有効な確認を1つ選ぶ。** 既存の決定論的チェックを優先し、環境診断なら可能な範囲でmodel非起動の確認を行う。ただしdry runは実model実行・認証隔離・Run acceptanceを証明しない。
4. **現行の権限内で判断する。** 必須条件をすべて満たすPASSなら既承認の次の操作へ。FAILなら原因を絞り修正・再検証。BLOCK/UNKNOWN/Permission問題ならSTOPし、Evidenceを残して既存の権限者へ判断を求める。失敗自体はRetry権限を生まない。
5. **Runの結果と次の判断を記録する。** 実行したコマンド、exit code、変更Artifactのidentity、観測時刻、必要な独立Reviewer判断、次の最小アクション。不完全・中断・評価不能を成功へ読み替えない。
6. **開発プロセスだけを改善する。** 確認の重複や待ち時間は開発Issue/PRまたはHarness learning ledgerへ。EXP-001の途中でFrozen treatmentを変更しない。

実測の進行順序は変えない: **承認済み必須Preflight/Reviewer判断 → fresh workspace/session → 固定Modelで実Run → Evidence回収 → single-run validation → 独立Reviewerの`ACCEPT` → 次のmatrix slot**。文書検証や静的PASSだけで再実行を許可しない。

### 過剰準備を抑える判断基準

- 新たな調査・設計・Reviewを要求する前に、**まだ満たしていない現行の必須条件**、具体的なEvidenceの欠落、観測された危険な挙動を示す。
- 仮定だけから必須Gateを増やさない。実際の重大な境界違反があればSTOPし、権限者が必要な変更を判断する。
- 同じ検討を繰り返しても識別力のあるEvidenceが増えなければ、障害として可視化し、範囲を区切った次のテストかSTOP判断へ進める。
- Repository開発変更は1目的・1最小PR。認証情報やPermissionの検査は省略しない。
- **Repository開発変更の撤回**は対象PRをrevertしてCI再検証する。Frozen Run、失敗attempt、履歴を消して「ロールバック」と扱わない。

## Agile Coach / Scrum Masterに相談する

2つのロールはDAT**リポジトリ開発に限定したread-onlyの助言エージェント**。T0/T1 empirical Role、Verifier、独立Reviewer、承認者ではない。

| Runtime | Agile Coach | Scrum Master |
| --- | --- | --- |
| Claude Code | `.claude/agents/agile-coach.md` | `.claude/agents/scrum-master.md` |
| Codex（project config） | `.codex/agents/agile-coach.toml` | `.codex/agents/scrum-master.toml` |

Runtimeがproject subagentをサポートする場合、必要なRoleに**相談タスクだけ**を委譲する。GitHubのIssue/PRリンク、サニタイズ済み観測、現在の権限境界のみを渡す。subagent起動手段がなければ同じ問いをread-onlyレビューで使い、**独立Agentが実行したと偽らない**。

Codex の助言ロールは `sandbox_mode = "read-only"` / `approval_policy = "never"` を指定する。これは**権限昇格を求めず、書き込みを許可しない**ための設定意図であり、読める秘密情報の範囲まで制限するattestationではない。実使用前に対象バージョンと設定優先順位を確認し、ダミーのファイル書き込み・ネットワーク・権限昇格の負側試験を行う。拒否が不明なら提案段階に留める。

**相談する条件（全Runでの呼び出しは不要）:**

- **Agile Coach:** 学習Goalが不明、準備が膨張、次の最小安全な実験を決められない。
- **Scrum Master:** Review/承認/担当がボトルネック、同じ障害がcheckpointを跨いで残る。
- 単純なPASSで次の承認済み行動が明確なら相談せず進む。新たな会議やmandatory gateは作らない。

相談時の最小Input:

```text
Goal / 現在承認済みの次アクション:
一次ソース（Issue/PR/実行手順）:
観測した事実と時刻:
未達または不明の必須条件:
改善可能な開発・Operator運用の範囲:
変更不可（Feature Freeze / Security / Approval）:
この役割に聞く1つの問い:
```

期待する簡潔なOutput:

- **Agile Coach:** `Outcome / Hypothesis / Smallest safe test / Feedback source / Success signal / Next decision`。新しい準備だけを増やす案は問い直す。
- **Scrum Master:** `Current impediment / Owner or authority / Waiting on / Smallest next action / Next check / Stop condition`。障害と責任境界を明確にする。

助言は`advice`として別々に記録する。採否は既存契約に従いImplementerが検討し、必要な承認は独立Reviewer/Humanが行う。両ロールの一致も実験効果のEvidence、独立Verification、マージ/Run起動許可にはならない。

### 相談依頼の例（開発セッション内で使用）

Claude Code / Codexの**通常の開発セッション**で、実行環境が対応するプロジェクトSubagentの名前を明示して依頼する。単なるRoleの読み込みと、実際に独立Agentを起動したことは区別して記録する。

```text
DATのIssue #15とdocs/FAST_FEEDBACK_WORKFLOW.md、現在の未達Gateを確認。
agile-coachにread-onlyで相談し、実測へ進むための最小safe testを1つ提案して。
続いてscrum-masterにread-onlyで相談し、現在のimpedimentと判断待ち、
担当権限、次の1アクションをまとめて。余分な準備やGateを作らない。
双方の出力はadviceとして区別して記録。実RunやGitHub書き込みはしない。
```

相談結果は開発Issue/PRへ集約してよいが、Frozen Run用のfresh sessionへ転記しない。Runtimeでsubagentが使えない場合はread-onlyロール視点の単独レビューへ降格し、実際の独立Agentレビューとしては報告しない。

## 開発プロセスの軽量計測

Frozen `RunEvaluation`や実験Metricの意味論を変更せず、観測できた範囲でIssue/PRに記録する。

| Signal | 観測する時刻 | 解釈 |
| --- | --- | --- |
| Time to first useful signal | 作業着手 → 最初の関連した決定論的PASS/FAIL | 正しいsignalであることが前提 |
| Blocked duration / cause | STOP/UNKNOWN検出 → 承認された解消判断 | 環境、権限、レビュー待ちのどれかを切り分ける |
| Time to accepted empirical Run | 承認済み作業の着手 → 実Runの`ACCEPT` | 静的PreflightのPASSだけでは進捗に数えない |
| Avoidable repeat checks | 状態が変わっていないのに繰り返した確認 | 既存Gateの許す範囲で自動化・共有を検討 |

速度だけを最適化しない。境界違反・Evidenceの妥当性・Human attentionのコストも同時に確認し、負荷が増えるなら運用を単純化する。

## EXP-001へ今から適用する

Runの**現在地と実行許可は必ず [Issue #15](https://github.com/s977043/dynamic-agent-topology/issues/15) の最新記録と承認済みRunbookで再確認**する。過去のcheckpointは最新でない場合がある。

1. 現在承認されているT1 r01 retryに必要な未完の決定とPreflightだけを完了する。推測による「完璧な環境Gate」を追加しない。
2. 必須のSecurity/Permission条件がFAIL・UNKNOWNならSTOPして原因を分離し、modelを起動しない。新たなretry allowanceも生成しない。
3. 既存Runbookに従って許可されたら実測へ進み、結果Artifactを速やかに確認する。
4. 次の作業に向けた無駄な待ち時間を計測し、**Repository開発の別の小さなPR**で改善する。後続のFrozen実験条件には反映しない。

関連: [Issue #123](https://github.com/s977043/dynamic-agent-topology/issues/123)。この文書が新しい実行権限を生むことはない。
