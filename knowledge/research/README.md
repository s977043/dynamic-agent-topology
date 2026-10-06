# Research Notes

`knowledge/research/` contains **non-normative research notes** used to preserve source claims, DAT interpretations, hypotheses, and deferred evaluation candidates.

A research note is not an adopted DAT contract merely because it exists in this directory.

Current adoption state is recorded in [`../sources.yaml`](../sources.yaml). If a source has `adopted: []`, it is tracked or reviewed but has not been adopted into current DAT contracts.

## Current notes

| Note | Primary source(s) | Tracking issue |
|---|---|---|
| [Raven executable-configuration evolution](raven-executable-configuration-evolution.md) | Raven / HarnessBank | [#21](https://github.com/s977043/dynamic-agent-topology/issues/21) |
| [Claude Code Mods runtime guardrails](claude-code-mods-runtime-guardrails.md) | Anthropic Claude Code Mods | [#59](https://github.com/s977043/dynamic-agent-topology/issues/59) |
| [Evidence-backed compiled knowledge integrity](evidence-backed-compiled-knowledge-integrity.md) | Joon An LLM Wiki operating report | [#63](https://github.com/s977043/dynamic-agent-topology/issues/63) |

Tracking Issues are the live status source of truth; this index intentionally does not duplicate blocked/open/progress state. The live EXP-001 state is tracked in [Issue #15](https://github.com/s977043/dynamic-agent-topology/issues/15).

## Expected structure

Research notes should separate, where applicable:

1. status and freeze boundary;
2. primary source / provenance;
3. source claims;
4. DAT interpretation;
5. falsifiable hypothesis or candidate invariant;
6. cheapest useful verification;
7. rejection / deferral evidence;
8. adoption gate.

The exact headings may vary when the source or question requires it. Do not force a template when it would obscure the actual evidence.

## Intake path

For a new research-derived proposal, prefer the repository's [Research or design proposal Issue Form](../../.github/ISSUE_TEMPLATE/research_proposal.yml).

That form requires:

- a concrete problem or observed friction;
- affected Engineering Layer / Work Unit;
- primary source material;
- source claim separated from DAT interpretation;
- a falsifiable hypothesis;
- the cheapest useful verification;
- rejection or deferral evidence;
- an explicit freeze check.

## Evidence boundary

Keep these distinctions explicit:

```text
Source Claim != DAT benchmark result
Research candidate != adopted contract
Generated summary != source evidence
Observed success != semantic correctness
Candidate implementation != evidence of improvement
```

When a candidate is later adopted, update the relevant canonical artifact(s), documentation, applicable validation, and `../sources.yaml` together so the adoption state remains auditable.

During the active EXP-001 Feature Freeze, research notes may preserve hypotheses and post-freeze evaluation candidates, but they must not silently change frozen experiment semantics or runtime behavior.
