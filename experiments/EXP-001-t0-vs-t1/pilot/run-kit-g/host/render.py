#!/usr/bin/env python3
"""Render a run-kit-g template. Only the Run-specific placeholders are substituted.

usage: render.py <template> <output> KEY=VALUE ...
Every placeholder in the template must be given, every given key must occur, and each
value must match its allow-list pattern (so the value cannot change shell syntax).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RULES = {
    "PROMPT_SHA256": r"[0-9a-f]{64}",
    "RAN": r"[1-9][0-9]*",
    "FAILED_LINE": r"FAILED \((failures|errors)=[1-9][0-9]*(, (failures|errors)=[1-9][0-9]*)?\)",
    "KIND": r"FAIL|ERROR",
    "TEST": r"test_[A-Za-z0-9_]+",
    "ASSERT_TYPE": r"[A-Za-z]+Error",
    "ASSERT_MSG": r"[^\"$`\\\n]+",
}


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    template, output = Path(argv[0]), Path(argv[1])
    values: dict[str, str] = {}
    for item in argv[2:]:
        key, sep, value = item.partition("=")
        if not sep or key not in RULES or key in values:
            print(f"STOP: bad or duplicate parameter {key!r}", file=sys.stderr)
            return 1
        if not re.fullmatch(RULES[key], value):
            print(f"STOP: value for {key} does not match {RULES[key]}", file=sys.stderr)
            return 1
        values[key] = value
    text = template.read_text(encoding="utf-8")
    used = set(re.findall(r"@@([A-Z0-9_]+)@@", text))
    if used != set(values):
        print(f"STOP: placeholders {sorted(used)} != parameters {sorted(values)}", file=sys.stderr)
        return 1
    for key, value in values.items():
        text = text.replace(f"@@{key}@@", value)
    if "@@" in text:
        print("STOP: unresolved placeholder", file=sys.stderr)
        return 1
    if output.exists():
        print(f"STOP: {output} already exists", file=sys.stderr)
        return 1
    output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
