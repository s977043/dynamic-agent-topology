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

## Minimum success and stop conditions

- Zero observed critical dangerous false accepts **in the pilot sample**; this does not prove a zero population rate.
- Every accepted candidate has evidence pointers and an explicit risk/unknown disposition; report selection denominator and rejected/abstained cases.
- No run is counted as successful without observed results and independent quality assessment.
- Stop on permission-boundary ambiguity, missing ground truth, a non-reproducible fixture, sensitive-data exposure, confounded comparisons or budget exhaustion.
- Reject or defer any extra model/reviewer layer that does not demonstrate enough benefit for its coordination cost.

## Adoption boundary

This note adds **no runtime capability, autonomous issue dispatch, new schema, benchmark claim, source promotion, model routing, CI schedule or merge permission**. The OpenAI article is an external engineering report; DAT must obtain its own evidence before adoption. Existing [experiment evaluation](../../docs/EXPERIMENTS.md), [metrics](../../docs/METRICS.md) and [knowledge admission](../README.md) own downstream decisions.
