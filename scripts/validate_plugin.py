#!/usr/bin/env python3
"""Check the plugin manifests and skills/ that distribute DAT.

- .claude-plugin/plugin.json, .claude-plugin/marketplace.json and
  .codex-plugin/plugin.json are JSON objects and share name, version and skills
- the manifest version equals CITATION.cff version (the DAT spec version that
  dat-observe records as metadata.datVersion)
- the marketplace entry's source points to a plugin root holding
  .claude-plugin/plugin.json, and its version (if any) matches the manifest
- every <skills>/<name>/SKILL.md, with <skills> taken from the manifest, has
  YAML frontmatter whose name equals <name> and a non-empty description
- links written as `](relative/path)` in SKILL.md resolve to existing files;
  other link syntaxes are not checked
Malformed inputs are reported as NG lines, never as a traceback.
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
    rel = path.relative_to(ROOT)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"{rel}: {exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{rel}: top level must be an object")
        return {}
    return data


def citation_version(errors: list[str]) -> str | None:
    try:
        data = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        errors.append(f"CITATION.cff: {exc}")
        return None
    if not isinstance(data, dict) or "version" not in data:
        errors.append("CITATION.cff: version is missing")
        return None
    return str(data["version"])


def check_manifests(errors: list[str]) -> dict:
    claude = load_json(ROOT / ".claude-plugin/plugin.json", errors)
    codex = load_json(ROOT / ".codex-plugin/plugin.json", errors)
    market = load_json(ROOT / ".claude-plugin/marketplace.json", errors)
    plugins = market.get("plugins")
    if not isinstance(plugins, list) or not all(isinstance(p, dict) for p in plugins):
        errors.append("marketplace.json: plugins must be an array of objects")
        plugins = []
    entries = [p for p in plugins if p.get("name") == claude.get("name")]
    if not entries:
        errors.append("marketplace.json: no plugin entry named as .claude-plugin/plugin.json")
    for entry in entries:
        source = entry.get("source")
        if not isinstance(source, str) or not (ROOT / source / ".claude-plugin/plugin.json").is_file():
            errors.append(f"marketplace.json: source does not point to a plugin root: {source}")
        if "version" in entry and entry["version"] != claude.get("version"):
            errors.append("marketplace.json: entry version differs from .claude-plugin/plugin.json")
    version = citation_version(errors)
    if version is not None and version != claude.get("version"):
        errors.append("plugin.json version differs from CITATION.cff version")
    for key in ("name", "version", "skills"):
        if claude.get(key) != codex.get(key):
            errors.append(f"plugin.json {key} differs between .claude-plugin and .codex-plugin")
    return claude


def check_skills(manifest: dict, errors: list[str]) -> None:
    value = manifest.get("skills")
    skills_dir = ROOT / value if isinstance(value, str) else None
    if skills_dir is None or not skills_dir.is_dir():
        errors.append(f"plugin.json skills does not point to a directory: {value}")
        return
    skill_files = sorted(skills_dir.glob("*/SKILL.md"))
    if not skill_files:
        errors.append(f"{value}: no SKILL.md found")
    for path in skill_files:
        rel = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{rel}: {exc}")
            continue
        parts = text.split("---", 2)
        if not text.startswith("---") or len(parts) < 3:
            errors.append(f"{rel}: missing frontmatter")
            continue
        try:
            meta = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError as exc:
            errors.append(f"{rel}: invalid frontmatter YAML: {exc}")
            continue
        if not isinstance(meta, dict):
            errors.append(f"{rel}: frontmatter must be a mapping")
            continue
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
    manifest = check_manifests(errors)
    check_skills(manifest, errors)
    for error in errors:
        print(f"NG {error}")
    if errors:
        return 1
    print("OK plugin manifests and skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
