#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "scripts" / "prepare_pilot_run.py"
ATTEST = ROOT / "scripts" / "attest_pilot_run.py"
STATUS = ROOT / "scripts" / "pilot_status.py"
PILOT = ROOT / "experiments" / "EXP-001-t0-vs-t1" / "pilot" / "pilot.yaml"
MATRIX = ROOT / "experiments" / "EXP-001-t0-vs-t1" / "pilot" / "run-matrix.yaml"


def run_prepare(pilot, matrix, run_id, workspace, workspace_id):
    return subprocess.run(
        [
            sys.executable, str(PREPARE),
            "--pilot", str(pilot),
            "--matrix", str(matrix),
            "--run-id", run_id,
            "--workspace", str(workspace),
            "--workspace-id", workspace_id,
        ],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )


def run_attest(
    pilot, matrix, run_id, session_id,
    fresh_session="true", cross_run_feedback_used="false",
    runtime="codex", model="gpt-6.1-sol", effort="high",
):
    return subprocess.run(
        [
            sys.executable, str(ATTEST),
            "--pilot", str(pilot),
            "--matrix", str(matrix),
            "--run-id", run_id,
            "--session-id", session_id,
            "--fresh-session", fresh_session,
            "--cross-run-feedback-used", cross_run_feedback_used,
            "--runtime", runtime,
            "--model", model,
            "--effort", effort,
            "--started-at", "2026-10-05T06:00:00+09:00",
            "--finished-at", "2026-10-05T06:01:00+09:00",
        ],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )


def run_status(pilot, matrix):
    return subprocess.run(
        [sys.executable, str(STATUS), "--pilot", str(pilot), "--matrix", str(matrix), "--json"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )


failures = []

with tempfile.TemporaryDirectory(dir=ROOT) as tmp, tempfile.TemporaryDirectory() as ws_tmp:
    tmp_path = Path(tmp)
    ws_root = Path(ws_tmp)
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
    other_firsts = [
        item for item in matrix["spec"]["runs"][2:]
        if item["executionOrder"] == 1 and item["blockId"] != first["blockId"]
    ]

    result = run_prepare(
        pilot_path, matrix_path, first["runId"],
        ws_root / "workspace-1", "workspace-001"
    )
    if result.returncode != 0:
        failures.append("valid prepare must pass\n" + result.stdout)

    run_dir = artifact_root / first["runId"]
    meta_path = run_dir / "run-meta.yaml"
    prompt_path = run_dir / "prompt.md"
    if not meta_path.is_file() or not prompt_path.is_file():
        failures.append("prepare must create run-meta.yaml and prompt.md")
    else:
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        spec = meta["spec"]
        for premature in ("sessionId", "freshSession", "crossRunFeedbackUsed", "startedAt", "finishedAt"):
            if premature in spec:
                failures.append(f"prepare must not claim runtime fact {premature}")
        actual_hash = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
        if spec.get("promptSha256") != actual_hash:
            failures.append("run-meta promptSha256 must match prompt.md")

    status_result = run_status(pilot_path, matrix_path)
    if status_result.returncode != 0 or '"prepared": 1' not in status_result.stdout:
        failures.append("status must report one prepared run before runtime attestation")

    attested = run_attest(pilot_path, matrix_path, first["runId"], "session-001")
    if attested.returncode != 0:
        failures.append("post-run attestation must be writable after preparation\n" + attested.stdout)
    att_path = run_dir / "execution-attestation.yaml"
    if not att_path.is_file():
        failures.append("attestation helper must create execution-attestation.yaml")
    else:
        att = yaml.safe_load(att_path.read_text(encoding="utf-8"))
        if att["spec"].get("freshSession") is not True:
            failures.append("attestation must preserve explicit freshSession observation")
        if att["spec"].get("crossRunFeedbackUsed") is not False:
            failures.append("attestation must preserve explicit crossRunFeedback observation")

    status_result = run_status(pilot_path, matrix_path)
    if status_result.returncode != 0 or '"in-progress": 1' not in status_result.stdout:
        failures.append("attestation without result artifacts must be in-progress, not complete")

    blocked_order = run_prepare(
        pilot_path, matrix_path, second["runId"],
        ws_root / "workspace-order-blocked", "workspace-order"
    )
    if blocked_order.returncode == 0:
        failures.append("executionOrder=2 must remain blocked until prior run fully validates")

    duplicate_run = run_prepare(
        pilot_path, matrix_path, first["runId"],
        ws_root / "workspace-dup-run", "workspace-002"
    )
    if duplicate_run.returncode == 0:
        failures.append("re-preparing the same runId must fail")

    second_first = other_firsts[0]
    prep2 = run_prepare(
        pilot_path, matrix_path, second_first["runId"],
        ws_root / "workspace-2", "workspace-002"
    )
    if prep2.returncode != 0:
        failures.append("another executionOrder=1 run should prepare")
    duplicate_session = run_attest(
        pilot_path, matrix_path, second_first["runId"], "session-001"
    )
    if duplicate_session.returncode == 0:
        failures.append("duplicate execution sessionId must fail")

    bad_session_claim = run_attest(
        pilot_path, matrix_path, second_first["runId"], "session-002",
        fresh_session="false"
    )
    if bad_session_claim.returncode != 0:
        failures.append("attestation helper should record observed non-compliance rather than rewrite it")
    else:
        bad_attestation_path = artifact_root / second_first["runId"] / "execution-attestation.yaml"
        bad_attestation = yaml.safe_load(bad_attestation_path.read_text(encoding="utf-8"))
        if bad_attestation["spec"].get("freshSession") is not False:
            failures.append("attestation helper must preserve observed freshSession=false without normalization")

    third_first = other_firsts[1]
    duplicate_workspace = run_prepare(
        pilot_path, matrix_path, third_first["runId"],
        ws_root / "workspace-3", "workspace-001"
    )
    if duplicate_workspace.returncode == 0:
        failures.append("duplicate workspaceId must fail")

    unknown = run_prepare(
        pilot_path, matrix_path, "does-not-exist",
        ws_root / "workspace-unknown", "workspace-004"
    )
    if unknown.returncode == 0:
        failures.append("unknown runId must fail")

    existing_ws = ws_root / "already-exists"
    existing_ws.mkdir()
    non_fresh = run_prepare(
        pilot_path, matrix_path, third_first["runId"],
        existing_ws, "workspace-005"
    )
    if non_fresh.returncode == 0:
        failures.append("existing workspace must fail even when empty")

    inside_repo = run_prepare(
        pilot_path, matrix_path, third_first["runId"],
        tmp_path / "workspace-inside-repo", "workspace-006"
    )
    if inside_repo.returncode == 0:
        failures.append("workspace inside DAT repository must fail")



with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
    tmp_path = Path(tmp)
    pilot = yaml.safe_load(PILOT.read_text(encoding="utf-8"))
    matrix_path = tmp_path / "matrix.yaml"
    pilot_path = tmp_path / "pilot.yaml"
    pilot["spec"]["artifactRoot"] = "../operator-kit-outside"
    pilot["spec"]["matrixPath"] = str(matrix_path.relative_to(ROOT))
    pilot_path.write_text(yaml.safe_dump(pilot, sort_keys=False), encoding="utf-8")
    MATRIX_DATA = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
    matrix_path.write_text(yaml.safe_dump(MATRIX_DATA, sort_keys=False), encoding="utf-8")
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

with tempfile.TemporaryDirectory(dir=ROOT) as tmp, tempfile.TemporaryDirectory() as ws_tmp:
    tmp_path = Path(tmp)
    pilot = yaml.safe_load(PILOT.read_text(encoding="utf-8"))
    matrix = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
    pilot_path = tmp_path / "pilot.yaml"
    matrix_path = tmp_path / "matrix.yaml"
    pilot["spec"]["artifactRoot"] = str((tmp_path / "artifacts").relative_to(ROOT))
    pilot["spec"]["matrixPath"] = str(matrix_path.relative_to(ROOT))
    matrix["spec"]["runs"][0]["condition"] = "BROKEN"
    pilot_path.write_text(yaml.safe_dump(pilot, sort_keys=False), encoding="utf-8")
    matrix_path.write_text(yaml.safe_dump(matrix, sort_keys=False), encoding="utf-8")
    result = run_prepare(
        pilot_path,
        matrix_path,
        matrix["spec"]["runs"][0]["runId"],
        Path(ws_tmp) / "workspace-tampered",
        "workspace-tampered",
    )
    if result.returncode == 0:
        failures.append("prepare must reject a matrix that validate_pilot rejects")
    attested = run_attest(
        pilot_path,
        matrix_path,
        matrix["spec"]["runs"][0]["runId"],
        "session-tampered",
    )
    if attested.returncode == 0:
        failures.append("attestation helper must reject a matrix that validate_pilot rejects")

if failures:
    print("Operator Kit tests failed:")
    for failure in failures:
        print(f"- {failure}")
    raise SystemExit(1)

print("Operator Kit tests passed.")
