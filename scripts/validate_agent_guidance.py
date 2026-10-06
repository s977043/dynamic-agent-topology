#!/usr/bin/env python3
"""Detect drift between agent guidance files and the repository."""
import argparse
import fnmatch
import json
from pathlib import Path
import re
import sys

import yaml


GUIDANCE_FILES = ("AGENTS.md", "CLAUDE.md")
FREEZE_MANIFEST = "experiments/EXP-001-t0-vs-t1/pilot/freeze.yaml"
EXPERIMENT_DIR = "experiments/EXP-001-t0-vs-t1"
CLAUDE_SETTINGS = ".claude/settings.json"
PATH_TOKEN = re.compile(r"`([A-Za-z0-9_.\-/]+)`")
GUARDED_TOOLS = ("Edit", "Write")


def referenced_paths(text):
    for token in PATH_TOKEN.findall(text):
        if "/" in token or re.search(r"\.(md|py|ya?ml|json|toml)$", token):
            yield token


def path_exists(root, token):
    if "/" not in token:
        return any(".git" not in p.parts for p in root.rglob(token))
    return (root / token).exists() or (root / EXPERIMENT_DIR / token).exists()


def guarded_paths(root):
    """Frozen files plus the manifest itself, whose edits are freeze revisions."""
    manifest = yaml.safe_load((root / FREEZE_MANIFEST).read_text(encoding="utf-8"))
    files = manifest["spec"]["files"] if "spec" in manifest else manifest["files"]
    return sorted({FREEZE_MANIFEST, *(f["path"] if isinstance(f, dict) else f for f in files)})


def ask_patterns(root, tool):
    settings = json.loads((root / CLAUDE_SETTINGS).read_text(encoding="utf-8"))
    prefix = f"{tool}(/"
    return [
        rule[len(prefix):-1]
        for rule in settings.get("permissions", {}).get("ask", [])
        if rule.startswith(prefix) and rule.endswith(")")
    ]


def validate(root):
    errors = []
    for name in GUIDANCE_FILES:
        path = root / name
        if not path.exists():
            continue
        for token in sorted(set(referenced_paths(path.read_text(encoding="utf-8")))):
            if not path_exists(root, token):
                errors.append(f"{name}: referenced path does not exist: {token}")

    frozen = guarded_paths(root)
    for tool in GUARDED_TOOLS:
        patterns = ask_patterns(root, tool)
        for frozen_path in frozen:
            if not any(fnmatch.fnmatch(frozen_path, p) for p in patterns):
                errors.append(f"{CLAUDE_SETTINGS}: frozen file has no {tool} ask rule: {frozen_path}")
        for pattern in patterns:
            matched = [p for p in frozen if fnmatch.fnmatch(p, pattern)]
            if not matched:
                errors.append(f"{CLAUDE_SETTINGS}: {tool} ask rule matches no frozen file: {pattern}")
            unfrozen = [
                str(p.relative_to(root))
                for p in root.glob(pattern)
                if p.is_file() and "__pycache__" not in p.parts and str(p.relative_to(root)) not in frozen
            ]
            for extra in sorted(unfrozen):
                errors.append(f"{CLAUDE_SETTINGS}: {tool} ask rule {pattern} also covers non-frozen file: {extra}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    errors = validate(Path(args.root).resolve())
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("Agent guidance is consistent with the repository.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
