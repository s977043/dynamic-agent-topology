#!/usr/bin/env python3
"""Validate the canonical learning ledger and its generated Markdown view."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'knowledge/learning-ledger.json'
SCHEMA = ROOT / 'schemas/learning-ledger.schema.json'
DOCUMENT = ROOT / 'docs/AGENT_HARNESS.md'
START = '<!-- learning-ledger:generated:start -->'
END = '<!-- learning-ledger:generated:end -->'


def validate(data: dict) -> list[dict]:
    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(data)
    entries = data['entries']
    ids = [entry['id'] for entry in entries]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate learning ledger ID')
    for entry in entries:
        dates = entry['observedDates']
        if dates != sorted(dates):
            raise ValueError(f"{entry['id']}: observedDates must be sorted")
        if len(dates) > entry['count']:
            raise ValueError(f"{entry['id']}: dated observations exceed count")
    return entries


def load(path: Path = LEDGER) -> list[dict]:
    return validate(json.loads(path.read_text(encoding='utf-8')))


def legacy_rows(entries: list[dict]) -> list[dict[str, str]]:
    """Keep the established harness-metrics summary and Markdown columns stable."""
    return [dict(zip(('ID', '観測', 'Evidence', '回数', '状態', '対策'),
                     (e['id'], e['observation'], e['evidence']['description'],
                      str(e['count']), e['state'], e['countermeasure']))) for e in entries]


def render(entries: list[dict]) -> str:
    lines = [START, '| ID | 観測 | Evidence | 回数 | 状態 | 対策 |',
             '| --- | --- | --- | --- | --- | --- |']
    lines.extend('| ' + ' | '.join(row.values()) + ' |' for row in legacy_rows(entries))
    return '\n'.join([*lines, END])


def check_document(text: str, entries: list[dict]) -> None:
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError('generated ledger markers must occur exactly once')
    start, end = text.index(START), text.index(END) + len(END)
    if text[start:end] != render(entries):
        raise ValueError('generated ledger differs: run python scripts/learning_ledger.py --write')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='refresh generated table only')
    args = parser.parse_args(argv)
    entries = load()
    text = DOCUMENT.read_text(encoding='utf-8')
    if args.write:
        if text.count(START) != 1 or text.count(END) != 1 or text.index(START) > text.index(END):
            raise ValueError('invalid generated ledger markers')
        text = text[:text.index(START)] + render(entries) + text[text.index(END) + len(END):]
        DOCUMENT.write_text(text, encoding='utf-8')
    check_document(text, entries)
    print(f'Learning ledger: PASS ({len(entries)} entries)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
