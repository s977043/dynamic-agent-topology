#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
errors = []
EXPECTED = "python -m unittest discover -s tests"

def load(path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)

for scenario_path in sorted((ROOT / "experiments" / "EXP-001-t0-vs-t1" / "scenarios").glob("*.yaml")):
    scenario_set = load(scenario_path)
    for scenario in scenario_set["spec"]["scenarios"]:
        fixture = (ROOT / scenario["fixturePath"]).resolve()
        try:
            fixture.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"{scenario_path}: fixture escapes repository: {fixture}")
            continue

        if EXPECTED not in scenario["evidenceCommands"]:
            errors.append(f"{scenario_path}: {scenario['id']!r} must include the canonical unittest evidence command")
            continue

        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=fixture,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if completed.returncode == 0:
            errors.append(
                f"{scenario_path}: fixture {scenario['id']!r} already passes the baseline test; "
                "the bugfix experiment would no longer start from a failing state"
            )

if errors:
    print("Fixture validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("Fixture validation passed: all EXP-001 fixtures start from a failing unittest state.")
