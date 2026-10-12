#!/usr/bin/env python3
"""Network-free tests for the independent review kit (gh and git are faked)."""
from __future__ import annotations

from pathlib import Path
import argparse
import contextlib
import io
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from review_package import (  # noqa: E402
    DEFAULT_TEMPLATE, TEMPLATE_DIR, build, comment_id, launch_command, main, parse_review, render_prompt,
    strip_file_links,
)

HEAD = "a" * 40
MAIN = "b" * 40
PR = {
    "number": 7, "title": "feat: x", "url": "https://github.com/o/r/pull/7", "author": {"login": "alice"},
    "body": "PR body", "headRefOid": HEAD, "baseRefName": "main", "baseRefOid": MAIN,
    "comments": [{"author": {"login": "bob"}, "createdAt": "2026-10-12T01:02:03Z",
                  "url": "https://github.com/o/r/pull/7#issuecomment-11", "body": "looks fine"}],
}
ISSUE = {"number": 15, "title": "Run", "url": "https://github.com/o/r/issues/15", "author": {"login": "carol"},
         "createdAt": "2026-10-01T00:00:00Z", "body": "issue body"}
COMMENT = {"id": 99, "html_url": "https://github.com/o/r/issues/15#issuecomment-99", "user": {"login": "dave"},
           "created_at": "2026-10-11T09:00:00Z", "body": "judgment"}


def check(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def expect_exit(fn, reason: str) -> str:
    try:
        fn()
    except SystemExit as exc:
        return str(exc)
    raise AssertionError(reason)


def fake_runner(calls: list, fetched: str = HEAD, checkout_head: str = HEAD):
    def runner(cmd: list[str]) -> str:
        calls.append(cmd)
        if cmd[:3] == ["gh", "pr", "view"]:
            return json.dumps(PR)
        if cmd[:3] == ["gh", "issue", "view"]:
            return json.dumps(ISSUE)
        if cmd[:2] == ["gh", "api"]:
            check(cmd[2] == "repos/o/r/issues/comments/99", "Issue comment is fetched by ID")
            return json.dumps(COMMENT)
        if cmd[-2:] == ["rev-parse", "FETCH_HEAD"]:
            return fetched + "\n"
        if cmd[-2:] == ["rev-parse", "origin/main"]:
            return MAIN + "\n"
        if cmd[-2:] == ["rev-parse", "HEAD"]:
            return checkout_head + "\n"
        if "diff" in cmd:
            check(cmd[-1] == f"origin/main...{HEAD}", "diff is taken against the base")
            return "diff --git a/x b/x\n"
        return ""
    return runner


def build_args(out: Path, no_checkout: bool = False) -> argparse.Namespace:
    return argparse.Namespace(pr=7, out=out, issue=[15], comment=["https://github.com/o/r/issues/15#issuecomment-99"],
                              no_checkout=no_checkout, repo="o/r", git_dir=Path("/repo"))


# build
check(comment_id("123") == "123" and comment_id("https://x/issues/1#issuecomment-456") == "456",
      "comment ID is taken from an ID or URL")
expect_exit(lambda: comment_id("abc"), "invalid comment reference is rejected")

with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / "pkg"
    calls: list = []
    package = build(build_args(out), fake_runner(calls))
    materials = out / "materials"
    pr_md = (materials / "pr.md").read_text(encoding="utf-8")
    check("PR body" in pr_md and f"head: {HEAD}" in pr_md, "pr.md has the body and head")
    check("### bob 2026-10-12T01:02:03Z https://github.com/o/r/pull/7#issuecomment-11" in pr_md,
          "PR comments carry author, time and URL")
    check("issue body" in (materials / "issue-15.md").read_text(encoding="utf-8"), "Issue body is saved")
    comment_md = (materials / "comment-99.md").read_text(encoding="utf-8")
    check("dave" in comment_md and "2026-10-11T09:00:00Z" in comment_md and COMMENT["html_url"] in comment_md,
          "Issue comment carries author, time and URL")
    check((materials / "pr-diff.patch").read_text(encoding="utf-8").startswith("diff --git"), "diff is saved")
    check((materials / "main-sha.txt").read_text(encoding="utf-8").strip() == MAIN, "main SHA is saved")
    check(["git", "-C", "/repo", "worktree", "add", "--detach", str(out.resolve() / "checkout"), HEAD] in calls,
          "PR head is checked out as a detached worktree")
    check(json.loads((out / "package.json").read_text(encoding="utf-8")) == package
          and package["head"] == HEAD and package["checkout"] == str(out.resolve() / "checkout"),
          "package.json records the package")

with tempfile.TemporaryDirectory() as tmp:
    calls = []
    package = build(build_args(Path(tmp), no_checkout=True), fake_runner(calls))
    check(package["checkout"] is None and not any("worktree" in cmd for cmd in calls), "--no-checkout skips the worktree")

with tempfile.TemporaryDirectory() as tmp:
    message = expect_exit(lambda: build(build_args(Path(tmp)), fake_runner([], fetched="c" * 40)),
                          "a PR head that moved during build must stop")
    check("moved" in message, "moved head is explained")

with tempfile.TemporaryDirectory() as tmp:
    (Path(tmp) / "checkout").mkdir()
    expect_exit(lambda: build(build_args(Path(tmp)), fake_runner([], checkout_head="c" * 40)),
                "an existing checkout at another commit must stop")

# prompt
PACKAGE = {"pr": 7, "head": HEAD, "checkout": "/pkg/checkout", "materials": "/pkg/materials"}
template = DEFAULT_TEMPLATE.read_text(encoding="utf-8")
agy = render_prompt(PACKAGE, "agy", template)
codex = render_prompt(PACKAGE, "codex", template)
for text in (agy, codex):
    check(f"PR #7 の head `{HEAD}`" in text, "prompt names the PR and head")
    check("`/pkg/checkout/`" in text and "`/pkg/materials/`" in text, "prompt lists readable absolute paths")
    check(all(word in text for word in ("安全:", "秘密値:", "プロトコル:", "回収不能:")) and "「推奨」" in text,
          "criteria limit required findings to 4 categories")
    check("Verdict: MERGE_OK | CHANGES_REQUIRED" in text and "確認した範囲:" in text, "output format is fixed")
check("シェルは使えない" in agy and "再計算はせず" in agy, "agy is told it has no shell")
check("シェルは使えない" not in codex and "読み取りコマンド" in codex, "codex is told it may use read commands")

research = render_prompt(PACKAGE, "codex", (TEMPLATE_DIR / "research-note.md").read_text(encoding="utf-8"))
check("PR #7 は研究ノート" in research and "{{" not in research, "template placeholders are filled")
check("Feature Freeze" in research, "template perspectives are embedded")
expect_exit(lambda: render_prompt(PACKAGE, "agy", "{{UNKNOWN}}"), "unknown placeholder is rejected")

no_checkout = dict(PACKAGE, checkout=None)
text = render_prompt(no_checkout, "agy", template)
check("checkout:" not in text and "checkout はない" in text, "no-checkout prompt lists only materials")

agy_cmd = launch_command(PACKAGE, "agy", Path("/pkg/prompt-agy.md"), "m")
check("cd /pkg/checkout" in agy_cmd and "-p " in agy_cmd and "--mode plan --sandbox" in agy_cmd
      and "--add-dir /pkg/materials" in agy_cmd and "--output-format json" in agy_cmd
      and "--dangerously-skip-permissions" not in agy_cmd, "agy command follows AGENT_HARNESS.md")
codex_cmd = launch_command(PACKAGE, "codex", Path("/pkg/prompt-codex.md"), "m")
check("codex exec -C /pkg/checkout -s read-only -m m" in codex_cmd and "-o /pkg/review-codex.md" in codex_cmd,
      "codex command is read-only and saves the last message")
check("--add-dir" not in launch_command(no_checkout, "agy", Path("/p"), "m"), "no-checkout agy runs in materials")

with tempfile.TemporaryDirectory() as tmp:
    pkg = Path(tmp)
    (pkg / "package.json").write_text(json.dumps(dict(PACKAGE, materials=str(pkg / "materials"))), encoding="utf-8")
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        main(["prompt", "--package", str(pkg), "--reviewer", "agy"])
    written = (pkg / "prompt-agy.md").read_text(encoding="utf-8")
    check("シェルは使えない" in written and "agy -p" in stdout.getvalue() and "gemini-3.8-flash-high" in stdout.getvalue(),
          "prompt writes the file and prints the launch command")

# record
check(strip_file_links("see [a.md](file:///Users/x/a.md) and <file:///tmp/b> file:///c/d ok") == "see a.md and   ok",
      "file:// links are removed")
check(parse_review("**Verdict:** CHANGES_REQUIRED\n必須（merge を妨げる）: **2** 件\n推奨: 1 件")
      == {"verdict": "CHANGES_REQUIRED", "required": "2", "recommended": "1"}, "verdict and counts are parsed")
check(parse_review("no verdict")["verdict"] == "不明", "missing verdict is reported as unknown")

CODEX_OUT = "Verdict: MERGE_OK\n必須（merge を妨げる）: 0 件\n推奨: 1 件\n- [a.py:1] x\n確認した範囲:\n- diff\n"
AGY_JSON = {"conversation_id": "conv-1", "status": "SUCCESS",
            "response": "Verdict: MERGE_OK\n必須（merge を妨げる）: 0 件\n推奨: 0 件\n確認した範囲:\n- [x](file:///Users/me/x.md)\n"}

with tempfile.TemporaryDirectory() as tmp:
    codex_path = Path(tmp) / "review-codex.md"
    codex_path.write_text(CODEX_OUT, encoding="utf-8")
    agy_path = Path(tmp) / "review-agy.json"
    agy_path.write_text(json.dumps(AGY_JSON), encoding="utf-8")
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        main(["record", "--head", HEAD, "--date", "2026-10-12", "--codex", str(codex_path), "--codex-session", "s-1",
              "--codex-version", "0.160.1", "--agy", str(agy_path)])
    comment = stdout.getvalue()
    check(comment.startswith("## 独立レビュー（AI 独立 Reviewer 2 本）— 2026-10-12"), "record has a heading")
    check(f"対象 head: `{HEAD}`" in comment, "record names the reviewed head")
    check("| 1 | codex 0.160.1 / gpt-6-luna（read-only） | `s-1` | **MERGE_OK** | 0 | 1 |" in comment,
          "Codex row has runtime, model, session, verdict and counts")
    check("| 2 | antigravity / gemini-3.8-flash-high（plan + sandbox） | `conv-1` | **MERGE_OK** | 0 | 0 |" in comment,
          "agy row uses conversation_id as the session")
    check("file://" not in comment and "/Users/me" not in comment and "- x" in comment, "agy file links are removed")
    check("<details><summary>Reviewer 1（Codex）の出力</summary>" in comment and "- [a.py:1] x" in comment,
          "reviewer outputs are folded into details")

    agy_path.write_text(json.dumps({"conversation_id": "conv-2", "status": "SUCCESS", "response": "",
                                    "denied_actions": ["run_command"]}), encoding="utf-8")
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        main(["record", "--head", HEAD, "--agy", str(agy_path)])
    check("**不明**" in stdout.getvalue() and "response が空" in stdout.getvalue() and "run_command" in stdout.getvalue(),
          "an empty agy response is recorded with its denied actions")

    expect_exit(lambda: main(["record", "--head", HEAD, "--codex", str(codex_path)]), "Codex needs a session ID")
    expect_exit(lambda: main(["record", "--head", HEAD]), "record needs at least one reviewer")

print("review package tests OK")
