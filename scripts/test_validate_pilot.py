#!/usr/bin/env python3
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_pilot.py"
PILOT = ROOT / "experiments" / "EXP-001-t0-vs-t1" / "pilot" / "pilot.yaml"
MATRIX = ROOT / "experiments" / "EXP-001-t0-vs-t1" / "pilot" / "run-matrix.yaml"

def run(pilot, matrix, *extra):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--pilot", str(pilot), "--matrix", str(matrix), *extra],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )

failures = []

valid = run(PILOT, MATRIX)
if valid.returncode != 0:
    failures.append("valid pilot must pass\n" + valid.stdout)

with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
    tmp_path = Path(tmp)
    pilot_path = tmp_path / "pilot.yaml"
    matrix_path = tmp_path / "matrix.yaml"
    pilot = yaml.safe_load(PILOT.read_text(encoding="utf-8"))
    matrix = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
    pilot["spec"]["matrixPath"] = str(matrix_path.relative_to(ROOT))
    matrix["spec"]["runs"][0]["condition"] = "BROKEN"
    pilot_path.write_text(yaml.safe_dump(pilot, sort_keys=False), encoding="utf-8")
    matrix_path.write_text(yaml.safe_dump(matrix, sort_keys=False), encoding="utf-8")
    result = run(pilot_path, matrix_path)
    if result.returncode == 0:
        failures.append("tampered matrix must fail")

with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
    tmp_path = Path(tmp)
    pilot_path = tmp_path / "pilot.yaml"
    matrix_path = tmp_path / "matrix.yaml"
    pilot = yaml.safe_load(PILOT.read_text(encoding="utf-8"))
    pilot["spec"]["matrixPath"] = str(matrix_path.relative_to(ROOT))
    pilot["spec"]["artifactRoot"] = "../outside-dat-pilot"
    pilot_path.write_text(yaml.safe_dump(pilot, sort_keys=False), encoding="utf-8")
    shutil.copy2(MATRIX, matrix_path)
    result = run(pilot_path, matrix_path)
    if result.returncode == 0:
        failures.append("artifactRoot path escape must fail")

with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
    tmp_path = Path(tmp)
    pilot_path = tmp_path / "pilot.yaml"
    matrix_path = tmp_path / "matrix.yaml"
    artifact_root = tmp_path / "artifacts"
    pilot = yaml.safe_load(PILOT.read_text(encoding="utf-8"))
    matrix = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
    first_run = matrix["spec"]["runs"][0]["runId"]
    prepared_run = ROOT / pilot["spec"]["artifactRoot"] / first_run
    isolated_run = artifact_root / first_run
    isolated_run.mkdir(parents=True)
    for filename in ("run-meta.yaml", "prompt.md"):
        shutil.copy2(prepared_run / filename, isolated_run / filename)
    pilot["spec"]["matrixPath"] = str(matrix_path.relative_to(ROOT))
    pilot["spec"]["artifactRoot"] = str(artifact_root.relative_to(ROOT))
    pilot_path.write_text(yaml.safe_dump(pilot, sort_keys=False), encoding="utf-8")
    matrix_path.write_text(yaml.safe_dump(matrix, sort_keys=False), encoding="utf-8")

    incomplete = run(pilot_path, matrix_path, "--require-complete")
    if incomplete.returncode == 0:
        failures.append("require-complete must fail for incomplete isolated artifacts")

    single_incomplete = run(pilot_path, matrix_path, "--run-id", first_run)
    if single_incomplete.returncode == 0:
        failures.append("single-run artifact validation must fail for preparation-only artifacts")
    if "missing execution-attestation.yaml" not in single_incomplete.stdout:
        failures.append("single-run validation must require post-run execution attestation")

unknown_run = run(PILOT, MATRIX, "--run-id", "does-not-exist")
if unknown_run.returncode == 0:
    failures.append("single-run artifact validation must reject unknown runId")

if failures:
    print("Pilot validator tests failed:")
    for failure in failures:
        print(f"- {failure}")
    raise SystemExit(1)

print("Pilot validator negative tests passed.")
