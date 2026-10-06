# Claude Code Mods: runtime permission and audit guardrails

## Status

**Research note / deferred runtime-specific evaluation candidate.**

This note does not change EXP-001, its frozen artifacts, DAT schemas, canonical topologies, routing policies, Runtime Adapter behavior, or evaluation semantics.

DAT is currently in the EXP-001 evidence-acquisition phase. Any runtime behavior change derived from Claude Code Mods is deferred until the EXP-001 Feature Freeze is completed.

Tracking: [Issue #59](https://github.com/s977043/dynamic-agent-topology/issues/59)

## Primary source

- Anthropic: [Customize Claude Code with mods](https://claude.com/blog/claude-code-mods)
- Published: 2026-10-01
- Product: Claude Code

## Source claims

Anthropic describes Mods as TypeScript functions that intercept Claude Code events. A Mod can run before, after, instead of, or around an event.

The official announcement states that Mods can, among other things:

- rewrite a prompt before it reaches the model;
- block, rewrite, or retry a tool call;
- approve or deny a permission request;
- redact secrets from tool output before the model reads it;
- modify or replace parts of the Claude Code UI;
- ship inside plugins and run in the CLI and desktop app.

Anthropic also states that Mods are **not sandboxed** and run with the same machine access as Claude Code itself.

For Team / Enterprise and machines using managed settings, Anthropic documents a built-in `sec-default` Mod that loads first by default and restricts risky behavior by subsequently loaded Mods. Administrators can choose a different first-loaded Mod; Anthropic recommends retaining `sec-default` in that case.

These are source claims, not DAT benchmark results.

## DAT interpretation

Claude Code Mods should be treated as a **runtime-specific implementation mechanism**, not as a new DAT Architecture Plane.

The closest existing DAT concepts are:

- **Runtime Mapping** — map abstract capability and permission intent to Claude Code-native mechanisms;
- **Observed Execution** — record runtime-visible actions, permission decisions, and violations;
- **Harness diagnostic layer** — diagnose whether actual tools, permissions, policy, and evidence paths enforce the intended invariant;
- **Permission Boundary** — keep Role intent separate from actually enforced capabilities.

Conceptually:

```text
DAT Role / Permission intent
        ↓
Runtime Mapping
        ↓
Claude Code native controls
        +
optional Mod enforcement / observation
        ↓
Observed Execution
        ↓
Evidence / Evaluation
```

Mods therefore fit below DAT's provider-agnostic contracts. They should not leak Claude Code-specific event or plugin concepts into canonical Topology definitions without evidence that a provider-agnostic abstraction is needed.

## Why this matters

DAT already distinguishes:

```text
Role != Permission
Declared intent != Runtime-enforced capability
Attestation != Verification
Reviewer != Verifier
```

Prompt instructions alone cannot establish a strong runtime permission boundary.

Mods create a candidate mechanism for enforcing or observing parts of that boundary at Claude Code runtime events. This is potentially useful, but the existence of the mechanism is not evidence that DAT should adopt it.

## Candidate uses to evaluate

After EXP-001, evaluate only against an observed runtime gap.

Candidate uses include:

1. **Permission enforcement**
   - block a tool call that violates an explicit no-write or restricted-write boundary;
   - deny a permission request that conflicts with DAT runtime binding.

2. **High-risk action confirmation**
   - require explicit operator confirmation before a harmless test fixture simulates a destructive or high-impact action;
   - keep the policy runtime-specific rather than changing canonical Topology.

3. **Sensitive-output handling**
   - redact known synthetic secret markers from tool output before model consumption;
   - verify that redaction does not become a substitute for credential isolation.

4. **Audit observation**
   - record tool and permission events for later comparison with ExecutionTrace;
   - keep audit observation distinct from independent Verification.

5. **Runtime UI**
   - expose boundary state, current role, or pending approval to the operator;
   - treat UI as observability, not enforcement unless the underlying runtime event is actually blocked.

## Security and trust boundary

A Mod must **not** be treated as a sandbox or independent security boundary.

Important implications:

- a Mod runs with the same machine access as Claude Code;
- plugin / Mod provenance is part of the trust model;
- Mod ordering may affect behavior;
- a compromised or incorrectly ordered Mod may weaken intended controls;
- runtime-native permission policy and OS / container isolation remain separate controls;
- production credentials or infrastructure must not be exposed merely because a Mod is present.

For managed environments, `sec-default` may provide an additional product-level protection layer, but DAT should verify actual configured behavior rather than infer it from documentation.

## Hypotheses

### H1 — runtime permission enforcement

If an observed Claude Code task has a reproducible boundary violation that prompt-only or current Manual Adapter controls do not reliably prevent, a minimal Mod guard may reduce violations.

### H2 — evidence completeness

A first-loaded audit Mod may improve completeness of observable tool / permission events and make runtime divergence easier to diagnose.

This would improve observation only. It would not make the Mod's own log an independent Verifier.

### H3 — operational cost

Mods may introduce enough maintenance, ordering, plugin-supply-chain, false-positive, or runtime coupling cost that native Claude Code controls remain preferable.

Rejecting the Mod approach is a valid result.

## Cheapest useful verification after EXP-001

Do not build a generic Mod framework first.

Use this order:

1. identify a concrete observed Permission / Harness gap;
2. confirm that Prompt, Context, existing native policy, or current Runtime Adapter configuration cannot address it sufficiently;
3. create an isolated disposable fixture with harmless files and no production credentials;
4. define one explicit invariant, such as "Verifier cannot modify implementation files";
5. compare current/native enforcement with one minimal Mod-based candidate;
6. include negative cases that attempt the forbidden action against the disposable fixture;
7. measure boundary violations, false positives, operator interventions, evidence completeness, latency, and operational failures;
8. verify Mod load ordering and managed-security behavior when relevant;
9. classify missing or ambiguous observations as `UNKNOWN` / `INCONCLUSIVE`;
10. adopt only if the observed benefit justifies runtime coupling and operational cost.

## Rejection / deferral evidence

Reject or defer Mod adoption when:

- Claude Code native controls already enforce the required invariant;
- the problem is actually a Prompt or Context defect;
- a Mod only improves UI without improving enforcement or evidence;
- required guarantees depend on OS / container isolation rather than in-process interception;
- false positives or ordering complexity create more operator cost than the measured benefit;
- the proposal requires Claude Code-specific concepts in DAT core without cross-runtime evidence;
- available evidence is too sparse to distinguish benefit from configuration noise.

## What is retained during the freeze

During EXP-001, retain only these hypotheses:

- runtime event interception may strengthen an existing Permission Boundary;
- runtime audit events may improve Observed Execution evidence;
- same-process Mods are not independent security boundaries;
- native / smaller controls should be preferred when sufficient.

No Claude Code Mod is adopted into DAT runtime behavior during the active freeze.

Accordingly, `knowledge/sources.yaml` records the Anthropic announcement with `adopted: []`.

## Adoption gate

Revisit this note only after EXP-001 unfreeze conditions are satisfied.

The first post-freeze review should start from observed EXP-001 or later Claude Code runtime friction. If no relevant gap exists, close Issue #59 without implementation.
