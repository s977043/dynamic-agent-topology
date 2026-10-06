# EXP-001 T1 incomplete attempt — STOP report

## Classification

- runId: `EXP-001-train-normalize-name-r01-T1`
- observed Codex thread ID: `01a1132a-1de0-70d2-b810-c500b79430c9`
- status: **incomplete / not accepted**; not a complete empirical Run
- complete empirical count remains **1 / 18**
- model, effort, and start/end timestamps were not verified from this event record; no execution attestation is created

## Observed events

- The task began in the prepared T1 workspace. The Worker changed `app.py` from `.strip().upper()` to `.strip().lower()`; the observed change is preserved in `patch.diff`.
- `python -m unittest discover -s tests` failed twice with exit 127 because `python` was not found. No successful deterministic test result is recorded.
- The event stream ends with a collaboration tool call in progress. It does not establish a completed independent Verifier handoff or review.
- The canonical run directory still contains only `run-meta.yaml` and `prompt.md`; no result artifact is inferred or fabricated.

## Preservation and next gate

- Preparation metadata and prompt are copied byte-for-byte from the canonical prepared run.
- The sanitized event sequence is summarized in `event-summary.json`. The raw `worker-events.jsonl` is not included because it contains agent messages and tool prompts. Its SHA-256 is recorded for source identification. The Operator reports retaining the raw source separately; reviewers cannot independently recompute the event facts from this archive alone.
- Do not reuse this modified workspace or rerun/re-prepare this `runId`. Keep the paired matrix paused until Issue #15 records an explicit reviewed disposition consistent with the Feature Freeze and Operator rules.
- This record captures an aborted/incomplete attempt only. It does not change the experiment contract, freeze manifest, canonical fixtures, or empirical count.
