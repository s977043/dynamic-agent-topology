# AIモデル切替に伴うWorkflow再検証 — research note

## Status / freeze boundary

**Research-only / proposal, not adopted.** Tracking: [Issue #162](https://github.com/s977043/dynamic-agent-topology/issues/162).

EXP-001 [#15](https://github.com/s977043/dynamic-agent-topology/issues/15) の完了・Feature Freeze解除までは既存のExperiment、Model、Effort、Runtime、Schema、評価条件、Run受理条件を変更しない。このノートは研究候補であり、Runtimeへの適用、昇格、承認権限の変更を行わない。

## Primary source / provenance

- Stefan Wolpers, [To Switch, or Not to Switch the AI Model](https://www.scrum.org/resources/blog/switch-or-not-switch-ai-model), Scrum.org, 2026-10-11.
- **Source claim**: token単価が下がっても、workflowの再検証・人間による修正・手戻り・継続監視を含む総費用が下がるとは限らない。形式が正しくても、ブロック中の案件を「順調」と誤記する意味的な失敗は起こり得る。
- **Source proposal**: workflow owner、workflow別の品質基準、成功/失敗case、入力と設定、現行baseline結果を保管し、移行前に再検証、移行後に観測する。スターター5例は最初の学習用で、品質保証ではない。
- **DAT interpretation (unverified)**: model migrationには、Topologyの効果や失敗時のmodel escalationとは別の、同一workflow上のchanged-model比較が必要かもしれない。

記事の記述はDATの実測証拠ではない。記事の「AI Definition of Done」はworkflow別の受入基準であり、ScrumのIncrementに対する正式なDefinition of Doneの置換ではない。

## Problem / boundary

既存の [#88](https://github.com/s977043/dynamic-agent-topology/issues/88) は失敗からのmodel escalationとhandoffを研究する。本件は既存workflowのモデルを置換して継続利用できるかという別の意思決定である。

- Model escalation (recovery) != Model migration (continued-use decision)
- Price per token != quality-adjusted workflow total cost
- Format/schema PASS != semantic correctness PASS
- Evidence != workflow owner judgment; Trigger != Permission
- Model change != permission to delete/simplify Harness gates

既存のTopology、Role、Model、Runtime、Permission分離を維持する。同時にPrompt、Skill、Context、Effort、Evaluator、Topologyを変更するときは要因を分離するか交絡と記録する。

## Falsifiable hypotheses

1. **H1:** 形式チェックをPASSするが根拠と矛盾するsemantic failureを、独立した評価者が負例で検出できる。
2. **H2:** 同一workflowの旧/候補モデル比較では、token単価に現れない修正・再試行・検証労力・品質差が観測され得る。
3. **H3:** 低リスク探索と高影響の本番運用とで検証の深さを分けることで、重大な品質リスクを見落とさず検証工数を抑えられる可能性がある（未実証）。

差が認められない、比較可能性が不足する、費用対効果が劣る場合はREJECT / INCONCLUSIVEを許す。結果を見た後で合格基準を変えない。

## Cheapest useful verification — post-freeze only

1. **1 workflowを選択。** Owner、business risk、受け入れ可能/不可の出力、品質下限と評価基準を事前定義。Prompt/Skill/Context・Runtime・Model version・Effortと参照先を記録する。機密データは匿名化。
2. **スターター5ケース。** 通常入力、ブロック状態の反転、根拠の欠落、誤った根拠、入力欠損/不明を候補とする。事前確定の根拠と期待結果を保存する。5件通過は本番承認条件ではない。
3. **Matched paired test。** 旧モデルと候補モデルで同一workflow/input、固定されたprompt・skill・workspace policy・budget・evaluatorを用い、それぞれfresh sessionで実行する。順序をcounterbalanceする。API仕様や環境差など制御できない要因はconfoundとして記録。
4. **Evidenceを記録。** Case ID、run/session、arm、provider/runtime/model ID/version、effort、revision、匿名化input、output identity、形式/semantic verdict、独立reviewer、retries、Human修正時間、tokens/価格の前提、移行再検証人時、制約、rollback候補。未測定値はunknownとし0にしない。
5. **Decision。** 重大なsemantic誤り、承認違反、虚偽のverificationはNO_GO。検証不十分ならINCONCLUSIVE。品質下限を満たした場合に限り総コストや便益を比較し、継続利用はworkflow ownerが判断する。導入後のドリフト観測と新たなfailureの回帰ケース化も計画する。

### Cost screening

比較単位は「合意済み品質を満たす検証済みworkflow 1完了あたりの総コスト」。モデルの呼び出し費だけでなく、retry、validation、Human correction、障害復旧、one-off migration/revalidation人時、定常保守を分離して記録する。

移行後の月間純節約が正である場合のみ、移行+再検証の一時費用 / 月間純節約で回収月数を試算する。品質・能力向上目的の移行は金銭回収率だけでは評価しない。

## Review lenses and risks

| Lens | Check |
|---|---|
| Scientific validity | Model以外の要因と実行順序を管理し、paired effectを過大評価しない |
| Correctness | 表面上成功しているsemantic failureを負例で検出する |
| Autonomy | EvidenceとOwnerのJudgmentを分け、既存のHuman gateを保持する |
| Economics | 修正・監視・移行・再検証費用の未測定値を0扱いしない |
| Fast Feedback | 1 workflow / 5件から開始、必要性が見えなければ拡張しない |
| Security | 未サニタイズのtrace・機密情報・Promptを公開しない |

## Non-goals / adoption gate

既存の [Experiment principles](../../docs/EXPERIMENTS.md) / [Metrics](../../docs/METRICS.md) を変更しない。異なるModelの実測を現行集計へ混ぜない。EXP-001のfreeze、Run acceptance、固定matrix、retry権限を変更しない。外部OSS/SDK/クラウド依存を追加しない。

**Adoption gate**: #15完了・unfreeze確認 → 最小実験計画とリスクの独立レビュー → 実測Evidence → 採否判断。必要と確認された場合にだけcanonical契約とvalidationの変更を別Issueで提案する。現状のsource adoptionはempty。
