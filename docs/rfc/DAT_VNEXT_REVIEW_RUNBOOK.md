# DAT vNext — Independent multi-perspective review runbook

- Status: **READY TO DISPATCH / NO INDEPENDENT AGENT REVIEWS PERFORMED BY THIS DOCUMENT**
- Parent: [Issue #268](https://github.com/s977043/dynamic-agent-topology/issues/268)
- Review targets: [RFC](DAT_VNEXT_RFC.md) + [P0 Baseline](DAT_VNEXT_BASELINE.md), the referenced code and public contracts.
- Draft author and review executor must be **different sessions**. Prefer **different models** for at least one review. 6 perspectives are not 6 independent agents unless genuinely executed in isolated contexts.
- This runbook requests **read-only review**; it does not start model sessions or grant approval, budget or merge permission.

## 1. Objective and non-negotiable rules

Question: **Should DAT vNext be built from scratch, incrementally improved, or redesigned with selective reuse?** Do not assume the initial recommendation B is correct.

The reviewer MUST:
- Verify claims against the target repository *at the exact reviewed head SHA*, not an earlier summary. Identify file paths, line ranges or code symbols as evidence.
- Separate observed code behavior, inferred risk, untested hypothesis, and review recommendation.
- Challenge the design rather than merely paraphrase it. Identify cases where **A is preferable to B**, or C becomes warranted.
- Respect `AGENTS.md`, `docs/AGENT_HARNESS.md`, `docs/EXPERIMENTS.md`, `docs/RELEASE_READINESS.md`.
- Never alter frozen EXP-001 inputs, repo rules, permissions, model settings or billing.
- Do not launch a paid model evaluation or copy official Anthropic reference code.
- Do not report approval on behalf of other agents or sessions.
- A static review is not evidence that Runtime permissions are effective or that vNext improves developer experience.

## 2. Suggested independent review split

Run these as separate sessions, each supplied with the **exact PR head SHA and links to the actual diff**, not with the previous reviewer's conclusions.

| Session | Tool (example) | Primary lenses | Explicit adversarial question |
| --- | --- | --- | --- |
| R-A | Claude Code (fresh) | Architecture / Developer Experience / Maintainability | Is this a new architecture solving an observed problem, or redundant abstraction? |
| R-B | Codex CLI (fresh) | Experiment Design / Security / OSS Compatibility | Can the claimed A/B improvement be measured without evaluation leakage or contractual breakage? |
| R-C (optional, separate from author and R-A/R-B) | Claude Code or Codex fresh model/session | Challenge review of R-A + R-B findings, evidence adjudication | Did either reviewer assume or invent evidence, omit a blocker, or approve its own work? |

Do not substitute two personas in a single context for independent reviewers. Reviewer identity/session, model and effective tool access are recorded in the PR. If a review cannot be run, mark **NOT_RUN**.

## 3. Exact review prompt — Claude Code (R-A)

Copy into a new Claude Code session with repository access, preferably a separate clean checkout. Replace `<HEAD_SHA>` with the PR's actual SHA.

```text
あなたはDAT vNext RFCの独立アーキテクチャ・DX・保守性Reviewerです。
作成セッションと独立した新しいコンテキストで、read-onlyにレビューしてください。
対象: https://github.com/s977043/dynamic-agent-topology/pulls (対象Draft PRを選ぶ)
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

Run in another fresh session, not using R-A's findings as input before independent judgment.

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

One record per genuinely executed session:

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

- Issue author may consolidate conflicting reviewer findings but **must not self-approve**.
- BLOCKER: safety breach, invalid Evidence attribution, frozen file risk, loss of public contract without migration or authorization.
- MAJOR: insufficient objective/measurement, untestable hypothesis, missing negative case, avoidable duplicate architecture.
- MINOR: unclear definition, imprecise evidence pointer, small UX gap.
- NOTE: optional improvement, not a launch blocker.
- After corrections, reviewers inspect the **updated head**, not only old feedback. Any unverified critical claim -> INCONCLUSIVE.
- Even APPROVE of this docs-only RFC does **not** authorize experiment runs, permission changes, paid budget or public release.

## 6. PR readiness and stop rule

Before marking review complete:
- [ ] R-A genuinely executed and recorded with head SHA
- [ ] R-B genuinely executed and recorded with head SHA
- [ ] Separate session; at least one different model if available
- [ ] Findings consolidated and justified; critical required findings resolved
- [ ] Author's own view not labeled independent
- [ ] `main` and PR head SHA reviewed; required CI status verified
- [ ] Scope remains docs-only; EXP-001 original immutable blobs untouched
- [ ] No billed model evaluation, no prompt/secret exposure
- [ ] Merge per `docs/AGENT_HARNESS.md` only after full applicable gates

**Until reviews are actually run: R-A = NOT_RUN; R-B = NOT_RUN; R-C = NOT_RUN.**
