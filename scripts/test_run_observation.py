#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_observation.py"
FIXTURES = ROOT / "fixtures" / "run-observation"

failures = []


def run(*args, env=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )


def variant(source, workdir, observation_id, project):
    record = yaml.safe_load((FIXTURES / "valid" / source).read_text(encoding="utf-8"))
    record["metadata"]["observationId"] = observation_id
    record["metadata"]["project"] = project
    path = workdir / f"{observation_id}.yaml"
    path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
    return path


def expect(result, code, text, label):
    if result.returncode != code or text not in result.stdout:
        failures.append(f"{label}: expected exit {code} with {text!r}, got {result.returncode}\n{result.stdout}")


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    store = tmp / "store"
    work = tmp / "work"
    work.mkdir()

    first = FIXTURES / "valid" / "t1-separate-session-verifier.yaml"
    result = run("save", str(first), "--store", str(store))
    expect(result, 0, "OK obs-0001", "save valid record")
    if not (store / "project-a" / "obs-0001.yaml").is_file():
        failures.append("save must write <store>/<project>/<observationId>.yaml")

    expect(run("save", str(first), "--store", str(store)), 1, "already recorded", "duplicate observationId")

    unknown = variant("interrupted-no-merge-unknown-values.yaml", work, "obs-0002", "project-a")
    result = run("save", str(unknown), "--store", str(store))
    expect(result, 0, "rework.count", "save reports unknown fields")

    invalid = FIXTURES / "invalid" / "redaction-absolute-path-users.yaml"
    result = run("save", str(invalid), "--store", str(store))
    expect(result, 1, "NG", "invalid record")
    if any(store.glob("*/redaction*")) or len(list(store.glob("*/*.yaml"))) != 2:
        failures.append("invalid record must not be stored")

    expect(run("save", str(first), "--store", str(ROOT / "tmp-store")), 2, "outside the DAT repository", "store inside repo")
    if (ROOT / "tmp-store").exists():
        failures.append("refused store must not be created")

    env = {k: v for k, v in os.environ.items() if k != "DAT_OBSERVATION_STORE"}
    expect(run("sum", env=env), 2, "DAT_OBSERVATION_STORE", "missing store")

    other = variant("t0-no-delegation-advisory-only.yaml", work, "obs-0003", "project-b")
    env["DAT_OBSERVATION_STORE"] = str(store)
    expect(run("save", str(other), env=env), 0, "OK obs-0003", "store from environment")

    shutil.copyfile(invalid, store / "project-a" / "obs-bad.yaml")
    result = run("sum", "--store", str(store))
    for text in (
        "observations: 3",
        "skipped invalid: project-a/obs-bad.yaml",
        "| project-a | T1 | 2 |",
        "| project-b | T0 | 1 |",
        "| T1 | completed | 1 |",
        "| T1 | interrupted | 1 |",
        "| T1 | 1/2 | 0 |",
        "| T0 | 1/1 | 0 |",
        "not evidence that a topology is better",
    ):
        expect(result, 0, text, "sum output")

if failures:
    print("RunObservation CLI tests failed:")
    for failure in failures:
        print(f"- {failure}")
    sys.exit(1)

print("RunObservation CLI tests passed.")
