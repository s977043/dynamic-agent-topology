#!/usr/bin/env python3
"""Model-free tests for the hard-task calibration kit (dry-run and a local fake repository only)."""
from __future__ import annotations

from pathlib import Path
import contextlib
import io
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import hard_task_calibrate as htc  # noqa: E402


def check(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def run_cli(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = htc.main(argv)
    return rc, out.getvalue(), err.getvalue()


def dry_args(work: Path, prompt: Path, *extra: str) -> list[str]:
    return ["run", "--dry-run", "--work-root", str(work), "--prompt", str(prompt), "--timeout-s", "60",
            "--max-run-tokens", "200000", "--budget-tokens", "10000000", *extra]


def test_plan() -> None:
    runs = htc.plan(htc.load_candidates())
    ids = [r["runId"] for r in runs]
    check(len(ids) == 25 and len(set(ids)) == 25, "25 unique runs")
    check(ids[:5] == [f"HTC-0{i}-n1" for i in range(1, 6)], "rep-major order")
    check({r["order"] for r in runs} == {1, 2, 3, 4, 5}, "first five candidates")


def test_dry_run_and_summary(tmp: Path, prompt: Path) -> None:
    work = tmp / "ok"
    rc, out, err = run_cli(dry_args(work, prompt))
    check(rc == 0, f"dry-run rc {rc}: {err}")
    records = [json.loads(p.read_text()) for p in work.glob("HTC-*/run.json")]
    check(len(records) == 25, "25 records")
    check(all(r["status"] == "dry-run-ungraded" and r["dryRun"] for r in records), "dry-run status")
    check(all(r["command"][r["command"].index("-m") + 1] == "gpt-6.1-sol" for r in records), "model pinned")
    check(all("model_reasoning_effort=high" in r["command"] for r in records), "effort pinned")
    check(not (work / htc.LOCK_NAME).exists(), "lock released")
    summary = htc.summarize(work)
    check(summary["m"] == 1.0 and summary["runsFound"] == 25, "m from synthetic tokens")
    check(all(c["band"] == "INCOMPLETE" for c in summary["candidates"]), "ungraded runs are not banded")
    rc, _, err = run_cli(dry_args(work, prompt))
    check(rc == 2 and "refusing to overwrite" in err, "existing results refused")
    rc, out, _ = run_cli(dry_args(work, prompt, "--skip-existing"))
    check(rc == 0 and out.count("skip existing") == 25, "skip-existing leaves runs untouched")


def test_control_deviation(tmp: Path, prompt: Path) -> None:
    work = tmp / "dev"
    rc, _, err = run_cli(dry_args(work, prompt, "--dry-run-model", "gpt-6-luna", "--dry-run-effort", "medium"))
    check(rc == 2 and "control deviation" in err, "mismatch stops")
    records = [json.loads(p.read_text()) for p in work.glob("HTC-*/run.json")]
    check(len(records) == 1 and records[0]["status"] == "control-deviation", "stopped after the first run")


def test_limits_and_lock(tmp: Path, prompt: Path) -> None:
    work = tmp / "budget"
    rc, _, err = run_cli(dry_args(work, prompt)[:-1] + ["300000"])
    check(rc == 2 and "budget" in err and len(list(work.glob("HTC-*"))) == 2, "budget stop before third run")
    work = tmp / "tok"
    rc, _, err = run_cli(dry_args(work, prompt, "--dry-run-tokens", "300000"))
    check(rc == 2 and "exceeded" in err and len(list(work.glob("HTC-*"))) == 1, "per-run token limit stops")
    work = tmp / "lock"
    work.mkdir()
    (work / htc.LOCK_NAME).write_text("{}")
    rc, _, err = run_cli(dry_args(work, prompt))
    check(rc == 2 and "lock exists" in err and not list(work.glob("HTC-*")), "duplicate launch refused")
    rc, _, err = run_cli(dry_args(ROOT / "tmp-calibration", prompt))
    check(rc == 2 and "outside" in err, "work root inside repo refused")


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def test_workspace_and_grade(tmp: Path) -> None:
    mirror = tmp / "mirror"
    repo = mirror / "toy"
    (repo / "tests").mkdir(parents=True)
    git(tmp, "init", "-q", str(repo))
    (repo / "toy.py").write_text("def add(a, b):\n    return a - b\n")
    (repo / "tests/__init__.py").write_text("")
    (repo / "tests/test_toy.py").write_text("import unittest\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "base")
    base = git(repo, "rev-parse", "HEAD")
    (repo / "toy.py").write_text("def add(a, b):\n    return a + b\n")
    (repo / "tests/test_toy.py").write_text(
        "import unittest\nimport toy\n\nclass T(unittest.TestCase):\n"
        "    def test_add(self):\n        self.assertEqual(toy.add(1, 2), 3)\n")
    git(repo, "commit", "-qam", "fix add")
    fix = git(repo, "rev-parse", "HEAD")
    cand = {"order": 1, "repo": "https://example.invalid/o/toy", "revision": base, "fixCommit": fix,
            "acceptanceCriteria": {"testFilesFromFixCommit": ["tests/test_toy.py"],
                                   "command": "python3.12 -m unittest tests/test_toy.py",
                                   "failingBeforeFix": ["test_add (tests.test_toy.T.test_add)"]}}
    ws = tmp / "run1" / "workspace"
    ws.parent.mkdir()
    htc.prepare_workspace(cand, ws, mirror)
    check("return a - b" in (ws / "toy.py").read_text(), "workspace at the parent revision")
    check(subprocess.run(["git", "-C", str(ws), "cat-file", "-e", fix + "^{commit}"], capture_output=True).returncode != 0, "fix unreachable")
    ac_files = htc.load_ac_files([cand], mirror)[1]
    py = sys.executable
    check(not htc.grade(cand, ws, tmp / "run1" / "grade", ac_files, py)["verifiedSuccess"], "unfixed fails")
    (ws / "toy.py").write_text("def add(a, b):\n    return a + b\n")
    result = htc.grade(cand, ws, tmp / "run1" / "grade2", ac_files, py)
    check(result["verifiedSuccess"] and result["negativeOraclePassed"], "fixed passes")
    (ws / "tests/test_toy.py").write_text("import unittest\n")
    (ws / "toy.py").write_text("def add(a, b):\n    return 0\n")
    check(not htc.grade(cand, ws, tmp / "run1" / "grade3", ac_files, py)["verifiedSuccess"],
          "editing the visible test does not change the AC")


def main() -> int:
    test_plan()
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d).resolve()
        prompt = tmp / "prompt.md"
        prompt.write_text("Fix the bug in {repo} at {revision}.\n")
        test_dry_run_and_summary(tmp, prompt)
        test_control_deviation(tmp, prompt)
        test_limits_and_lock(tmp, prompt)
        test_workspace_and_grade(tmp)
    print("test_hard_task_calibrate: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
