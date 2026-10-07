#!/usr/bin/env python3
"""Read-only static audit for the reviewed EXP-001 T1 r01 one-time retry.

This is NOT authorization to invoke the model or proof of sandbox readiness.
The operator must follow docs/EXP-001_RETRY_T1_R01.md and Issue #15.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "EXP-001-train-normalize-name-r01-T1"
T0_ID = "EXP-001-train-normalize-name-r01-T0"
ATTEMPT_ID = "01a1132a-1de0-70d2-b810-c500b79430c9"
ARCHIVE_REL = (
    Path("experiments/EXP-001-t0-vs-t1/runs/infrastructure-failures")
    / RUN_ID / ATTEMPT_ID
)
CANONICAL_REL = Path("experiments/EXP-001-t0-vs-t1/runs/pilot-codex") / RUN_ID
T0_REL = Path("experiments/EXP-001-t0-vs-t1/runs/pilot-codex") / T0_ID

# Reviewed immutable evidence in docs/EXP-001_RETRY_T1_R01.md (PR #100).
REVIEWED_SHA256 = {
    "STOP-REPORT.md": "622130cffc631295f97033b858c46bc7b206011f3aa1ad81a6c728a989e10cbd",
    "evidence.txt": "3fc80c177276d9d5fe9874f3856326b629fc9ad1954348335d86617ed6ed6a71",
    "event-summary.json": "b6f542d3f9bbcc7a6e0ffae99b919cb0429764380f1cb20b60fdebcad32b0fbf",
    "patch.diff": "a204da931aaf8dc68627a9b29dd74eaf2e0335c4f63830016d37378727f71c00",
    "prompt.md": "d98fdfb3c56ecc5659466d8b4ba607bb94e77c2a7d74360175b9657b6b93bf86",
    "run-meta.yaml": "2621205e473c0cd1f3eb6c75aa023be70e02053ba6532cceb03e6e50a9fc5ca6",
}


def require_regular(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"required regular file missing or symlink: {path}")
    return path.read_bytes()


def digest(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def verify_archive(archive: Path, expected: dict[str, str]) -> None:
    """Compare review-pinned digests, SHA256SUMS ledger and actual archive bytes."""
    ledger = require_regular(archive / "SHA256SUMS").decode("utf-8")
    actual: dict[str, str] = {}
    for line in ledger.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  ([*]?[^/\x00]+)", line)
        if not match:
            raise ValueError(f"malformed SHA256SUMS entry: {line!r}")
        sha, name = match.groups()
        name = name.removeprefix("*")
        if name in actual:
            raise ValueError(f"duplicate SHA256SUMS entry: {name}")
        if name not in expected or name in {".", ".."}:
            raise ValueError(f"unreviewed SHA256SUMS entry: {name!r}")
        actual[name] = sha
    if actual != expected:
        raise ValueError("archive SHA256SUMS differs from reviewed six-file ledger")
    for name, sha in expected.items():
        if digest(require_regular(archive / name)) != sha:
            raise ValueError(f"reviewed archive file hash mismatch: {name}")


def verify_preparation(
    root: Path,
    archive_meta: dict,
    expected_prompt_sha: str,
    *,
    require_new_workspace_id: bool,
) -> None:
    """Check static preparation only; this never attests to an actual run."""
    canonical = root / CANONICAL_REL
    archive = root / ARCHIVE_REL
    prompt_bytes = require_regular(canonical / "prompt.md")
    if digest(prompt_bytes) != expected_prompt_sha:
        raise ValueError("canonical T1 prompt digest differs from reviewed prompt")
    if prompt_bytes != require_regular(archive / "prompt.md"):
        raise ValueError("canonical T1 prompt bytes differ from archived prompt")

    current = yaml.safe_load(require_regular(canonical / "run-meta.yaml"))
    if current.get("apiVersion") != "dat/v1alpha1" or current.get("kind") != "PilotRunMetadata":
        raise ValueError("canonical preparation metadata kind/version mismatch")
    if current.get("metadata") != archive_meta.get("metadata"):
        raise ValueError("canonical preparation identity differs from archived matrix slot")
    identity = current.get("metadata", {})
    if identity.get("runId") != RUN_ID or identity.get("condition") != "T1":
        raise ValueError("canonical preparation metadata points to wrong run")
    archived_spec = archive_meta.get("spec", {})
    current_spec = current.get("spec", {})
    workspace_id = current_spec.get("workspaceId")
    if not isinstance(workspace_id, str) or not workspace_id:
        raise ValueError("canonical workspaceId is missing")
    if {
        k: v for k, v in current_spec.items() if k != "workspaceId"
    } != {
        k: v for k, v in archived_spec.items() if k != "workspaceId"
    }:
        raise ValueError("canonical preparation metadata changed beyond workspaceId")
    if current_spec.get("promptSha256") != expected_prompt_sha:
        raise ValueError("run-meta promptSha256 differs from reviewed prompt")
    if require_new_workspace_id and workspace_id == archived_spec.get("workspaceId"):
        raise ValueError("post-reset workspaceId has not changed from the archived attempt")
    t0 = yaml.safe_load(require_regular(root / T0_REL / "run-meta.yaml"))
    if workspace_id == t0.get("spec", {}).get("workspaceId"):
        raise ValueError("T1 workspaceId duplicates accepted T0")


def validate_existing_gates(root: Path) -> None:
    checks = [
        [sys.executable, "scripts/validate_experiment_freeze.py"],
        [
            sys.executable,
            "scripts/validate_pilot.py",
            "--pilot", "experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml",
            "--matrix", "experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml",
            "--run-id", T0_ID,
        ],
    ]
    for check in checks:
        completed = subprocess.run(check, cwd=root, capture_output=True, text=True, check=False)
        if completed.returncode:
            raise ValueError(
                f"existing gate failed ({check[1]}, exit={completed.returncode}): "
                + (completed.stderr or completed.stdout).strip()[:800]
            )
    freeze = yaml.safe_load(require_regular(
        root / "experiments/EXP-001-t0-vs-t1/pilot/freeze.yaml"
    ))
    if freeze.get("metadata", {}).get("status") != "active" or freeze.get("metadata", {}).get("revision") != 3:
        raise ValueError("this one-time retry requires active Feature Freeze revision 3")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-new-workspace-id",
        action="store_true",
        help="Use AFTER approved reset/reprepare; assert workspace ID changed (not workspace existence).",
    )
    args = parser.parse_args()
    try:
        archive = ROOT / ARCHIVE_REL
        verify_archive(archive, REVIEWED_SHA256)
        archive_meta = yaml.safe_load(require_regular(archive / "run-meta.yaml"))
        verify_preparation(
            ROOT,
            archive_meta,
            REVIEWED_SHA256["prompt.md"],
            require_new_workspace_id=args.require_new_workspace_id,
        )
        validate_existing_gates(ROOT)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"EXP-001 T1 static preflight: FAIL — {exc}", file=sys.stderr)
        return 1
    print("EXP-001 T1 static preflight: PASS (reviewed archive, prompt, metadata, freeze, T0)")
    print("NOT VERIFIED: external workspace/fixture, native python in normal sandbox,")
    print("sandbox write allow/deny, fresh Codex session, independent Verifier, retry allowance.")
    print("No Codex model invocation occurred. Follow docs/EXP-001_RETRY_T1_R01.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
