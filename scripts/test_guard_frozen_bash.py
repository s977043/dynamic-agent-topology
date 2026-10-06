#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "guard_frozen_bash.py"


def decision(command):
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(ROOT)}),
        text=True,
        stdout=subprocess.PIPE,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)},
        check=True,
    )
    if not result.stdout:
        return None
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


CASES = {
    "sed -i '' s/a/b/ roles/worker.yaml": "ask",
    "echo x > experiments/EXP-001-t0-vs-t1/pilot/prompts/T0.md": "ask",
    "echo x >> ./roles/verifier.yaml": "ask",
    'echo x > "roles/worker.yaml"': "ask",
    "echo x > 'roles/verifier.yaml'": "ask",
    "git checkout main -- experiments/EXP-001-t0-vs-t1/pilot/freeze.yaml": "ask",
    "echo x 1>roles/worker.yaml": "ask",
    "git checkout -- .": "ask",
    "git restore .": "ask",
    "rm -rf fixtures": "ask",
    "cat roles/worker.yaml": None,
    "python scripts/validate_pilot.py --pilot experiments/EXP-001-t0-vs-t1/pilot/pilot.yaml 2>&1 | tail -3": None,
    "python scripts/validate_semantics.py > /tmp/out.txt": None,
    "sed -i '' s/a/b/ docs/README.md": None,
}

for raw in ("not json", json.dumps({"tool_name": "Bash", "tool_input": None})):
    result = subprocess.run([sys.executable, str(HOOK)], input=raw, text=True, capture_output=True)
    if result.returncode != 0 or result.stderr:
        print(f"FAIL: hook must fail open on {raw!r}: {result.stderr}")
        sys.exit(1)

failures = [f"{command!r}: expected {want}, got {decision(command)}" for command, want in CASES.items() if decision(command) != want]
if failures:
    for failure in failures:
        print(f"FAIL: {failure}")
    sys.exit(1)
print("Frozen Bash guard tests passed.")
