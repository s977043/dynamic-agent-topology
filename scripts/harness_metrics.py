#!/usr/bin/env python3
"""Read-only harness metrics: CI first-pass rate, review loops, learning ledger summary."""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = "s977043/dynamic-agent-topology"
DEFAULT_LEDGER = ROOT / "docs" / "AGENT_HARNESS.md"
API_ROOT = "https://api.github.com"
API_VERSION = "2022-11-28"
CHECK_NAME = "validate"
# spec-lint uses cancel-in-progress, so a cancelled run says nothing about the commit.
NON_VERDICT = {"cancelled", "skipped", "neutral", "stale"}
LEDGER_STATES = ("candidate", "promoted", "rejected")
REVIEW_LOOP_NOTE = "GitHub に review / review comment として残っていないレビュー（口頭・チャット・ローカル指摘）は数えられない。"

Fetcher = Callable[[str], tuple[Any, str | None]]


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def next_link(link_header: str | None) -> str | None:
    for part in (link_header or "").split(","):
        match = re.search(r'<([^>]+)>;\s*rel="next"', part)
        if match:
            return match.group(1)
    return None


def github_fetcher(token: str | None) -> Fetcher:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "dynamic-agent-topology-harness-metrics",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    def fetch(url: str) -> tuple[Any, str | None]:
        if not url.startswith("http"):
            url = API_ROOT + url
        try:
            with urlopen(Request(url, headers=headers, method="GET"), timeout=20) as response:
                return json.load(response), next_link(response.headers.get("Link"))
        except HTTPError as error:
            raise RuntimeError(f"GET {url}: HTTP {error.code}") from error

    return fetch


def fetch_all(fetch: Fetcher, url: str, item_key: str | None = None) -> list[Any]:
    items: list[Any] = []
    next_url: str | None = url
    while next_url:
        data, next_url = fetch(next_url)
        items.extend(data[item_key] if item_key else data)
    return items


def merged_pulls(fetch: Fetcher, repo: str, since: datetime) -> list[dict[str, Any]]:
    pulls: list[dict[str, Any]] = []
    next_url: str | None = f"/repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=100"
    while next_url:
        page, next_url = fetch(next_url)
        for pr in page:
            if pr.get("merged_at") and parse_time(pr["merged_at"]) >= since:
                pulls.append(pr)
        if page and parse_time(page[-1]["updated_at"]) < since:
            break
    return sorted(pulls, key=lambda pr: pr["number"])


def commit_time(commit: dict[str, Any]) -> datetime:
    return parse_time(commit["commit"]["committer"]["date"])


def first_head_sha(pr: dict[str, Any], commits: list[dict[str, Any]]) -> str | None:
    """Head commit at PR creation: the last commit committed at or before created_at."""
    if not commits:
        return None
    created = parse_time(pr["created_at"])
    at_open = [c for c in commits if commit_time(c) <= created]
    return (at_open[-1] if at_open else commits[0])["sha"]


def first_validate_conclusion(fetch: Fetcher, repo: str, sha: str) -> str | None:
    runs = fetch_all(fetch, f"/repos/{repo}/commits/{sha}/check-runs?check_name={CHECK_NAME}&filter=all&per_page=100", "check_runs")
    completed = [
        r for r in runs
        if r.get("status") == "completed" and r.get("started_at") and r.get("conclusion") not in NON_VERDICT
    ]
    if not completed:
        return None
    return min(completed, key=lambda r: r["started_at"])["conclusion"]


def review_loops(reviews: list[dict[str, Any]], comments: list[dict[str, Any]], commits: list[dict[str, Any]]) -> int:
    events = [(parse_time(r["submitted_at"]), "feedback") for r in reviews if r.get("submitted_at")]
    events += [(parse_time(c["created_at"]), "feedback") for c in comments]
    events += [(commit_time(c), "commit") for c in commits]
    loops = 0
    pending_feedback = False
    for _, kind in sorted(events, key=lambda e: (e[0], e[1] == "commit")):
        if kind == "feedback":
            pending_feedback = True
        elif pending_feedback:
            loops += 1
            pending_feedback = False
    return loops


def percentile(values: list[int], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round(pct * len(ordered) + 0.5) - 1))
    return float(ordered[index])


def collect_pr_metrics(fetch: Fetcher, repo: str, since: datetime) -> dict[str, Any]:
    rows = []
    for pr in merged_pulls(fetch, repo, since):
        number = pr["number"]
        commits = fetch_all(fetch, f"/repos/{repo}/pulls/{number}/commits?per_page=100")
        reviews = fetch_all(fetch, f"/repos/{repo}/pulls/{number}/reviews?per_page=100")
        comments = fetch_all(fetch, f"/repos/{repo}/pulls/{number}/comments?per_page=100")
        sha = first_head_sha(pr, commits)
        conclusion = first_validate_conclusion(fetch, repo, sha) if sha else None
        rows.append({
            "number": number,
            "title": pr["title"],
            "first_sha": sha,
            "first_validate": conclusion,
            "review_loops": review_loops(reviews, comments, commits),
        })
    judged = [r for r in rows if r["first_validate"] is not None]
    passed = [r for r in judged if r["first_validate"] == "success"]
    loops = [r["review_loops"] for r in rows]
    return {
        "pulls": rows,
        "ci_first_pass": {
            "passed": len(passed),
            "judged": len(judged),
            "undeterminable": len(rows) - len(judged),
            "rate": len(passed) / len(judged) if judged else None,
        },
        "review_loops": {
            "median": float(statistics.median(loops)) if loops else None,
            "p90": percentile(loops, 0.9),
            "note": REVIEW_LOOP_NOTE,
        },
    }


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_ledger(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == "## Learning ledger")
    except StopIteration as error:
        raise ValueError("Learning ledger section not found") from error
    table = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if line.strip().startswith("|"):
            table.append(line)
        elif table:
            break
    if len(table) < 2:
        raise ValueError("Learning ledger table not found")
    header = split_row(table[0])
    return [dict(zip(header, split_row(line))) for line in table[2:]]


def summarize_ledger(entries: list[dict[str, str]]) -> dict[str, Any]:
    by_state = {state: 0 for state in LEDGER_STATES}
    repeated_candidates = []
    missing_evidence = []
    for entry in entries:
        state = entry.get("状態", "")
        by_state[state] = by_state.get(state, 0) + 1
        try:
            count = int(entry.get("回数", ""))
        except ValueError:
            count = 0
        if state == "candidate" and count >= 2:
            repeated_candidates.append(entry.get("ID", ""))
        if not entry.get("Evidence", "").strip("-— "):
            missing_evidence.append(entry.get("ID", ""))
    return {
        "total": len(entries),
        "by_state": by_state,
        "repeated_candidates": repeated_candidates,
        "missing_evidence": missing_evidence,
    }


def fmt(value: float | None, pattern: str = "{:.1f}") -> str:
    return "n/a" if value is None else pattern.format(value)


def render_markdown(report: dict[str, Any]) -> str:
    ci = report["ci_first_pass"]
    loops = report["review_loops"]
    ledger = report["ledger"]
    out = [
        f"# Harness metrics ({report['repo']})",
        "",
        f"期間: {report['since']} 〜 {report['until']}（merged PR {len(report['pulls'])} 件）",
        "",
        "## CI 初回 pass 率",
        "",
        f"- `{CHECK_NAME}` 初回 success: {ci['passed']} / {ci['judged']}（{fmt(None if ci['rate'] is None else ci['rate'] * 100, '{:.0f}%')}）",
        f"- 判定不能（最初の head commit の run なし、分母外）: {ci['undeterminable']} 件",
        "",
        "## レビューループ数",
        "",
        f"- 中央値: {fmt(loops['median'])} / p90: {fmt(loops['p90'])}",
        f"- 注記: {loops['note']}",
        "",
        "| PR | 初回 validate | ループ数 |",
        "| -- | ------------- | -------- |",
    ]
    out += [f"| #{p['number']} | {p['first_validate'] or '判定不能'} | {p['review_loops']} |" for p in report["pulls"]]
    out += [
        "",
        "## Learning ledger（再発率の代替）",
        "",
        f"- 総数: {ledger['total']}（" + ", ".join(f"{k}: {v}" for k, v in ledger["by_state"].items()) + "）",
        f"- 回数 2 以上の candidate: {', '.join(ledger['repeated_candidates']) or 'なし'}",
        f"- Evidence 欠落: {', '.join(ledger['missing_evidence']) or 'なし'}",
    ]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    window = parser.add_mutually_exclusive_group()
    window.add_argument("--days", type=int, default=7)
    window.add_argument("--since", help="ISO date/time (UTC if no offset)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    args = parser.parse_args(argv)

    until = datetime.now(timezone.utc)
    if args.since:
        since = datetime.fromisoformat(args.since)
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
    else:
        since = until - timedelta(days=args.days)

    report = {
        "repo": args.repo,
        "since": since.isoformat(timespec="seconds"),
        "until": until.isoformat(timespec="seconds"),
        **collect_pr_metrics(github_fetcher(os.environ.get("GH_TOKEN")), args.repo, since),
        "ledger": summarize_ledger(parse_ledger(args.ledger.read_text(encoding="utf-8"))),
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
