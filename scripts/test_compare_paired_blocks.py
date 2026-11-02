#!/usr/bin/env python3
"""Tests for compare_paired_blocks.py."""
from pathlib import Path
import contextlib
import io
import sys
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compare_paired_blocks import compare, main  # noqa: E402

SPEC = {
    "metadata": {"name": "EXP-X"},
    "spec": {
        "conditions": [{"id": "T0"}, {"id": "T1"}],
        "controls": {"sameRuntime": True, "sameModel": True, "sameEffort": True},
    },
}


def run(condition, block, scenario="s1", tokens=(100, 0), wall=10, model="m"):
    efficiency = {"agentInvocations": 1, "coordinationTransitions": 0, "wallClockMs": wall}
    if tokens is not None:
        efficiency.update(inputTokens=tokens[0], outputTokens=tokens[1])
    return {
        "kind": "RunEvaluation",
        "metadata": {"runId": f"{scenario}-{block}-{condition}", "experiment": "EXP-X", "scenario": scenario,
                     "condition": condition, "blockId": block},
        "executionContext": {"runtime": "r", "model": model, "effort": "high"},
        "outcome": {"taskSuccess": True, "regressionDetected": False},
        "collaboration": {"humanInterventions": 0, "boundaryViolations": 0},
        "efficiency": efficiency,
    }


def check(condition, reason):
    if not condition:
        raise AssertionError(reason)


def invalid_reasons(result):
    return {(b["scenario"], b["blockId"]): b["reasons"] for b in result["invalidBlocks"]}


# Same blockId under different scenarios is not paired.
result = compare([run("T0", "b1", "s1"), run("T1", "b1", "s2")], SPEC, "T0", "T1", {})
check(result["pairedBlockCount"] == 0 and result["invalidBlockCount"] == 2, "cross-scenario blocks must not pair")
check(result["status"] == "INCONCLUSIVE" and result["meanTotalTokensRatio"] is None, "no pairs is INCONCLUSIVE")

# Missing and duplicate conditions, and control mismatch, make a block invalid.
result = compare([run("T0", "miss"), run("T0", "dup"), run("T0", "dup"), run("T1", "dup"),
                  run("T0", "ctl"), run("T1", "ctl", model="other"), run("T0", "ok"), run("T1", "ok")],
                 SPEC, "T0", "T1", {})
reasons = invalid_reasons(result)
check(any("expected" in r for r in reasons[("s1", "miss")]), "missing condition must be reported")
check(any("duplicate" in r for r in reasons[("s1", "dup")]), "duplicate condition must be reported")
check(reasons[("s1", "ctl")] == ["mixes models"], "control mismatch must be reported")
check(result["pairedBlockCount"] == 1 and result["status"] == "PARTIAL", "valid block still pairs")

# Missing tokens and zero denominators become null with a reason.
result = compare([run("T0", "a", tokens=None), run("T1", "a"), run("T0", "z", tokens=(0, 0), wall=0),
                  run("T1", "z")], SPEC, "T0", "T1", {})
blocks = {b["blockId"]: b for b in result["pairedBlocks"]}
check(blocks["a"]["delta"]["totalTokens"] is None and blocks["a"]["totalTokensRatio"] is None, "missing is null")
check("delta.totalTokens: value missing" in blocks["a"]["nullReasons"], "missing has a reason")
check(blocks["z"]["totalTokensRatio"] is None and "totalTokensRatio: zero denominator" in blocks["z"]["nullReasons"],
      "zero denominator is null with a reason")
check(blocks["z"]["wallClockMsRatio"] is None, "zero wall clock denominator is null")
check(result["conditionMeans"]["T0"]["totalTokensRuns"] == 1, "missing tokens are not averaged as 0")

# Exclusions are applied and kept with their reason.
result = compare([run("T0", "a", tokens=(100, 0)), run("T1", "a", tokens=(300, 0)),
                  run("T0", "b", tokens=(100, 0)), run("T1", "b", tokens=(200, 0))],
                 SPEC, "T0", "T1", {"a": "confounded"})
check(result["excludedBlocks"][0]["blockId"] == "a" and result["excludedBlocks"][0]["reason"] == "confounded",
      "excluded block and reason must be in output")
check(result["pairedBlockCount"] == 1 and result["meanTotalTokensRatio"] == 2.0, "excluded block is not aggregated")

# Condition-mean ratio differs from block ratios; deltas are candidate - baseline.
base_fail = run("T0", "a", tokens=(100, 0))
base_fail["outcome"]["taskSuccess"] = False
result = compare([base_fail, run("T1", "a", tokens=(200, 0)), run("T0", "b", tokens=(300, 0)),
                  run("T1", "b", tokens=(300, 0))], SPEC, "T0", "T1", {})
blocks = {b["blockId"]: b for b in result["pairedBlocks"]}
check([blocks["a"]["totalTokensRatio"], blocks["b"]["totalTokensRatio"]] == [2.0, 1.0], "block ratios")
check(result["meanTotalTokensRatio"] == 1.25, "mean ratio is mean(candidate) / mean(baseline)")
check(blocks["a"]["delta"]["taskSuccess"] == 1 and blocks["a"]["delta"]["totalTokens"] == 100, "delta direction")

# Runtime and effort mismatches are reported.
other_runtime, missing_effort = run("T1", "rt"), run("T1", "ef")
other_runtime["executionContext"]["runtime"] = "other"
del missing_effort["executionContext"]["effort"]
reasons = invalid_reasons(compare([run("T0", "rt"), other_runtime, run("T0", "ef"), missing_effort],
                                  SPEC, "T0", "T1", {}))
check(reasons[("s1", "rt")] == ["mixes runtimes"], "runtime mismatch must be reported")
check(reasons[("s1", "ef")] == ["requires effort values"], "missing effort must be reported")

# CLI input errors exit 2 with empty stdout.
SAMPLE = ROOT / "examples" / "experiment-run" / "T0-evaluation.yaml"
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    cases = {
        "missing": tmp / "missing.yaml",
        "empty": tmp / "empty.yaml",
        "broken": tmp / "broken.yaml",
        "list": tmp / "list.yaml",
        "partial": tmp / "partial.yaml",
        "string-bool": tmp / "string-bool.yaml",
    }
    cases["empty"].write_text("", encoding="utf-8")
    cases["broken"].write_text("a: [\n", encoding="utf-8")
    cases["list"].write_text("- 1\n", encoding="utf-8")
    cases["partial"].write_text("kind: RunEvaluation\n", encoding="utf-8")
    cases["string-bool"].write_text(
        SAMPLE.read_text(encoding="utf-8").replace("taskSuccess: true", 'taskSuccess: "false"'), encoding="utf-8")
    for name, path in cases.items():
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["--baseline", "T0", "--candidate", "T1", str(path)])
        check(code == 2 and out.getvalue() == "" and str(path) in err.getvalue(), f"{name} input must exit 2")

# CLI rejects an experiment spec whose controls are missing or not boolean.
EXP_DIR = ROOT / "experiments" / "EXP-001-t0-vs-t1"
RUN = EXP_DIR / "runs" / "pilot-codex" / "EXP-001-train-normalize-name-r02-T0" / "evaluation.yaml"
with tempfile.TemporaryDirectory() as tmp:
    for name, controls in (("empty-controls", {}), ("string-bool-control", {"sameModel": "false"})):
        spec = yaml.safe_load((EXP_DIR / "experiment.yaml").read_text(encoding="utf-8"))
        if controls:
            spec["spec"]["controls"].update(controls)
        else:
            spec["spec"]["controls"] = controls
        path = Path(tmp) / f"{name}.yaml"
        path.write_text(yaml.safe_dump(spec), encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["--baseline", "T0", "--candidate", "T1", "--experiment-spec", str(path), str(RUN)])
        check(code == 2 and out.getvalue() == "" and str(path) in err.getvalue(), f"{name} must exit 2")

# With three conditions, a block needs all of them; the chosen two are compared.
SPEC3 = {**SPEC, "spec": {**SPEC["spec"], "conditions": [{"id": "T0"}, {"id": "T1"}, {"id": "T2"}]}}
result = compare([run("T0", "a"), run("T1", "a"), run("T0", "b"), run("T1", "b"), run("T2", "b")],
                 SPEC3, "T0", "T1", {})
check([b["blockId"] for b in result["pairedBlocks"]] == ["b"], "three-condition block pairs only when complete")
check([b["blockId"] for b in result["invalidBlocks"]] == ["a"], "missing third condition is invalid")

# CLI rejects an exclusion without a reason.
with contextlib.redirect_stderr(io.StringIO()):
    try:
        main(["--baseline", "T0", "--candidate", "T1", "--exclude", "a=", "x.yaml"])
    except SystemExit as error:
        check(error.code == 2, "empty exclusion reason is a usage error")
    else:
        raise AssertionError("empty exclusion reason must fail")

# Ratio populations use complete metric pairs, not each condition's nonnull rows.
for missing_conditions in (("T0",), ("T1",), ("T0", "T1")):
    rows = [run(c, "missing", tokens=None if c in missing_conditions else (100, 0)) for c in ("T0", "T1")]
    rows += [run("T0", "complete", tokens=(200, 0)), run("T1", "complete", tokens=(400, 0))]
    result = compare(rows, SPEC, "T0", "T1", {})
    check(result["meanTotalTokensRatio"] == 2.0, "token ratio must use identical complete-pair populations")
    summary = result["pairedMetricSummary"]["totalTokens"]
    check(summary["pairedBlockCount"] == 1 and summary["missingBlockCount"] == 1, "metric pair counts")
    check(summary["baselineMean"] == 200 and summary["candidateMean"] == 400, "paired means")
    check(summary["missingBlocks"] == [{"scenario": "s1", "blockId": "missing",
                                        "missingConditions": list(missing_conditions)}], "missing sides and block identity")
    for condition in ("T0", "T1"):
        check(result["conditionMeans"][condition]["totalTokensRuns"] == (1 if condition in missing_conditions else 2),
              "descriptive condition means retain their original observation counts")
    check(result["pairedBlockCount"] == 2 and result["status"] == "PAIRED", "structural pair status is unchanged")
    check(result["pairedMetricSummary"]["wallClockMs"]["pairedBlockCount"] == 2, "token missingness does not drop wall time")

# Equal nonnull counts do not prove that the same blocks were measured.
result = compare([run("T0", "a", tokens=(100, 0)), run("T1", "a", tokens=None),
                  run("T0", "b", tokens=None), run("T1", "b", tokens=(400, 0))], SPEC, "T0", "T1", {})
check(result["meanTotalTokensRatio"] is None, "disjoint observed populations have no paired ratio")
check(result["pairedMetricSummary"]["totalTokens"]["pairedBlockCount"] == 0, "no metric-complete pair")
check("meanTotalTokensRatio: value missing" in result["ratioNullReasons"], "unavailable ratio has a reason")

# A partly recorded token total is unavailable; zero is an observed value.
partial = run("T1", "partial")
del partial["efficiency"]["outputTokens"]
result = compare([run("T0", "partial"), partial, run("T0", "zero", tokens=(0, 0), wall=0),
                  run("T1", "zero", tokens=(0, 0), wall=0)], SPEC, "T0", "T1", {})
summary = result["pairedMetricSummary"]["totalTokens"]
check(summary["pairedBlockCount"] == 1 and summary["baselineMean"] == 0, "measured zero remains in population")
check(result["meanTotalTokensRatio"] is None and "meanTotalTokensRatio: zero denominator" in result["ratioNullReasons"],
      "zero denominator is null, not a missing measurement")

# Zero-denominator blocks remain in a ratio-of-means population.
result = compare([run("T0", "zero", tokens=(0, 0)), run("T1", "zero", tokens=(100, 0)),
                  run("T0", "nonzero", tokens=(100, 0)), run("T1", "nonzero", tokens=(100, 0))],
                 SPEC, "T0", "T1", {})
check(result["meanTotalTokensRatio"] == 2.0, "do not drop observed zeros or average block ratios")
check(result["pairedMetricSummary"]["totalTokens"]["pairedBlockCount"] == 2, "both measured pairs count")

# Reused block IDs are valid unless the exclusion itself is ambiguous.
rows = [run(c, "shared", scenario=s) for s in ("s1", "s2") for c in ("T0", "T1")]
check(compare(rows, SPEC, "T0", "T1", {})["pairedBlockCount"] == 2, "reused block IDs still pair by scenario")
try:
    compare(rows, SPEC, "T0", "T1", {"shared": "confounded"})
except ValueError as error:
    check("ambiguous across scenarios" in str(error), "ambiguity has an actionable error")
else:
    raise AssertionError("ambiguous exclusion must fail rather than drop multiple scenarios")
result = compare(rows[:2], SPEC, "T0", "T1", {"shared": "confounded"})
check(result["excludedBlockCount"] == 1 and result["status"] == "INCONCLUSIVE", "one-scenario exclusion remains valid")
check(result["pairedMetricSummary"]["totalTokens"]["pairedBlockCount"] == 0, "excluded pairs never enter metric summary")
check(result["meanTotalTokensRatio"] is None, "no pairs is null, not zero")

# Invalid/excluded blocks do not contribute to missingness of accepted pairs.
result = compare([run("T0", "valid"), run("T1", "valid", tokens=(200, 0)),
                  run("T0", "invalid", tokens=None), run("T1", "invalid", model="other"),
                  run("T0", "excluded", tokens=None), run("T1", "excluded")],
                 SPEC, "T0", "T1", {"excluded": "predeclared confound"})
check(result["pairedMetricSummary"]["totalTokens"]["missingBlockCount"] == 0, "only structurally accepted pairs summarized")
check(result["pairedMetricSummary"]["totalTokens"]["pairedBlockCount"] == 1, "only valid pair summarized")
check(result["meanTotalTokensRatio"] == 2.0 and result["invalidBlockCount"] == 1 and result["excludedBlockCount"] == 1,
      "invalid/excluded evidence stays separate")

# Exercise the real CLI validation and error contract with synthetic fixture copies.
with tempfile.TemporaryDirectory() as tmp:
    spec_name = yaml.safe_load((EXP_DIR / "experiment.yaml").read_text(encoding="utf-8"))["metadata"]["name"]

    def invoke_synthetic_cli(rows, extra=()):
        paths = []
        for index, row in enumerate(rows):
            fixture = yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))
            fixture["metadata"] = {**row["metadata"], "experiment": spec_name}
            fixture["executionContext"] = row["executionContext"]
            fixture["efficiency"] = row["efficiency"]
            path = Path(tmp) / f"synthetic-{index}.yaml"
            path.write_text(yaml.safe_dump(fixture), encoding="utf-8")
            paths.append(str(path))
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["--baseline", "T0", "--candidate", "T1", "--experiment-spec",
                         str(EXP_DIR / "experiment.yaml"), *extra, *paths])
        return code, out.getvalue(), err.getvalue()

    rows = [run("T0", "a"), run("T1", "a", tokens=None),
            run("T0", "b", tokens=(200, 0)), run("T1", "b", tokens=(400, 0))]
    code, out, err = invoke_synthetic_cli(rows)
    check(code == 0 and not err and yaml.safe_load(out)["meanTotalTokensRatio"] == 2.0,
          "CLI returns complete-pair ratio after real schema validation")
    rows = [run(c, "shared", scenario=s) for s in ("s1", "s2") for c in ("T0", "T1")]
    for extra, message in ((["--exclude", "shared=confounded"], "ambiguous across scenarios"),
                           (["--exclude", "absent=confounded"], "not found in input"),
                           (["--exclude", "shared=first", "--exclude", "shared=second"], "more than once")):
        code, out, err = invoke_synthetic_cli(rows, extra)
        check(code == 2 and out == "" and message in err, "CLI fails closed with empty stdout")
    code, out, err = invoke_synthetic_cli(rows[:2], ["--exclude", "shared=confounded"])
    check(code == 0 and not err and yaml.safe_load(out)["excludedBlockCount"] == 1,
          "CLI keeps an unambiguous exclusion usable")

# Historical canonical inputs are read-only: complete-data ratios stay unchanged.
for label, paths in (
    ("18 runs", sorted((EXP_DIR / "runs" / "pilot-codex").glob("*/evaluation.yaml"))),
    ("16 runs", sorted(path for path in (EXP_DIR / "runs" / "pilot-codex").glob("*/evaluation.yaml")
                       if path.parent.name not in ("EXP-001-train-normalize-name-r01-T0",
                                                   "EXP-001-train-normalize-name-r01-T1"))),
):
    evaluations = [yaml.safe_load(path.read_text(encoding="utf-8")) for path in paths]
    historical_spec = yaml.safe_load((EXP_DIR / "experiment.yaml").read_text(encoding="utf-8"))
    result = compare(evaluations, historical_spec, "T0", "T1", {})
    expected_count = 18 if label == "18 runs" else 16
    check(len(evaluations) == expected_count and result["pairedBlockCount"] == expected_count // 2,
          f"historical {label} population must stay explicit")
    check(result["invalidBlockCount"] == 0, "historical pairs remain valid")
    totals = {condition: [r["efficiency"]["inputTokens"] + r["efficiency"]["outputTokens"]
                         for r in evaluations if r["metadata"]["condition"] == condition]
              for condition in ("T0", "T1")}
    expected_ratio = (sum(totals["T1"]) / len(totals["T1"])) / (sum(totals["T0"]) / len(totals["T0"]))
    check(abs(result["meanTotalTokensRatio"] - expected_ratio) < 1e-12, "historical ratio unchanged")
    check(result["pairedMetricSummary"]["totalTokens"]["missingBlockCount"] == 0,
          "historical comparison is complete-data, not an imputed population")
    print(f"historical {label}: {result['pairedBlockCount']} pairs, token ratio={result['meanTotalTokensRatio']:.12f}")

print("compare_paired_blocks tests passed")
