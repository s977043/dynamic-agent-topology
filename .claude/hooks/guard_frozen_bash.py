#!/usr/bin/env python3
"""Ask before Bash commands that look like they write EXP-001 frozen files.

Edit/Write tool calls are covered by ask rules in .claude/settings.json.
This heuristic only adds a prompt; CI validate_experiment_freeze.py stays the guard.
Any internal error fails open so the hook never blocks or tracebacks.
Known gap: paths relative to a changed directory (`cd dir && ...`) are not resolved.
"""
import json
import os
from pathlib import Path
import re
import shlex
import sys


MANIFEST = "experiments/EXP-001-t0-vs-t1/pilot/freeze.yaml"
REDIRECT_TARGET = re.compile(r">>?\s*([^\s;&|]+)")
WRITE_PATTERN = re.compile(
    r"(\btee\b|\bsed\s+-i|\bperl\s+-[a-z]*i|\bmv\b|\bcp\b|\brm\b|\btouch\b|\btruncate\b"
    r"|\bgit\s+(checkout|restore|apply|am|mv|rm)\b|\bpatch\b|\bwrite_text\b|\bopen\(.*['\"][wa])"
)


def guarded_paths(root):
    manifest = root / MANIFEST
    paths = re.findall(r"^\s*-\s*path:\s*(\S+)\s*$", manifest.read_text(encoding="utf-8"), re.M)
    return [MANIFEST, *paths]


def write_operands(command):
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    for token in tokens:
        token = token.strip("\"'")
        if not token:
            continue
        while token.startswith("./"):
            token = token[2:]
        yield token.rstrip("/") or "."


def names_guarded(operand, path):
    return operand == "." or path == operand or path.startswith(operand + "/")


def check(event):
    if event.get("tool_name") != "Bash":
        return None
    command = (event.get("tool_input") or {}).get("command") or ""
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR", event.get("cwd", ".")))
    if not (root / MANIFEST).exists():
        return None
    guarded = guarded_paths(root)
    targets = [target.strip("\"'") for target in REDIRECT_TARGET.findall(command)]
    hits = [p for p in guarded if any(t.endswith(p) for t in targets)]
    if WRITE_PATTERN.search(command):
        operands = list(write_operands(command))
        hits += [
            p for p in guarded
            if p not in hits and (p in command or any(names_guarded(o, p) for o in operands))
        ]
    return hits


def main():
    try:
        hits = check(json.load(sys.stdin))
    except Exception:
        return 0
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
