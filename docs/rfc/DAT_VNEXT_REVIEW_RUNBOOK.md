# DAT vNext — Independent multi-perspective review runbook

> **非規範的な設計案（未採用）。** 正本は既存文書（[AGENTS.md](../../AGENTS.md)、[AGENT_HARNESS.md](../AGENT_HARNESS.md)、[EXPERIMENTS.md](../EXPERIMENTS.md)、[RELEASE_READINESS.md](../RELEASE_READINESS.md) など）で、矛盾する場合は正本が優先する。関係文書: [MAINTENANCE_COST_REVIEW.md](../MAINTENANCE_COST_REVIEW.md)、[POST_EXP001_EVALUATION_DESIGN.md](../POST_EXP001_EVALUATION_DESIGN.md)、[RESEARCH_AUTONOMOUS_CODING_LOOP_REFERENCES.md](../RESEARCH_AUTONOMOUS_CODING_LOOP_REFERENCES.md)、[CURRENT_EXECUTION_PLAN.md](../CURRENT_EXECUTION_PLAN.md)。

- 状態: **READY TO DISPATCH / 本文書自体は独立レビューを実施していない**
- 親Issue: [Issue #268](https://github.com/s977043/dynamic-agent-topology/issues/268)
- レビュー対象: [RFC](DAT_VNEXT_RFC.md) + [P0 Baseline](DAT_VNEXT_BASELINE.md)、参照されているコードと公開契約。
- 起案者とレビュー実行者は**別セッション**にする。少なくとも1本は**別モデル**が望ましい。6視点は、実際に隔離したcontextで実行しない限り6つの独立Agentではない。
- 本runbookは**read-onlyレビュー**を依頼するもので、model sessionの起動や、承認・予算・mergeの許可を与えない。

## 1. Objective and non-negotiable rules

問い: **DAT vNextは、ゼロから作るべきか、段階的に改善すべきか、選択的に再利用して再設計すべきか。** 初期推奨のBが正しいと仮定しない。

Reviewerは次を必ず守る:
- 以前の要約ではなく、*レビュー対象のhead SHA時点の*リポジトリで主張を確認する。根拠としてファイルパス、行範囲、またはコードシンボルを示す。
- 観測したコードの挙動、推測したリスク、未検証の仮説、レビューとしての推奨を分ける。
- 設計を言い換えるだけでなく反論する。**AがBより望ましい**場合や、Cが妥当になる場合を示す。
- `AGENTS.md`、`docs/AGENT_HARNESS.md`、`docs/EXPERIMENTS.md`、`docs/RELEASE_READINESS.md` に従う。
- 凍結済みのEXP-001入力、リポジトリ規則、権限、モデル設定、課金を変更しない。
- 有料モデルの評価を起動しない。Anthropicの公式reference codeをコピーしない。
- 他のAgentやsessionに代わって承認を報告しない。
- 静的レビューは、Runtime権限が有効であることや、vNextが開発者体験を改善することの証拠ではない。

## 2. Suggested independent review split

各セッションには、前のReviewerの結論ではなく、**PRの正確なhead SHAと実際のdiffへのリンク**を渡して、別々に実行する。

| Session | ツール（例） | 主な視点 | 反対側からの問い |
| --- | --- | --- | --- |
| R-A | Claude Code（fresh） | Architecture / Developer Experience / Maintainability | これは観測された問題を解く新しいArchitectureか、それとも冗長な抽象化か |
| R-B | Codex CLI（fresh） | Experiment Design / Security / OSS Compatibility | 主張するA/B改善を、評価の漏洩や契約の破壊なしに測定できるか |
| R-C（任意。起案者・R-A・R-Bと別） | Claude CodeまたはCodexのfreshなmodel/session | R-AとR-Bの指摘への反論レビュー、Evidenceの裁定 | どちらかのReviewerがEvidenceを仮定・捏造したり、blockerを見落としたり、自分の作業を承認したりしていないか |

RFC G1の6視点とセッションの対応:

| RFC G1の視点 | 担当セッション |
| --- | --- |
| Architecture | R-A |
| Developer Experience（DX） | R-A |
| Maintainability | R-A |
| Evaluation（Experiment Design） | R-B |
| Security | R-B |
| OSS（OSS Compatibility） | R-B |

R-Cは6視点のどれかを新たに担当するのではなく、R-AとR-Bの指摘を横断して検証する。

1つのcontextで2つのpersonaを演じても、独立Reviewerの代わりにはならない。Reviewerのidentity/session、model、実効的なtool accessはPRに記録する。レビューを実行できなかった場合は **NOT_RUN** とする。

## 3. Exact review prompt — Claude Code (R-A)

リポジトリにアクセスできる新しいClaude Code sessionに貼り付ける。できれば別のclean checkoutで実行する。`<PR_URL>` と `<HEAD_SHA>` をPRの実際の値に置き換える。

```text
あなたはDAT vNext RFCの独立アーキテクチャ・DX・保守性Reviewerです。
作成セッションと独立した新しいコンテキストで、read-onlyにレビューしてください。
対象: <PR_URL>
Issue: https://github.com/s977043/dynamic-agent-topology/issues/268
Reviewed head: <HEAD_SHA>

必ず AGENTS.md、docs/AGENT_HARNESS.md、docs/ARCHITECTURE.md、
docs/NORTH_STAR.md、docs/RELEASE_READINESS.md、
docs/rfc/DAT_VNEXT_RFC.md、docs/rfc/DAT_VNEXT_BASELINE.md、
docs/rfc/DAT_VNEXT_REVIEW_RUNBOOK.md と対象diffを確認してください。

主張を source-verified / repository-reported / hypothetical / untested に分類。
A現行局所改善、Bゼロベース設計+選択的再利用、C全面再構築を
意図的に反対側から比較してください。

必須:
1. DAT（評価基盤）とSingle-Agent Loop（評価対象）を混同していないか
2. 新しいUX導線に、実測の痛点と最小vertical sliceがあるか
3. 既存dat-select/dat-observeと機能重複しないか
4. 互換性が必要なSchema/CLI/Skill/Pluginとfreezeの扱いは適切か
5. 観察から効用を誤推論していないか
6. Bを採用しない方がよい反例を最低2件示す

各Findingを severity (BLOCKER/MAJOR/MINOR/NOTE)、path:line、
根拠、影響、具体的な最小修正、検証方法で報告。
行番号が取得できない場合は path + 見出し/該当テキストと明記。
未実行のテストをPASSと記述しない。Issue/PRへの書込み・mergeは禁止。
最後に APPROVE / CHANGES_REQUIRED / INCONCLUSIVE と独立性を明記。
```

## 4. Exact review prompt — Codex CLI (R-B)

別の新しいsessionで実行する。独立に判断する前に、R-Aの指摘を入力に使わない。

```text
DAT vNext Issue #268のDraft PRに対し、
独立した実験設計・セキュリティ・OSS互換性レビューをread-onlyで行ってください。
対象repo: s977043/dynamic-agent-topology
Reviewed head SHA: <HEAD_SHA>
対象docs: docs/rfc/DAT_VNEXT_RFC.md,
docs/rfc/DAT_VNEXT_BASELINE.md,
docs/rfc/DAT_VNEXT_REVIEW_RUNBOOK.md
必ず実際のdiff、既存AGENTS.md、docs/AGENT_HARNESS.md、
docs/EXPERIMENTS.md、docs/METRICS.md、
docs/RELEASE_READINESS.md、関連Issue #248/#244/#223を照合してください。

反証の主眼:
- P0操作Baselineの計測無しでBの有効性を断定していないか
- train/test/regression/paired block/Task difficulty/Oracleの統制があるか
- Synthetic fixtureを実モデル実測へ誤昇格させていないか
- run_observationと比較実験の目的を混同していないか
- 同一Task/Runtime/Model/Effort/ACの制御と、欠測・中断・コストが扱えるか
- Role/Permission分離、Human Approval、Frozen 33 blobsは安全か
- 既存0.4.1の公開API/CLI exit code/Skill nameの互換性は維持できるか
- 直接依存や課金を導入せずに最小の検証を実行できるか
- 少なくとも2つのNO-GO理由と、Aへ戻すトリガーを示す

変更は一切行わない。請求が発生するモデル実験を起動しない。
出力: severity (BLOCKER/MAJOR/MINOR/NOTE)、path:line、根拠、
反例、修正案、受入テスト、未検証点。
最後に APPROVE / CHANGES_REQUIRED / INCONCLUSIVE。
自分で作成した変更を承認してはならない。
```

## 5. Report template — MUST NOT fabricate

実際に実行したsessionごとに1件記録する:

```text
Review: R-A | R-B | R-C
Executor: <tool/model/session id or NOT_RUN>
Independence: separate-session | separate-model | same-session | NOT_VERIFIED
Reviewed head: <full SHA>
Diff range: <base...head>
Review date/time: <actual>
Scope: <files/lenses>
Validation actually executed: <commands + exit statuses or NOT_RUN>
Findings:
- [BLOCKER|MAJOR|MINOR|NOTE] path:line — fact / risk / impact / smallest fix
- ...
Verdict: APPROVE | CHANGES_REQUIRED | INCONCLUSIVE | NOT_RUN
Blocking open findings: <n or unknown>
Follow-up: <code/doc correction + re-review requirement>
```

### Adjudication

- Issueの起案者は対立するReviewerの指摘を統合してよいが、**自己承認してはならない**。
- BLOCKER: 安全性の侵害、不正なEvidenceの帰属、frozen fileへのリスク、移行や承認のない公開契約の喪失。
- MAJOR: 目的・計測の不足、検証不能な仮説、negative caseの欠落、避けられる重複Architecture。
- MINOR: 不明確な定義、不正確なEvidenceの参照先、小さなUXのgap。
- NOTE: 任意の改善。着手を止めるものではない。
- 修正後、Reviewerは古い指摘だけでなく**更新後のhead**を確認する。未検証のcriticalな主張が残れば INCONCLUSIVE。
- このdocs-only RFCがAPPROVEされても、実験の実行、権限変更、有料予算、公開Releaseは**許可されない**。

## 6. PR readiness and stop rule

レビュー完了とする前に:
- [ ] R-Aを実際に実行し、head SHAとともに記録した
- [ ] R-Bを実際に実行し、head SHAとともに記録した
- [ ] 別session。可能なら少なくとも1本は別model
- [ ] 指摘を統合して理由を示し、必須のcriticalな指摘を解消した
- [ ] 起案者自身の見解を独立レビューと表示していない
- [ ] `main` とPR headのSHAを確認し、必須CIの状態を確認した
- [ ] 範囲がdocs-onlyのまま。EXP-001の不変の原本blobに触れていない
- [ ] 課金されるmodel評価なし、prompt/secretの露出なし
- [ ] mergeは `docs/AGENT_HARNESS.md` に従い、該当するGateをすべて満たした後だけ

**レビューを実際に実行するまでは R-A = NOT_RUN、R-B = NOT_RUN、R-C = NOT_RUN。**
