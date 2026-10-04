#!/usr/bin/env python3
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "scripts" / "prepare_pilot_run.py"
STATUS = ROOT / "scripts" / "pilot_status.py"
PILOT = ROOT / "experiments" / "EXP-001-t0-vs-t1" / "pilot" / "pilot.yaml"
MATRIX = ROOT / "experiments" / "EXP-001-t0-vs-t1" / "pilot" / "run-matrix.yaml"


def run_prepare(pilot, matrix, run_id, workspace, session_id, workspace_id):
    return subprocess.run(
        [
            sys.executable, str(PREPARE),
            "--pilot", str(pilot),
            "--matrix", str(matrix),
            "--run-id", run_id,
            "--workspace", str(workspace),
            "--session-id", session_id,
            "--workspace-id", workspace_id,
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def run_status(pilot, matrix):
    return subprocess.run(
        [sys.executable, str(STATUS), "--pilot", str(pilot), "--matrix", str(matrix), "--json"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


failures = []

with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
    tmp_path = Path(tmp)
    pilot = yaml.safe_load(PILOT.read_text(encoding="utf-8"))
    matrix = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
    pilot_path = tmp_path / "pilot.yaml"
    matrix_path = tmp_path / "matrix.yaml"
    artifact_root = tmp_path / "artifacts"
    pilot["spec"]["artifactRoot"] = str(artifact_root.relative_to(ROOT))
    pilot["spec"]["matrixPath"] = str(matrix_path.relative_to(ROOT))
    pilot_path.write_text(yaml.safe_dump(pilot, sort_keys=False), encoding="utf-8")
    matrix_path.write_text(yaml.safe_dump(matrix, sort_keys=False), encoding="utf-8")

    first = matrix["spec"]["runs"][0]
    second = matrix["spec"]["runs"][1]
    ws1 = tmp_path / "workspace-1"
    result = run_prepare(
        pilot_path, matrix_path, first["runId"], ws1, "session-001", "workspace-001"
    )
    if result.returncode != 0:
        failures.append("valid prepare must pass\n" + result.stdout)
    if not (ws1 / "tests").exists():
        failures.append("prepare must copy the fixture into a fresh workspace")
    if not (artifact_root / first["runId"] / "run-meta.yaml").is_file():
        failures.append("prepare must create run-meta.yaml")
    if not (artifact_root / first["runId"] / "prompt.md").is_file():
        failures.append("prepare must create prompt.md")

    status_result = run_status(pilot_path, matrix_path)
    if status_result.returncode != 0 or '"prepared": 1' not in status_result.stdout:
        failures.append("status must report exactly one prepared run after preparation")

    blocked_order = run_prepare(
        pilot_path, matrix_path, second["runId"], tmp_path / "workspace-order-blocked",
        "session-order", "workspace-order"
    )
    if blocked_order.returncode == 0:
        failures.append("executionOrder=2 must be blocked until the prior run has result artifacts")

    duplicate_run = run_prepare(
        pilot_path, matrix_path, first["runId"], tmp_path / "workspace-dup-run",
        "session-002", "workspace-002"
    )
    if duplicate_run.returncode == 0:
        failures.append("re-preparing the same runId must fail")

    prior_dir = artifact_root / first["runId"]
    for name in ("trace.yaml", "evaluation.yaml", "patch.diff", "evidence.txt"):
        (prior_dir / name).write_text("test-artifact\n", encoding="utf-8")

    duplicate_session = run_prepare(
        pilot_path, matrix_path, second["runId"], tmp_path / "workspace-2",
        "session-001", "workspace-003"
    )
    if duplicate_session.returncode == 0:
        failures.append("duplicate sessionId must fail")

    duplicate_workspace = run_prepare(
        pilot_path, matrix_path, second["runId"], tmp_path / "workspace-3",
        "session-003", "workspace-001"
    )
    if duplicate_workspace.returncode == 0:
        failures.append("duplicate workspaceId must fail")

    unknown = run_prepare(
        pilot_path, matrix_path, "does-not-exist", tmp_path / "workspace-unknown",
        "session-004", "workspace-004"
    )
    if unknown.returncode == 0:
        failures.append("unknown runId must fail")

    existing_ws = tmp_path / "already-exists"
    existing_ws.mkdir()
    non_fresh = run_prepare(
        pilot_path, matrix_path, second["runId"], existing_ws,
        "session-005", "workspace-005"
    )
    if non_fresh.returncode == 0:
        failures.append("existing workspace must fail even when empty")

with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
    tmp_path = Path(tmp)
    pilot = yaml.safe_load(PILOT.read_text(encoding="utf-8"))
    matrix_path = tmp_path / "matrix.yaml"
    pilot_path = tmp_path / "pilot.yaml"
    pilot["spec"]["artifactRoot"] = "../operator-kit-outside"
    pilot["spec"]["matrixPath"] = str(matrix_path.relative_to(ROOT))
    pilot_path.write_text(yaml.safe_dump(pilot, sort_keys=False), encoding="utf-8")
    shutil.copy2(MATRIX, matrix_path)
    escaped = run_status(pilot_path, matrix_path)
    if escaped.returncode == 0:
        failures.append("status must reject artifactRoot path escape")


base_prompt = (ROOT / "experiments" / "EXP-001-t0-vs-t1" / "pilot" / "prompts" / "BASE.md").read_text(encoding="utf-8")
for condition in ("T0", "T1"):
    overlay = (ROOT / "experiments" / "EXP-001-t0-vs-t1" / "pilot" / "prompts" / f"{condition}.md").read_text(encoding="utf-8")
    for placeholder in ("{{instruction}}", "{{acceptance_criteria}}", "{{evidence_commands}}"):
        if placeholder in overlay:
            failures.append(f"{condition} overlay must not duplicate task/evidence placeholder {placeholder}")
if "{{topology_contract}}" not in base_prompt:
    failures.append("BASE prompt must own the topology contract insertion point")

if failures:
    print("Operator Kit tests failed:")
    for failure in failures:
        print(f"- {failure}")
    raise SystemExit(1)

print("Operator Kit tests passed.")
