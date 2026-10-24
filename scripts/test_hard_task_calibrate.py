#!/usr/bin/env python3
"""Model-free tests for the hard-task calibration kit (dry-run and a local fake repository only)."""
from __future__ import annotations

from pathlib import Path
import contextlib
import io
import json
import shutil
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
    return ["run", "--dry-run", "--work-root", str(work), "--task-dir", str(prompt), "--timeout-s", "60",
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
    work = tmp / "real"
    rc, _, err = run_cli([a for a in dry_args(work, prompt) if a != "--dry-run"])
    check(rc == 2 and not list(work.glob("HTC-*")), f"real run without isolation inputs stops before any Run: {err}")


def test_resume_counts_existing_tokens(tmp: Path, prompt: Path) -> None:
    work = tmp / "resume"
    base = dry_args(work, prompt)[:-1]
    rc, _, _ = run_cli(base + ["300000"])
    check(rc == 2 and len(list(work.glob("HTC-*"))) == 2, "first batch stops on budget")
    rc, out, err = run_cli(base + ["300000", "--skip-existing"])
    check(rc == 2 and "136044" in out and "budget" in err and len(list(work.glob("HTC-*"))) == 2,
          "resume counts existing tokens against the budget")
    rc, _, _ = run_cli(base + ["400000", "--skip-existing"])
    check(rc == 2 and len(list(work.glob("HTC-*"))) == 3, "resume with a larger budget adds only what fits")
    record = work / "HTC-03-n1" / "run.json"
    data = json.loads(record.read_text())
    del data["totalTokens"]
    record.write_text(json.dumps(data))
    rc, _, err = run_cli(base + ["10000000", "--skip-existing"])
    check(rc == 2 and "no totalTokens" in err and len(list(work.glob("HTC-*"))) == 3, "unknown usage stops resume")


class Args:
    codex_dir = "/opt/cx"
    auth_file = "/home/op/.codex/auth.json"


def test_container_isolation(tmp: Path) -> None:
    work = tmp / "iso"
    rdir = work / "HTC-01-n1"
    cmd = htc.docker_run_command(Args, rdir, "c")
    binds = [cmd[i + 1] for i, a in enumerate(cmd) if a == "-v"]
    check(len(binds) == 4, "four bind mounts")
    under_root = [b.split(":")[0] for b in binds if b.startswith(str(work))]
    check(all(s.startswith(str(rdir.resolve())) for s in under_root), "only this Run's files are mounted")
    check("--cap-drop" in cmd and "--read-only" in cmd and f"seccomp={htc.SECCOMP}" in cmd, "EXP-001 constraints")
    check(any(b.endswith(":/work") for b in binds) and all(b.endswith(":ro") for b in binds if not b.endswith(":/work")),
          "only /work is writable")
    expected = htc.expected_mounts(Args, rdir)
    profile = htc.SECCOMP.read_text(encoding="utf-8")
    compact = json.dumps(json.loads(profile), separators=(",", ":"))

    def inspect(mounts, **host):
        base = {"Privileged": False, "CapAdd": None, "CapDrop": ["ALL"], "ReadonlyRootfs": True,
                "Tmpfs": {"/tmp": "", htc.CODEX_HOME: "uid=1"},
                "SecurityOpt": [f"seccomp={compact}", "no-new-privileges"]}
        return {"Mounts": [{"Type": t, "Source": s, "Destination": d, "RW": rw} for t, s, d, rw in mounts],
                "HostConfig": {**base, **host}}

    evidence = htc.check_container(inspect(expected), expected, work.resolve())
    check(evidence["seccompMatchesLaunchedProfile"] and evidence["seccompLaunchedSha256"] == htc.SECCOMP_SHA256,
          "seccomp recorded against the launched profile")
    ro_work = [(t, s, d, False if d == "/work" else rw) for t, s, d, rw in expected]
    rw_auth = [(t, s, d, True if d.endswith("auth.json") else rw) for t, s, d, rw in expected]
    bad_cases = [
        (inspect(expected + [("bind", str(work / "HTC-02-n1"), "/past", False)]), expected, "extra bind"),
        (inspect(expected + [("volume", "v", "/data", True)]), expected, "volume mount"),
        (inspect(ro_work), expected, "RW flag on /work"),
        (inspect(rw_auth), expected, "writable auth.json"),
        (inspect(expected, Tmpfs={"/tmp": ""}), expected, "HostConfig.Tmpfs missing codex-home"),
        (inspect(expected, Tmpfs={"/tmp": "", htc.CODEX_HOME: "", "/var": ""}), expected, "extra tmpfs"),
        (inspect(expected, Privileged=True), expected, "privileged"),
        (inspect(expected, SecurityOpt=["seccomp=unconfined", "no-new-privileges"]), expected, "unconfined"),
        (inspect(expected, SecurityOpt=['seccomp={"defaultAction":"SCMP_ACT_ALLOW"}', "no-new-privileges"]),
         expected, "different seccomp profile"),
    ]
    wide = [(t, str(work.resolve()) if d == "/work" else s, d, rw) for t, s, d, rw in expected]
    bad_cases.append((inspect(wide), wide, "whole work root"))
    for bad, exp, why in bad_cases:
        try:
            htc.check_container(bad, exp, work.resolve())
        except htc.Stop:
            continue
        raise AssertionError(f"container check accepted {why}")
    link = tmp / "auth-link.json"
    link.symlink_to("/home/op/.codex/auth.json")
    linked = [(t, str(link) if d.endswith("auth.json") else s, d, rw) for t, s, d, rw in expected]
    htc.check_container(inspect(linked), expected, work.resolve())


def test_auth_probe() -> None:
    htc.check_auth_probe(0, "SANDBOX_ALIVE\nAUTH_DENIED\n")
    for rc, out, why in ((0, "AUTH_DENIED\n", "no liveness marker"),
                         (4, "SANDBOX_ALIVE\nUNKNOWN: unexpected error class\n", "unknown error class"),
                         (3, "SANDBOX_ALIVE\nBLOCK: sandbox can read auth file\n", "readable"),
                         (1, "SANDBOX_ALIVE\nAUTH_DENIED\n", "nonzero exit"),
                         (0, "", "empty")):
        try:
            htc.check_auth_probe(rc, out)
        except htc.Stop:
            continue
        raise AssertionError(f"auth probe accepted {why}")
    check("SANDBOX_ALIVE" in htc.AUTH_PROBE and "Permission denied" in htc.AUTH_PROBE, "probe matches EXP-001")


def test_task_descriptions(tmp: Path, tasks: Path) -> None:
    cands = htc.load_candidates()
    loaded = htc.load_task_descriptions(tasks, cands)
    check(sorted(loaded) == [1, 2, 3, 4, 5], "five descriptions")
    for content, why in ((cands[0]["fixSubject"], "fix subject"), (cands[0]["fixCommit"], "fix commit"),
                         ("{fixSubject}", "placeholder"), ("  \n", "empty")):
        bad = tmp / f"bad-{why.replace(' ', '-')}"
        shutil.copytree(tasks, bad)
        (bad / "order-01.md").write_text(content + "\n")
        try:
            htc.load_task_descriptions(bad, cands)
        except htc.Stop:
            continue
        raise AssertionError(f"task description accepted {why}")
    rc, _, err = run_cli(dry_args(tmp / "notask", tmp / "missing-dir"))
    check(rc == 2 and "missing" in err, "missing task directory stops")


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
    probe = htc.probe_ac_sandbox(py)
    check(probe["control"] == "CONNECTED" and probe["sandboxed"] in ("ERRNO EPERM", "ERRNO EACCES"),
          "local listener reachable outside, denied inside the sandbox")
    try:
        htc.probe_ac_sandbox("/usr/bin/false")
    except htc.Stop:
        pass
    else:
        raise AssertionError("probe accepted a failing control")
    net_test = {"tests/test_toy.py": (
        b"import socket, unittest\n\nclass T(unittest.TestCase):\n    def test_add(self):\n"
        b"        socket.create_connection(('1.1.1.1', 53), timeout=3)\n")}
    check(not htc.grade(cand, ws, tmp / "run1" / "grade4", net_test, py)["verifiedSuccess"], "AC has no network")


def main() -> int:
    test_plan()
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d).resolve()
        prompt = tmp / "tasks"
        prompt.mkdir()
        for order in range(1, 6):
            (prompt / f"order-{order:02d}.md").write_text(f"Symptom-only description for candidate {order}.\n")
        test_task_descriptions(tmp, prompt)
        test_auth_probe()
        test_dry_run_and_summary(tmp, prompt)
        test_control_deviation(tmp, prompt)
        test_limits_and_lock(tmp, prompt)
        test_resume_counts_existing_tokens(tmp, prompt)
        test_container_isolation(tmp)
        test_workspace_and_grade(tmp)
    print("test_hard_task_calibrate: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
