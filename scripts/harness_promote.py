#!/usr/bin/env python3
"""Create documentation-only draft proposals for repeated ledger candidates."""
from __future__ import annotations
import argparse
import base64
import hashlib
import html
import json
import os
import re
import sys
import unicodedata
from urllib.parse import urlsplit
from learning_ledger import unique_keys, validate
from observe_learning import API, SafeFailure

PREFIX = 'automation/harness-promote-'
PATH = 'docs/harness-proposals/promote-candidates.md'


def text(value):
    # Keep source text inert: no HTML, Markdown links, mentions, or block syntax.
    return ''.join(f'[U+{ord(c):04X}]' if unicodedata.category(c).startswith('C') else f'&#{ord(c)};' if c in '\\`*_{}[]()#+-.!>@' else html.escape(c) for c in value)


def candidates(data, repo):
    entries = validate(data)
    result = []
    for entry in entries:
        if entry['state'] != 'candidate' or entry['count'] < 2:
            continue
        urls = entry['evidence']['urls']
        if not urls:
            raise SafeFailure('CANDIDATE_EVIDENCE_MISSING')
        for url in urls:
            parsed = urlsplit(url)
            if parsed.scheme != 'https' or parsed.netloc != 'github.com' or not parsed.path.startswith('/' + repo + '/') or re.search(r'[<>"\s\\]', url):
                raise SafeFailure('CANDIDATE_EVIDENCE_INVALID')
        result.append(entry)
    return sorted(result, key=lambda entry: entry['id'])


def render(entries):
    lines = ['# Learning ledger: Guard検討起案', '',
        'この文書は起案材料です。ledger state・規則・Guard・codeを変更しません。採用と実装はHuman承認の別PRで判断します。', '',
        '既存の `review_package.py` はL-009・L-010の対策です。既存対策の効果を先に確認し、新規Guardが必要とは断定しません。', '']
    for entry in entries:
        lines.extend([f'## {entry["id"]}', '', f'- 観測: {text(entry["observation"])}',
            f'- 回数: {entry["count"]}', f'- Evidence: {text(entry["evidence"]["description"])}'])
        lines.extend('- <' + url + '>' for url in sorted(entry['evidence']['urls']))
        lines.extend([f'- 対策検討候補: {text(entry["countermeasure"])}', '',
            '- [ ] 既存対策と再発Evidenceを照合', '- [ ] 必要性・反証可能な仮説・変更先を確定',
            '- [ ] 誤検知/取り逃しの検証とrollbackを定義', '- [ ] 独立レビューとHuman承認を別PRで取得', ''])
    return '\n'.join(lines) + '\n'


def open_proposal(api, base):
    return any(pr['head']['ref'].startswith(PREFIX) for pr in api.items(base + '/pulls?state=open&per_page=100'))


def publish(api, repo, head, content):
    base = '/repos/' + repo
    if open_proposal(api, base):
        return 'OPEN_PROPOSAL_EXISTS'
    def check_main():
        current, _ = api.call(base + '/git/ref/heads/main')
        if current['object']['sha'] != head:
            raise SafeFailure('MAIN_MOVED_RETRY')
    check_main()
    digest = hashlib.sha256(content.encode()).hexdigest()[:24]
    branch = PREFIX + digest
    # Never reuse even closed/unmerged refs or manipulate human-owned proposals.
    if api.items(base + '/git/matching-refs/heads/' + branch):
        raise SafeFailure('PROPOSAL_REF_EXISTS')
    history = api.items(base + '/pulls?state=all&head=' + repo.split('/')[0] + ':' + branch + '&per_page=100')
    if history:
        return 'PROPOSAL_HISTORY_EXISTS'
    commit, _ = api.call(base + '/git/commits/' + head)
    blob, _ = api.call(base + '/git/blobs', 'POST', {'content': content, 'encoding': 'utf-8'})
    tree, _ = api.call(base + '/git/trees', 'POST', {'base_tree': commit['tree']['sha'],
        'tree': [{'path': PATH, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']}]})
    newcommit, _ = api.call(base + '/git/commits', 'POST', {'message': 'docs: 繰り返しcandidateのGuard検討起案', 'tree': tree['sha'], 'parents': [head]})
    check_main()
    if open_proposal(api, base):
        return 'OPEN_PROPOSAL_EXISTS'
    api.call(base + '/git/refs', 'POST', {'ref': 'refs/heads/' + branch, 'sha': newcommit['sha']})
    pr, _ = api.call(base + '/pulls', 'POST', {'title': 'docs: 繰り返しcandidateのGuard検討起案', 'head': branch, 'base': 'main', 'draft': True,
        'body': '## Summary\ncount 2以上のcandidateをGuard検討文書にまとめます。\n\n## Why\n#159 施策④。\n\n## Scope\n文書一件のみ。state/規則/Guard/code変更なし。\n\n## Validation\nledger schema・Evidence同repo・公開文字を検査。GITHUB_TOKEN PRはCI自動起動なし。Humanがclose/reopenまたは別認証でCIを起動し確認してください（この経路は未実測）。\n\n## Evidence / compatibility impact\n文書に正本Evidenceを掲載。Guard採用はHuman承認の別PR。\n\n## EXP-001 feature-freeze check\n- [x] Frozen入力・semantics変更なし。\n\n## Security / privacy\n- [x] rawログ・secret転載なし。\n\n## Checklist\n- [x] 起案と採用を分離。独立レビュー/Human判断待ち。'})
    return f'DRAFT_PR_{int(pr["number"])}'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repo):
        raise SafeFailure('ARGUMENT_INVALID')
    api = API(os.environ.get('GH_TOKEN', ''))
    base = '/repos/' + args.repo
    metadata, _ = api.call(base)
    if metadata['default_branch'] != 'main' or args.publish and (os.environ.get('GITHUB_REF') != 'refs/heads/main' or os.environ.get('GITHUB_REPOSITORY') != args.repo):
        raise SafeFailure('TRUSTED_MAIN_REQUIRED')
    if open_proposal(api, base):
        print('OPEN_PROPOSAL_EXISTS'); return 0
    ref, _ = api.call(base + '/git/ref/heads/main')
    head = ref['object']['sha']
    def read(path):
        data, _ = api.call(base + '/contents/' + path + '?ref=' + head)
        return base64.b64decode(data['content']).decode('utf-8')
    entries = candidates(json.loads(read('knowledge/learning-ledger.json'), object_pairs_hook=unique_keys), args.repo)
    if not entries:
        print('NO_REPEATED_CANDIDATES'); return 0
    content = render(entries)
    # Tree lookup avoids treating an arbitrary API failure as a missing document.
    commit, _ = api.call(base + '/git/commits/' + head)
    tree, _ = api.call(base + '/git/trees/' + commit['tree']['sha'] + '?recursive=1')
    if tree.get('truncated'):
        raise SafeFailure('TREE_TRUNCATED')
    if any(item['path'] == PATH for item in tree['tree']) and read(PATH) == content:
        print('PROPOSAL_UNCHANGED'); return 0
    print(publish(api, args.repo, head, content) if args.publish else f'DRY_RUN_CANDIDATES_{len(entries)}')
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except SafeFailure as error:
        print(str(error), file=sys.stderr); raise SystemExit(1) from None
    except Exception:
        print('PROMOTE_FAILED', file=sys.stderr); raise SystemExit(1) from None
