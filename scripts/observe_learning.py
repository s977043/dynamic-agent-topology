#!/usr/bin/env python3
"""Collect bounded GitHub observations and propose candidate ledger facts only."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, build_opener
from urllib.error import HTTPError
from harness_metrics import ApiOnlyRedirectHandler, require_api_url, next_link
from learning_ledger import START, END, render, validate
from review_package import SUMMARY_LINES

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'automation/harness-observe-'
WORKFLOW = 'harness-observe.yml'
FAILURES = {'failure', 'timed_out', 'action_required', 'startup_failure'}

class SafeFailure(Exception):
    pass

class API:
    def __init__(self, token):
        self.token = token
        self.opener = build_opener(ApiOnlyRedirectHandler)
    def call(self, path, method='GET', data=None):
        url = path if path.startswith('https:') else 'https://api.github.com' + path
        try:
            require_api_url(url)
            body = None if data is None else json.dumps(data).encode()
            request = Request(url, data=body, method=method, headers={
                'Authorization': 'Bearer ' + self.token,
                'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
            with self.opener.open(request, timeout=20) as response:
                raw = response.read(8_000_001)
                if len(raw) > 8_000_000:
                    raise SafeFailure('API_SIZE_LIMIT')
                return json.loads(raw), next_link(response.headers.get('Link'))
        except HTTPError as error:
            raise SafeFailure(f'API_HTTP_{error.code}') from None
        except SafeFailure:
            raise
        except Exception:
            raise SafeFailure('API_REQUEST_FAILED') from None
    def items(self, path, key=None):
        result = []
        for _ in range(100):
            data, link = self.call(path)
            result.extend(data[key] if key else data)
            if not link:
                return result
            path = link
        raise SafeFailure('API_PAGE_LIMIT')

def stamp(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            raise ValueError()
        return result.astimezone(timezone.utc)
    except Exception:
        raise SafeFailure('SOURCE_TIMESTAMP_INVALID') from None

def summaries(body):
    # Parse only exact standalone summary lines. Ambiguous values remain absent.
    found = {key: [] for key in SUMMARY_LINES}
    for line in (body or '').splitlines():
        for key, (_, pattern) in SUMMARY_LINES.items():
            match = pattern.fullmatch(line.strip())
            if match:
                found[key].append(match.group(1))
    values = {k: v[0] for k, v in found.items() if len(v) == 1}
    if any(len(v) > 1 for v in found.values()):
        values = {}
    # Generated review record uses an exact fixed table header; ignore details body.
    lines = (body or '').splitlines()
    header = '| Reviewer | runtime / model | session | Verdict | 必須 | 推奨 |'
    if lines.count(header) > 1:
        return {}
    if lines.count(header) == 1:
        i = lines.index(header) + 2
        rows = []
        invalid = i > len(lines) or lines[i - 1].replace(' ', '') != '|---|---|---|---|---|---|'
        reviewers = set()
        while i < len(lines) and lines[i].startswith('|'):
            cells = [c.strip() for c in lines[i].strip('|').split('|')]
            if len(cells) == 6 and cells[0].isdigit() and cells[0] not in reviewers:
                reviewers.add(cells[0])
                verdict = cells[3].strip('*')
                if verdict in ('MERGE_OK', 'CHANGES_REQUIRED') and cells[4].isdigit() and cells[5].isdigit():
                    rows.append((verdict, int(cells[4]), int(cells[5])))
                else:
                    invalid = True
            else:
                invalid = True
            i += 1
        values = {}
        if rows and not invalid:
            # Table is canonical; duplicate summaries in details must not count twice.
            values = {'verdict': 'CHANGES_REQUIRED' if any(r[0] == 'CHANGES_REQUIRED' for r in rows) else 'MERGE_OK',
                      'required': str(sum(r[1] for r in rows)), 'recommended': str(sum(r[2] for r in rows))}
    return values

def collect(api, repo, since, until):
    base = '/repos/' + repo
    web = 'https://github.com/' + repo
    observations = {}
    def add(kind, ident, date, url, facts):
        if date is None:
            return  # Missing source date is not replaced with PR creation/update time.
        time = stamp(date)
        if since <= time < until:
            observations[(kind, ident)] = {'kind': kind, 'date': time.date().isoformat(),
                'url': url, 'facts': facts + '; source timestamp=' + time.isoformat()}
    for run in api.items(base + '/actions/runs?status=completed&per_page=100', 'workflow_runs'):
        if run.get('path', '').split('/')[-1] == WORKFLOW or run.get('head_branch', '').startswith(PREFIX):
            continue
        if run.get('conclusion') not in FAILURES:
            continue
        rid, attempt = int(run['id']), int(run['run_attempt'])
        jobs = api.items(f'{base}/actions/runs/{rid}/attempts/{attempt}/jobs?per_page=100', 'jobs')
        dates = [j['completed_at'] for j in jobs if j.get('completed_at')]
        if not dates or any(not j.get('completed_at') for j in jobs):
            continue
        completed = max(dates, key=stamp)
        add('ci', f'{rid}:{attempt}', completed, f'{web}/actions/runs/{rid}/attempts/{attempt}',
            f'CI conclusion={run["conclusion"]}; run_id={rid}; run_attempt={attempt}; final job completed_at')
    pulls = api.items(base + '/pulls?state=all&sort=updated&direction=desc&per_page=100')
    for pr in pulls:
        if pr['head']['ref'].startswith(PREFIX):
            continue
        if stamp(pr['updated_at']) < since:
            continue
        number = int(pr['number'])
        for kind, endpoint, timekey, anchor in [('review', 'reviews', 'submitted_at', 'pullrequestreview-'),
                ('comment', None, 'created_at', 'issuecomment-')]:
            path = f'{base}/pulls/{number}/{endpoint}?per_page=100' if endpoint else f'{base}/issues/{number}/comments?per_page=100'
            for source in api.items(path):
                parsed = summaries(source.get('body'))
                facts = []
                if source.get('state') == 'CHANGES_REQUESTED':
                    facts.append('review state=CHANGES_REQUESTED')
                if parsed.get('verdict') == 'CHANGES_REQUIRED':
                    facts.append('Verdict=CHANGES_REQUIRED')
                for label in ('required', 'recommended'):
                    if parsed.get(label, '').isdigit() and int(parsed[label]) > 0:
                        facts.append(f'{label}={int(parsed[label])}')
                if facts:
                    sid = int(source['id'])
                    add(kind, str(sid), source.get(timekey), f'{web}/pull/{number}#{anchor}{sid}', '; '.join(facts))
    return sorted(observations.values(), key=lambda x: (x['date'], x['url']))

def propose(data, document, observations):
    original = copy.deepcopy(data)
    validate(data)
    existing = {url for entry in data['entries'] for url in entry['evidence']['urls']}
    result = copy.deepcopy(data)
    index = max((int(e['id'][2:]) for e in data['entries']), default=0)
    for obs in observations:
        if obs['url'] in existing:
            continue
        index += 1
        result['entries'].append({'id': f'L-{index:03d}', 'observation': 'GitHub自動観測（' + obs['kind'] + '、原因未分類）',
            'evidence': {'description': obs['date'] + ' ' + obs['facts'], 'urls': [obs['url']]},
            'count': 1, 'state': 'candidate', 'countermeasure': '原因確認と改善案の検討待ち', 'observedDates': [obs['date']]})
        existing.add(obs['url'])
    assert data == original and result['entries'][:len(data['entries'])] == original['entries']
    validate(result)
    if document.count(START) != 1 or document.count(END) != 1:
        raise SafeFailure('DOCUMENT_MARKERS_INVALID')
    start, end = document.index(START), document.index(END) + len(END)
    if document.index(START) >= document.index(END):
        raise SafeFailure('DOCUMENT_MARKERS_INVALID')
    updated = document[:start] + render(result['entries']) + document[end:]
    return result, updated

def has_proposal(api, base):
    return any(pr['head']['ref'].startswith(PREFIX) for pr in api.items(base + '/pulls?state=open&per_page=100'))

def publish(api, repo, default, head, files, since, until):
    base = '/repos/' + repo
    if has_proposal(api, base):
        return 'OPEN_PROPOSAL_EXISTS'
    current, _ = api.call(base + '/git/ref/heads/' + default)
    if current['object']['sha'] != head:
        raise SafeFailure('MAIN_MOVED_RETRY')
    digest = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:16]
    branch = PREFIX + digest
    refs = api.items(base + '/git/matching-refs/heads/' + branch)
    if refs:
        raise SafeFailure('PROPOSAL_REF_EXISTS')
    commit, _ = api.call(base + '/git/commits/' + head)
    tree = []
    for path, content in files.items():
        blob, _ = api.call(base + '/git/blobs', 'POST', {'content': content, 'encoding': 'utf-8'})
        tree.append({'path': path, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
    newtree, _ = api.call(base + '/git/trees', 'POST', {'base_tree': commit['tree']['sha'], 'tree': tree})
    newcommit, _ = api.call(base + '/git/commits', 'POST', {'message': 'chore: GitHub観測をLearning ledger候補へ追記', 'tree': newtree['sha'], 'parents': [head]})
    if has_proposal(api, base):
        return 'OPEN_PROPOSAL_EXISTS'
    api.call(base + '/git/refs', 'POST', {'ref': 'refs/heads/' + branch, 'sha': newcommit['sha']})
    pr, _ = api.call(base + '/pulls', 'POST', {'title': 'chore: GitHub観測のLearning ledger追記案', 'head': branch, 'base': default, 'draft': True,
        'body': f'## Summary\nGitHub確定メタデータのcandidate追記案。原因分類・promotionなし。\n\n## Why\n#159 施策③。\n\n## Scope\nledgerと生成表だけ。\n\n## Validation\nschema・既存entry不変・生成領域外不変を検証。GITHUB_TOKEN作成PRはCIを起動しないため、HumanがPRをclose/reopenするか別認証でCIを起動し必須CIを確認する。\n\n## Evidence / compatibility impact\nUTC期間 [{since.isoformat()}, {until.isoformat()})。日付はsourceメタデータ。\n\n## EXP-001 feature-freeze check\n- [x] Frozen入力・semantics変更なし。\n\n## Security / privacy\n- [x] rawログ・本文・secret転載なし。\n\n## Checklist\n- [x] 事実と判断を分離。独立レビュー後にmerge判断。'})
    return f'DRAFT_PR_{int(pr["number"])}'

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--days', type=int, default=7)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo) or not 1 <= args.days <= 90:
        raise SafeFailure('ARGUMENT_INVALID')
    api = API(os.environ.get('GH_TOKEN', ''))
    base = '/repos/' + args.repo
    if has_proposal(api, base):
        print('OPEN_PROPOSAL_EXISTS'); return 0
    metadata, _ = api.call(base)
    default = metadata['default_branch']
    ref = os.environ.get('GITHUB_REF')
    if args.publish and ref != 'refs/heads/' + default:
        raise SafeFailure('DEFAULT_BRANCH_REQUIRED')
    head, _ = api.call(base + '/git/ref/heads/' + default)
    sha = head['object']['sha']
    # Files used for proposing must exactly match the captured main commit.
    import base64
    def contents(path):
        data, _ = api.call(base + '/contents/' + path + '?ref=' + sha)
        return base64.b64decode(data['content'], validate=False).decode()
    ledger = json.loads(contents('knowledge/learning-ledger.json'))
    doc = contents('docs/AGENT_HARNESS.md')
    until = datetime.now(timezone.utc)
    since = until - timedelta(days=args.days)
    observations = collect(api, args.repo, since, until)
    result, document = propose(ledger, doc, observations)
    count = len(result['entries']) - len(ledger['entries'])
    if not count:
        print('NO_NEW_OBSERVATIONS'); return 0
    files = {'knowledge/learning-ledger.json': json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'docs/AGENT_HARNESS.md': document}
    print(publish(api, args.repo, default, sha, files, since, until) if args.publish else f'DRY_RUN_CANDIDATES_{count}')
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except SafeFailure as error:
        print(str(error), file=sys.stderr); raise SystemExit(1) from None
    except Exception:
        print('OBSERVE_FAILED', file=sys.stderr); raise SystemExit(1) from None
