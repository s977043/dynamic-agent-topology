#!/usr/bin/env python3
"""Deterministic migration, schema, semantic and generated-view regression tests."""
import copy
import json
import tempfile
from pathlib import Path

from jsonschema import ValidationError

from learning_ledger import DOCUMENT, LEDGER, check_document, legacy_rows, load, render, validate
from harness_metrics import parse_ledger, summarize_ledger

entries = load()
data = json.loads(LEDGER.read_text(encoding='utf-8'))
assert len(entries) == 11
assert summarize_ledger(legacy_rows(entries)) == summarize_ledger(parse_ledger(DOCUMENT.read_text()))
assert [e['id'] for e in entries] == [f'L-{i:03d}' for i in range(1, 12)]
assert entries[0]['observedDates'] == []
assert entries[6]['observedDates'] == ['2026-10-08']
check_document(DOCUMENT.read_text(), entries)


def rejects(mutator):
    changed = copy.deepcopy(data)
    mutator(changed)
    try:
        validate(changed)
    except (ValueError, ValidationError):
        return
    raise AssertionError('invalid ledger accepted')


rejects(lambda d: d['entries'].append(copy.deepcopy(d['entries'][0])))
rejects(lambda d: d['entries'][0].update(state='accepted'))
rejects(lambda d: d['entries'][0].update(count=0))
rejects(lambda d: d['entries'][0].update(observedDates=['2026-02-30']))
rejects(lambda d: d['entries'][0].update(observedDates=['2026-10-09', '2026-10-08']))
rejects(lambda d: d['entries'][1].update(observedDates=['2026-10-08', '2026-10-09']))
rejects(lambda d: d['entries'][0]['evidence'].update(description=''))
rejects(lambda d: d['entries'][0]['evidence'].update(urls=['https://example.com/pull/1']))
rejects(lambda d: d['entries'][0].update(observation='broken | table'))
rejects(lambda d: d['entries'][0].update(unexpected='x'))
rejects(lambda d: d['entries'][0]['evidence'].update(description='   '))
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / 'duplicate.json'
    path.write_text('{"schemaVersion":1,"schemaVersion":1,"entries":[]}')
    try:
        load(path)
    except ValueError as error:
        assert 'duplicate JSON key' in str(error)
    else:
        raise AssertionError('duplicate JSON keys accepted')
for text in (DOCUMENT.read_text().replace('Agent guidance', 'Changed guidance'), render(entries) + render(entries)):
    try:
        check_document(text, entries)
    except ValueError:
        pass
    else:
        raise AssertionError('drift/duplicate markers accepted')
print('Learning ledger tests: PASS')
