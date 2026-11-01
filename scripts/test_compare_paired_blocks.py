#!/usr/bin/env python3
"""Tests for compare_paired_blocks.py."""
from pathlib import Path
import contextlib
import io
import sys
import tempfile

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

# CLI rejects an exclusion without a reason.
with contextlib.redirect_stderr(io.StringIO()):
    try:
        main(["--baseline", "T0", "--candidate", "T1", "--exclude", "a=", "x.yaml"])
    except SystemExit as error:
        check(error.code == 2, "empty exclusion reason is a usage error")
    else:
        raise AssertionError("empty exclusion reason must fail")

print("compare_paired_blocks tests passed")
