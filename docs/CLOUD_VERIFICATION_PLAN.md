# Cloud knowledge-integrity probe — preregistration

Issue [#63](https://github.com/s977043/dynamic-agent-topology/issues/63) candidate verification only. This plan is written before measurements. Independent review must authorize execution. No model runs, downloads, package installation, frozen-file edits, canonical validators, new Artifact kinds, schemas, or default CI changes. Python 3.12 standalone optional-dependency experiment: `scripts/probes/knowledge_integrity_probe.py`.

## Question and fixed comparison

Can a bounded, known-source recheck distinguish deliberately corrupted derived context from correct context when process success and links cannot? This is a conditional case oracle, not a production admission guarantee or an estimate of real-world error prevalence. H1/H2/H3 adoption remains INCONCLUSIVE outside this corpus.

Three separately reported checks: process baseline (extractor exit zero); link-only baseline (process success plus source/synthesis links); candidate (source hash and extractor provenance present, all declared critical facts match, no declared contradiction/foreign-source marker, source revision current, synthesis connection present). Factual integrity and connectivity are separate columns. Missing/ambiguous extraction, dependency failure, unknown revision, or absent evidence yields UNKNOWN, never invented values. Explicit contradictions yield FAIL. Case IDs and expected labels are reporting metadata only; gate functions receive evidence and source requirements, never case IDs or expected outcomes.

## Preregistered sources and oracles

Generate deterministic ReportLab PDFs (`invariant=1`), record SHA-256, chmod read-only, and compare hashes before/after extraction. Required critical facts are literal complete strings (whitespace normalization allowed; no semantic reconstruction):

| Source | Critical facts / exclusions | Presentation |
|---|---|---|
| signed | `Net change: -12 units`; `Required section: safety margin 7 units`; explicit contradiction `Net change: 12 units` is excluded | one text page |
| image | `Treatment A: -12`; `Treatment B: 7` | image-only table embedded in PDF, no hidden text |
| columns | `Left result: -12 units`; `Right result: 7 units` | two columns |
| foreign | `FOREIGN PAPER: unrelated result 99` | separate PDF, excluded from signed-source claims |

For image-only source, render PDF to PNG and have a separate reviewer visually confirm A=-12/B=7 before interpreting image outcomes. Extraction without OCR may produce empty text: UNKNOWN is expected, not a claim of an extractor bug. No OCR capability claim without actually running OCR (not planned). Multicolumn evaluation checks only the two declared facts, not general reading-order fidelity.

## Fixed cases (each extraction engine)

Use actual `pypdf` and `pdftotext` extraction, preserving raw output and exit code. Six unmodified extraction controls: signed linked, signed orphan, image linked, columns linked, signed missing-provenance, signed unknown-revision. Four derived-context mutations applied **after** actual signed extraction: lost minus (`-12`→`12`), missing required section, concatenation of actual foreign extraction, and linked correct signed content with a stale claimed source hash. These mutations are fault injection, never attributed to either extractor. Correct signed orphan demonstrates factual correctness without connectivity; linked corruption demonstrates connectivity without correctness. Missing provenance and unknown revision exercise UNKNOWN handling. No dropping failed or inconclusive cases.

Separately evaluate three text-context freshness cases, not PDF cases: fixed canonical source `freeze status completed; revision 3` at repository commit `3b760ffc56bd724d6378abaff1a46e7036365fab`, derived current claim at that revision; derived `freeze status active; revision 3` from prior revision with explicit superseded relation; missing source revision. These are synthetic mirrors of the observed #15 stale-completed-source incident, not fresh measurements of #15 itself. Current correct, explicit stale contradiction, and missing revision are respectively expected PASS, FAIL, UNKNOWN for fact/freshness checks (connection present). Source snapshot and superseded relation are retained.

The declared total is 20 PDF observations (10 cases × 2 extractors) plus 3 text-context observations. If an engine is unavailable or fails, preserve its observations as UNKNOWN and report reduced usable denominators. The frozen factual truth labels are independent of admission: signed linked/orphan/missing-provenance/unknown-revision/stale-hash and columns linked are factually correct; image linked has known correct source facts but extracted-claim truth is UNKNOWN if text is absent; lost-minus, missing-section, and foreign concatenation are factually incorrect (the latter two violate declared completeness/exclusivity). Text current is factually correct, stale active is incorrect, and missing-revision text remains factually correct but freshness UNKNOWN. Expected admission is separately PASS only for linked/provenanced/current, fully matching cases; correct orphan and stale-hash hold for connectivity/provenance, missing-provenance/revision hold UNKNOWN. Labels are evaluated after gate computation; never supplied to admission logic.

## Capture, execution, and analysis

After independent GO, run:

```sh
PYTHONDONTWRITEBYTECODE=1 python scripts/probes/knowledge_integrity_probe.py --output-dir /workspace/dat-readiness/knowledge63-firstrun
```

Refuse existing output directories. Capture Python/platform/library/tool versions; exact commands, exit codes, stdout/stderr, monotonic durations; script and plan hashes; raw PDFs, rendered image PNG, extraction text, source manifest, fixed oracle requirements, per-case evidence and outcomes as scratch JSON/CSV/text. No `apiVersion`/`kind` artifacts. Stdout points to evidence. Preserve source before/after hashes and report mutation if detected. No network or external writing.

Report measured counts by extraction vs injected vs text strata, baseline and candidate false acceptance among factually incorrect claims, false holds among factually correct claims (all non-PASS, separating FAIL and UNKNOWN and identifying operational holds due to connectivity/provenance/freshness), unknown claim truth separately, fact-match coverage/traceability, orphan detection independent of integrity, contradiction/freshness outcomes, wall time and evidence bytes. Monetary/model cost is not measured; human review time is not automatically inferred. Timing is descriptive for this machine/corpus. Expected outcomes remain a hypothesis until inspected; do not tune facts to observed extraction.

## Verify → review → fix → review

Implementation verification: Python 3.12 syntax, refusal to overwrite, inspect extraction records/CSV and raw hashes. Independent reviewer receives plan, script, outputs, and rendered image (not only author summary), verifies preregistration, factual expectations and label isolation. Fix implementation defects without rewriting measured history; reruns use new directories and retain the first run. Record limitations and any rerun in `docs/KNOWLEDGE_INTEGRITY_CLOUD_RESULTS.md`. Root handles later repository checks and independent PR review. No commits, pushes, merges or GitHub writes by this execution agent.

## Cloud verification matrix

| Area | Evidence scope | Status at preregistration |
|---|---|---|
| Existing repository specification/schema/provenance validators | main `3b760ff`, existing spec-lint steps; separate baseline agent | delegated, results not yet observed here |
| Git mock checks / local baseline observations | prior task records only | not rerun or claimed by this probe |
| Knowledge integrity #63 | this PDF/injection/text corpus | planned, not yet executed |
| Claude runtime, administration permissions, model arms | no runtime/admin/model execution in this probe | unmeasured / out of scope |

This matrix records scope, not new repository admission gates. Prior observations remain distinct from current Cloud execution.

## Pre-execution review corrections

Missing critical content yields UNKNOWN; only declared contradictions yield FAIL. The signed-source contradiction `Net change: 12 units` is fixed before measurement. Actual successful nonempty extraction truth is initially PENDING_REVIEW and cannot enter correct/incorrect metric denominators until a separate reviewer inspects source/output. Empty or failed extraction remains UNKNOWN, not discarded. Link baseline uses presence of a source hash as its link proxy, not hash validity. Frozen injected case labels describe known corrupted/incomplete source fidelity, not model truth judgments. No initial incomplete metric is a final result.
