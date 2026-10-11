# Hunk-scoped commit organization as a bounded harness experiment

## Status / freeze boundary

**Research-only / NOT ADOPTED** — 2026-10-12. Tracking: [#150](https://github.com/s977043/dynamic-agent-topology/issues/150).

EXP-001 Feature Freeze remains intact. This note does **not** revise any frozen experiment files, topology, role, routing policy, adapter, evaluation semantic, or AGENT_HARNESS authority. It installs no external code, CLI, Skill, plugin, or SDK. Decisions and runtime permission are not implied by this note.

## Sources and claims (not experimental evidence)

- Primary source: [raine/git-surgeon](https://github.com/raine/git-surgeon), README consulted 2026-10-12. It documents hunk IDs and non-interactive `hunks`, `show`, `stage`, `commit` operations; the same CLI also exposes destructive/rewrite operations.
- Discovery article: [kawarimidoll.com/posts/202610051](https://kawarimidoll.com/posts/202610051/), published 2026-10-05.
- The documented behavior is an upstream **capability claim**, not DAT-measured security, reliability, efficiency, or provenance. Versions, actual implementation, platform compatibility, tool invocation, and failure modes remain unverified locally.

## DAT interpretation

Git hunk selection is primarily a **Development Harness work-unit / change-ownership** concern, not a new Topology or agent Role.

```text
workspace ownership != visibility of git diff
hunk selection != verified intended change
commit produced != acceptance / independent review
tool availability != runtime permission
source claim != observed DAT improvement
```

Commit Organizer may be an internal task of the existing Worker. Adding a new agent, external dependency, or prompt-wide mandate is not justified without comparative evidence. When a worker is delegated under `no-commit`, it cannot gain commit permission through hunk tools.

## Post-freeze falsifiable hypothesis

H1: On changes where two intended units overlap within the same file, non-interactive hunk selection improves independently judged **per-commit semantic accuracy** versus standard path-scoped Git operations at tolerable incremental latency/complexity.

H0 / rejection conditions: the added mechanism has no meaningful benefit on typical workloads; worsens task success, recovery cost, leakage to another worker's changes, or human oversight; or violates a repository gate.

H2: For simple changes that map cleanly to file paths, the extra mechanism has **no net benefit** over a path-scoped baseline. Include these cases rather than only favorable mixed-hunk examples.

## Cheapest useful verification (post-freeze)

**Stage 0 — safety fixture, no runtime adoption.** Using only nonsecret disposable repositories/worktrees, create (a) one logical change in one file, (b) two changes in distinct files, (c) two intended changes in one hunk/file, (d) a conflicting/unowned change from another worker, and (e) intentionally stale hunk identifiers. Record initial worktree/index/tree hashes and expected per-commit diff.

**Stage 1 — paired comparison.** Keep fixture, initial state, accept criteria, and independent verifier constant. Compare:

| Arm | Mechanism | Purpose |
| --- | --- | --- |
| T0 | Standard Git: explicit path staging and reviewed patches if essential | Deterministic/minimal baseline |
| T1 | Non-interactive hunk selection, initially mocked or isolated; optional upstream CLI only after separate approval | Incremental hunk precision |

Randomize or counterbalance order and reset to equivalent fresh snapshots between arms. Include failures and aborted runs in the denominator.

Measure per-commit expected-to-actual hunk match, unowned changes committed, missing intended changes, residual worktree delta, branch/head integrity, test results, operator interventions, tool calls, time-to-verified-commit, and recoverability. Compare total costs as well as successful attempts, with paired cases and a prespecified minimum useful effect. Record `INCONCLUSIVE` if the case count or verifier is insufficient.

**Stage 2 — gated adoption only if evidence warrants.** The smallest useful operational change may be better scoping and verification with standard Git, not a new dependency or specialized role.

## Safety exclusions / decision ownership

- Never treat `discard`, `commit-to`, `split`, `fold`, `amend`, `squash`, `reword`, `move`, resets, or branch-history rewrites as authorized by this study.
- Avoid shared worktrees and secret-bearing fixtures; don't assume that an existing staged index belongs to the current worker.
- Treat stale hunk IDs, mismatched diff, unexpected untracked files, branch drift, unresolved merge/rebase state, or leaked unowned edits as stop conditions.
- No changes to EXP-001 cases until explicit post-freeze review; no self-issued independent review, fake attestation, or bypass of human-only merge gates.
- If adoption is ever proposed, update applicable DAT canonical artifacts and `knowledge/sources.yaml` through the proper review path, distinguishing observation from claimed effect.

## Status of evidence

Upstream README inspected; DAT runtime, security gates, hunk accuracy, benefits and cost **not measured**. Next action is the bounded experiment proposal in [#150](https://github.com/s977043/dynamic-agent-topology/issues/150), not installation.
