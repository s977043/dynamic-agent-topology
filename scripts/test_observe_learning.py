#!/usr/bin/env python3
"""Deterministic Observe tests: no network or repository writes."""
import copy
import json
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch
import observe_learning as observe

ROOT = Path(__file__).resolve().parents[1]

class FakeAPI:
    def __init__(self, data=None):
        self.data = data or {}
        self.writes = []
    def items(self, path, key=None):
        return copy.deepcopy(self.data.get(path, []))
    def call(self, path, method='GET', data=None):
        if method != 'GET':
            self.writes.append((path, data))
        return copy.deepcopy(self.data[path]), None

def main():
    base = '/repos/o/r'
    run_path = base + '/actions/runs?status=completed&per_page=100'
    pulls_path = base + '/pulls?state=all&sort=updated&direction=desc&per_page=100'
    api = FakeAPI({run_path: [
        {'id': 1, 'run_attempt': 2, 'conclusion': 'failure', 'path': '.github/workflows/spec-lint.yml'},
        {'id': 2, 'run_attempt': 1, 'conclusion': 'cancelled'},
        {'id': 3, 'run_attempt': 1, 'conclusion': 'failure', 'path': '.github/workflows/harness-observe.yml'},
        {'id': 4, 'run_attempt': 1, 'conclusion': 'failure'}],
        base + '/actions/runs/1/attempts/2/jobs?per_page=100': [{'completed_at': '2026-10-14T00:00:00Z'}],
        base + '/actions/runs/4/attempts/1/jobs?per_page=100': [{'completed_at': None}],
        pulls_path: [{'number': 10, 'updated_at': '2026-10-14T01:00:00Z', 'head': {'ref': 'work'}},
            {'number': 11, 'head': {'ref': observe.PREFIX + 'abc'}}],
        base + '/pulls/10/reviews?per_page=100': [{'id': 33, 'submitted_at': '2026-10-14T00:00:00Z', 'state': 'CHANGES_REQUESTED', 'body': 'secret\nVerdict: CHANGES_REQUIRED\n必須: 2件\n推奨: 1件'}],
        base + '/issues/10/comments?per_page=100': [{'id': 34, 'created_at': None, 'body': '必須: 1件'}]})
    since = datetime(2026, 10, 13, tzinfo=timezone.utc)
    until = datetime(2026, 10, 15, tzinfo=timezone.utc)
    observations = observe.collect(api, 'o/r', since, until)
    assert len(observations) == 2
    assert observations[0]['url'].endswith('/attempts/2')
    assert 'secret' not in json.dumps(observations)
    assert 'required=2' in observations[1]['facts']
    assert observe.summaries('必須: 1件\n必須: 2件\nVerdict: CHANGES_REQUIRED') == {}
    header = '| Reviewer | runtime / model | session | Verdict | 必須 | 推奨 |\n| --- | --- | --- | --- | --- | --- |\n'
    assert observe.summaries(header + '| 1 | x | s | MERGE_OK | 2 | 0 |')['required'] == '2'
    assert observe.summaries(header + '| 1 | x | s | MERGE_OK | 2 | 0 |\n| 1 | x | s | MERGE_OK | 2 | 0 |') == {}
    assert observe.summaries(header.replace('| --- |', '| bad |') + '| 1 | x | s | MERGE_OK | 2 | 0 |') == {}
    assert observe.summaries(header + '| 1 | x | s | MERGE_OK | 2 | 0 |\n| 2 | x | s | 不明 | 0 | 0 |') == {}
    ledger = json.loads((ROOT / 'knowledge/learning-ledger.json').read_text())
    document = (ROOT / 'docs/AGENT_HARNESS.md').read_text()
    before = copy.deepcopy(ledger)
    proposed, generated = observe.propose(ledger, document, observations)
    assert ledger == before and proposed['entries'][:len(ledger['entries'])] == ledger['entries']
    assert all(e['state'] == 'candidate' and e['count'] == 1 for e in proposed['entries'][len(ledger['entries']):])
    repeat, regenerated = observe.propose(proposed, generated, observations)
    assert repeat == proposed and regenerated == generated
    assert document.split(observe.START)[0] == generated.split(observe.START)[0]
    assert document.split(observe.END)[1] == generated.split(observe.END)[1]
    for existing in ('open', 'ref', 'moved'):
        mock = FakeAPI({base + '/pulls?state=open&per_page=100': [{'head': {'ref': observe.PREFIX + 'x'}}] if existing == 'open' else [],
            base + '/git/ref/heads/main': {'object': {'sha': 'different' if existing == 'moved' else 'head'}},
            base + '/git/matching-refs/heads/' + observe.PREFIX + __import__('hashlib').sha256(json.dumps({'a': 'b'}, sort_keys=True).encode()).hexdigest()[:16]: [{}] if existing == 'ref' else []})
        try:
            result = observe.publish(mock, 'o/r', 'main', 'head', {'a': 'b'}, since, until)
            assert existing == 'open' and result == 'OPEN_PROPOSAL_EXISTS'
        except observe.SafeFailure as error:
            assert str(error) in ('MAIN_MOVED_RETRY', 'PROPOSAL_REF_EXISTS')
        assert not mock.writes
    class Publisher(FakeAPI):
        def call(self, path, method='GET', data=None):
            if method == 'GET':
                return ({'object': {'sha': 'head'}} if '/git/ref/' in path else {'tree': {'sha': 'tree'}}), None
            self.writes.append((path, data))
            return {'sha': 'created', 'number': 99}, None
    pub = Publisher()
    files = {'knowledge/learning-ledger.json': 'ledger', 'docs/AGENT_HARNESS.md': 'document'}
    assert observe.publish(pub, 'o/r', 'main', 'head', files, since, until) == 'DRAFT_PR_99'
    tree = next(data for path, data in pub.writes if path.endswith('/git/trees'))
    assert {item['path'] for item in tree['tree']} == set(files)
    assert pub.writes[-1][1]['draft'] is True
    assert not any(path.endswith('/merge') for path, _ in pub.writes)
    # A denied PR leaves the created ref intact. Retrying identical input must
    # stop before creating any further Git objects or attempting another PR.
    class DeniedPublisher(Publisher):
        def __init__(self):
            super().__init__()
            self.calls = []
            self.created_ref = None
        def items(self, path, key=None):
            self.calls.append((path, 'GET'))
            if path.startswith(base + '/git/matching-refs/heads/'):
                branch = path.split('/git/matching-refs/heads/', 1)[1]
                return [{'ref': self.created_ref}] if self.created_ref == 'refs/heads/' + branch else []
            assert path == base + '/pulls?state=open&per_page=100'
            return []
        def call(self, path, method='GET', data=None):
            self.calls.append((path, method))
            if path == base + '/pulls' and method == 'POST':
                assert self.created_ref == 'refs/heads/' + data['head']
                self.writes.append((path, data))
                raise observe.SafeFailure('API_HTTP_403')
            if path == base + '/git/refs' and method == 'POST':
                assert self.created_ref is None
                self.created_ref = data['ref']
            return super().call(path, method, data)
    denied = DeniedPublisher()
    for expected_error in ('API_HTTP_403', 'PROPOSAL_REF_EXISTS'):
        call_count, write_count = len(denied.calls), len(denied.writes)
        try:
            observe.publish(denied, 'o/r', 'main', 'head', files, since, until)
            raise AssertionError('denied or orphaned proposal accepted')
        except observe.SafeFailure as error:
            assert str(error) == expected_error
        assert denied.created_ref is not None
        if expected_error == 'PROPOSAL_REF_EXISTS':
            assert len(denied.writes) == write_count
            assert all(method == 'GET' for _, method in denied.calls[call_count:])
    assert [path for path, _ in denied.writes] == [
        base + '/git/blobs', base + '/git/blobs', base + '/git/trees',
        base + '/git/commits', base + '/git/refs', base + '/pulls']
    # Even after one collected event, an API failure cannot enter publisher.
    broken = FakeAPI({base + '/pulls?state=open&per_page=100': []})
    import base64
    def content(value):
        return {'content': base64.b64encode(value.encode()).decode()}
    broken.data.update({base: {'default_branch': 'main'}, base + '/git/ref/heads/main': {'object': {'sha': 'head'}},
        base + '/contents/knowledge/learning-ledger.json?ref=head': content(json.dumps(ledger)),
        base + '/contents/docs/AGENT_HARNESS.md?ref=head': content(document)})
    def fail_collection(*args):
        raise observe.SafeFailure('API_HTTP_403')
    with patch.object(observe, 'API', return_value=broken), patch.object(observe, 'collect', side_effect=fail_collection), patch.dict(__import__('os').environ, {'GITHUB_REF': 'refs/heads/main'}):
        try:
            observe.main(['--repo', 'o/r', '--publish'])
            raise AssertionError('partial API error ignored')
        except observe.SafeFailure as error:
            assert str(error) == 'API_HTTP_403'
    assert not broken.writes
    real = observe.API('private-token')
    for url in ('https://evil.example/private-token', 'https://api.github.com@evil.example/'):
        try:
            real.call(url)
            raise AssertionError('external URL accepted')
        except observe.SafeFailure as error:
            assert str(error) == 'API_REQUEST_FAILED' and 'private-token' not in str(error)
    class Paged(observe.API):
        def call(self, path):
            return ([path], '/second' if path == '/first' else None)
    assert Paged('').items('/first') == ['/first', '/second']
    print('PASS: Observe event, privacy, idempotence, publish guards and pagination tests')

if __name__ == '__main__':
    main()
