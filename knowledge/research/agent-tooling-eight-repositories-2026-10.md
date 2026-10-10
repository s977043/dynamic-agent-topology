# Agent tooling reference patterns: eight repositories (2026-10-10)

## Status and scope

**Non-normative research / not adopted / EXP-001 post-freeze candidates only.**

- This note captures design patterns, caveats, and falsifiable questions from eight public repositories; it does **not** import code, SDKs, tools, agents, plugins, prompts, or their configuration files.
- Source behavior is based on the repository documents and selected implementation examples inspected on 2026-10-10. This is a static review, not a full code audit or execution benchmark.
- No DAT schema, canonical role/topology, runtime binding, routing policy, experiment, fixture, validator, or evaluation semantics change is authorized by this note.
- The EXP-001 feature freeze remains ACTIVE. EXP-001 measured evidence and decisions remain exclusively governed by [Issue #15](https://github.com/s977043/dynamic-agent-topology/issues/15) and the [freeze policy](../../experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md).
- Related post-freeze investigations already exist in [#88](https://github.com/s977043/dynamic-agent-topology/issues/88) (model escalation and compact handoff) and [#93](https://github.com/s977043/dynamic-agent-topology/issues/93) (compound execution). Avoid duplicating their scopes.

## Primary-source observations vs DAT interpretation

Each **Source observation** below describes an inspected repository's own published behavior or documentation; each **DAT interpretation** is an inference, **not** measured effectiveness in DAT.

### 1. Anthropic Claude Agent SDK for Python

- Source: [README](https://github.com/anthropics/claude-agent-sdk-python/blob/main/README.md), [type definitions](https://github.com/anthropics/claude-agent-sdk-python/blob/main/src/claude_agent_sdk/types.py), [hook examples](https://github.com/anthropics/claude-agent-sdk-python/blob/main/examples/hooks.py).
- **Source observation:** `query()` handles streamed responses; `ClaudeSDKClient` supports interactive sessions, custom tools, and hooks. `AgentDefinition` can specify model, effort, tools, and permission mode. `allowed_tools` grants automatic approval; it is not by itself a hard denylist. The SDK distinguishes tool calls and errors.
- **DAT interpretation:** runtime-specific permission mechanics belong in an adapter, not the canonical Role contract. A declared allowlist must never be treated as proof of an enforced boundary; observe effective behavior and violations.
- **Limitation:** hooks and SDK types are implementation details and version-dependent; string-pattern command filters alone cannot establish a security boundary. Do not add this SDK to DAT.

### 2. wshobson/agents

- Source: [architecture](https://github.com/wshobson/agents/blob/main/ARCHITECTURE.md), [cross-harness capability matrix](https://github.com/wshobson/agents/blob/main/docs/harnesses.md), [PluginEval](https://github.com/wshobson/agents/blob/main/docs/plugin-eval.md).
- **Source observation:** canonical Agent/Skill/Command definitions are translated through adapters for several harnesses; generated artifacts undergo structural validation and drift checks. PluginEval separates deterministic static lint from experimental LLM-judge and Monte Carlo scores, which its documentation says are not validated against human labels.
- **DAT interpretation:** compare desired capability declarations with the actual runtime mapping and execution. A generated valid configuration, or an LLM-generated quality badge, is not demonstrated task success.
- **Limitation:** mappings can be lossy, tools and model aliases differ across harnesses, and static validation cannot prove tool permission enforcement.

### 3. Anthropic Claude Code

- Source: [repository README](https://github.com/anthropics/claude-code/blob/main/README.md), [official documentation](https://code.claude.com/docs/en/overview), [license](https://github.com/anthropics/claude-code/blob/main/LICENSE.md).
- **Source observation:** Claude Code is an agentic coding runtime with terminal, IDE, and GitHub workflows; its public repository includes docs, examples, plugins, and issue tracking. The repository license reserves Anthropic rights and references commercial terms; the public repository is not evidence that the entire runtime is reusable OSS.
- **DAT interpretation:** treat Claude Code as one observed Runtime, not as a DAT framework dependency. Capability assertions are version- and configuration-specific.
- **Limitation:** neither README nor plugin manifests establish the runtime's actual execution trace or permission enforcement for a given run.

### 4. obra/superpowers

- Source: [subagent-driven development](https://github.com/obra/superpowers/blob/main/skills/subagent-driven-development/SKILL.md), [verification before completion](https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md), [TDD](https://github.com/obra/superpowers/blob/main/skills/test-driven-development/SKILL.md), [branch finishing](https://github.com/obra/superpowers/blob/main/skills/finishing-a-development-branch/SKILL.md).
- **Source observation:** task-isolated implementers receive scoped context, followed by specification/code-quality reviews and final branch review. A fresh command result is required before claiming success. The workflow includes bounded fix/review loops and preserves an explicit human integration decision.
- **DAT interpretation:** independent review and context isolation are candidate treatments, not universal quality improvements. Review latency, repeated context loading, and human handoffs count as costs. Preserve DAT human authority rather than copying autonomous decision instructions.
- **Limitation:** strict process/TDD for every task may over-constrain rapid experiments; extra reviews can be net-negative for simple workloads.

### 5. anthropics/skills

- Source: [README](https://github.com/anthropics/skills/blob/main/README.md), [skill template](https://github.com/anthropics/skills/blob/main/template/SKILL.md), [webapp-testing example](https://github.com/anthropics/skills/blob/main/skills/webapp-testing/SKILL.md).
- **Source observation:** skills package `SKILL.md` metadata, instructions, and optional scripts/references; contents are loaded as needed. License terms vary by subdirectory: some skills are Apache-2.0, while document-creation skills are source-available under separate terms.
- **DAT interpretation:** keep Role, Skill, and permission separate. `skill discovered` or `skill invoked` is activation evidence, not contribution evidence; test a skill-on/off ablation under controlled conditions.
- **Limitation:** skill triggers and content can influence context costs and behavior; do not copy external skill text or scripts into DAT.

### 6. modelcontextprotocol/servers

- Source: [README](https://github.com/modelcontextprotocol/servers/blob/main/README.md), [filesystem reference server](https://github.com/modelcontextprotocol/servers/blob/main/src/filesystem/README.md).
- **Source observation:** the repository explicitly calls these educational reference implementations rather than production-ready solutions. The filesystem example restricts accessible directories by startup arguments or dynamic MCP Roots, and advertises tool hints such as read-only, idempotent, and destructive.
- **DAT interpretation:** tool descriptions, Roots, annotations, prompt-level instructions, and runtime-enforced authorization are different things. Permission claims require negative tests of disallowed operations and authoritative runtime evidence.
- **Limitation:** tool annotations are advisory metadata, not an authorization mechanism; no server is installed.

### 7. anthropics/claude-code-action

- Source: [README](https://github.com/anthropics/claude-code-action/blob/main/README.md), [security guide](https://github.com/anthropics/claude-code-action/blob/main/docs/security.md), [capabilities/limitations](https://github.com/anthropics/claude-code-action/blob/main/docs/capabilities-and-limitations.md).
- **Source observation:** the action automates issue/PR work, but its security guide warns about untrusted PR checkouts, privileged workflow triggers, externally controlled bot prompts, and secret exposure. Published limits distinguish PR assistance from formal approval/merge.
- **DAT interpretation:** a trigger is not permission; a successful CI check is not human approval or independently verified correctness. Keep external content, tool permission, review, and merge authority separate.
- **Limitation:** treating workflows or comments as trusted instructions creates prompt-injection and privilege-escalation risk. Do not add the Action as a DAT dependency.

### 8. langfuse/langfuse

- Source: [README](https://github.com/langfuse/langfuse/blob/main/README.md), [review policy](https://github.com/langfuse/langfuse/blob/main/REVIEW.md), [license](https://github.com/langfuse/langfuse/blob/main/LICENSE).
- **Source observation:** Langfuse manages traces, prompt versions, datasets, and evaluation results. Its repository's main license is MIT for files outside enumerated enterprise directories, which have separate licensing. The review policy demands evidence for correctness, security, and performance findings and discourages unsupported assumptions.
- **DAT interpretation:** preserve raw ExecutionTrace independently of RunEvaluation and use consistent dataset/evaluator definitions for comparisons. Trace volume and an LLM judge score alone do not prove semantic correctness.
- **Limitation:** sampling, incomplete telemetry, sensitive data, scorer drift, and storage/operation cost need accounting; incomplete required evidence cannot be silently replaced with zero.

## Cross-source conclusions (research only)

| Question | Existing DAT contract or interpretation | Decision now |
|---|---|---|
| Does declaration equal enforcement? | Role != Permission; Declared Topology != Observed Execution | Keep the existing boundary; investigate only evidenced mapping gaps |
| Does skill activation improve results? | Capability-level ablation; Usage != Effectiveness | Retain a post-freeze candidate; do not change EXP-001 |
| Is a larger team or stronger model always better? | T0 baseline and cost-aware topology selection | No presumption; test marginal outcome and cost |
| Does a green CI / self-report establish correctness? | Evidence != Judgment; Attestation != Verification | Require fresh matching evidence and independent decision |
| Are traces sufficient for outcome evaluation? | ExecutionTrace != RunEvaluation | Keep completeness, missingness, independence, and provenance visible |
| Should model strategy be a topology? | Topology != Routing Policy; Role != Model | Existing #88/#93 own any post-freeze proposal; no new enum |

## Falsifiable post-freeze hypotheses and cheapest useful checks

1. **Runtime permission fidelity:** for a supported runtime, a declared read-only role is enforced under adversarial write attempts. Compare a positive allowed operation with a negative prohibited operation; observe tool response and filesystem effect. A prompt refusal alone is insufficient. First check existing adapter evidence before proposing any schema.
2. **Verifier marginal value:** independent verification improves task outcomes enough to justify its token, time, and coordination costs. EXP-001 is the existing T0-vs-T1 test; do **not** alter its controls or acceptance mid-run. Do not infer effectiveness before 18/18, reproducible summaries, and reviewed decision.
3. **Skill/role marginal value:** an optional skill or review step yields a practically meaningful improvement versus the same task without it. Predeclare outcome, regression boundaries, budget, and `INCONCLUSIVE`; keep Runtime, Model, Effort, task, evidence commands, and workspace policy matched. Record actual activation and handoff overhead.
4. **Model-routing economics:** an adaptive selector improves cost per verified completion over a fixed-model alternative without unacceptable regressions. First distinguish selector-quality evidence from treatment effect, and account for selection, context rebuild, escalation, retry, and verification costs. This is already within the research scope of #88/#93.

Expected confounders: unequal model/effort settings, cross-run contamination, prompt drift, changed tests, uncontrolled model versions, unavailable runtime capabilities, and missing or selectively sampled trace events. Prefer low-cost shadow observation or a small paired trial before architectural work. Stop or classify `INCONCLUSIVE` rather than retrofit a favorable conclusion.

## Adoption gate and explicit non-adoptions

- **Current status:** all eight sources are reference-only with `adopted: []` in `knowledge/sources.yaml`. Referencing a source never updates a DAT normative contract.
- **Do not:** clone/vendor upstream code, install packages/MCP servers/plugins, port their prompts/configuration, introduce a new orchestration runtime, expand canonical topologies, modify EXP-001 controls, or create a general-purpose observability platform.
- **Post-freeze only:** if measured DAT evidence identifies a specific unmet requirement, record hypothesis and baseline, test the smallest change, review security and licensing, compare measured outcomes including costs, and then update canonical artifacts, validation, and source ledger together.
- **Rejection criteria:** same-quality smaller intervention, no verified improvement, unsafe effective permissions, unmeasurable confounds, excessive coordination cost, or incompatibility with DAT provider neutrality.

## Review record

- Perspective 1 (design): separate Source Claim, DAT interpretation, and future hypothesis. Existing abstraction boundaries suffice; no canonical change.
- Perspective 2 (experiment): avoid causal claims from documentation or model-judge scores. Protect EXP-001 controls and future paired-comparison independence.
- Perspective 3 (security/OSS): no code copied; licenses are heterogeneous; authority must be runtime-enforced, not merely declared.
- Perspective 4 (delivery): retain the feature freeze and prioritize acquiring EXP-001 empirical evidence over new abstractions.

See [Research Notes index](README.md) and [experiment protocol](../../docs/EXPERIMENTS.md).
