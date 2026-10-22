#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import tempfile

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
    "redaction-high-entropy-string": "high-entropy string",
    "basis-organizer-with-grounding-review": "'organizer' is allowed only without a grounding review",
}

# Token-like values are assembled at run time so the repository holds no token-shaped string.
TOKEN_PREFIXES = ("gh" + "p_", "gh" + "o_", "gh" + "u_", "gh" + "s_", "gh" + "r_", "github" + "_pat_", "s" + "k-")

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

for prefix in TOKEN_PREFIXES:
    errors = vro.check_redaction({"value": prefix + "EXAMPLE"})
    if not any("token-like prefix" in error for error in errors):
        failures.append(f"token prefix {prefix!r} must be rejected, got {errors}")

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

# Parsing rules must agree at both public entry points, including malformed files.
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    source = (FIXTURES / "valid" / "no-reviews-explicit-zero.yaml").read_text(encoding="utf-8")
    cases = {
        "valid": (source.encode("utf-8"), 0, ""),
        "duplicate-top": ((source + "\noutcome: completed\n").encode("utf-8"), 1, "duplicate key"),
        "duplicate-nested": (source.replace("metadata:\n", "metadata:\n  project: shadow-project\n", 1).encode("utf-8"), 1, "duplicate key"),
        "malformed": (b"outcome: [broken\n", 1, "cannot read"),
        "invalid-utf8": (bytes([0xff, 0xfe]), 1, "cannot read"),
        "missing": (None, 1, "cannot read"),
    }
    for name, (data, expected_code, diagnostic) in cases.items():
        path = tmp / f"{name}.yaml"
        if data is not None:
            path.write_bytes(data)
        store = tmp / f"store-{name}"
        for command, args in (
            ("validator", [str(SCRIPT), str(path)]),
            ("save", [str(ROOT / "scripts" / "run_observation.py"), "save", str(path), "--store", str(store)]),
        ):
            result = subprocess.run([sys.executable, *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode != expected_code or diagnostic not in result.stdout or "Traceback" in result.stdout:
                failures.append(f"{name} {command}: expected exit {expected_code} / {diagnostic!r} without traceback, got {result.returncode}\n{result.stdout}")
        if expected_code and store.exists():
            failures.append(f"{name}: rejected input must not create a store")

    # One unreadable path must not prevent checking a later semantic failure.
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp / "missing.yaml"), str(invalid["redaction-absolute-path-users"])],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    if result.returncode != 1 or "cannot read" not in result.stdout or "absolute path" not in result.stdout or "Traceback" in result.stdout:
        failures.append("explicit path mode must continue after a read error\n" + result.stdout)

if failures:
    print("RunObservation validator tests failed:")
    for failure in failures:
        print(f"- {failure}")
    sys.exit(1)

print(f"RunObservation validator tests passed: {len(valid)} valid, {len(invalid)} invalid fixture(s).")
