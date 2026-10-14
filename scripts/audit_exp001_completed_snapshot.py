#!/usr/bin/env python3
"""Verify EXP-001's reviewed revision-3 snapshot against a fixed reference.

This reference was copied from main 55c47011116cf3e792df808135039ce21e05fd34,
where the original revision-3 snapshot had already passed experiment review.
It is intentionally independent of mutable freeze.yaml content. This CI guard
detects accidental/concurrent drift; it is NOT a malicious-maintainer boundary.
Changes to this code/workflow and freeze status require Human approval.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

import yaml

from validate_experiment_freeze import git_blob_sha

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "experiments/EXP-001-t0-vs-t1/pilot/freeze.yaml"
ORIGINAL_REVISION = 3
ORIGINAL_BASE_COMMIT = "f172eb1e273af736ec1ecbd72f8b4c8874739808"
ORIGINAL_BLOBS = {
    "experiments/EXP-001-t0-vs-t1/experiment.yaml": "6de1f902424fe4b386b1b2ab64986a291af32b1c",
    "experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml": "7f92c677d81ebf293593dbdbaefcf05a2b11a323",
    "experiments/EXP-001-t0-vs-t1/pilot/run-matrix.yaml": "313419d18c79f144e51fa4e80829f91aac567110",
    "experiments/EXP-001-t0-vs-t1/pilot/prompts/BASE.md": "0f7168872adb70e7917976606b051283880d7e2a",
    "experiments/EXP-001-t0-vs-t1/pilot/prompts/T0.md": "f4116986555ccc0e3ab3f1cb9cb1d2b758a19c22",
    "experiments/EXP-001-t0-vs-t1/pilot/prompts/T1.md": "980e3a55c827ae206c775bcf5169206bfca5d8e0",
    "experiments/EXP-001-t0-vs-t1/scenarios/train.yaml": "475638b3287d80a1b659476e5b2d1e7de3c672e9",
    "experiments/EXP-001-t0-vs-t1/scenarios/test.yaml": "6b08881de0fc40131b262eefab4b427b4513c21a",
    "experiments/EXP-001-t0-vs-t1/scenarios/regression.yaml": "dd23bb2c8b41d7d2ba6c6cc91a3fc88f7770dec9",
    "fixtures/exp-001/train/normalize-name/app.py": "fd376b2ba74662a4732dee77bbc24ce64502c970",
    "fixtures/exp-001/train/normalize-name/tests/test_app.py": "3a22d58cd11fda0005813276af345e1b7426d13e",
    "fixtures/exp-001/test/clamp-boundaries/app.py": "c5d373ebc3817069cb26f02e0d188c2fda1aa9fb",
    "fixtures/exp-001/test/clamp-boundaries/tests/test_app.py": "a65bbd5e802e08e35091cb760d26a212d850bd87",
    "fixtures/exp-001/regression/safe-divide/app.py": "62c1b16bf9c910a53a9e34c80076dabc12ffc109",
    "fixtures/exp-001/regression/safe-divide/tests/test_app.py": "a992829a40fbcde2c9436366d2e589ff3c6e44bb",
    "topologies/canonical/T0_single_agent.yaml": "d958f4b0d62c558d338afd292499c0c94901fb64",
    "topologies/canonical/T1_worker_verifier.yaml": "1697a8c1407254d16903ce1eb352fa1cb6f2e28b",
    "roles/worker.yaml": "c37e93419edb1281618ab15fd51e9cb8eb4526d7",
    "roles/verifier.yaml": "8ff65aff6d1d66c082073f9c22791bf175944c8a",
    "schemas/experiment.schema.json": "0358267ebcf390e6dc680cdec6d74fc44fdb4fd2",
    "schemas/scenario-set.schema.json": "5d375a915c7b1c0f8b28b424591cd45be3bb1e00",
    "schemas/pilot.schema.json": "30ae5713ffef8dd9c4cce75d9dcdf2305f7373a0",
    "schemas/pilot-run-meta.schema.json": "637721420375d70feab1e7498563c03ed7eeab48",
    "schemas/pilot-execution-attestation.schema.json": "acb234872454346492ca61aca3928408f81d2f8c",
    "schemas/execution-trace.schema.json": "ee224362edb0ef1073f1e96a696f4b44b76cf9b3",
    "schemas/evaluation.schema.json": "05ac3a4307924389fa292dafb9f892541ec6e6d9",
    "scripts/generate_pilot_matrix.py": "101031715a92bc573e2247c85ee8498725b1b579",
    "scripts/prepare_pilot_run.py": "97287e905fc1ddec06371cadf385b8905b664d5d",
    "scripts/attest_pilot_run.py": "6350f647172e9ed2c41440c5de4cc5e6502e2da1",
    "scripts/validate_pilot.py": "6f2221e2ae9024ac8d20087a304102ef5b616772",
    "scripts/pilot_status.py": "8d7253364ebd0d4c896aa0ac44e6cbc5a51cbd1c",
    "scripts/summarize_experiment.py": "4817e99ff9385b8987b9f5df4517be9b510ce74f",
    "scripts/validate_experiment_freeze.py": "5584dc7426bf1cc49e3712315bf39a2fe74df8cb"
}


def audit_snapshot(
    manifest: dict,
    root: Path = ROOT,
    blob_sha: Callable[[Path], str] = git_blob_sha,
) -> list[str]:
    """Return all observed errors; missing/invalid evidence never becomes PASS."""
    errors: list[str] = []
    if not isinstance(manifest, dict) or manifest.get("kind") != "ExperimentFreeze":
        return ["invalid ExperimentFreeze manifest"]
    metadata = manifest.get("metadata")
    spec = manifest.get("spec")
    if not isinstance(metadata, dict) or not isinstance(spec, dict):
        return ["invalid manifest metadata/spec"]
    if metadata.get("status") != "completed":
        errors.append("completed snapshot audit requires status=completed")
    if metadata.get("revision") != ORIGINAL_REVISION:
        errors.append("revision differs from reviewed revision-3 snapshot")
    if spec.get("baselineCommit") != ORIGINAL_BASE_COMMIT:
        errors.append("baselineCommit changed from reviewed snapshot")
    files = spec.get("files")
    if not isinstance(files, list) or len(files) != len(ORIGINAL_BLOBS):
        return errors + [f"expected {len(ORIGINAL_BLOBS)} frozen file entries"]
    seen: set[str] = set()
    for item in files:
        if not isinstance(item, dict):
            errors.append("malformed file item")
            continue
        value, claimed = item.get("path"), item.get("gitBlobSha")
        if not isinstance(value, str) or not isinstance(claimed, str):
            errors.append("missing/invalid file path or gitBlobSha")
            continue
        if value in seen:
            errors.append(f"duplicate frozen path: {value}")
            continue
        seen.add(value)
        original = ORIGINAL_BLOBS.get(value)
        if original is None:
            errors.append(f"unexpected frozen path: {value}")
            continue
        if claimed != original:
            errors.append(f"reviewed blob identity replaced in manifest: {value}")
        path = root / value
        if Path(value).is_absolute() or ".." in Path(value).parts or path.is_symlink():
            errors.append(f"invalid frozen file path: {value}")
            continue
        if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            errors.append(f"missing/outside frozen file: {value}")
            continue
        try:
            actual = blob_sha(path)
        except OSError as exc:
            errors.append(f"unreadable frozen file {value}: {exc}")
            continue
        if actual != original:
            errors.append(f"frozen file differs from reviewed original: {value}")
    if seen != set(ORIGINAL_BLOBS):
        errors.append("reviewed frozen path set changed")
    return errors


def main() -> int:
    try:
        manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"EXP-001 completed snapshot audit failed to read manifest: {exc}", file=sys.stderr)
        return 1
    errors = audit_snapshot(manifest)
    if errors:
        print("EXP-001 reviewed revision-3 snapshot mismatch:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"EXP-001 reviewed original snapshot: {len(ORIGINAL_BLOBS)} blobs intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
