#!/usr/bin/env python3
"""Deterministic controls, negative fixtures and read-only EXP-001 smoke audit."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import subprocess
import sys

from audit_provenance import (
    ROOT, PASS, FAIL, UNKNOWN, audit, audit_directory, compare, compare_instants,
    load_artifact, overall,
)

FIXTURES = ROOT / "fixtures/provenance-audit"
CASES = {
    "baseline-consistent": PASS,
    "ctl-trace-model-mismatch": FAIL,
    "neg-session-id-mismatch": FAIL,
    "neg-fresh-session-mismatch": FAIL,
    "neg-timestamp-mismatch": FAIL,
    "neg-token-mismatch": FAIL,
    "neg-token-field-missing": UNKNOWN,
    "neg-wallclock-field-missing": UNKNOWN,
    "neg-trace-session-unknown": UNKNOWN,
}
for name, expected in CASES.items():
    run_dir = FIXTURES / name / "runs/EXP-001-train-normalize-name-r01-T0"
    actual = overall(audit_directory(run_dir))
    assert actual == expected, f"{name}: wanted {expected}, received {actual}"

base = FIXTURES / "baseline-consistent/runs/EXP-001-train-normalize-name-r01-T0"
att = load_artifact(base / "execution-attestation.yaml")
trace = load_artifact(base / "trace.yaml")
evaluation = load_artifact(base / "evaluation.yaml")
assert att and trace and evaluation
assert compare(0, 0) == PASS
assert compare(False, False) == PASS
assert compare(False, 0) == FAIL
assert compare(None, 0) == UNKNOWN
assert compare_instants("2026-01-01T00:00:00+0000", "2026-01-01T00:00:00+00:00") == PASS
assert compare_instants("2026-01-01T00:00:00", "2026-01-01T00:00:00+00:00") == UNKNOWN
assert compare_instants("garbage", "2026-01-01T00:00:00+00:00") == UNKNOWN

duplicate = deepcopy(trace)
duplicate["events"].append(deepcopy(trace["events"][0]))
checks = audit(att, duplicate, evaluation)
assert checks["start.sessionId"] == UNKNOWN
assert checks["start.timestamp"] == UNKNOWN
assert overall(checks) == UNKNOWN

corrupt_time = deepcopy(trace)
corrupt_time["events"][0]["timestamp"] = "not-a-date"
assert overall(audit(att, corrupt_time, evaluation)) == UNKNOWN
assert overall(audit(att, None, evaluation)) == UNKNOWN
assert overall(audit(att, trace, None)) == UNKNOWN

# Smoke regression only: do not revise existing run verdicts if the new
# observational audit has incomplete evidence. A FAIL here is worth investigating.
runs_root = ROOT / "experiments/EXP-001-t0-vs-t1/runs/pilot-codex"
real_runs = sorted(path for path in runs_root.iterdir() if path.is_dir())
assert len(real_runs) == 18, f"expected 18 historical runs, found {len(real_runs)}"
verdicts = [overall(audit_directory(path)) for path in real_runs]
assert FAIL not in verdicts, "observational audit reported a mismatch in historical accepted Run"
print("Historical accepted Runs: " + ", ".join(verdicts) + " (report only)")

# Process status remains separate from tri-state: a mismatch fails; missing
# evidence must remain printed as UNKNOWN even when process exit is zero.
for name, expected_status, expected_exit in (
    ("neg-session-id-mismatch", FAIL, 1),
    ("neg-trace-session-unknown", UNKNOWN, 0),
):
    run_dir = FIXTURES / name / "runs/EXP-001-train-normalize-name-r01-T0"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/audit_provenance.py"), "--run-dir", str(run_dir)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == expected_exit, result.stdout + result.stderr
    assert f"{run_dir.name}: {expected_status}" in result.stdout, f"{name}: {result.stdout}"

print("Provenance audit tests: 9 fixtures, missing/duplicate/time controls, 18 historical runs, CLI PASS.")
