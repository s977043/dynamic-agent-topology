#!/usr/bin/env python3
"""Ask before Bash commands that look like they write EXP-001 frozen files.

Edit/Write tool calls are covered by ask rules in .claude/settings.json.
This heuristic only adds a prompt; CI validate_experiment_freeze.py stays the guard.
"""
import json
import os
from pathlib import Path
import re
import sys


MANIFEST = "experiments/EXP-001-t0-vs-t1/pilot/freeze.yaml"
REDIRECT_TARGET = re.compile(r"(?<![0-9&])>>?\s*([^\s;&|]+)")
WRITE_PATTERN = re.compile(
    r"(\btee\b|\bsed\s+-i|\bperl\s+-[a-z]*i|\bmv\b|\bcp\b|\brm\b|\btouch\b|\btruncate\b"
    r"|\bgit\s+(checkout|restore|apply|am|mv|rm)\b|\bpatch\b|\bwrite_text\b|\bopen\(.*['\"][wa])"
)


def guarded_paths(root):
    manifest = root / MANIFEST
    paths = re.findall(r"^\s*-\s*path:\s*(\S+)\s*$", manifest.read_text(encoding="utf-8"), re.M)
    return [MANIFEST, *paths]


def main():
    event = json.load(sys.stdin)
    if event.get("tool_name") != "Bash":
        return 0
    command = event.get("tool_input", {}).get("command", "")
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR", event.get("cwd", ".")))
    if not (root / MANIFEST).exists():
        return 0
    guarded = guarded_paths(root)
    targets = [target.strip("\"'") for target in REDIRECT_TARGET.findall(command)]
    hits = [p for p in guarded if any(t.endswith(p) for t in targets)]
    if WRITE_PATTERN.search(command):
        hits += [p for p in guarded if p in command and p not in hits]
    if not hits:
        return 0
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": "Command may modify EXP-001 frozen files: " + ", ".join(hits),
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
