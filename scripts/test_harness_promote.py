#!/usr/bin/env python3
"""Boundary and publishing regression checks without network writes."""
import copy
import json
from pathlib import Path
from harness_promote import PATH, PREFIX, SafeFailure, candidates, publish, render, text

REPO = 's977043/dynamic-agent-topology'
data = json.loads((Path(__file__).resolve().parents[1] / 'knowledge/learning-ledger.json').read_text())
original = copy.deepcopy(data)
entries = candidates(data, REPO)
assert [e['id'] for e in entries] == ['L-009', 'L-010']
assert data == original
assert render(entries) == render(list(entries))
assert '@' not in text('<script>@user [x](url)') and '<script>' not in text('<script>')
assert 'main SHA' not in render(entries)
for mutate in ('no-url', 'foreign', 'one', 'promoted', 'rejected'):
    changed = copy.deepcopy(data)
    e = changed['entries'][8]
    if mutate == 'no-url': e['evidence']['urls'] = []
    if mutate == 'foreign': e['evidence']['urls'] = ['https://github.com/other/repo/pull/1']
    if mutate == 'one': e['count'] = 1
    if mutate in ('promoted', 'rejected'): e['state'] = mutate
    try:
        selected = candidates(changed, REPO)
        assert mutate in ('one', 'promoted', 'rejected') and e not in selected
    except SafeFailure:
        assert mutate in ('no-url', 'foreign')

class Fake:
    def __init__(self, ref=False, history=False, open=False, move=False):
        self.ref, self.history, self.open, self.move = ref, history, open, move
        self.calls = []
        self.reads = 0
    def items(self, path):
        if '/matching-refs/' in path: return [{}] if self.ref else []
        if 'state=all' in path: return [{}] if self.history else []
        return [{'head': {'ref': PREFIX + 'foreign'}}] if self.open else []
    def call(self, path, method='GET', data=None):
        self.calls.append((path, method, data))
        if '/git/ref/' in path:
            self.reads += 1
            return {'object': {'sha': 'moved' if self.move and self.reads > 1 else 'head'}}, None
        if method == 'GET': return {'tree': {'sha': 'tree'}}, None
        return {'sha': 'created', 'number': 123}, None

api = Fake()
assert publish(api, REPO, 'head', render(entries)) == 'DRAFT_PR_123'
trees = [d for p, m, d in api.calls if p.endswith('/git/trees')]
assert len(trees) == 1 and trees[0]['tree'][0]['path'] == PATH and len(trees[0]['tree']) == 1
pr = [d for p, m, d in api.calls if p.endswith('/pulls')][0]
assert pr['draft'] is True and pr['base'] == 'main'
assert len([p for p, m, d in api.calls if '/git/refs' in p]) == 1
for kwargs, result in [({'open': True}, 'OPEN_PROPOSAL_EXISTS'), ({'history': True}, 'PROPOSAL_HISTORY_EXISTS')]:
    api = Fake(**kwargs)
    assert publish(api, REPO, 'head', render(entries)) == result
    assert not any(m != 'GET' for p, m, d in api.calls)
for kwargs, reason in [({'ref': True}, 'PROPOSAL_REF_EXISTS'), ({'move': True}, 'MAIN_MOVED_RETRY')]:
    api = Fake(**kwargs)
    try:
        publish(api, REPO, 'head', render(entries))
        raise AssertionError('unsafe publish accepted')
    except SafeFailure as error:
        assert str(error) == reason
    assert not any('/git/refs' in p or p.endswith('/pulls') for p, m, d in api.calls)
print('Promote proposal tests: PASS')

# Published content does not contain generation clocks or ref SHA: main advancement
# alone must leave the exact proposal unchanged.
import base64
import os
from unittest.mock import patch
import harness_promote
class MainFake(Fake):
    def __init__(self, unchanged=False, empty=False):
        super().__init__()
        self.unchanged, self.empty = unchanged, empty
    def call(self, path, method='GET', data=None):
        self.calls.append((path, method, data))
        if path == '/repos/' + REPO: return {'default_branch': 'main'}, None
        if '/contents/' in path:
            content = render(entries) if PATH in path else json.dumps({'schemaVersion': 1, 'entries': []} if self.empty else original)
            return {'content': base64.b64encode(content.encode()).decode()}, None
        if '/git/trees/' in path: return {'tree': [{'path': PATH}] if self.unchanged else [], 'truncated': False}, None
        return super().call(path, method, data)

for kwargs in ({'unchanged': True}, {'empty': True}):
    fake = MainFake(**kwargs)
    with patch.object(harness_promote, 'API', return_value=fake), patch.dict(os.environ, {'GITHUB_REF':'refs/heads/main', 'GITHUB_REPOSITORY':REPO}):
        assert harness_promote.main(['--repo', REPO, '--publish']) == 0
    assert not any(m != 'GET' for p, m, d in fake.calls)
fake = MainFake()
with patch.object(harness_promote, 'API', return_value=fake), patch.dict(os.environ, {'GITHUB_REF':'refs/heads/evil', 'GITHUB_REPOSITORY':REPO}):
    try:
        harness_promote.main(['--repo', REPO, '--publish'])
        raise AssertionError('untrusted ref accepted')
    except SafeFailure as e:
        assert str(e) == 'TRUSTED_MAIN_REQUIRED'
assert not any(m != 'GET' for p, m, d in fake.calls)
print('Promote main idempotence and trusted ref tests: PASS')

assert text('a\u202eb\x7f\x85') == 'a[U+202E]b[U+007F][U+0085]'
for mutate in ('duplicate-id', 'newline'):
    invalid = copy.deepcopy(original)
    if mutate == 'duplicate-id': invalid['entries'].append(copy.deepcopy(invalid['entries'][0]))
    else: invalid['entries'][0]['observation'] += '\nwrong'
    try:
        candidates(invalid, REPO)
        raise AssertionError('invalid ledger accepted')
    except (ValueError, __import__('jsonschema').ValidationError):
        pass
try:
    json.loads('{"x":1,"x":2}', object_pairs_hook=harness_promote.unique_keys)
    raise AssertionError('duplicate key accepted')
except ValueError:
    pass

class Broken(Fake):
    def call(self, path, method='GET', data=None):
        if path.endswith('/pulls') and method == 'POST':
            self.ref = True
            raise SafeFailure('API_HTTP_403')
        return super().call(path, method, data)
broken = Broken()
try:
    publish(broken, REPO, 'head', render(entries))
    raise AssertionError('PR failure ignored')
except SafeFailure as e:
    assert str(e) == 'API_HTTP_403'
count = len(broken.calls)
try:
    publish(broken, REPO, 'head', render(entries))
    raise AssertionError('orphan ref reused')
except SafeFailure as e:
    assert str(e) == 'PROPOSAL_REF_EXISTS'
assert all(method == 'GET' for path, method, body in broken.calls[count:])

class Truncated(MainFake):
    def call(self, path, method='GET', data=None):
        if '/git/trees/' in path: return {'tree': [], 'truncated': True}, None
        return super().call(path, method, data)
class Unreadable(MainFake):
    def call(self, path, method='GET', data=None):
        if '/contents/' in path: raise SafeFailure('API_HTTP_403')
        return super().call(path, method, data)
for fake, reason in ((Truncated(), 'TREE_TRUNCATED'), (Unreadable(), 'API_HTTP_403')):
    with patch.object(harness_promote, 'API', return_value=fake), patch.dict(os.environ, {'GITHUB_REF':'refs/heads/main', 'GITHUB_REPOSITORY':REPO}):
        try:
            harness_promote.main(['--repo', REPO, '--publish'])
            raise AssertionError('read failure ignored')
        except SafeFailure as e:
            assert str(e) == reason
    assert all(method == 'GET' for path, method, body in fake.calls)
print('Promote failure recovery and hostile input tests: PASS')
