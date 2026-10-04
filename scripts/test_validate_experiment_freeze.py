#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_experiment_freeze.py"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("utf-8") + data).hexdigest()


def run(manifest: Path):
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--manifest",
            str(manifest.relative_to(ROOT)),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


failures = []
target = ROOT / "README.md"
actual = git_blob_sha(target)

with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
    manifest = Path(tmp) / "freeze.yaml"
    data = {
        "apiVersion": "dat/v1alpha1",
        "kind": "ExperimentFreeze",
        "metadata": {
            "name": "test-freeze",
            "experiment": "EXP-TEST",
            "status": "active",
            "revision": 1,
        },
        "spec": {
            "files": [
                {"path": "README.md", "gitBlobSha": actual},
            ]
        },
    }
    manifest.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    result = run(manifest)
    if result.returncode != 0:
        failures.append("matching blob identity must pass\n" + result.stdout)

    data["spec"]["files"][0]["gitBlobSha"] = "0" * 40
    manifest.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    result = run(manifest)
    if result.returncode == 0:
        failures.append("drifted blob identity must fail")

    data["spec"]["files"] = [
        {"path": "README.md", "gitBlobSha": actual},
        {"path": "README.md", "gitBlobSha": actual},
    ]
    manifest.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    result = run(manifest)
    if result.returncode == 0:
        failures.append("duplicate frozen path must fail")

    data["spec"]["files"] = [
        {"path": "does-not-exist", "gitBlobSha": "0" * 40},
    ]
    manifest.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    result = run(manifest)
    if result.returncode == 0:
        failures.append("missing frozen artifact must fail")



with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
    manifest = Path(tmp) / "freeze.yaml"
    data = {
        "apiVersion": "dat/v1alpha1",
        "kind": "ExperimentFreeze",
        "metadata": {
            "name": "test-freeze",
            "experiment": "EXP-TEST",
            "status": "activ",
            "revision": 1,
        },
        "spec": {
            "files": [
                {"path": "README.md", "gitBlobSha": actual},
            ]
        },
    }
    manifest.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    result = run(manifest)
    if result.returncode == 0:
        failures.append("unknown freeze status must fail")

with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
    manifest = Path(tmp) / "freeze.yaml"
    data = {
        "apiVersion": "dat/v1alpha1",
        "kind": "ExperimentFreeze",
        "metadata": {
            "name": "test-freeze",
            "experiment": "EXP-TEST",
            "status": "active",
            "revision": 0,
        },
        "spec": {
            "files": [
                {"path": "README.md", "gitBlobSha": actual},
            ]
        },
    }
    manifest.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    result = run(manifest)
    if result.returncode == 0:
        failures.append("freeze revision < 1 must fail")

if failures:
    print("Feature freeze validator tests failed:")
    for failure in failures:
        print(f"- {failure}")
    raise SystemExit(1)

print("Feature freeze validator tests passed.")
