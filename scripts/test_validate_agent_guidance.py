#!/usr/bin/env python3
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_agent_guidance.py"


def run(root):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def copy_repo(tmp):
    target = Path(tmp) / "repo"
    shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__"))
    return target


def edit_settings(repo, change):
    path = repo / ".claude" / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data["permissions"]["ask"])
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


failures = []

with tempfile.TemporaryDirectory() as tmp:
    result = run(copy_repo(tmp))
    if result.returncode != 0:
        failures.append("current repository guidance must pass\n" + result.stdout)

with tempfile.TemporaryDirectory() as tmp:
    repo = copy_repo(tmp)
    agents = repo / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8") + "\nSee `docs/DOES_NOT_EXIST.md`.\n", encoding="utf-8")
    result = run(repo)
    if result.returncode == 0 or "DOES_NOT_EXIST" not in result.stdout:
        failures.append("missing referenced path must fail")

with tempfile.TemporaryDirectory() as tmp:
    repo = copy_repo(tmp)
    edit_settings(repo, lambda ask: ask.remove("Edit(/roles/worker.yaml)"))
    result = run(repo)
    if result.returncode == 0 or "roles/worker.yaml" not in result.stdout:
        failures.append("frozen file without ask rule must fail")

with tempfile.TemporaryDirectory() as tmp:
    repo = copy_repo(tmp)
    edit_settings(repo, lambda ask: ask.append("Edit(/experiments/EXP-001-t0-vs-t1/pilot/**)"))
    result = run(repo)
    if result.returncode == 0 or "non-frozen file" not in result.stdout:
        failures.append("ask rule covering non-frozen files must fail")

if failures:
    for failure in failures:
        print(f"FAIL: {failure}")
    sys.exit(1)
print("Agent guidance validator tests passed.")
