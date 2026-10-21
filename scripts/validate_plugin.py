#!/usr/bin/env python3
"""Check the plugin manifests and skills/ that distribute DAT.

- .claude-plugin/plugin.json, .claude-plugin/marketplace.json and
  .codex-plugin/plugin.json parse as JSON and share name and version
- every skills/<name>/SKILL.md has frontmatter whose name equals <name> and a
  non-empty description
- relative links in SKILL.md resolve to existing files
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


def load_json(path: Path, errors: list[str]) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: {exc}")
        return {}


def check_manifests(errors: list[str]) -> None:
    claude = load_json(ROOT / ".claude-plugin/plugin.json", errors)
    codex = load_json(ROOT / ".codex-plugin/plugin.json", errors)
    market = load_json(ROOT / ".claude-plugin/marketplace.json", errors)
    entries = [p for p in market.get("plugins", []) if p.get("name") == claude.get("name")]
    if not entries:
        errors.append("marketplace.json: no plugin entry named as .claude-plugin/plugin.json")
    for key in ("name", "version", "skills"):
        if claude.get(key) != codex.get(key):
            errors.append(f"plugin.json {key} differs between .claude-plugin and .codex-plugin")
    skills = ROOT / str(claude.get("skills", ""))
    if not skills.is_dir():
        errors.append(f"plugin.json skills does not point to a directory: {claude.get('skills')}")


def check_skills(errors: list[str]) -> None:
    skill_files = sorted((ROOT / "skills").glob("*/SKILL.md"))
    if not skill_files:
        errors.append("skills/: no SKILL.md found")
    for path in skill_files:
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        if not text.startswith("---") or len(parts) < 3:
            errors.append(f"{rel}: missing frontmatter")
            continue
        meta = yaml.safe_load(parts[1]) or {}
        if meta.get("name") != path.parent.name:
            errors.append(f"{rel}: frontmatter name must be {path.parent.name}")
        if not str(meta.get("description") or "").strip():
            errors.append(f"{rel}: frontmatter description is empty")
        for target in LINK.findall(parts[2]):
            if "://" in target:
                continue
            if not (path.parent / target).exists():
                errors.append(f"{rel}: broken link {target}")


def main() -> int:
    errors: list[str] = []
    check_manifests(errors)
    check_skills(errors)
    for error in errors:
        print(f"NG {error}")
    if errors:
        return 1
    print("OK plugin manifests and skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
