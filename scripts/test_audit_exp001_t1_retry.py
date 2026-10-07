#!/usr/bin/env python3
"""Regression tests for the read-only EXP-001 T1 retry static audit."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_exp001_t1_retry import (  # noqa: E402
    ARCHIVE_REL, CANONICAL_REL, RUN_ID, T0_REL, digest,
    verify_archive, verify_preparation,
)


def check(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    archive = root / ARCHIVE_REL
    canonical = root / CANONICAL_REL
    t0 = root / T0_REL
    archive.mkdir(parents=True)
    canonical.mkdir(parents=True)
    t0.mkdir(parents=True)

    expected = {}
    for name in ("STOP-REPORT.md", "evidence.txt", "event-summary.json",
                 "patch.diff", "prompt.md", "run-meta.yaml"):
        contents = f"{name}\n".encode()
        (archive / name).write_bytes(contents)
        expected[name] = digest(contents)
    (archive / "SHA256SUMS").write_text(
        "".join(f"{sha}  {name}\n" for name, sha in expected.items()),
        encoding="utf-8",
    )
    verify_archive(archive, expected)

    bad = archive / "patch.diff"
    bad.write_text("changed")
    try:
        verify_archive(archive, expected)
        raise AssertionError("tampered archive must fail")
    except ValueError as exc:
        check("hash mismatch" in str(exc), "must signal tampered archive")
    bad.write_bytes(b"patch.diff\n")

    ledger = archive / "SHA256SUMS"
    original_ledger = ledger.read_text()
    for bad_entry in (
        original_ledger + f"{'0'*64}  ../escape\n",
        original_ledger + f"{'0'*64}  patch.diff\n",
        original_ledger.replace("  prompt.md", "  other.md"),
        original_ledger.replace("  patch.diff\n", "  ../patch.diff\n"),
    ):
        ledger.write_text(bad_entry)
        try:
            verify_archive(archive, expected)
            raise AssertionError("malformed/unreviewed/duplicate entry must fail")
        except ValueError:
            pass
    ledger.write_text(original_ledger)
    verify_archive(archive, expected)

    missing = archive / "STOP-REPORT.md"
    preserved = missing.read_bytes()
    missing.unlink()
    try:
        verify_archive(archive, expected)
        raise AssertionError("missing archive artifact must fail")
    except ValueError as exc:
        check("missing" in str(exc), "missing-file check must fail closed")
    missing.write_bytes(preserved)

    symlink_file = archive / "evidence.txt"
    symlink_contents = symlink_file.read_bytes()
    symlink_file.unlink()
    symlink_file.symlink_to(archive / "STOP-REPORT.md")
    try:
        verify_archive(archive, expected)
        raise AssertionError("symlinked archive artifact must fail")
    except ValueError as exc:
        check("symlink" in str(exc), "symlink artifact must fail closed")
    symlink_file.unlink()
    symlink_file.write_bytes(symlink_contents)
    verify_archive(archive, expected)

    archived = {
        "apiVersion": "dat/v1alpha1",
        "kind": "PilotRunMetadata",
        "metadata": {
            "runId": RUN_ID,
            "blockId": "EXP-001-train-normalize-name-r01",
            "scenario": "train-normalize-name",
            "condition": "T1",
        },
        "spec": {
            "repetition": 1, "executionOrder": 2,
            "workspaceId": "old-id", "freshWorkspace": True,
            "promptSha256": expected["prompt.md"],
        },
    }
    (canonical / "prompt.md").write_bytes((archive / "prompt.md").read_bytes())
    (canonical / "run-meta.yaml").write_text(yaml.safe_dump(archived))
    (t0 / "run-meta.yaml").write_text(yaml.safe_dump({"spec": {"workspaceId": "t0-id"}}))
    verify_preparation(root, archived, expected["prompt.md"], require_new_workspace_id=False)

    try:
        verify_preparation(root, archived, expected["prompt.md"], require_new_workspace_id=True)
        raise AssertionError("post-reset should reject old workspaceId")
    except ValueError as exc:
        check("has not changed" in str(exc), "post-reset must inspect workspace ID")

    fresh = yaml.safe_load((canonical / "run-meta.yaml").read_text())
    fresh["spec"]["workspaceId"] = "new-id"
    (canonical / "run-meta.yaml").write_text(yaml.safe_dump(fresh))
    verify_preparation(root, archived, expected["prompt.md"], require_new_workspace_id=True)

    fresh["spec"]["freshWorkspace"] = False
    (canonical / "run-meta.yaml").write_text(yaml.safe_dump(fresh))
    try:
        verify_preparation(root, archived, expected["prompt.md"], require_new_workspace_id=True)
        raise AssertionError("non-workspace metadata drift must fail")
    except ValueError as exc:
        check("beyond workspaceId" in str(exc), "metadata drift must be identified")
    fresh["spec"]["freshWorkspace"] = True

    fresh["spec"]["promptSha256"] = "0" * 64
    (canonical / "run-meta.yaml").write_text(yaml.safe_dump(fresh))
    try:
        verify_preparation(root, archived, expected["prompt.md"], require_new_workspace_id=True)
        raise AssertionError("changed prepared prompt digest must fail")
    except ValueError as exc:
        check("beyond workspaceId" in str(exc), "prepared prompt hash drift must fail")
    fresh["spec"]["promptSha256"] = expected["prompt.md"]

    (canonical / "prompt.md").write_bytes(b"modified prompt")
    try:
        verify_preparation(root, archived, expected["prompt.md"], require_new_workspace_id=True)
        raise AssertionError("changed prompt bytes must fail")
    except ValueError as exc:
        check("prompt digest" in str(exc), "prompt bytes drift must fail")
    (canonical / "prompt.md").write_bytes((archive / "prompt.md").read_bytes())

    fresh["spec"]["workspaceId"] = "t0-id"
    (canonical / "run-meta.yaml").write_text(yaml.safe_dump(fresh))
    try:
        verify_preparation(root, archived, expected["prompt.md"], require_new_workspace_id=True)
        raise AssertionError("duplicate T0 workspace ID must fail")
    except ValueError as exc:
        check("duplicates accepted T0" in str(exc), "workspace ID collision must fail")

print("T1 static retry audit negative tests passed.")
