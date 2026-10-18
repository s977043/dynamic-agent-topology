# Ruflo meta-harness: authority boundary, routing and auditable decisions (research-only)

## Status / scope

- **2026-10-18 JST — external-source analysis only. No Ruflo, plugin, MCP server or SDK is installed in DAT.**
- Reference snapshot: [ruvnet/ruflo](https://github.com/ruvnet/ruflo/tree/b93144803bb171b12993b715fe7b2dd936b6edd5) (`main` at review time). Individual documentation and issues can evolve independently; re-check before running any experiment.
- DAT baseline: [EXP-001 decision](../../experiments/EXP-001-t0-vs-t1/DECISION.md), 18/18 accepted runs, 9/9 pairs, **Keep T0 for this pilot only**. EXP-001 freeze completed revision 3; its original evidence and semantics remain untouched.
- Ownership: [#59](https://github.com/s977043/dynamic-agent-topology/issues/59) for Claude Code permission/audit mechanisms; [#93](https://github.com/s977043/dynamic-agent-topology/issues/93) for additional orchestration/strategy cost. This note creates no new implementation owner or approval.
- This is **not** a recommendation to install Ruflo or enable Mods. Any third-party implementation, experimental runtime execution, policy changes, network access, or extra cost needs separately reviewed authorization.

## Question and smallest work unit

> With delegation, skills and memory already present, does an extra meta-harness measurably improve **enforced authorization and reviewable provenance** compared with Claude Code/Codex native controls?

- Engineering Layer: principally **Harness** (actual permission enforcement), **Loop** (routing/approval/retry), and **Evaluation** (evidence completeness and quality). Console UI is an observability surface, not a security boundary.
- Architecture: **Control Plane ↔ Runtime Mapping ↔ Observed Execution**. No new DAT plane, graph, canonical topology, role, model selector, or schema is implied.
- Smallest suspect unit: **one permission decision + the action it actually gated**, not an additional manager agent.
- Distinctions: Role ≠ Permission; Prompt routing ≠ authorization; policy file ≠ runtime enforcement; event/log ≠ independent attestation; a source claim ≠ DAT empirical evidence; a trigger ≠ operator permission.

## Source observations (what the upstream code/docs actually say)

1. **Execution trust.** The Ruflo README states that Mods run with the user's account privileges, without a sandbox. [Project README](https://github.com/ruvnet/ruflo/blob/b93144803bb171b12993b715fe7b2dd936b6edd5/README.md), [ruflo-mods README](https://github.com/ruvnet/ruflo/blob/b93144803bb171b12993b715fe7b2dd936b6edd5/plugins/ruflo-mods/README.md). This is about Mods, not proof that every Ruflo execution mode has identical controls.
2. **Routing.** In [route-task.ts](https://github.com/ruvnet/ruflo/blob/b93144803bb171b12993b715fe7b2dd936b6edd5/plugins/ruflo-mods/hooks/route/route-task.ts), the in-process router matches fixed keyword groups, chooses first match, and returns heuristic confidence 0.6 when matched, 0.3 otherwise (default coder). These are constants, **not calibrated task-success probabilities**. [route/index.ts](https://github.com/ruvnet/ruflo/blob/b93144803bb171b12993b715fe7b2dd936b6edd5/plugins/ruflo-mods/hooks/route/index.ts) injects routing/ranked-memory context via `prompt.submit`; a suggestion to the model is not a permission grant.
3. **Tool gating.** [guard/index.ts](https://github.com/ruvnet/ruflo/blob/b93144803bb171b12993b715fe7b2dd936b6edd5/plugins/ruflo-mods/hooks/guard/index.ts) merges the upstream `tool.check` verdict with a stricter verdict (never relaxes allow/ask/deny). Guard failure falls back to `ask` when necessary, *within this intercepted path*. [guard/policy.ts](https://github.com/ruvnet/ruflo/blob/b93144803bb171b12993b715fe7b2dd936b6edd5/plugins/ruflo-mods/hooks/guard/policy.ts) accepts `observe` and `enforce` projections; it inspects only explicit `claude-code.*` rules, not unmatched default-deny. This does not prove all host processes, tools, MCP transports or child agents are gated.
4. **Mod admission.** [trust.ts](https://github.com/ruvnet/ruflo/blob/b93144803bb171b12993b715fe7b2dd936b6edd5/plugins/ruflo-mods/hooks/trust.ts) classifies sensitive calls/hooks; `modTrust=observe` is the default, and `refuse-risky` requires an explicit provenance allow-list. It sees *subsequently admitted user-tier* modules, not earlier or builtin/managed modules. A registration scan and a provenance label are not OS isolation.
5. **Runtime claims and caveats.** The [Mods README](https://github.com/ruvnet/ruflo/blob/b93144803bb171b12993b715fe7b2dd936b6edd5/plugins/ruflo-mods/README.md) describes session-cost budget, optional agent-spawn hard stop and console visibility. These are different controls: an agent-spawn hard stop does not automatically block every other expensive tool call.
6. **Upstream defect history must be versioned.** Upstream [#3787](https://github.com/ruvnet/ruflo/issues/3787) and [#3801](https://github.com/ruvnet/ruflo/issues/3801) describe earlier trust-risk coverage gaps, marked **fixed** by maintainers in later Mods releases; do not claim they remain exploitable at current HEAD. [#4095](https://github.com/ruvnet/ruflo/issues/4095) records corrected `refuse-risky` documentation. Upstream [#3807](https://github.com/ruvnet/ruflo/issues/3807) remains **open at this review** and documents unresolved/review-needed behavior concerning child-process ownership propagation, moving worktree root, `@inline` provenance, malformed settings fallback, and cost-stop coverage. Issue statements are upstream reports, **not DAT reproductions**.

## Threat and authority model (candidate, not implemented)

| Boundary | Who can authorize? | Required evidence before claiming enforcement | Failure candidate |
| --- | --- | --- | --- |
| Operator → orchestrator | Human operator and actual host policy | Exact actor, action, resource, scope, policy revision, explicit authorization record | Prompt text mistaken for consent |
| Orchestrator → subagent | Host/runtime capability grant, within existing operator scope | Child process/agent identity and inherited effective capabilities, not role label alone | Delegation broadens authority |
| Mod/plugin → host tools | Native permissions plus verified interception, not plugin self-report | Positive **and** negative calls with observed pre-action verdicts and effect | Unmatched/alternate path bypasses guard |
| Router → model context | Context advice only; never grants authorization | Route decision + task, matched/default and measured outcomes | Fixed heuristic confidence treated as probability |
| Execution → audit log | Append/observe under actual access controls | Correlation of request, effective policy, verdict, execution outcome and artifact | Same-process code alters or omits its own log |
| Approval → merge/release | Independent review and human-owned boundary per DAT governance | GitHub-native approval, exact-head required CI, provenance; human-only gates stay human-only | Console's auto-confirm mistaken for release approval |

### Narrow experiment proposal (requires separate go/no-go)

**Precondition:** #59 provides a concrete, reproducible native-control gap. If not, **STOP / REJECT extra harness**. No live tests, dependency installs, privileged accounts, destructive actions or paid workloads are authorized by this note.

When that precondition is satisfied, draft a minimal **read-only/disposable** study:

- A = native Claude Code permission controls only (T0-style control); B = same controls plus Ruflo observation-only; C = same controls plus one explicitly configured enforcement check. D = a fuller meta-harness is **optional and separate**, only if B/C justify it; Codex runs are a separate runtime stratum, not assumed equivalent to Claude Code Mods.
- Hold constant: task/fixture, runtime version, model, effort, tool inventory, effective native policy, operator, timeout and resource limit; randomize paired treatment order; pin upstream revision. Never weaken baseline native controls for a treatment.
- **Safe positive case:** allow an explicitly permitted write to a disposable file; measure false blocks and work completion.
- **Safe negative case:** try an explicitly forbidden write against a harmless fixture; count whether the operation actually occurred, not merely whether a hook emitted `deny`.
- **Coverage cases:** unmatched `claude-code.*` rule, policy projection unreadable, approval required, a mod admitted before the trust gate, session/root switch and child-process inheritance (in an isolated fake or safe local sandbox), invalid `modTrust` value, agent-spawn budget vs non-spawn calls. Treat feature/version differences as stratification; never run real destructive payloads or untrusted plugin code.
- **Observability:** independently compare tool verdict, actual file diff, child identity, policy version, operator acknowledgment, ordered event IDs and omitted/redacted events; record missing or mutable evidence as `UNKNOWN`, not `PASS`.
- Metrics: policy violation rate, false allow, false block, provenance completeness, reviewer intervention, elapsed time, token/monetary cost where attributable, maintenance/configuration overhead, and **task success conditioned on no authorization violation**.

### Decision rule

Reject/default to native controls when they enforce the invariant and evidence is sufficient; when Ruflo only improves dashboards; when evidence provenance is self-attested; when permission coverage is incomplete; when operational overhead/false blocks dominate; or when the paired evaluation is missing. If a measurable incremental benefit survives controls and independent review, evaluate the **smallest capability** rather than adopting the whole meta-harness.

## Three-loop review record (scope of this change)

The three cycles are **same-session perspective checks, not independent reviewer approvals**:

1. **Architecture review:** avoid duplicate framework/role/schema and reuse #59/#93. Action: research-only note, no dependencies.
2. **Security/threat review:** treat same-account Mods, unmatched policies, admission order, cross-process propagation, approval and audit mutability as separate failure modes. Action: add negative and positive verification cases, explicit evidence states.
3. **Experiment/operations review:** require observed native gap, pinned versions, isolated fixtures, paired costs, negative tests, separate actor permissions and explicit stop conditions. Action: register external source with `adopted: []`; hold any runtime changes for a future independent review.

**Evidence boundary:** inspected external source and DAT design only. No actual permission bypass was attempted; no Ruflo or Claude Code execution was performed; therefore no effectiveness or security guarantee is claimed.

## Revisit / stop conditions

- Research-only documentation can be reviewed now; **no runtime implementation PR** without #59's gap/pre-registration, isolated test plan, permission owner, budget and independent reviewer.
- #59 owns the Claude Code guard question; #93 owns *whether extra orchestration improves outcome per unit cost*. Avoid duplicate tracking issues until a distinct measured failure exists.
- This note does not change the current EXP-001 decision or authorize merges, releases or bypass of repository governance.
