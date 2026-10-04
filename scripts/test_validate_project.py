#!/usr/bin/env python3
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_project.py"
EXAMPLE = ROOT / "examples" / "brownfield"


def run(project):
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--project",
            str(project),
            "--dat-root",
            str(ROOT),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def copy_example(tmp):
    target = Path(tmp) / "project"
    shutil.copytree(EXAMPLE, target)
    return target


failures = []

with tempfile.TemporaryDirectory() as tmp:
    project = copy_example(tmp)
    result = run(project)
    if result.returncode != 0:
        failures.append("valid brownfield example must pass\n" + result.stdout)

with tempfile.TemporaryDirectory() as tmp:
    project = copy_example(tmp)
    runtimes_path = project / ".dat" / "runtimes.yaml"
    data = yaml.safe_load(runtimes_path.read_text(encoding="utf-8"))
    data["spec"]["bindings"][0]["runtime"] = "does-not-exist"
    runtimes_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    result = run(project)
    if result.returncode == 0:
        failures.append("unknown runtime must fail")

with tempfile.TemporaryDirectory() as tmp:
    project = copy_example(tmp)
    evidence_path = project / ".dat" / "evidence.yaml"
    evidence_path.unlink()
    result = run(project)
    if result.returncode == 0:
        failures.append("A3 project without evidence must fail")

with tempfile.TemporaryDirectory() as tmp:
    project = copy_example(tmp)
    policy_path = project / ".dat" / "policy.yaml"
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    policy["spec"]["escalation"]["maxTopology"] = "T3-specialized-team"
    policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")
    result = run(project)
    if result.returncode == 0:
        failures.append("unsupported escalation maxTopology must fail")



with tempfile.TemporaryDirectory() as tmp:
    project = copy_example(tmp)
    runtimes_path = project / ".dat" / "runtimes.yaml"
    data = yaml.safe_load(runtimes_path.read_text(encoding="utf-8"))
    data["spec"]["bindings"][0]["mode"] = "generated"
    runtimes_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    result = run(project)
    if result.returncode == 0:
        failures.append("generated runtime binding must fail until compiler support exists")

if failures:
    print("External project validator tests failed:")
    for failure in failures:
        print(f"- {failure}")
    raise SystemExit(1)

print("External project validator tests passed.")
