# Claude Code Advisor × read-only Researcher: 3-model collaboration experiment

## Status / scope

**Research-only, deferred candidate** (observed 2026-10-11). Tracking: [#93](https://github.com/s977043/dynamic-agent-topology/issues/93) for compound execution; [#88](https://github.com/s977043/dynamic-agent-topology/issues/88) for model escalation and handoff.

This note records an option for future DAT experiments, **not** a default Claude Code configuration or an adopted DAT contract. EXP-001 Feature Freeze revision 3 remains in effect. No frozen artifacts, Experiment schema, canonical Topology, Role, Routing Policy, runtime adapter, evaluation semantics, or development-harness policy is changed here. No external SDK, OSS code, or dependency is introduced.

## Source material and verification boundary

Discovery: user-provided setup concept, 2026-10-11: **Sonnet 5.5 main / Haiku 5.5 read-only search subagents / Opus 5.5 Advisor**. It is a proposed workflow, not measured DAT evidence.

Official product documentation (consulted 2026-10-11):

- [Anthropic — Advisor tool](https://code.claude.com/docs/en/advisor)
- [Anthropic — Create custom subagents](https://code.claude.com/docs/en/sub-agents)

### Confirmed product capabilities

- Claude Code supports `--advisor` or `/advisor`. Sonnet 5.5 main + Opus 5.5 advisor is an allowed model pairing. Advisor is **experimental**, server-side, Anthropic-API-only (not Bedrock/Vertex/Foundry); supported model/version/feature flags and billing eligibility must be checked in the actual runtime.
- The main model decides *when* to invoke Advisor; prose instructions cannot enforce or cap calls. Advisor sees the **full conversation, including tool calls and results**. Advisor's own transcript read is not cached. API-billed use incurs model-token charges; subscription use counts toward plan usage limits (not necessarily a separately itemized monetary charge).
- **Subagents inherit Advisor configuration** and independently apply model-pairing checks; thus an Opus Advisor may be invoked by a Haiku Researcher, not just Sonnet. No assumption of “Opus consultation only by Sonnet” without observed evidence.
- Project subagents support `model`, `effort`, and `tools` allowlists. Model selection can be overridden by per-invocation arguments and provider/organization availability. Inspect actual resolved model rather than equating configuration with observation.
- `tools: Read, Grep, Glob` omits shell, writes and MCP tools from the subagent's configured tool pool. **Read-only tools are not confidential-data access control**: file-read access, project trust, parent permissions, and actual runtime behavior still need bounded negative tests.

For the full 5.5 pairing, verify an appropriate Claude Code version; the official Advisor documentation requires v2.1.293+ for Haiku 5.5 use. Version support is not evidence that a specific local environment is ready.

## DAT interpretation

Separate these concepts:

```text
semantic Role != model binding != tool permission != execution strategy
Advisor advice != independent Reviewer Judgment != deterministic Verification
declared model/tool list != observed invocation / effective restriction
added Agent count != task improvement
```

- Sonnet: optional main Orchestrator / Builder binding; ownership of implementation and verification commands is unchanged.
- Haiku: optional bounded Explorer/Researcher binding; independent, read-only exploration and concise file/path evidence. A natural-language “do not edit” instruction alone is not a security guard.
- Opus Advisor: optional **in-context decision-support leg**, not an automatically scheduled independent reviewer, verifier, or gate. Seeing the full solver transcript is a different intervention from an isolated critic with controlled input.
- Keep independent reviewer / verifier and human-owned gates distinct. Advice may suggest checks but cannot attest their execution or approve the author's PR.
- Do not hard-code Sonnet/Haiku/Opus into provider-independent DAT schemas or runtime adapters on the strength of product support alone.

## Falsifiable hypotheses (post-freeze)

H1: Adding bounded read-only Researcher delegation to Sonnet can reduce completion time or cost **without lowering independently verified task quality** for repository-search-heavy tasks.

H2: Adding optional Opus Advisor can improve verified quality / reduce costly rework on ambiguous, multi-step tasks **after accounting for complete Advisor context-read cost**.

H3: Combining Researcher + Advisor can be better or worse than their individual effects; concurrency and Advisor inheritance can create interaction costs. “Three models” is not automatically optimal.

H4: Model/tool isolation declared in configuration corresponds to actual observed behavior in the chosen runtime, or is explicitly recorded as unsupported/unknown.

### Cheapest useful verification

**Stage 0 — safety and feasibility (without touching EXP-001 runs):**

1. On a disposable nonsecret fixture and an explicitly selected runtime, record Claude Code version, provider, effective model IDs/effort, project trust, tool allowlist, Advisor enabled/disabled state, and whether a subagent inherits Advisor.
2. Verify allowed `Read`/`Grep`/`Glob` outcomes; test prohibited `Write`, `Edit`, shell, MCP and network paths without real secrets or external side effects. A mere static YAML inspection is **not** a negative runtime test.
3. Check sanitized logs for any unexpected Advisor call originating from the Haiku leg. If subagent Advisor cannot be reliably suppressed, retain it as an explicit co-intervention/confounder.
4. Stop rather than promote configuration if isolation, observability, billing, or provider compatibility is unverified.

**Stage 1 — preregistered capability ablation after #15 closes and freeze is lifted:**

| Arm | Main | Researcher | Advisor | What it helps isolate |
|---|---|---|---|---|
| A | Sonnet | none | off | single-agent baseline |
| B | Sonnet | Haiku read-only | off | marginal Researcher package (B−A) |
| C | Sonnet | none | Opus | marginal Advisor package (C−A) |
| D | Sonnet | Haiku read-only | Opus | joint package and interaction (D−B−C+A) |

- Predeclare task classes, allocation, verified acceptance criteria, practical improvement threshold, regression limit, security stop conditions, and feasible run budget. Include simple tasks where extra models should have **no value**, not just hard tasks.
- For each task/arm use an equivalent repository revision, input, clean workspace and fresh session. Hold evidence commands and external evaluator constant. Counterbalance execution order and prevent cross-arm leakage.
- Separate **configured availability**, **actual Researcher invocation**, **actual Advisor invocation** (including Haiku-originated calls), **Advisor returned / declined / unavailable**, **effective model IDs**, **tool restrictions**, and **verified outcomes**. Report assignment-to-arm effects separately from observed activation; if a leg is not activated, do not infer that its execution improved the outcome.
- Record per-leg plus total fresh input, cache read/write, output tokens, latency, failures, recovery, human intervention, regressions, permission denials, and accuracy of any “consult now” decision. For API-billed runs, record price version and observed billing/cost where supported; for subscriptions, record reported usage against plan limits and mark actual per-run charges **not observed**, rather than inventing a dollar amount. Count declined, unavailable, failed and discarded legs.
- Advisor reads the full transcript, whereas an isolated Reviewer sees controlled evidence. Don't interpret C or D as proof of independent Review. Keep a separate independent evaluator blind to arms when feasible.
- H1/H2/H3 effects are specific to the observed workload and bindings. With limited pairs, report `INCONCLUSIVE` rather than asserting an improvement. If inherited Advisor use changes the intended D treatment, report the intervention as actually run; do not silently relabel it.

**Stage 2 — optional policy study:** only if treatment works, evaluate *when* to activate Researcher/Advisor over a mixed workload. Compare selective routing with always-off and always-on, retaining unnecessary and missed activations and **all** decision/coordination overhead. Do not infer selector quality from successful escalations alone.

## Adoption / rejection boundaries

- **Adopt after post-freeze evidence** only if a measured, repeatable benefit per verified success clears preregistered thresholds and effective permissions are independently demonstrated; start with manual runtime mapping rather than adding a new DAT contract.
- **Reject or defer** if verification quality regresses, Advisor token cost outweighs improvements, search delegation increases latency/noise, inherited advisor calls confound allocation, security negative tests fail, or the existing topology/routing vocabulary suffices.
- This research document may be merged independently of runtime adoption. Never modify `CLAUDE.md`, `.claude/agents/`, or `docs/AGENT_HARNESS.md` without the repository's human-owned harness-change approval and runtime negative tests.

## Relationship to open work

- [#15](https://github.com/s977043/dynamic-agent-topology/issues/15): **current priority**, EXP-001 empirical runs and active freeze. Do not switch its runtime/model/effort.
- [#88](https://github.com/s977043/dynamic-agent-topology/issues/88): Advisor differs from fresh-session **model escalation with compact handoff**; Advisor sees the full transcript and leaves main-session execution with Sonnet.
- [#93](https://github.com/s977043/dynamic-agent-topology/issues/93): owns testing optional compound execution. This four-arm study is a candidate subexperiment, not a canonical strategy taxonomy.
- [#82](https://github.com/s977043/dynamic-agent-topology/issues/82): independent adversarial Judgment remains separate from Advisor.
- [#59](https://github.com/s977043/dynamic-agent-topology/issues/59) and [#123](https://github.com/s977043/dynamic-agent-topology/issues/123): permission enforcement and **developer-harness** role configuration require their own evidence/approvals.

### Research review (author-led, not independent approval)

1. **Architecture:** KEEP: product-specific bindings remain optional; no canonical schema or EXP-001 modifications. REJECT: “Advisor = verifier” and mandatory 3-model topology.
2. **Experiment method:** CHANGE from naive 3-arm to four-arm comparison. B and C identify separate packages; D exposes interaction. If Haiku invokes inherited Advisor, this must be explicitly observed as part of D.
3. **Security / cost / governance:** KEEP with safeguards: permission and data-read limits require actual runtime tests; full-transcript Advisor sharing and all-token accounting must be disclosed; existing human approval boundaries remain.

These are author-led design checks. They do **not** satisfy an independent GitHub PR review or empirical smoke test.
