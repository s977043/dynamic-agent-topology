#!/usr/bin/env python3
"""Independent review kit: build a review package, generate reviewer prompts, render the PR record comment.

build  -- materials/ (PR, diff, Issues, Issue comments, main SHA) and a detached checkout of the PR head
prompt -- reviewer prompt from a perspective template (codex / agy) and the launch command example (not run)
record -- Markdown review record comment from the reviewer outputs (printed, not posted)
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = "s977043/dynamic-agent-topology"
TEMPLATE_DIR = ROOT / "scripts" / "review_templates"
DEFAULT_TEMPLATE = TEMPLATE_DIR / "general.md"
PACKAGE_FILE = "package.json"
REVIEWERS = ("codex", "agy")
DEFAULT_MODELS = {"codex": "gpt-6-luna", "agy": "gemini-3.8-flash-high"}
TEMPLATE_KEYS = ("PR", "HEAD", "CHECKOUT", "MATERIALS")
PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")
LOCAL_PATH = re.compile(r"(?<![\w.~-])/(?:Users|private/tmp)/[^\s`'\"()\[\]<>]*")
SUMMARY_LINES = {
    "verdict": ("Verdict", re.compile(r"\**Verdict\**\s*[:：]\s*\**\s*(MERGE_OK|CHANGES_REQUIRED)\s*\**")),
    "required": ("必須", re.compile(r"\**必須(?:（merge を妨げる）)?\**\s*[:：]\s*\**\s*(\d+)\s*\**\s*件\**")),
    "recommended": ("推奨", re.compile(r"\**推奨\**\s*[:：]\s*\**\s*(\d+)\s*\**\s*件\**")),
}

TOOLS_TEXT = {
    "codex": "ファイルの読み取りコマンド（cat・sed・grep・ls・git log / git show など）と作業ディレクトリの確認は使えます。",
    "agy": "シェルは使えないので、ファイル読み取りだけで判断してください。コマンドの再実行や値（ハッシュ・集計など）の再計算はせず、記録された値どうしを突き合わせてください。",
}

CRITERIA = """## 判定基準

「必須」は次の 4 分類に当てはまるものだけとします。

- 安全: 破壊的操作・権限の拡大・承認ゲートの迂回を招く
- 秘密値: token・鍵・個人情報などが含まれる
- プロトコル: Feature Freeze・自律境界・承認ゲートなど DAT の規定に反する
- 回収不能: merge 後に戻せない損失や Evidence の欠落を生む

それ以外（表現の改善、整合の細部、より良い書き方）は「推奨」とし、merge を妨げません。"""

OUTPUT_FORMAT = """## 出力（日本語）

```
Verdict: MERGE_OK | CHANGES_REQUIRED
必須（merge を妨げる）: N 件
- [ファイル:行] 問題 / 根拠 / 修正案
推奨: N 件
- [ファイル:行] 内容
確認した範囲:
```"""

Runner = Callable[[list[str]], str]


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"command failed ({result.returncode}): {shlex.join(cmd)}\n{result.stderr.strip()}")
    return result.stdout


# --- build -----------------------------------------------------------------


def comment_id(value: str) -> str:
    match = re.fullmatch(r"(?:.*#issuecomment-)?(\d+)", value.strip())
    if not match:
        raise SystemExit(f"--comment must be an Issue comment ID or URL: {value}")
    return match.group(1)


def render_pr(pr: dict) -> str:
    lines = [
        f"# PR #{pr['number']} {pr['title']}",
        f"URL: {pr['url']}",
        f"author: {pr['author']['login']}",
        f"head: {pr['headRefOid']}",
        f"base: {pr['baseRefName']} {pr['baseRefOid']}",
        "",
        "## Body",
        "",
        pr["body"] or "",
        "",
        "## Comments",
    ]
    for comment in pr["comments"]:
        lines += ["", f"### {comment['author']['login']} {comment['createdAt']} {comment['url']}", "", comment["body"]]
    return "\n".join(lines) + "\n"


def render_issue(issue: dict) -> str:
    return (
        f"# Issue #{issue['number']} {issue['title']}\nURL: {issue['url']}\n"
        f"author: {issue['author']['login']} created: {issue['createdAt']}\n\n{issue['body'] or ''}\n"
    )


def render_comment(comment: dict) -> str:
    return (
        f"# Issue comment {comment['id']}\nURL: {comment['html_url']}\n"
        f"author: {comment['user']['login']} created: {comment['created_at']}\n\n{comment['body'] or ''}\n"
    )


def build(args: argparse.Namespace, runner: Runner = run) -> dict:
    out = args.out.resolve()
    materials = out / "materials"
    checkout = out / "checkout"
    git = ["git", "-C", str(args.git_dir)]

    pr = json.loads(runner([
        "gh", "pr", "view", str(args.pr), "-R", args.repo, "--json",
        "number,title,url,author,body,comments,headRefOid,baseRefName,baseRefOid",
    ]))
    head = pr["headRefOid"]
    base = pr["baseRefName"]
    runner([*git, "fetch", "--quiet", "origin", f"refs/pull/{args.pr}/head"])
    fetched = runner([*git, "rev-parse", "FETCH_HEAD"]).strip()
    if fetched != head:
        raise SystemExit(f"PR head moved while building: gh reports {head}, fetched {fetched}; retry")
    runner([*git, "fetch", "--quiet", "origin", *dict.fromkeys(["main", base])])
    base_sha = runner([*git, "rev-parse", f"origin/{base}"]).strip()
    if base_sha != pr["baseRefOid"]:
        raise SystemExit(f"base {base} moved while building: gh reports {pr['baseRefOid']}, fetched {base_sha}; retry")
    main_sha = runner([*git, "rev-parse", "origin/main"]).strip()

    materials.mkdir(parents=True, exist_ok=True)
    (materials / "pr.md").write_text(render_pr(pr), encoding="utf-8")
    (materials / "pr-diff.patch").write_text(runner([*git, "diff", f"origin/{base}...{head}"]), encoding="utf-8")
    for number in args.issue:
        issue = json.loads(runner([
            "gh", "issue", "view", str(number), "-R", args.repo, "--json", "number,title,url,author,body,createdAt",
        ]))
        (materials / f"issue-{number}.md").write_text(render_issue(issue), encoding="utf-8")
    for value in args.comment:
        cid = comment_id(value)
        comment = json.loads(runner(["gh", "api", f"repos/{args.repo}/issues/comments/{cid}"]))
        (materials / f"comment-{cid}.md").write_text(render_comment(comment), encoding="utf-8")
    (materials / "main-sha.txt").write_text(main_sha + "\n", encoding="utf-8")

    if not args.no_checkout:
        if checkout.exists():
            current = runner(["git", "-C", str(checkout), "rev-parse", "HEAD"]).strip()
            if current != head:
                raise SystemExit(f"{checkout} exists at {current}, not PR head {head}; remove it or use another --out")
            if runner(["git", "-C", str(checkout), "status", "--porcelain"]).strip():
                raise SystemExit(f"{checkout} has uncommitted changes; remove it or use another --out")
        else:
            runner([*git, "worktree", "add", "--detach", str(checkout), head])

    package = {
        "repo": args.repo,
        "pr": pr["number"],
        "head": head,
        "base": base,
        "main": main_sha,
        "materials": str(materials),
        "checkout": None if args.no_checkout else str(checkout),
    }
    (out / PACKAGE_FILE).write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return package


# --- prompt ----------------------------------------------------------------


def fill_template(template: str, values: dict[str, str]) -> str:
    unknown = sorted(set(PLACEHOLDER.findall(template)) - set(values))
    if unknown:
        raise SystemExit(f"unknown template placeholder(s): {', '.join(unknown)}; use {', '.join(TEMPLATE_KEYS)}")
    return PLACEHOLDER.sub(lambda m: values[m.group(1)], template)


def render_prompt(package: dict, reviewer: str, template: str) -> str:
    checkout = package["checkout"]
    materials = package["materials"]
    values = {"PR": str(package["pr"]), "HEAD": package["head"], "CHECKOUT": checkout or "", "MATERIALS": materials}
    workdir = (
        f"作業ディレクトリは PR #{package['pr']} の head `{package['head']}` の checkout です。"
        if checkout else
        f"PR #{package['pr']} の head は `{package['head']}` です。checkout はないので、差分（`pr-diff.patch`）で判断してください。"
    )
    dirs = [f"- checkout: `{checkout}/`"] if checkout else []
    dirs.append(
        f"- 材料: `{materials}/`（`pr.md`＝PR 本文とコメント、`pr-diff.patch`＝base との差分、"
        "`issue-*.md`＝関連 Issue、`comment-*.md`＝関連 Issue コメント、`main-sha.txt`＝main の SHA）"
    )
    return "\n".join([
        f"あなたは dynamic-agent-topology（DAT）の独立 Reviewer です。PR #{package['pr']} の作成には関与していません。"
        f"{workdir}読み取り専用で作業し、ファイル編集・git 書き込み・ネットワークアクセスはしないでください。",
        TOOLS_TEXT[reviewer],
        "読めるのは次のディレクトリの中だけです（絶対パス）。",
        *dirs,
        "判断に必要な材料はここにそろえています。足りない材料があれば推測で補わず、「確認した範囲」に未確認として書いてください。",
        "指摘箇所や確認した範囲には、リポジトリ相対パス（例: `scripts/x.py:12`）や `materials/pr.md` の形を使い、絶対パスは書かないでください（記録は公開されます）。",
        "",
        "## 観点",
        "",
        fill_template(template, values).strip(),
        "",
        CRITERIA,
        "",
        OUTPUT_FORMAT,
        "",
    ])


def launch_command(package: dict, reviewer: str, prompt_path: Path, model: str) -> str:
    pkg = Path(package["materials"]).parent
    workdir = package["checkout"] or package["materials"]
    q = shlex.quote
    if reviewer == "codex":
        return (
            f"codex exec -C {q(workdir)} -s read-only -m {q(model)} -c model_reasoning_effort=high "
            f"-o {q(str(pkg / 'review-codex.md'))} \"$(cat {q(str(prompt_path))})\" "
            f"> {q(str(pkg / 'review-codex-log.txt'))} 2>&1\n"
            f"# session ID: grep '^session id:' {q(str(pkg / 'review-codex-log.txt'))}"
        )
    add_dir = f"--add-dir {q(package['materials'])} " if package["checkout"] else ""
    return (
        f"(cd {q(workdir)} && agy -p \"$(cat {q(str(prompt_path))})\" --model {q(model)} --mode plan --sandbox "
        f"{add_dir}--output-format json --print-timeout 1500s > {q(str(pkg / 'review-agy.json'))})"
    )


def load_package(path: Path) -> dict:
    file = path / PACKAGE_FILE
    if not file.is_file():
        raise SystemExit(f"{file} not found; run `build` first")
    return json.loads(file.read_text(encoding="utf-8"))


def prompt(args: argparse.Namespace) -> str:
    package = load_package(args.package.resolve())
    text = render_prompt(package, args.reviewer, args.template.read_text(encoding="utf-8"))
    prompt_path = args.package.resolve() / f"prompt-{args.reviewer}.md"
    prompt_path.write_text(text, encoding="utf-8")
    model = args.model or DEFAULT_MODELS[args.reviewer]
    return (
        f"prompt: {prompt_path}\n\n"
        f"# 起動コマンド例（このスクリプトは実行しない）\n{launch_command(package, args.reviewer, prompt_path, model)}\n"
    )


# --- record ----------------------------------------------------------------


def strip_file_links(text: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\(file://[^)]*\)", r"\1", text)
    text = re.sub(r"<file://[^>]*>", "", text)
    return re.sub(r"file://[^\s`'\"()\[\]<>]+", "", text)


def local_replacements(package: dict | None) -> list[tuple[str, str]]:
    pairs = []
    if package:
        pairs += [(package[key], f"<{key}>") for key in ("checkout", "materials") if package.get(key)]
    pairs.append((str(Path.home()), "~"))
    # macOS reports /tmp paths under /private/tmp; reviewers may print either form.
    pairs += [(path.removeprefix("/private"), label) for path, label in pairs if path.startswith("/private/tmp/")]
    return sorted(pairs, key=lambda pair: len(pair[0]), reverse=True)


def sanitize(text: str, replacements: list[tuple[str, str]]) -> str:
    """Remove file:// links and local absolute paths from text that will be posted publicly."""
    text = strip_file_links(text)
    for path, label in replacements:
        text = re.sub(re.escape(path) + r"(?![\w.-])", label, text)
    return LOCAL_PATH.sub("<local-path>", text)


def parse_review(text: str) -> tuple[dict, list[str]]:
    """Read verdict and counts only from the prescribed summary lines; anything but exactly one line is unknown."""
    hits: dict[str, list[str]] = {key: [] for key in SUMMARY_LINES}
    for line in text.splitlines():
        for key, (_, pattern) in SUMMARY_LINES.items():
            match = pattern.fullmatch(line.strip())
            if match:
                hits[key].append(match.group(1))
    parsed, notes = {}, []
    for key, (label, _) in SUMMARY_LINES.items():
        if len(hits[key]) == 1:
            parsed[key] = hits[key][0]
        else:
            parsed[key] = "不明"
            found = f" {len(hits[key])} 行ある" if hits[key] else "見つからない"
            notes.append(f"{label} のサマリー行が{found}ため、確定値を記録していません")
    return parsed, notes


def load_agy(path: Path) -> tuple[str, str, str]:
    """Return (conversation_id, response, note) from `agy --output-format json`."""
    data = json.loads(path.read_text(encoding="utf-8"))
    response = data.get("response") or ""
    note = ""
    if not response.strip():
        denied = data.get("denied_actions")
        note = f"response が空です（status: {data.get('status')}、denied_actions: {json.dumps(denied, ensure_ascii=False)}）"
    return data.get("conversation_id") or "不明", response, note


def runtime_label(name: str, version: str | None) -> str:
    return f"{name} {version}" if version else name


def record(args: argparse.Namespace) -> str:
    replacements = local_replacements(load_package(args.package.resolve()) if args.package else None)
    reviewers = []
    if args.codex:
        if not args.codex_session:
            raise SystemExit("--codex needs --codex-session")
        reviewers.append({
            "name": "Codex",
            "runtime": f"{runtime_label('codex', args.codex_version)} / {args.codex_model}（read-only）",
            "session": args.codex_session,
            "output": sanitize(args.codex.read_text(encoding="utf-8"), replacements),
            "note": "",
        })
    if args.agy:
        session, response, note = load_agy(args.agy)
        reviewers.append({
            "name": "Antigravity",
            "runtime": f"{runtime_label('antigravity', args.agy_version)} / {args.agy_model}（plan + sandbox）",
            "session": session,
            "output": sanitize(response, replacements),
            "note": sanitize(note, replacements),
        })
    if not reviewers:
        raise SystemExit("record needs --codex and/or --agy")

    lines = [
        f"## 独立レビュー（AI 独立 Reviewer {len(reviewers)} 本）— {args.date}",
        "",
        f"対象 head: `{args.head}`（PR の作成に関与していない新規セッション）。"
        "必須は 4 分類（安全・秘密値・プロトコル・回収不能）だけです。",
        "",
        "| Reviewer | runtime / model | session | Verdict | 必須 | 推奨 |",
        "|---|---|---|---|---|---|",
    ]
    notes = []
    for i, reviewer in enumerate(reviewers, 1):
        parsed, parse_notes = parse_review(reviewer["output"])
        notes += [f"- Reviewer {i}: {note}" for note in parse_notes]
        lines.append(
            f"| {i} | {reviewer['runtime']} | `{reviewer['session']}` | **{parsed['verdict']}** "
            f"| {parsed['required']} | {parsed['recommended']} |"
        )
    if notes:
        lines += ["", "注記（`不明` の理由。出力の本文で確認してください）:", "", *notes]
    for i, reviewer in enumerate(reviewers, 1):
        lines += ["", f"<details><summary>Reviewer {i}（{reviewer['name']}）の出力</summary>", ""]
        if reviewer["note"]:
            lines.append(reviewer["note"])
        else:
            lines.append(reviewer["output"].strip())
        lines += ["", "</details>"]
    return "\n".join(lines) + "\n"


# --- CLI -------------------------------------------------------------------


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("build", help="materials/ と PR head の checkout/ を作る")
    b.add_argument("pr", type=int)
    b.add_argument("--out", type=Path, required=True, help="パッケージの出力ディレクトリ")
    b.add_argument("--issue", type=int, action="append", default=[], help="本文を入れる Issue 番号（複数可）")
    b.add_argument("--comment", action="append", default=[], help="入れる Issue コメントの ID または URL（複数可）")
    b.add_argument("--no-checkout", action="store_true", help="checkout/ を作らない")
    b.add_argument("--repo", default=DEFAULT_REPO)
    b.add_argument("--git-dir", type=Path, default=ROOT, help="worktree を作る元の git repository")

    pr_ = sub.add_parser("prompt", help="レビュー依頼文を生成し、起動コマンド例を表示する")
    pr_.add_argument("--package", type=Path, required=True, help="build の出力ディレクトリ")
    pr_.add_argument("--reviewer", choices=REVIEWERS, required=True)
    pr_.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="観点テンプレート")
    pr_.add_argument("--model", help="起動コマンド例に入れる model（既定: codex は gpt-6-luna、agy は gemini-3.8-flash-high）")

    r = sub.add_parser("record", help="PR に投稿するレビュー記録コメントを標準出力に出す")
    r.add_argument("--head", required=True, help="レビューした PR head の SHA")
    r.add_argument("--package", type=Path, help="build の出力ディレクトリ（checkout・materials のパスを伏せる）")
    r.add_argument("--codex", type=Path, help="codex exec -o の出力ファイル")
    r.add_argument("--codex-session", help="Codex の session ID")
    r.add_argument("--codex-model", default=DEFAULT_MODELS["codex"])
    r.add_argument("--codex-version", help="例: 0.160.1")
    r.add_argument("--agy", type=Path, help="agy --output-format json の出力ファイル")
    r.add_argument("--agy-model", default=DEFAULT_MODELS["agy"], help="agy の --model に明示した値")
    r.add_argument("--agy-version", help="例: 1.3.3")
    r.add_argument("--date", default=date.today().isoformat())
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "build":
        package = build(args)
        print(json.dumps(package, ensure_ascii=False, indent=2))
    elif args.command == "prompt":
        print(prompt(args), end="")
    else:
        print(record(args), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
