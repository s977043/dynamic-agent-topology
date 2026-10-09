# Fast Feedback workflow — DAT repository work and EXP-001 operations

> Status: proposed development-harness procedure. This document is **not** a new EXP-001 experiment condition, Runtime Adapter, Run acceptance rule, or permission grant.
>
> Source of truth: [Agent Development Harness](AGENT_HARNESS.md) for agent autonomy and approval boundaries; [EXP-001 Issue #15](https://github.com/s977043/dynamic-agent-topology/issues/15) for live progress; [Feature Freeze](../experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md) and [Operator procedure](../experiments/EXP-001-t0-vs-t1/pilot/OPERATOR.md) for empirical runs.

## Outcome and boundaries

**Outcome:** reduce the elapsed time from a discovered obstacle to the next *valid empirical observation*. Completing a preparation checklist is not a substitute for collecting a real Run.

**Strict:** credentials, access rights, frozen inputs, deterministic evidence, real-runtime attestation, one-time retry allowance, and the independent Run acceptance gate cannot be relaxed by advice from an agent.

**Fast:** reduce repeated manual inspection, oversized investigations, avoidable handoffs, and review queues. Reuse immutable evidence only when the existing gate permits it; re-check any runtime/security property that needs fresh observation.

DAT has two independent feedback loops:

| Loop | Can adapt now | Must not do |
| --- | --- | --- |
| **Repository development** | Small docs/guard/tool changes, local validation, review, learn, next improvement PR within the existing approval policy | Silently change a frozen file, grant itself authority, auto-merge a protected Harness change |
| **EXP-001 empirical** | Execute the already-authorized frozen matrix one Run at a time; validate captured artifacts promptly; report operational impediments outside the fresh Run context | Change prompt, topology, role, fixture, evaluation semantics, matrix, fixed model/effort, or use earlier Run feedback in later Run prompts |

Cross-run feedback prohibition remains absolute for EXP-001: improvements discovered in one empirical Run must not alter later frozen Run conditions. A repository development consultation is **not** a component of T0 or T1, does not run inside the empirical Codex session, and is never fed into its frozen prompt. The Operator follows the approved Run procedure without improvising a different environment.

## Smallest safe feedback loop

1. **Name the next observable outcome.** Example: “A T1 r01 retry can start only after all current mandatory preflight and reviewer conditions pass”; never “complete all possible preparatory hardening”.
2. **Classify the next obstacle.** Distinguish `SECURITY/BOUNDARY`, `INFRASTRUCTURE`, `EXPERIMENT-CONTRACT`, `TASK/IMPLEMENTATION`, and `UNKNOWN`. Record its first observable symptom and the smallest broken work unit.
3. **Choose one smallest useful check.** Run the existing, cheapest *applicable* deterministic check first. Prefer a non-model dry run when testing infrastructure; never claim it proves actual model execution, identity, or Run acceptance.
4. **Act only within current authority.** PASS + all other current mandatory conditions satisfied → proceed to the **already-authorized** next action. FAIL → repair the smallest cause and recheck. BLOCK / UNKNOWN / permission issue → STOP, preserve evidence, and request the existing authorized disposition. Retry permission never follows from failure by itself.
5. **Observe and decide.** Capture command, exit code, changed artifact identity, relevant timestamps, reviewer judgment (where required), and the next *single* action. Failed/aborted/inconclusive executions remain observable; do not relabel them as successful Runs.
6. **Inspect / adapt the development process.** Put friction and proposed improvements in a development Issue/PR or the Harness learning ledger. Do not adapt an EXP-001 frozen treatment mid-pilot.

For an empirical Run the required order is always: approved preflight and reviewer disposition → fresh workspace/session → fixed model invocation → evidence capture → single-run validation → independent Reviewer `ACCEPT` → next matrix slot. A documentation-only PASS is not authorization to launch a retry.

### Avoid preparation creep

- Before requesting another design investigation or review, identify the concrete **currently unsatisfied** required condition, evidence gap, or observed unsafe behavior.
- Do not turn hypothetical “what-if” concerns into mandatory new gates without an observed blocking risk and the existing authority's decision.
- If investigation repeatedly produces no new discriminating evidence, record the impediment and ask for a **bounded** next test or a STOP decision; do not silently continue exploratory work.
- Favor one scoped change and one focused review over a large bundle. Security failures still fail closed.
- When reverting a *repository development* change, revert its own PR/commit and re-run applicable CI. Never reset a frozen empirical Run or discard failed attempts as a “rollback”.

## Agile Coach and Scrum Master consultations

These are **read-only, advisory repository-development agents**, not empirical T0/T1 roles, reviewers, verifiers, or approval authorities. Their role definitions are local to DAT:

| Runtime | Agile Coach | Scrum Master |
| --- | --- | --- |
| Claude Code | `.claude/agents/agile-coach.md` | `.claude/agents/scrum-master.md` |
| Codex (project config) | `.codex/agents/agile-coach.toml` | `.codex/agents/scrum-master.toml` |

The agent runner can delegate a **consultation** to the named role when its runtime supports project subagents. The caller must supply only the repository Issue/PR links and sanitized, task-scoped observations. If no subagent mechanism is available, use the same questions in a regular read-only review; record that it was a role-based consultation, **not an independently executed agent review**.

**When to consult (not every Run):**

- **Agile Coach:** when the next learning goal is unclear, preparation is expanding, or two candidate experiments need to be reduced to one smallest useful check.
- **Scrum Master:** when a decision/review/ownership queue blocks progress, or the same impediment remains unresolved across checkpoints.
- For a simple PASS with a clear next authorized action, proceed without both consultations. Never make these roles an extra mandatory gate or ceremony.

**Single small input packet:**

```text
Goal / current authorized action:
Source links (Issue/PR/procedure):
Observed facts + time:
Current mandatory condition not met (or unknown):
Changeable development/operation scope:
Unchangeable freeze / security / approval boundaries:
Question for this one role:
```

**Expected outputs:**

- **Agile Coach:** `Outcome / Hypothesis / Smallest safe test / Feedback source / Success signal / Next decision`. Challenge whether the proposal generates an earlier *real* observation, rather than more preparation.
- **Scrum Master:** `Current impediment / Owner or decision authority / Waiting on / Smallest next action / Next check`. Make blockers visible without scheduling unnecessary meetings.

Record both perspectives separately with `advice` status. The implementer selects a proposal consistent with existing contracts. A distinct, authorized Reviewer/Human makes any final judgment that requires approval. Two coaching agents agreeing is **not** independent verification, not evidence of EXP-001 effectiveness, and not a merge/Run authorization.

## Lightweight measurements (repository process only)

Record in the development Issue/PR when observable, without changing `RunEvaluation` or frozen metric semantics:

| Signal | What to timestamp | Interpretation |
| --- | --- | --- |
| Time to first useful signal | Work starts → first deterministic relevant PASS/FAIL | Shorter is better only if the signal is valid |
| Blocked duration and cause | STOP/UNKNOWN first detected → approved disposition or fix | Locate permission, environment, waiting, review bottlenecks |
| Time to accepted empirical Run | Authorized work starts → actual Run `ACCEPT` | The outcome indicator; no fake progress from static preflight |
| Avoidable repeat checks | Checks re-run without relevant state change | Target for caching or automation only when permitted |

Do not optimize for speed alone. Compare alongside boundary violations, validity of captured evidence, and human attention cost. An improvement proposal is accepted only when the observable benefit justifies added operating cost; otherwise simplify or remove it.

## Initial EXP-001 application

Use [Issue #15](https://github.com/s977043/dynamic-agent-topology/issues/15) as the sole live Run tracker. Inspect the *latest* reviewed disposition and mandatory requirements immediately before acting; prior checkpoints can be stale.

1. Finish only the remaining required decision/checks for the currently authorized T1 r01 retry; no additional “perfect environment” gate based on speculation.
2. If a necessary safety property fails or cannot be established, STOP and isolate the cause. Do not start the model or consume another retry allowance.
3. Once authorized under the existing Runbook, collect the actual next Run and review its artifact consistency promptly.
4. Track the largest source of avoidable waiting and improve the **repository process** in a separate, small PR, without feeding interim data back into frozen future Run conditions.

Related development proposal: [Issue #123](https://github.com/s977043/dynamic-agent-topology/issues/123). This procedure creates no new powers and changes none of the EXP-001 freeze manifest objects.
