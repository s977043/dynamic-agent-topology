# Changelog

All notable user-facing changes to Dynamic Agent Topology (DAT) are documented here.

This project uses SemVer-style `MAJOR.MINOR.PATCH` version identifiers while the compatibility policy is still evolving. Repository `main` may contain unreleased work; a version is considered published only when an immutable Git tag and matching GitHub Release exist.

## Unreleased

### Added

- RunObservation `apiVersion: dat/v1alpha2` with the optional `rework.sources`: the count of `rework.count` per source (`spec-change`, `human-return`, `review-finding`, `ci-failure`, `self-correction`, `unknown`), as designed in `docs/RUN_OBSERVATION_DESIGN.md` §5.5 (#321, #322). `schemas/run-observation.schema.json` accepts both `dat/v1alpha1` and `dat/v1alpha2`, allows `rework.sources` only in `dat/v1alpha2`, and rejects `rework.sources` together with `rework.triggers`; `scripts/validate_run_observation.py` checks the sources against `rework.count` (§5.5.3, §5.5.4). `rework.triggers` is deprecated in `dat/v1alpha2`.
- `scripts/run_observation.py sum` prints a `rework by source` table per topology with the exclusions of §5.5.8, and accepts several `--store` options, checking `observationId` across all of them before counting. The existing tables are unchanged. Whether this output change is breaking under `docs/RELEASE_READINESS.md` is decided in the release PR (§5.5.9).

### Changed

- The plugin version in `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` is now `0.4.0` (Human decision V1 in #321). The adapter examples now use `dat/v1alpha2`.

### Migration

- A validator or `sum` before this change accepts only `dat/v1alpha1` and **rejects every `dat/v1alpha2` record**. An old `sum` on a store with new records prints `skipped invalid` for them, prints tables of the remaining records only, and exits 1.
- Update every reader of a store (each environment that runs `sum`, shared copies, scripts that read records) before any recorder writes `dat/v1alpha2`. Until then keep writing `apiVersion: dat/v1alpha1` without `rework.sources`, even with the new plugin. If an old reader must stay, save new records in a separate store and do not let the old reader read it; the new `sum` with both `--store` options stops on an `observationId` duplicated across the stores.
- Do not rewrite existing `dat/v1alpha1` records, and do not infer `rework.sources` from `rework.triggers` or from memory.
- Do not treat a `sum` table that came with exit code 1 (`skipped invalid`) as a full count; check the exit code in any process that reuses the tables.

## 0.6.0 — 2026-11-11

Content candidate: `876c05f129a5187a8aa9b04be8106d16e9f1f4b6`.

Previous boundary: tag `v0.5.0` (`2144faf2cb9843bb317f842195f865098199e758`).

### Breaking

- `scripts/compare_paired_blocks.py` now rejects an `--exclude BLOCK_ID=REASON` whose block ID appears in more than one scenario of the input, with a `ValueError` message (`excluded block IDs are ambiguous across scenarios`) and exit code 2; 0.5.0 accepted it (#289). Migration: when excluding a block ID that is reused across scenarios, pass input files for one scenario per run.
- `scripts/compare_paired_blocks.py` now computes `meanTotalTokensRatio` and `meanWallClockMsRatio` from complete pairs only (blocks where both conditions have the metric), reported in the new `pairedMetricSummary` field; in 0.5.0 they were the ratio of the descriptive `conditionMeans`, which could use different observed populations (#289). Migration: the same input can give a different ratio; do not compare 0.6.0 ratios directly with ratios produced by 0.5.0 when any paired block misses a metric, and re-run 0.5.0 comparisons with 0.6.0 when a ratio is reused. `conditionMeans` keeps its previous meaning.
- `scripts/hard_task_calibrate.py` now rejects an aborted run record (`status` `aborted-timeout` or another aborted status) unless `tokenUsageKnown` is `true` with an integer `totalTokens`, or `false` with no `totalTokens`. The check is in `read_record()`, so it also applies to the existing `run` resume and `summarize`; a 0.5.0 record with `status: aborted-timeout` and `totalTokens` but no `tokenUsageKnown` is now refused (#307, #309). The existing `run` now also collects the trace after a timeout, records whether token usage is known, and stops the batch when the usage after a timeout is unknown or when `docker stop` after a timeout fails (#307, #309, #310, #311). Migration: set `tokenUsageKnown: true` and `totalTokens` only for runs whose usage was confirmed from the trace; for unconfirmed usage set `tokenUsageKnown: false` and remove `totalTokens`, and do not fill in estimated values. A consistent record with unknown usage is read by `summarize` (and left out of the token totals), but resuming the batch still stops until its usage is recorded. A token count taken from the trace collected after a timeout is a lower bound: it excludes usage not recorded before the stop. Before resuming a stopped batch, confirm that the run's container has stopped.
- `scripts/review_package.py` now also fetches the PR from the REST API and stops with exit code 1 (`SystemExit` with a message) without writing the package when that fetch fails or the snapshot is inconsistent (PR number mismatch, missing or invalid head / base SHA, or a head SHA or base ref that differs from `gh pr view`); 0.5.0 had no such stop (#297). Migration: when it stops on an inconsistent snapshot, re-run after the PR head and base are stable; when the REST fetch fails, fix access and re-run. No package is produced in either case.

### Added

- `pairedMetricSummary` in the `scripts/compare_paired_blocks.py` output: per metric, the complete-pair count, missing blocks with their missing conditions, and the paired means (#289). `docs/METRICS.md` describes the populations, and `docs/HUMAN_ATTENTION_PILOT.md` and `docs/human-attention-pilot/` add a Human Attention measurement procedure and a one-pair packet (#289, #290).
- Hard-task screening mode in `scripts/hard_task_calibrate.py` (`screen-plan`, `screen`, `screen-summarize`) with the runbook update (#244; #307), task descriptions for orders 6 to 44 except the pre-excluded orders 10, 11, 16, 26, 28, 32, and 38 (#304), and a draft pre-screening exclusion addendum to the preregistration (#305).
- `scripts/subagent_folding_oracle.py`, a synthetic oracle, and `docs/SUBAGENT_FOLDING_DESIGN.md` with a minimum verification plan; spec-lint runs `scripts/test_subagent_folding_oracle.py` (#288).
- Runtime canary records under `docs/runtime-canary/`: one manually dispatched T0/T1 pair with independent grading (#293), repeated grading with Verifier execution evidence (#300), and live runtime conditions (#301). These are observations, not a T0/T1 comparison result.
- Codex Cloud verification results and Docker measurements in `adapters/codex/` (#291, #292).
- `docs/ADOPTION.md` connects task-level selection and role sharing to existing observations (#306).
- Research note on Auctopus PI-led evidence gates as a verification candidate, registered in `knowledge/sources.yaml`; it is not an adopted contract (#296, #298).

### Changed

- `scripts/hard_task_calibrate.py`: fixes from the screening rehearsal and reviews (stop and aggregation defects, review recommendations, `write_record` keeps the umask and resume checks are stronger) (#309, #310, #311, #315); the compatibility impact on existing records and `run` is listed under Breaking.
- `scripts/review_package.py` reads the PR base SHA from the REST API for gh 2.46 compatibility, and `pr-diff.patch` is now built from `{base SHA}...{head}` instead of `origin/{base}...{head}` (#297); the new stop is listed under Breaking. Tests cover bases other than `main` (#299, #303).
- `AGENTS.md` and `docs/AGENT_HARNESS.md` define the scope of "check scripts" for rule-change PRs (#313).
- `docs/RELEASE_READINESS.md` records `v0.5.0` in the current release line and the completed EXP-001 state (#284, #285); `docs/CURRENT_EXECUTION_PLAN.md` is synced (#308, #312).
- CI dependencies are bumped: `check-jsonschema` 0.39.0 and the GitHub Actions group (#282, #314). The relay test in `scripts/test_model_role_split_pilot.py` no longer lets server completion cancel reader pacing (#301). A regression test fixes the `write_record` temporary-file refusal and unchanged umask (#316).

### Experiment status

- No EXP-001 frozen input or evaluation semantic changed. Hard-task screening, Human Attention, Subagent folding, and runtime canary work are preparation and observations; no T0/T1 or topology comparison result is claimed in this release. The plugin version is unchanged.

## 0.5.0 — 2026-11-02

Content candidate: `5cf7ba04218e390f0f4faec0f05f5aceae0dfce2`.

Previous boundary: tag `v0.4.1` (`4475b3004ecd07ae5da313121543067119a59479`).

### Added

- `scripts/compare_paired_blocks.py` compares a baseline and a candidate condition per paired block `(experiment, scenario, blockId)`, reporting block deltas and ratios, condition-mean ratios, invalid blocks, and excluded blocks with reasons as JSON (null with a reason for missing values and zero denominators); `scripts/summarize_experiment.py` is unchanged. spec-lint now runs `scripts/test_compare_paired_blocks.py` and a smoke run on `examples/experiment-run/` (#278, #279).
- DAT vNext design material under `docs/rfc/`: the P0 Baseline, the redesign RFC, and the independent review runbook (#269), and `docs/rfc/DAT_VNEXT_P0_JOURNEYS.md`, which records offline runs of P0 Journeys A to D (#271) and the follow-up status of the observed gaps (#274, #280, #281). The vNext design is a proposal and is not adopted. The records are offline observations; they do not measure whether human effort decreases or whether vNext is better than the current design.

### Changed

- `skills/dat-observe/SKILL.md` now points to the design §5.4 rule for `verifierKind` when `verification` is not `yes`, and to the no-verification example; no rule or contract changed.
- `scripts/validate_run_observation.py` (and `run_observation.py save`) now adds a hint pointing to design §5.4 when a schema error comes with `verifierKind` written although `verification` is not `yes`; the existing error lines, exit codes, and checks are unchanged.
- `docs/QUICKSTART.md` now lists the validator warnings expected right after copying `examples/brownfield/.dat` and how to clear each; validator behavior is unchanged.
- `skills/dat-select/SKILL.md` now points to the routing policy branch conditions (`when`), and to the escalation policy, when a selection is put on hold; no rule changed.
- `docs/ARCHITECTURE.md` now describes the meaning of the four R0 routing inputs with non-binding examples, and the current behavior (first matching rule in the `dat-select` procedure, no fallback rule, rule (1) does not read `risk`), and `skills/dat-select/SKILL.md` links to it; R0, schemas, and validators are unchanged.
- The plugin version in `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` is now `0.3.1`, following the skill updates since `0.3.0` (`dat-observe` in #250 and #272, and `dat-select` in #273 and #277). The plugin version is managed separately from the DAT spec version in `CITATION.cff`.

### Experiment status

- No EXP-001 frozen input or evaluation semantic changed. No schema, specification rule, or existing validator / CLI exit code changed; the public contract changes are additive (a new CLI, a hint line appended to an already failing validator output, skill wording, and the plugin patch version).

## 0.4.1 — 2026-10-29

Content candidate: `dd785a17e0093314b1e59b98913105ba49363b04`.

Previous boundary: tag `v0.4.0` (`f43e83e7b4b2bfd1be021a2405fc0b63855b4ed6`).

### Changed

- Release publication can be delegated to an agent under HOTL conditions after a per-version human approval; `docs/RELEASE_READINESS.md` adds the Who publishes and Compatibility boundary sections, and an agent-published release requires a Scorecard run on the release commit itself (#265).
- spec-lint now runs `scripts/test_hard_task_calibrate.py`; where `/usr/bin/sandbox-exec` is unavailable (Linux), the grade and AC sandbox probe checks are skipped after confirming the probe stops (#266).

### Experiment status

- No EXP-001 frozen input or evaluation semantic changed. No public contract (schemas, validator / CLI behavior, specification, skills, plugin packaging) changed.

## 0.4.0 — 2026-10-28

Content candidate: `9bf2c5a3e18756e8b35b06c6fe700d64ebe06b46`.

Previous boundary: tag `v0.3.0` (`0dd236ee1bc5e69b5620af151e93537e32a987dc`).

### Added

- RunObservation: `schemas/run-observation.schema.json`, `scripts/validate_run_observation.py`, valid / invalid fixtures, and Claude Code / Codex adapter recording guides (#226, #227). None of these existed in 0.3.0.
- RunObservation save / summarize CLI `scripts/run_observation.py` (#229). `save` refuses an `observationId` already stored anywhere in the store (by file name or by `metadata.observationId`) and refuses, without writing, while any YAML file in the store cannot be read or parsed; `sum` exits 1 without tables when counted records share an `observationId` and reports invalid records as `skipped invalid` (#229, #232, #234, #250). `save` also refuses a destination inside a nested Git working tree (#234).
- The Claude Code / Codex adapter recording guides put the recording time in `endedAt` when no other reliable end time exists (#240).
- The validator and CLI share one YAML loading rule: records with duplicate mapping keys or YAML merge keys (`<<:`) are rejected, and unreadable records report `cannot read: ...` with exit 1 (#235; `docs/RUN_OBSERVATION_DESIGN.md` §6).
- `topologyBasis.independentReview: 'yes'` is accepted only when a `role: advisory` review has `reviewerKind` `separate-session`, `separate-model`, or `human`; same-session advisory reviews alone do not count (#226, #250).
- Optional RunObservation fields `interruptionKind`, `rework.triggers`, `taskDifficulty`, and `usage`, plus aggregation rules in `docs/OBSERVATION_MEASUREMENT.md` (#250).
- RunObservation H1 / H2 judgment records and open questions U4 (verifier coverage when several artifacts are merged) and U5 (grounding `specialistRole: yes` outside `topologyBasis`) in `docs/RUN_OBSERVATION_DESIGN.md` §10 (#238, #260). U4 / U5 are undecided review candidates, not rule changes.
- DAT plugin packaging (`.claude-plugin/`, `.codex-plugin/`) with the `dat-select` and `dat-observe` skills and `scripts/validate_plugin.py` (#230). The plugin manifest `version` is managed separately from the DAT specification version (`skills/dat-observe/SKILL.md`).
- Hard-task T0/T1 comparison: evaluation design, preregistration (final second edition), candidate table, calibration runbook and kit (`scripts/hard_task_calibrate.py`, `scripts/hard_task_power_sim.py`), and task descriptions for the first five candidates (#237, #241, #243, #245, #251, #253, #255, #258).
- Model role split comparison: evaluation design, preregistration, candidate table, runbook, 18-task fixtures (`fixtures/model-role-split/`), and a two-run pilot kit (`scripts/model_role_split_pilot.py`) with proxy, relay, and teardown handling; Run containers have no network, and teardown stops on leftovers (#236, #246, #247, #249, #252, #254, #257, #261, #263).
- spec-lint now runs RunObservation fixture / validator / CLI tests, plugin validation, and the model role split pilot kit tests (#226, #229, #230, #262).
- Evaluation design notes for post-EXP-001 evaluation and elapsed-time signals, and further deferred research notes; these remain candidates, not adopted contracts (#194, #200, #202, #204, #205, #206, #207, #208, #211, #214, #219).

### Changed

- Agent operation rules move toward HOTL and widen the scope of agent merges (#242).
- GitHub Actions dependencies are bumped (#256).

### Experiment status

- No EXP-001 frozen input or evaluation semantic changed. Hard-task and model role split work is preregistration and preparation; no comparison result is claimed in this release.

## 0.3.0 — 2026-10-21

Content candidate: `d66cbdfea8fde66db0c77d01079757005893a8f8`.

Release commit: `0dd236ee1bc5e69b5620af151e93537e32a987dc` (tag `v0.3.0`). The tagged `CITATION.cff` and this heading say 2026-10-20; the GitHub Release was actually published on 2026-10-21, and the tag is not moved.

Previous boundary: historical content point `717a03fa389fb77a47694b9cf8a0c6e97ac0888b` (`0.2.1`, unpublished).

### Experiment status

- EXP-001 (T0 vs T1 pilot) completed 18 / 18 runs with recorded Run Artifacts; `DECISION.md` records **Keep T0**. This is a pilot-scope experiment conclusion, not a change to project adoption status and not evidence that T1, a Verifier, or any other Topology/Capability is effective or ineffective in general.

### Added

- Current Cloud execution plan with per-issue prerequisites and human-owned boundaries, refreshed reviewer-material failure observations, and explicit executor checks in review requests.

- Optional Cloud knowledge-integrity probe, preregistered PDF/pipeline/context cases, and independently reviewed synthetic-corpus observations; actual extraction, injected corruption, and operational holds remain distinct, with general efficacy unproven.

- Independent, read-only provenance audit with PASS / FAIL / UNKNOWN reports and negative tests; historical Run acceptance remains unchanged. Operational evaluation records fixture coverage, local execution cost, and unmeasured manual-review limits.

- EXP-001 pilot execution, artifact-capture, freeze, and operator guidance.
- EXP-001 18-run aggregation, `DECISION.md`, completed-snapshot audit, and documented one-time retry / recovery procedures.
- Pilot preparation and execution-attestation schemas and tooling.
- Deferred research notes for Raven / evidence-gated executable-configuration evolution, Claude Code Mods runtime guardrails, evidence-backed compiled-knowledge integrity, adversarial judgment gates, evidence-driven model escalation with compact handoff, HydraFusion adaptive execution strategy, agent population ecological safety, an eight-repository agent tooling survey, workflow revalidation after model switches, Claude Code Advisor / read-only Haiku Researcher comparison, production-agent capability mapping to DAT experiments, Grok Bot team operations, hunk-level commit organization, and recoverable coding-loop OSS references. These remain deferred candidates, not adopted contracts.
- Knowledge Base navigation that separates source claims, deferred research candidates, and adopted design principles, plus an indexed Research Note intake/tracking surface.
- Dogfooding and EXP-001 execution/measurement guidance.
- Public contribution, support, research-proposal, and security-reporting paths.
- CodeQL, Dependabot, and OpenSSF Scorecard supply-chain checks.
- Scheduled read-only repository-settings drift audit with GitHub Actions summary/artifact evidence.
- Schema-validated repository-settings target contract for earlier configuration-error detection.
- Git-tracked public repository policy and release discipline.
- Engineering Layer Diagnostics for Prompt / Context / Harness / Loop / Graph / Evaluation failure localization.
- Documentation navigation and document-role guidance under `docs/README.md`.
- Non-normative provenance-audit design proposal (`docs/PROVENANCE_AUDIT_DESIGN.md`, not adopted) with synthetic negative fixtures under `fixtures/provenance-audit/` that reproduce cross-artifact inconsistencies; no validator, schema, or EXP-001 evaluation-semantic change.
- Development harness: agent guidance validation, a schema-validated Learning ledger (`schemas/learning-ledger.schema.json`), read-only harness metrics, scheduled Observe/Promote draft-PR workflows, and independent-review package tooling.
- Optional A0 Workflow Brief adoption guide, Fast Feedback workflow, practice-evolution policy, and environment / knowledge-ownership guidance.
- Deferred research note on Uber Software Factory outcome-unit cost and quality evaluation; the source is registered but not adopted.
- Maintenance cost review recording the Observe workflow's safe stop after a rejected draft PR, with a regression test.

### Changed

- EXP-001 preparation provenance is separated from runtime execution attestation.
- Security reporting and coordinated-disclosure expectations are explicit.
- GitHub Actions use least-privilege permissions and immutable action SHAs.
- Release preparation distinguishes an unpublished version proposal from a published tag/Release; the draft publication date is provisional and must match the actual Human-approved publication date.
- Execution planning and Learning ledger record completed Freeze/EXP-001 status and release-candidate drift; unsupported failure attribution remains unknown.
- Brownfield adoption now documents an evidence-based complexity-promotion rule instead of treating additional agents, loops, or graph structure as default progress.
- Human-facing supervision is clarified as a coordination cost: experiments should control or disclose materially different human-facing concurrency, while `human_interventions` remains a count rather than a cognitive-load metric.
- Agent operation follows a Human-on-the-loop (HOTL) autonomy boundary documented in `docs/AGENT_HARNESS.md`.
- The repository-settings target key `requiredApprovingReviewCount` is deprecated (still accepted) in favor of `requiredApprovingReviewCountExact`.
- Documentation terminology, source-of-truth boundaries, evidence claims, experiment semantics, and release-boundary wording were reviewed and hardened.

### Security

- Added CodeQL scanning and OpenSSF Scorecard reporting.
- Hardened workflow credentials and dependency pinning.
- Updated pinned CodeQL (4.39.0) and OpenSSF Scorecard (2.5.0) actions.
- Clarified that prompts and role names are not permission-enforcement boundaries.

## 0.2.1 — historical content point (unpublished)

Metadata date: `2026-10-04`.

Historical content point: `717a03fa389fb77a47694b9cf8a0c6e97ac0888b`.

### Added

- Manual brownfield adoption kit.
- Complete `.dat/` reference layout.
- Runtime Binding and DAT Lock contracts.
- External project validator.
- GitHub Actions integration example.
- Quick Start and manual-adapter guidance for supported runtimes.

### Changed

- Project adoption status moved to **Manual adoption-ready**.
- README and citation metadata moved to version `0.2.1`.

> Note: no immutable `v0.2.1` Git tag or GitHub Release had been published when this changelog was introduced. If the historical release is published later, the tag must point to the historical content point above rather than current `main`.

## Release integrity

Do not move a published version tag. If a released version needs additional fixes, publish a new patch or minor version.

See [Public repository policy](docs/PUBLIC_REPOSITORY_POLICY.md) and [Contributing](CONTRIBUTING.md) for the release process.
