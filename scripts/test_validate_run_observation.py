#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_run_observation.py"
FIXTURES = ROOT / "fixtures" / "run-observation"

sys.path.insert(0, str(ROOT / "scripts"))
import validate_run_observation as vro  # noqa: E402

EXPECTED_ERRORS = {
    "basis-verifier-kind-mismatch": "does not match grounding review",
    "basis-verifier-kind-without-grounding-review": "no grounding role: verifier review",
    "basis-verifier-not-targeting-merged-artifact": "no grounding role: verifier review",
    "basis-same-session-verifier": "same-session review cannot have role verifier",
    "basis-verifier-review-without-verification": "verification: must be yes",
    "basis-advisory-without-independent-review": "independentReview: does not match",
    "basis-independent-review-without-advisory": "independentReview: does not match",
    "basis-independent-review-unknown-with-reviews": "independentReview: does not match",
    "topology-not-following-basis": "does not follow from topologyBasis",
    "topology-t1-claimed-with-unknown-basis": "does not follow from topologyBasis",
    "unknown-rework-count-null": "schema: rework/count",
    "unknown-wall-clock-without-times": "requires both startedAt and endedAt",
    "unknown-delegated-exceeds-total": "greater than tasks.total",
    "redaction-string-too-long": "longer than 200 characters",
    "redaction-multiline-outcome-reason": "must be a single line",
    "redaction-absolute-path-users": "absolute path",
    "redaction-absolute-path-home": "absolute path",
    "redaction-absolute-path-windows": "absolute path",
    "redaction-token-ghp-prefix": "token-like prefix",
    "redaction-token-sk-prefix": "token-like prefix",
    "redaction-high-entropy-string": "high-entropy string",
}

failures = []
validator = vro.load_validator()

valid = sorted((FIXTURES / "valid").glob("*.yaml"))
if not valid:
    failures.append("no valid fixtures found")
for path in valid:
    errors = vro.validate_file(path, validator)
    if errors:
        failures.append(f"{path.name} must pass: {errors}")

invalid = {path.stem: path for path in (FIXTURES / "invalid").glob("*.yaml")}
if set(invalid) != set(EXPECTED_ERRORS):
    failures.append(f"invalid fixtures and expectations differ: {sorted(set(invalid) ^ set(EXPECTED_ERRORS))}")
for name, expected in EXPECTED_ERRORS.items():
    if name not in invalid:
        continue
    errors = vro.validate_file(invalid[name], validator)
    if not any(expected in error for error in errors):
        failures.append(f"{name} must fail with {expected!r}, got {errors}")

for text in ("2026-01-05T09:00:00Z", "separate-session-verifier-merge-ok", "0.3.0"):
    if vro.check_redaction({"value": text}):
        failures.append(f"ordinary value must not be flagged: {text!r}")

result = subprocess.run([sys.executable, str(SCRIPT)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
if result.returncode != 0:
    failures.append("fixture mode must pass\n" + result.stdout)

result = subprocess.run(
    [sys.executable, str(SCRIPT), str(invalid["redaction-absolute-path-users"])],
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)
if result.returncode == 0:
    failures.append("explicit path mode must fail on an invalid record")

if failures:
    print("RunObservation validator tests failed:")
    for failure in failures:
        print(f"- {failure}")
    sys.exit(1)

print(f"RunObservation validator tests passed: {len(valid)} valid, {len(invalid)} invalid fixture(s).")
