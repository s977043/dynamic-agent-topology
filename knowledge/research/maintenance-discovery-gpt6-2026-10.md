# GPT-6系によるソフトウェア保守 — Maintenance Discovery research note

> Status: **research-only / unverified locally / not adopted** (2026-10-17)
> Primary source: [OpenAI, Maintaining software with the GPT-6 family](https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family)
> Related existing work: [#162 workflow model change](https://github.com/s977043/dynamic-agent-topology/issues/162), [#88 evidence-based escalation](https://github.com/s977043/dynamic-agent-topology/issues/88), [#93 execution strategy](https://github.com/s977043/dynamic-agent-topology/issues/93)

## Source claim (OpenAI's environment, NOT a DAT observation)

OpenAI reports maintenance tasks involving unused code, stale experimentation state, flaky tests, CI and dependency reduction. Its report includes experiments comparing GPT-6 family models, effort and investigation cost. Reported counts and cost ratios are **case-specific**, not a general benchmark or a DAT adoption decision.

## DAT interpretation (hypothesis only)

A maintenance candidate's **discovery** and its **verified safe disposition** are distinct outcomes. A model finding many candidates is not necessarily better when false safe-deletion decisions, review burden, missed indirect use or total cost are considered. Selective independent review may help in high-risk categories, but prior [EXP-001 Keep T0](../../experiments/EXP-001-t0-vs-t1/DECISION.md) remains the only local pilot decision; do not infer T1 superiority from this article.

- Discovery evidence != verification evidence != owner judgment.
- Apparent dead code != proven unused code (runtime/dynamic reference and operational kill switches are counterexamples).
- A CI green check != demonstrated absence of regression in production.
- Proposal != change permission; review verdict != merge authorization.
- Source claims, sanitized local observations and human confirmations must carry separate provenance.

## Falsifiable questions

1. At a fixed repository revision, does a higher-effort or different model increase **verified valid findings per total cost**, without increasing dangerous false accepts?
2. Does independent verification change acceptance accuracy enough to justify its additional token, elapsed-time and human-attention costs relative to T0?
3. Do deterministic static checks plus a single agent suffice for a scoped low-risk test/CI maintenance task?
4. When the evidence is incomplete, does each condition abstain or escalate instead of treating absence of references or telemetry as proof of non-use?

## Cheapest useful evaluation (proposal; not executed)

1. Register one owner-approved, non-production repository snapshot and a **read-only** maintenance class. Start with reproducible test-result accounting; do not mutate deployment settings or delete code.
2. Build a small **held-out** set with positive and negative examples: truly unused symbol, dynamic reference, required kill switch, missing telemetry, stale-but-intentional configuration, and a test whose removal merely hides a failure. Have a human independently confirm the expected verdict or mark it UNKNOWN.
3. Freeze repository SHA, instructions, tool access, runtime, task budget, evaluation criteria and evidence visibility. Run a deterministic/static baseline P0, then T0 with the same inputs. Compare model or effort separately from topology; counterbalance order and use fresh sessions. Do not expose held-out answers to the discovering agent.
4. Record candidate IDs, provenance/source ref, discovered risks, abstention, human adjudication, tested conditions, actual run cost, latency and remediation/review time. Missing usage or outcome is UNKNOWN, never 0 or PASS.
5. Escalate to T1/independent review only on predeclared risk classes or measured T0 limitations. Use matched pairs with the same acceptance oracle. Capture regression and harmful false-positive cases.
6. Decide **KEEP T0 / EXPAND / REJECT / INCONCLUSIVE** after independent outcome evaluation and authority review. Keep unchanged schemas, canonical topologies, runtime adapters and EXP-001 artifacts unless separately approved.

## Available external pilot candidates (not DAT measurements)

[PlanGate #1586](https://github.com/s977043/PlanGate/issues/1586) records repository-specific maintenance cost observations at base SHA `5fcdb2e3`, including CI workflow duration, E2E flakiness and maintenance surfaces. This is **external local-repository evidence**, not a completed DAT experiment. The current target main SHA, status and safety classification must be rechecked before constructing a fixture. The associated [PlanGate #1585](https://github.com/s977043/PlanGate/issues/1585) owns the integration proposal, not model or topology adoption.

- If an observation concerns protected workflow files or approval-token guard tests, use it as a **read-only or negative example**, not an Agent-editable remediation task. Explicit Human and HO procedures remain authoritative.
- The source's observed 1,000-run sample must not be treated as 1,000 independently validated candidate findings. Record denominators, source windows and the separate quality oracle.
- **Metric comparability warning (2026-10-18)**: PlanGate #1586 now separately records main `1d624d95` [Test run 39028937133](https://github.com/s977043/PlanGate/actions/runs/39028937133) (wall-clock 421 seconds, success) and `5fcdb2e3` [run 38872144619](https://github.com/s977043/PlanGate/actions/runs/38872144619) (429 seconds, success). Its older aggregate `210 Test runs / ~2,155 min` implies ~10.26 minutes/run, not comparable with these ~7-minute individual wall times without establishing denominator, billable unit and aggregation method. **No savings or model effect was measured**.
- [Flaky E2E #1556](https://github.com/s977043/PlanGate/issues/1556) is **closed/completed as of 2026-10-17** after corrective PR #1569 and ten observed successful job executions (one PR + nine main, with zero failures). Treat it as a **historical verified correction example**, not an open remediation task or a zero-population-flake-rate claim. Newly observed failures would require fresh dated evidence and Owner triage; other open work remains with its existing owners.
- **Negative evidence-ordering example:** PlanGate [run 38330052668](https://github.com/s977043/PlanGate/actions/runs/38330052668) failed with `TemporaryDirectory.cleanup` / `ENOTEMPTY(pack)` on **2026-10-13**; the correcting [Issue #1578](https://github.com/s977043/PlanGate/issues/1578) was completed on **2026-10-15**. The original run cannot be called a *post-fix recurrence*. Current main's `test_ratchet.py` disables `gc.auto` and `maintenance.auto`. Future recurrence remains UNKNOWN without newer runs. Source: [PlanGate #1586](https://github.com/s977043/PlanGate/issues/1586) timeline correction.
- Any pilot case selected after approval must preserve separate `observedAtSha`, `evaluatedAtSha`, and review/decision timestamps. Missing values remain UNKNOWN, including human time and operational savings.

### Cross-PR integration note

[Research PR #203](https://github.com/s977043/dynamic-agent-topology/pull/203) independently edits `knowledge/research/README.md` and `knowledge/sources.yaml`. Integrators must reconcile both new rows/entries after the first PR merges; do not resolve by silently discarding either source. This is a merge-order warning, **not** a request to promote or merge either PR without its required independent review.

## Minimum success and stop conditions

- Zero observed critical dangerous false accepts **in the pilot sample**; this does not prove a zero population rate.
- Every accepted candidate has evidence pointers and an explicit risk/unknown disposition; report selection denominator and rejected/abstained cases.
- No run is counted as successful without observed results and independent quality assessment.
- Stop on permission-boundary ambiguity, missing ground truth, a non-reproducible fixture, sensitive-data exposure, confounded comparisons or budget exhaustion.
- Reject or defer any extra model/reviewer layer that does not demonstrate enough benefit for its coordination cost.

## Adoption boundary

This note adds **no runtime capability, autonomous issue dispatch, new schema, benchmark claim, source promotion, model routing, CI schedule or merge permission**. The OpenAI article is an external engineering report; DAT must obtain its own evidence before adoption. Existing [experiment evaluation](../../docs/EXPERIMENTS.md), [metrics](../../docs/METRICS.md) and [knowledge admission](../README.md) own downstream decisions.
