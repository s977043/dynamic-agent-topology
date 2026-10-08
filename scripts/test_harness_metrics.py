#!/usr/bin/env python3
"""Network-free tests for the read-only harness metrics script."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from harness_metrics import (  # noqa: E402
    collect_pr_metrics, fmt, next_link, parse_ledger, render_markdown, summarize_ledger,
)

REPO = "o/r"
SINCE = datetime(2026, 10, 1, tzinfo=timezone.utc)


def check(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def pr(number: int, created: str, merged: str | None, updated: str) -> dict:
    return {"number": number, "title": f"PR {number}", "created_at": created,
            "merged_at": merged, "updated_at": updated}


def commit(sha: str, date: str) -> dict:
    return {"sha": sha, "commit": {"committer": {"date": date}}}


def check_run(conclusion: str, started: str) -> dict:
    return {"status": "completed", "conclusion": conclusion, "started_at": started}


CHECK_RUNS_QUERY = "check-runs?check_name=validate&filter=all&per_page=100"


def pr_fixture(n: int, sha: str, commits: list, reviews: list, comments: list, runs: dict) -> dict:
    return {
        f"/repos/{REPO}/pulls/{n}/commits?per_page=100": (commits, None),
        f"/repos/{REPO}/pulls/{n}/reviews?per_page=100": (reviews, None),
        f"/repos/{REPO}/pulls/{n}/comments?per_page=100": (comments, None),
        f"/repos/{REPO}/commits/{sha}/{CHECK_RUNS_QUERY}": (runs, None),
    }


PULLS_PAGE_2 = "https://api.github.com/repos/o/r/pulls?page=2"
RESPONSES = {
    f"/repos/{REPO}/pulls?state=closed&sort=updated&direction=desc&per_page=100": (
        [
            pr(3, "2026-10-05T00:00:00Z", "2026-10-06T00:00:00Z", "2026-10-06T00:00:00Z"),
            pr(2, "2026-10-03T00:00:00Z", "2026-10-04T00:00:00Z", "2026-10-04T00:00:00Z"),
            pr(5, "2026-10-02T00:00:00Z", None, "2026-10-03T00:00:00Z"),
        ],
        PULLS_PAGE_2,
    ),
    PULLS_PAGE_2: (
        [
            pr(1, "2026-10-01T12:00:00Z", "2026-10-02T00:00:00Z", "2026-10-02T00:00:00Z"),
            pr(0, "2026-09-01T00:00:00Z", "2026-09-02T00:00:00Z", "2026-09-02T00:00:00Z"),
        ],
        "https://api.github.com/must-not-be-fetched",
    ),
    # PR 1: first head fails, fix pushed after review -> 1 loop.
    **pr_fixture(
        1, "a1",
        [commit("a1", "2026-10-01T11:00:00Z"), commit("a2", "2026-10-01T15:00:00Z")],
        [{"submitted_at": "2026-10-01T13:00:00Z"}],
        [{"created_at": "2026-10-01T13:05:00Z"}],
        {"check_runs": [check_run("success", "2026-10-01T16:00:00Z"),
                        check_run("failure", "2026-10-01T11:01:00Z")]}),
    # PR 2: two commits at open, success on the last one; two review loops.
    **pr_fixture(
        2, "b2",
        [commit("b1", "2026-10-02T23:00:00Z"), commit("b2", "2026-10-02T23:30:00Z"),
         commit("b3", "2026-10-03T05:00:00Z"), commit("b4", "2026-10-03T09:00:00Z")],
        [{"submitted_at": "2026-10-03T04:00:00Z"}, {"submitted_at": "2026-10-03T08:00:00Z"},
         {"submitted_at": None}],
        [],
        {"check_runs": [check_run("cancelled", "2026-10-02T23:29:00Z"),
                        check_run("success", "2026-10-02T23:31:00Z")]}),
    # PR 3: no check run for the first head -> undeterminable; no review.
    **pr_fixture(
        3, "c1",
        [commit("c1", "2026-10-04T00:00:00Z")],
        [],
        [],
        {"check_runs": [{"status": "in_progress", "conclusion": None, "started_at": "2026-10-04T00:01:00Z"}]}),
}


def fake_fetch(url: str):
    if url not in RESPONSES:
        raise AssertionError(f"unexpected request: {url}")
    return RESPONSES[url]


metrics = collect_pr_metrics(fake_fetch, REPO, SINCE)
rows = {row["number"]: row for row in metrics["pulls"]}
check(sorted(rows) == [1, 2, 3], "only PRs merged in window, unmerged excluded, paging stops")
check(rows[1]["first_sha"] == "a1" and rows[1]["first_validate"] == "failure",
      "earliest validate run of the first head decides")
check(rows[2]["first_sha"] == "b2", "head at PR creation is the last commit before created_at")
check(rows[2]["first_validate"] == "success", "cancelled runs are not a verdict")
check(rows[3]["first_validate"] is None, "missing completed run is undeterminable")
check(metrics["ci_first_pass"] == {"passed": 1, "judged": 2, "undeterminable": 1, "rate": 0.5},
      "undeterminable PRs are excluded from the denominator")
check([rows[n]["review_loops"] for n in (1, 2, 3)] == [1, 2, 0], "review -> commit round trips")
check(metrics["review_loops"]["median"] == 1.0 and metrics["review_loops"]["p90"] == 2.0,
      "median and p90 of review loops")
check("数えられない" in metrics["review_loops"]["note"], "untracked reviews must be noted")

check(next_link('<https://x/?page=2>; rel="next", <https://x/?page=9>; rel="last"') == "https://x/?page=2",
      "Link header next")
check(next_link('<https://x/?page=9>; rel="last"') is None, "no next link")

LEDGER = """# Harness

## Learning ledger

| ID    | 観測 | Evidence | 回数 | 状態      | 対策 |
| ----- | ---- | -------- | ---- | --------- | ---- |
| L-001 | a    | PR #1    | 4    | promoted  | x    |
| L-002 | b    | PR #2    | 2    | candidate | y    |
| L-003 | c    |          | 1    | candidate | z    |
| L-004 | d    | -        | 3    | rejected  | w    |

状態は candidate / promoted / rejected。

## Roadmap

| ID | 観測 | Evidence | 回数 | 状態 | 対策 |
| -- | ---- | -------- | ---- | ---- | ---- |
| X-1 | not ledger | | 9 | candidate | |
"""
summary = summarize_ledger(parse_ledger(LEDGER))
check(summary["total"] == 4, "only the Learning ledger table is parsed")
check(summary["by_state"] == {"candidate": 2, "promoted": 1, "rejected": 1}, "count by state")
check(summary["repeated_candidates"] == ["L-002"], "candidates with count >= 2")
check(summary["missing_evidence"] == ["L-003", "L-004"], "blank or dash Evidence is missing")

try:
    parse_ledger("# no ledger\n")
    raise AssertionError("missing ledger must fail")
except ValueError as exc:
    check("not found" in str(exc), "missing ledger error message")

real = summarize_ledger(parse_ledger((ROOT / "docs" / "AGENT_HARNESS.md").read_text(encoding="utf-8")))
check(real["total"] > 0, "repository ledger is parseable")

markdown = render_markdown({"repo": REPO, "since": "s", "until": "u", **metrics, "ledger": summary})
check("1 / 2（50%）" in markdown and "判定不能（最初の head commit の run なし、分母外）: 1 件" in markdown,
      "markdown shows rate and undeterminable count")
check("| #3 | 判定不能 | 0 |" in markdown, "per-PR row")
check(all(fmt(p / q, "{:.0%}") == "{:.0f}%".format(p / q * 100) for q in range(1, 201) for p in range(q + 1)),
      "percent format matches the previous rate * 100 rendering")

print("harness metrics tests OK")
