#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
errors = []

def load(path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)

for scenario_path in sorted((ROOT / "experiments").glob("EXP-*/scenarios/*.yaml")):
    scenario_set = load(scenario_path)
    for scenario in scenario_set["spec"]["scenarios"]:
        fixture = (ROOT / scenario["fixturePath"]).resolve()
        try:
            fixture.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"{scenario_path}: fixture escapes repository: {fixture}")
            continue

        any_failed = False
        for command in scenario["evidenceCommands"]:
            completed = subprocess.run(
                command,
                cwd=fixture,
                shell=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            if completed.returncode != 0:
                any_failed = True

        if not any_failed:
            errors.append(
                f"{scenario_path}: fixture {scenario['id']!r} already passes all evidence commands; "
                "the bugfix experiment would no longer have a failing baseline"
            )

if errors:
    print("Fixture validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("Fixture validation passed: every experiment fixture has at least one failing evidence command.")
