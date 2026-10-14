#!/usr/bin/env python3
"""Non-normative provenance report: positive/negative fixtures and historical Runs."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import json
import subprocess
import sys

from audit_provenance import MISSING, audit, audit_directory, compare, instant

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures/provenance-audit"
RUNS = ROOT / "experiments/EXP-001-t0-vs-t1/runs/pilot-codex"


def check(actual, expected, label):
    if actual != expected:
        raise AssertionError(f"{label}: expected={expected!r}, observed={actual!r}")


def main() -> int:
    expected = {
        "baseline-consistent": "PASS",
        "ctl-trace-model-mismatch": "FAIL",
        "neg-session-id-mismatch": "FAIL",
        "neg-fresh-session-mismatch": "FAIL",
        "neg-timestamp-mismatch": "FAIL",
        "neg-token-mismatch": "FAIL",
        "neg-token-field-missing": "UNKNOWN",
        "neg-wallclock-field-missing": "UNKNOWN",
        "neg-trace-session-unknown": "UNKNOWN",
    }
    for name, verdict in expected.items():
        run_dirs = list((FIXTURES / name / "runs").glob("EXP-001-*"))
        check(len(run_dirs), 1, f"{name}: fixture count")
        result = audit_directory(run_dirs[0])
        check(result["verdict"], verdict, name)
        if verdict == "UNKNOWN":
            assert "UNKNOWN" in result["checks"].values(), name

    runs = sorted(RUNS.glob("EXP-001-*"))
    check(len(runs), 18, "historical Run count")
    first = runs[0] / "trace.yaml"
    original_sha = hashlib.sha256(first.read_bytes()).hexdigest()
    for directory in runs:
        check(audit_directory(directory)["verdict"], "PASS", directory.name)
    check(hashlib.sha256(first.read_bytes()).hexdigest(), original_sha, "historical artifact unchanged")

    check(instant("2026-10-14T01:58:20+0000"),
          instant("2026-10-14T01:58:20+00:00"), "same UTC instant")
    check(compare("bad time", "2026-10-14T01:58:20+00:00", timestamp=True),
          "UNKNOWN", "unparseable timestamp")
    check(compare("2026-10-14T01:58:20", "2026-10-14T01:58:20+00:00", timestamp=True),
          "UNKNOWN", "timezone-less timestamp")
    check(compare(MISSING, "value"), "UNKNOWN", "missing value")
    check(compare(False, 0), "UNKNOWN", "bool not integer")

    spec = {"sessionId": "s1", "freshSession": True, "crossRunFeedbackUsed": False,
            "startedAt": "2026-10-14T01:00:00+00:00", "finishedAt": "2026-10-14T01:01:00+00:00",
            "runtime": "codex", "model": "m", "effort": "high"}
    start = {"type": "start", "actor": "worker", "timestamp": "2026-10-14T01:00:00+00:00",
             "details": {"sessionId": "s1", "freshSession": True, "crossRunFeedbackUsed": False}}
    finish = {"type": "finish", "actor": "worker", "timestamp": "2026-10-14T01:01:00+00:00"}
    trace = {"events": [start, finish], "runtime": {"name": "codex"},
             "model": {"id": "m", "effort": "high"},
             "summary": {"inputTokens": 1, "outputTokens": 2, "wallClockMs": 60000}}
    attestation = {"spec": spec}
    evaluation = {"efficiency": {"inputTokens": 1, "outputTokens": 2, "wallClockMs": 60000}}
    check(audit(attestation, trace, evaluation)["verdict"], "PASS", "synthetic baseline")
    ambiguous = deepcopy(trace)
    ambiguous["events"].insert(0, deepcopy(start))
    check(audit(attestation, ambiguous, evaluation)["verdict"], "UNKNOWN", "duplicate start")
    contradictory = deepcopy(ambiguous)
    contradictory["summary"]["inputTokens"] = 99
    check(audit(attestation, contradictory, evaluation)["verdict"], "FAIL", "FAIL takes precedence")
    # The CLI must not equate exit 0 with ACCEPT; the JSON verdict is authoritative.
    sample = next((FIXTURES / "neg-session-id-mismatch" / "runs").glob("EXP-001-*"))
    proc = subprocess.run([sys.executable, "scripts/audit_provenance.py", "--run-dir", str(sample)],
                          cwd=ROOT, capture_output=True, text=True, check=False)
    check(proc.returncode, 0, "report-only exit code")
    report = json.loads(proc.stdout)
    check(report["nonNormative"], True, "not an acceptance gate")
    check(report["counts"]["FAIL"], 1, "structured failure evidence")
    print("provenance audit tests PASS: nine fixtures, 18 legacy Runs, negative and CLI cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
