#!/usr/bin/env python3
"""Model-free tests for the hard-task calibration kit (dry-run and a local fake repository only)."""
from __future__ import annotations

from pathlib import Path
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types

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


def test_retry_never_launched(tmp: Path, prompt: Path) -> None:
    work = tmp / "retry"
    rc, _, _ = run_cli(dry_args(work, prompt))
    check(rc == 0, "full dry batch")
    stopped = work / "HTC-02-n3"
    record = json.loads((stopped / "run.json").read_text())
    record.update({"status": "isolation-stop", "modelLaunched": False, "stopReason": "mounts differ"})
    record.pop("totalTokens")
    (stopped / "run.json").write_text(json.dumps(record))
    summary = htc.summarize(work)
    check(summary["m"] == 1.0 and summary["totalTokensSpent"] == 24 * 68022, "never-launched Run not in m or spend")
    rc, out, err = run_cli(dry_args(work, prompt, "--skip-existing"))
    check(rc == 0 and "retry HTC-02-n3" in out and out.count("skip existing") == 24, f"retried: {err}")
    kept = work / "attempts" / "HTC-02-n3" / "attempt-1" / "run.json"
    check(json.loads(kept.read_text())["status"] == "isolation-stop", "failed attempt preserved")
    check(json.loads((stopped / "run.json").read_text())["status"] == "dry-run-ungraded", "Run re-executed")
    check(htc.summarize(work)["runsFound"] == 25, "25 Runs after retry")
    launched = json.loads((work / "HTC-01-n1" / "run.json").read_text())
    launched.update({"status": "isolation-stop", "modelLaunched": True})
    (work / "HTC-01-n1" / "run.json").write_text(json.dumps(launched))
    rc, out, _ = run_cli(dry_args(work, prompt, "--skip-existing"))
    check(rc == 0 and "retry" not in out, "a Run that launched the model is not retried")


def test_missing_launch_flag(tmp: Path, prompt: Path) -> None:
    work = tmp / "legacy"
    rc, _, _ = run_cli(dry_args(work, prompt))
    check(rc == 0, "full dry batch")
    path = work / "HTC-03-n2" / "run.json"
    record = json.loads(path.read_text())
    record.pop("modelLaunched")
    record.update({"status": "isolation-stop", "totalTokens": 0})
    path.write_text(json.dumps(record))
    rc, _, err = run_cli(dry_args(work, prompt, "--skip-existing"))
    check(rc == 2 and str(path) in err and "modelLaunched" in err, "resume stops on a record without the flag")
    rc, _, err = run_cli(["summarize", "--work-root", str(work)])
    check(rc == 2 and str(path) in err, "summarize stops on a record without the flag")
    record["modelLaunched"] = "no"
    path.write_text(json.dumps(record))
    rc, _, err = run_cli(["summarize", "--work-root", str(work)])
    check(rc == 2 and str(path) in err, "non-boolean flag stops")


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
    if not Path("/usr/bin/sandbox-exec").exists():
        try:
            htc.probe_ac_sandbox(py)
        except htc.Stop:
            pass
        else:
            raise AssertionError("probe ran without sandbox-exec")
        print("skip: /usr/bin/sandbox-exec not found; grade and AC sandbox probe checks skipped")
        return
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


def write_reuse(root: Path) -> None:
    """Synthetic calibration results: 1, 4 succeed; 2, 3 fail n1..n3 (2 succeeds at n4); 5 succeeds n1..n4."""
    successes = {1: {1, 2, 3, 4, 5}, 2: {4}, 3: set(), 4: {1, 2, 3, 4, 5}, 5: {1, 2, 3, 4}}
    cands = {c["order"]: c for c in htc.load_candidates()}
    for order, ok in successes.items():
        for k in range(1, 6):
            rdir = root / f"HTC-{order:02d}-n{k}"
            rdir.mkdir(parents=True)
            rec = {"runId": rdir.name, "order": order, "calRep": k, "dryRun": False, "status": "completed",
                   "repo": cands[order]["repo"], "revision": cands[order]["revision"],
                   "modelLaunched": True, "verifiedSuccess": k in ok, "totalTokens": 1000 * order,
                   "trace": {"contexts": [[htc.MODEL, htc.EFFORT]], "cliVersion": "0.160.1"}}
            (rdir / "run.json").write_text(json.dumps(rec))


def screen_args(work: Path, reuse: Path, tasks: Path, *extra: str, budget: str = "50000000",
                cand: str = "10000000", run: str = "4000000") -> list[str]:
    return ["screen", "--dry-run", "--work-root", str(work), "--reuse-root", str(reuse), "--task-dir", str(tasks),
            "--timeout-s", "1800", "--max-run-tokens", run, "--max-candidate-tokens", cand, "--budget-tokens", budget,
            *extra]


def test_screen_constants() -> None:
    text = (ROOT / "docs/HARD_TASK_T0_FAIL_T1_PREREGISTRATION_ADDENDUM_1.md").read_text(encoding="utf-8")
    section = text.split("## 2.", 1)[1].split("## 3.", 1)[0]
    listed = tuple(int(m) for m in re.findall(r"^\| (\d+) \| `https://", section, flags=re.M))
    check(listed == htc.PRE_EXCLUDED, f"PRE_EXCLUDED {htc.PRE_EXCLUDED} != addendum 1 §2 {listed}")
    missing = tuple(o for o in range(6, 45)
                    if not (ROOT / f"docs/hard-task/task-descriptions/order-{o:02d}.md").exists())
    check(missing == htc.PRE_EXCLUDED, "pre-excluded orders are exactly those without a task description")
    check(len(htc.screen_targets(htc.load_screen_candidates())) == 32, "32 candidates to screen")
    check({p.name for p in htc.SCREEN_BLOBS} == {"HARD_TASK_T0_FAIL_T1_PREREGISTRATION.md",
                                                 "HARD_TASK_T0_FAIL_T1_PREREGISTRATION_ADDENDUM_1.md", "CANDIDATES.yaml"},
          "screening checks the second edition, addendum 1, and the candidate table")
    rc, out, _ = run_cli(["screen-plan"])
    lines = out.splitlines()
    check(rc == 0 and len(lines) == 45, "44 candidates plus the stop rule")
    check(all("pre-excluded" in lines[o - 1] for o in htc.PRE_EXCLUDED), "plan shows pre-excluded orders")
    check(all("reuse HTC-0" in lines[o - 1] for o in range(1, 6)), "plan shows reuse for 1..5")
    check(lines[5].startswith("06\tHTS-06-n1"), "screening Run IDs do not collide with calibration")


def test_screen_flow(tmp: Path, reuse: Path, tasks: Path) -> None:
    work = tmp / "screen"
    rc, out, err = run_cli(screen_args(work, reuse, tasks, "--dry-run-success", "6,8"))
    check(rc == 0 and "target-reached" in out, f"screen dry-run: {err}")
    check(not list(work.glob("HTS-06-n2")) and (work / "HTS-06-n1").exists(), "truncated at the first success")
    check(all(not list(work.glob(f"HTS-{o:02d}-*")) for o in htc.PRE_EXCLUDED), "pre-excluded orders never run")
    check(not list(work.glob("HTS-21-*")), "stops when 12 candidates are 0/3")
    check(len(list(work.glob("HTS-*/run.json"))) == 1 + 3 + 1 + 9 * 3, "32 Runs")
    check(not (work / htc.LOCK_NAME).exists(), "lock released")
    s = htc.screen_summarize(work, reuse)
    check(s["selectedZero"] == [2, 3, 7, 9, 12, 13, 14, 15, 17, 18, 19, 20], f"selected {s['selectedZero']}")
    check(not s["feasibilityOnly"] and s["stopReason"] == "target-reached" and s["dryRun"], "stop reason")
    check(s["truncated"] == [1, 4, 5, 6, 8], "reuse uses n1..n3 only; screening truncates")
    check(s["preExcluded"] == list(htc.PRE_EXCLUDED) and not s["budgetExcluded"], "pre-excluded are not budget-excluded")
    rows = {r["order"]: r for r in s["candidates"]}
    check(all(rows[o]["outcome"] == "pre-excluded" and rows[o]["runs"] == [] for o in htc.PRE_EXCLUDED), "pre-excluded rows")
    check([r["k"] for r in rows[2]["runs"]] == [1, 2, 3], "reuse reads n1..n3 only")
    check(rows[21]["outcome"] == "not-started", "candidates after the stop are not started")
    check(s["screeningTokens"] == 32 * 68022 and s["reusedTokensNotCounted"] == 3 * 1000 * 15, "token accounting")
    rc, _, err = run_cli(screen_args(work, reuse, tasks))
    check(rc == 2 and "refusing to overwrite" in err, "existing screening results refused")
    rc, out, _ = run_cli(screen_args(work, reuse, tasks, "--skip-existing"))
    check(rc == 0 and "target-reached" in out and len(list(work.glob("HTS-*/run.json"))) == 32,
          "resume runs nothing new")
    rc, _, err = run_cli(screen_args(ROOT / "tmp-screen", reuse, tasks))
    check(rc == 2 and "outside" in err, "work root inside repo refused")
    work = tmp / "screen-real"
    rc, _, err = run_cli([a for a in screen_args(work, reuse, tasks) if a != "--dry-run"])
    check(rc == 2 and not list(work.glob("HTS-*")), f"real screen without isolation inputs stops before any Run: {err}")


def test_screen_limits(tmp: Path, reuse: Path, tasks: Path) -> None:
    work = tmp / "cand-cap"
    rc, out, _ = run_cli(screen_args(work, reuse, tasks, "--dry-run-success", ",".join(str(o) for o in range(7, 45)),
                                     run="100000", cand="200000"))
    check(rc == 0 and not (work / "HTS-06-n3").exists() and (work / "HTS-07-n1").exists(),
          "candidate cap: third Run not started, next candidate continues")
    s = htc.screen_summarize(work, reuse)
    check([b["order"] for b in s["budgetExcluded"]] == [6] and 6 not in s["selectedZero"], "budget-excluded, not 0/3")
    check(s["feasibilityOnly"] and s["stopReason"] == "candidates-exhausted", "feasibility-only when exhausted")
    work = tmp / "global-cap"
    rc, _, err = run_cli(screen_args(work, reuse, tasks, run="100000", cand="1000000", budget="300000"))
    check(rc == 2 and "budget" in err and len(list(work.glob("HTS-*/run.json"))) == 3, "global cap stops before Run 4")
    s = htc.screen_summarize(work, reuse)
    check(s["stopReason"].startswith("budget") and s["feasibilityOnly"] and s["screeningTokens"] == 3 * 68022,
          "stop reason recorded; reuse not counted against the budget")
    rc, out, err = run_cli(screen_args(work, reuse, tasks, "--skip-existing", run="100000", cand="1000000",
                                     budget="400000"))
    check(rc == 2 and "204066" in out and len(list(work.glob("HTS-*/run.json"))) == 5,
          "resume counts existing tokens and adds only what fits")
    work = tmp / "run-cap"
    rc, _, err = run_cli(screen_args(work, reuse, tasks, "--dry-run-tokens", "150000", run="100000"))
    check(rc == 2 and "exceeded" in err and len(list(work.glob("HTS-*/run.json"))) == 1, "per-run overrun stops")
    s = htc.screen_summarize(work, reuse)
    excluded = s["budgetExcluded"][0]
    check(excluded["order"] == 6 and 6 not in s["selectedZero"] and excluded["tokens"] == 150000,
          "overrun Run is not a failure and its spend is kept")
    check(excluded["reason"].startswith("token limit: HTS-06-n1") and "150000" in excluded["reason"] and "100000" in excluded["reason"],
          f"reason names the usage and the limit: {excluded['reason']}")
    work = tmp / "cand-exact"
    rc, _, _ = run_cli(screen_args(work, reuse, tasks, "--dry-run-success", "7", run="100000", cand="168022", budget="168022"))
    check(rc == 2 and (work / "HTS-06-n2").exists(), "spent + max per run equal to the caps starts the Run")
    work = tmp / "cand-one-less"
    rc, _, _ = run_cli(screen_args(work, reuse, tasks, run="100000", cand="168021", budget="1000000"))
    check(not (work / "HTS-06-n2").exists() and (work / "HTS-06.budget-excluded.json").exists(), "one token less does not")
    work = tmp / "budget-one-less"
    rc, _, err = run_cli(screen_args(work, reuse, tasks, run="100000", cand="1000000", budget="168021"))
    check(rc == 2 and "budget" in err and not (work / "HTS-06-n2").exists(), "one token less of the budget stops")
    work = tmp / "args"
    try:
        run_cli([a for a in screen_args(work, reuse, tasks) if a not in ("--max-candidate-tokens", "10000000")])
    except SystemExit as exc:
        check(exc.code == 2, "missing limit is a usage error")
    else:
        raise AssertionError("screen accepted a missing --max-candidate-tokens")


def test_screen_reuse_and_blobs(tmp: Path, reuse: Path, tasks: Path) -> None:
    for name, mutate in (("missing", lambda rec, p: p.unlink()),
                         ("timeout", lambda rec, p: p.write_text(json.dumps({**rec, "status": "aborted-timeout"}))),
                         ("dry", lambda rec, p: p.write_text(json.dumps({**rec, "dryRun": True}))),
                         ("version", lambda rec, p: p.write_text(json.dumps(
                             {**rec, "trace": {**rec["trace"], "cliVersion": "0.159.0"}}))),
                         ("not-launched", lambda rec, p: p.write_text(json.dumps({**rec, "modelLaunched": False}))),
                         ("no-launch-flag", lambda rec, p: p.write_text(json.dumps(
                             {a: b for a, b in rec.items() if a != "modelLaunched"}))),
                         ("revision", lambda rec, p: p.write_text(json.dumps({**rec, "revision": "0" * 40}))),
                         ("repo", lambda rec, p: p.write_text(json.dumps({**rec, "repo": "https://example.invalid/x"}))),
                         ("run-id", lambda rec, p: p.write_text(json.dumps({**rec, "runId": "HTC-03-n3"})))):
        bad = tmp / f"reuse-{name}"
        shutil.copytree(reuse, bad)
        path = bad / "HTC-03-n2" / "run.json"
        mutate(json.loads(path.read_text()), path)
        work = tmp / f"screen-{name}"
        rc, _, err = run_cli(screen_args(work, bad, tasks))
        check(rc == 2 and "reuse" in err and not list(work.glob("HTS-*")), f"unusable reuse ({name}) stops")
    saved = dict(htc.SCREEN_BLOBS)
    for path in saved:
        htc.SCREEN_BLOBS[path] = "0" * 40
        work = tmp / f"blob-{path.stem}"
        rc, _, err = run_cli(screen_args(work, reuse, tasks))
        htc.SCREEN_BLOBS.update(saved)
        check(rc == 2 and "blob mismatch" in err and not work.exists(), f"blob mismatch stops ({path.name})")


def test_screen_record_states(tmp: Path, reuse: Path, tasks: Path) -> None:
    check(htc.run_outcome({"runId": "x", "status": "aborted-timeout"}) == "budget-excluded", "timeout is not a failure")
    check(htc.run_outcome({"runId": "x", "status": "control-deviation"}) == "control-deviation",
          "control deviation is kept apart from the outcomes")
    try:
        htc.run_outcome({"runId": "x", "status": "started"})
    except htc.Stop:
        pass
    else:
        raise AssertionError("classified status started")
    work = tmp / "mix"
    rc, _, _ = run_cli(screen_args(work, reuse, tasks, budget="300000", run="100000"))
    check(rc == 2 and (work / "HTS-06-n1").exists(), "partial dry batch")
    args = htc.parser().parse_args([a for a in screen_args(work, reuse, tasks, "--skip-existing") if a != "--dry-run"])
    saved = htc.preflight_screen
    htc.preflight_screen = lambda _a: None
    try:
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            rc = htc.cmd_screen(args)
    finally:
        htc.preflight_screen = saved
    check(rc == 2 and "must not mix" in err.getvalue(), "real resume over synthetic Runs stops")
    work = tmp / "started"
    rc, _, _ = run_cli(screen_args(work, reuse, tasks, budget="300000", run="100000"))
    path = work / "HTS-06-n1" / "run.json"
    record = json.loads(path.read_text())
    record.update({"status": "started", "modelLaunched": False})
    record.pop("totalTokens")
    path.write_text(json.dumps(record))
    rc, _, err_text = run_cli(screen_args(work, reuse, tasks, "--skip-existing"))
    check(rc == 2 and "no totalTokens" in err_text, "Run left in started state (e.g. timeout without a trace) stops resume")


class FakeRealRun:
    """Drives the real (non-dry) run path with the container, workspace, and grading replaced; no model or container."""

    def __init__(self, timeouts: dict[str, bool], success_at: dict[int, int] | None = None):
        self.timeouts, self.success_at = timeouts, success_at or {}

    def container(self, args, rdir, _prompt, evidence, _on_launched=None):
        evidence["modelLaunched"] = True
        if self.timeouts.get(rdir.name) is False:  # timed out with no usable trace
            return None, evidence
        htc.fake_codex(args, rdir / "sessions")
        evidence["timeoutTrace"] = {"killExitCode": 0, "collectedAfterKill": True, "stopExitCode": 0}
        return (None if rdir.name in self.timeouts else 0), evidence

    def grade(self, cand, ws, _grade_dir, _ac, _py):
        k = int(ws.parent.name.rsplit("n", 1)[1])
        return {"verifiedSuccess": self.success_at.get(cand["order"]) == k, "acExitCode": 0}

    def __enter__(self):
        names = ("container_exec_codex", "grade", "prepare_workspace", "load_ac_files", "preflight_screen", "preflight")
        self.saved = {n: getattr(htc, n) for n in names}
        htc.container_exec_codex = self.container
        htc.grade = self.grade
        htc.prepare_workspace = lambda _c, ws, _m: ws.mkdir()
        htc.load_ac_files = lambda _c, _m: {}
        htc.preflight_screen = htc.preflight = lambda *_a: None
        return self

    def __exit__(self, *_exc):
        for name, value in self.saved.items():
            setattr(htc, name, value)


def real_args(args: list[str]) -> list[str]:
    return [a for a in args if a != "--dry-run"]


def test_timeout_reaches_aborted(tmp: Path, reuse: Path, tasks: Path) -> None:
    work = tmp / "to-known"
    limits = {"run": "100000", "cand": "1000000", "budget": "10000000"}
    with FakeRealRun({"HTS-06-n1": True}, {o: 1 for o in range(7, 45)}):
        rc, _, err = run_cli(real_args(screen_args(work, reuse, tasks, **limits)))
    check(rc == 0, f"known usage: batch continues after a timeout: {err}")
    record = json.loads((work / "HTS-06-n1" / "run.json").read_text())
    check(record["status"] == "aborted-timeout" and record["modelLaunched"] is True and record["totalTokens"] == 68022
          and record["tokenUsageKnown"] is True and "timeout-s" in record["stopReason"], f"saved: {record}")
    check(not (work / "HTS-06-n2").exists(), "candidate stops at the timeout")
    s = htc.screen_summarize(work, reuse)
    check(s["budgetExcluded"][0]["order"] == 6 and 6 not in s["selectedZero"] and s["budgetExcluded"][0]["tokens"] == 68022
          and "68022" in s["budgetExcluded"][0]["reason"] and not s["usageUnknownRuns"], "known timeout is budget-excluded")

    work = tmp / "to-unknown"
    with FakeRealRun({"HTS-06-n1": False}):
        rc, _, err = run_cli(real_args(screen_args(work, reuse, tasks, **limits)))
    check(rc == 2 and "unknown" in err, "unknown usage stops the batch")
    path = work / "HTS-06-n1" / "run.json"
    record = json.loads(path.read_text())
    check(record["status"] == "aborted-timeout" and record["modelLaunched"] is True and record["tokenUsageKnown"] is False
          and "totalTokens" not in record, f"saved without a guess: {record}")
    s = htc.screen_summarize(work, reuse)
    check(s["usageUnknownRuns"] == ["HTS-06-n1"] and s["budgetExcluded"][0]["usageUnknown"] == ["HTS-06-n1"]
          and "unknown" in s["budgetExcluded"][0]["reason"], "summary shows budget-excluded and unknown usage")
    with FakeRealRun({}):
        rc, _, err = run_cli(real_args(screen_args(work, reuse, tasks, "--skip-existing", **limits)))
    check(rc == 2 and "unknown" in err and not (work / "HTS-07-n1").exists(), "resume waits for the usage")
    path.write_text(json.dumps({**record, "totalTokens": 70000, "tokenUsageKnown": True}))
    with FakeRealRun({}, {o: 1 for o in range(7, 45)}):
        rc, _, err = run_cli(real_args(screen_args(work, reuse, tasks, "--skip-existing", **limits)))
    check(rc == 0 and json.loads(path.read_text())["totalTokens"] == 70000 and (work / "HTS-07-n1").exists()
          and not (work / "attempts").exists(), f"resolved: resumes without redoing the aborted Run: {err}")

    work = tmp / "to-run"
    base = real_args(dry_args(work, tmp / "tasks"))
    with FakeRealRun({"HTC-01-n1": False}):
        rc, _, err = run_cli(base)
    record = json.loads((work / "HTC-01-n1" / "run.json").read_text())
    check(rc == 2 and record["status"] == "aborted-timeout" and "totalTokens" not in record, "run: unknown usage stops")
    rc, _, err = run_cli(["summarize", "--work-root", str(work)])
    check(rc == 0, f"run: summarize reads the aborted Run: {err}")
    with FakeRealRun({}):
        rc, _, err = run_cli(base + ["--skip-existing"])
    check(rc == 2 and "no totalTokens" in err, "run: resume waits for the usage")
    work = tmp / "to-run-known"
    with FakeRealRun({"HTC-01-n1": True}):
        rc, _, err = run_cli(real_args(dry_args(work, tmp / "tasks")))
    record = json.loads((work / "HTC-01-n1" / "run.json").read_text())
    check(rc == 0 and record["status"] == "aborted-timeout" and (work / "HTC-02-n1").exists(),
          f"run: known usage proceeds to the next Run: {err}")


class TimeoutHandlerRun(FakeRealRun):
    """Keeps the real container_exec_codex timeout handler; only docker, the Codex client, and tar are replaced."""

    def __init__(self, kill, collect, force=0, stop=0):
        super().__init__({})
        self.kill_mode, self.collect_mode, self.force_mode, self.stop_mode = kill, collect, force, stop
        self.calls: list[str] = []
        self.bounds: list[int | None] = []

    def fake_docker(self, *a, stdin=None, check=True, timeout=None):
        result = subprocess.CompletedProcess(a, 0, htc.RUNTIME_VERSION, "")
        if a[0] == "inspect":
            result.stdout = "[{}]"
        elif "kill -s KILL" in " ".join(a):
            self.calls.append("exec-kill")
            self.bounds.append(timeout)
            if self.kill_mode == "hang":
                raise subprocess.TimeoutExpired("docker", timeout)
            if self.kill_mode == "oserror":
                raise OSError("docker")
            result.returncode = self.kill_mode
        elif a[0] == "kill":
            self.calls.append("force-kill")
            self.bounds.append(timeout)
            if self.force_mode == "hang":
                raise subprocess.TimeoutExpired("docker", timeout)
            if self.force_mode == "oserror":
                raise OSError("docker")
        elif a[0] == "stop":
            self.calls.append("stop")
            self.bounds.append(timeout)
            if self.stop_mode == "oserror":
                raise OSError("docker")
            if self.stop_mode == "hang":
                raise subprocess.TimeoutExpired("docker", timeout)
            result.returncode = self.stop_mode
        return result

    def fake_collect(self, _name, rdir, timeout=None):
        self.calls.append("collect")
        self.bounds.append(timeout)
        if self.collect_mode == "hang":
            raise subprocess.TimeoutExpired("tar", timeout)
        if self.collect_mode == "fail":
            raise subprocess.CalledProcessError(1, "tar")
        if self.collect_mode == "oserror":
            raise OSError("docker")
        args = types.SimpleNamespace(dry_run_model=htc.MODEL, dry_run_effort=htc.EFFORT, dry_run_tokens=68022)
        htc.fake_codex(args, rdir / "sessions")
        if self.collect_mode == "no-token-count":
            trace = rdir / "sessions" / "rollout-dry-run.jsonl"
            trace.write_text("".join(ln + "\n" for ln in trace.read_text().splitlines() if "token_count" not in ln))

    def __enter__(self):
        super().__enter__()
        runner = self

        class FakePopen:
            def __init__(self, *_a, **_k):
                self.returncode = None

            def communicate(self, _prompt, timeout):
                raise subprocess.TimeoutExpired("codex", timeout)

            def kill(self):
                runner.calls.append("client-kill")

            def wait(self, timeout=None):
                runner.bounds.append(timeout)
                return -9

        self.handler_saved = (htc.docker, htc.check_container, htc.check_auth_probe, htc.collect_sessions, subprocess.Popen)
        htc.container_exec_codex = self.saved["container_exec_codex"]
        htc.docker, htc.collect_sessions = self.fake_docker, self.fake_collect
        htc.check_container, htc.check_auth_probe = (lambda *_a: {}), (lambda *_a: None)
        subprocess.Popen = FakePopen
        return self

    def __exit__(self, *exc):
        htc.docker, htc.check_container, htc.check_auth_probe, htc.collect_sessions, subprocess.Popen = self.handler_saved
        super().__exit__(*exc)


def test_timeout_handler(tmp: Path, reuse: Path, tasks: Path) -> None:
    clean = ["exec-kill", "client-kill", "collect", "stop"]
    collect_failed = ["exec-kill", "client-kill", "collect", "force-kill", "stop"]
    kill_failed = ["exec-kill", "client-kill", "force-kill", "stop"]
    cases = [("ok", 0, "ok", 0, 0, clean, True), ("collect-fail", 0, "fail", 0, 0, collect_failed, False),
             ("collect-hang", 0, "hang", 0, 0, collect_failed, False),
             ("collect-oserror", 0, "oserror", 0, 0, collect_failed, False),
             ("no-count", 0, "no-token-count", 0, 0, clean, False),
             ("kill-nonzero", 1, "ok", 0, 0, kill_failed, False), ("kill-hang", "hang", "ok", 0, 0, kill_failed, False),
             ("kill-oserror", "oserror", "ok", 0, 0, kill_failed, False),
             ("force-hang", "hang", "ok", "hang", 0, kill_failed, False),
             ("force-oserror", 1, "ok", "oserror", 0, kill_failed, False),
             ("stop-oserror-after-kill", 0, "ok", 0, "oserror", clean, True),
             ("stop-hang-after-kill", 0, "ok", 0, "hang", clean, True),
             ("stop-nonzero-after-kill", 0, "ok", 0, 1, clean, True),
             ("stop-oserror-after-kill-fail", 1, "ok", 0, "oserror", kill_failed, False),
             ("stop-oserror-after-force-fail", "hang", "ok", "oserror", "oserror", kill_failed, False)]
    for name, kill, collect, force, stop, calls, known in cases:
        work = tmp / f"handler-{name}"
        args = real_args(screen_args(work, reuse, tasks))
        with TimeoutHandlerRun(kill, collect, force, stop) as runner:
            rc, _, err = run_cli(args)
        check(runner.calls[:len(calls)] == calls, f"{name}: order {runner.calls}")
        check(all(b == htc.TIMEOUT_STEP_S for b in runner.bounds), f"{name}: every step is bounded {runner.bounds}")
        path = work / "HTS-06-n1" / "run.json"
        record = json.loads(path.read_text())
        trace = record["isolation"]["timeoutTrace"]
        check(record["status"] == "aborted-timeout" and record["modelLaunched"] is True
              and record["tokenUsageKnown"] is known, f"{name}: {record}")
        check(trace["collectedAfterKill"] is (collect in ("ok", "no-token-count") and kill == 0),
              f"{name}: collect evidence {trace}")
        if stop:
            check(trace["stopExitCode"] == (stop if stop == 1 else None) and (stop == 1 or trace["stopError"])
                  and "docker stop" in err, f"{name}: stop failure kept and shown: {trace} {err}")
        else:
            check(trace["stopExitCode"] == 0 and "stopError" not in trace and "docker stop" not in err,
                  f"{name}: stop evidence {trace}")
        s = htc.screen_summarize(work, reuse)
        excluded = s["budgetExcluded"][0]
        check(excluded["order"] == 6 and 6 not in s["selectedZero"], f"{name}: budget-excluded")
        if known:
            check(record["totalTokens"] == 68022 and "lower bound" in record["tokenUsageBasis"]
                  and not s["usageUnknownRuns"] and s["screeningTokens"] >= 68022, f"{name}: observed value kept")
            if not stop:
                check(rc == 0, f"{name}: continues: {err}")
                continue
            check(rc == 2 and "container" in err and not (work / "HTS-07-n1").exists()
                  and len(list(work.glob("HTS-*/run.json"))) == 1, f"{name}: batch stops on a failed stop: {err}")
            check(s["stopReason"].startswith("HTS-06-n1 timed out and docker stop failed"), f"{name}: stop reason")
            with TimeoutHandlerRun(0, "ok"):
                rc, _, err = run_cli(args + ["--skip-existing"])
            kept = json.loads(path.read_text())
            check(rc == 0 and (work / "HTS-07-n1").exists() and not (work / "HTS-06-n2").exists()
                  and kept == record, f"{name}: resumes without redoing or changing the Run: {err}")
            continue
        check(rc == 2 and "unknown" in err and "totalTokens" not in record and not (work / "HTS-06-n2").exists()
              and not (work / "HTS-07-n1").exists(), f"{name}: stops without a guess: {err}")
        check(s["usageUnknownRuns"] == ["HTS-06-n1"] and "unknown" in excluded["reason"], f"{name}: summary")
        with TimeoutHandlerRun(0, "ok"):
            rc, _, err = run_cli(args + ["--skip-existing"])
        check(rc == 2 and "unknown" in err and not (work / "HTS-07-n1").exists(), f"{name}: resume refused")

    work = tmp / "handler-run-stop"
    with TimeoutHandlerRun(0, "ok", 0, "oserror"):
        rc, _, err = run_cli(real_args(dry_args(work, tmp / "tasks")))
    record = json.loads((work / "HTC-01-n1" / "run.json").read_text())
    check(rc == 2 and "docker stop failed" in err and record["totalTokens"] == 68022
          and not (work / "HTC-02-n1").exists(), f"run: batch stops on a failed stop: {err}")
    with TimeoutHandlerRun(0, "ok"):
        rc, out, err = run_cli(real_args(dry_args(work, tmp / "tasks", "--skip-existing")))
    check(rc == 0 and "skip existing HTC-01-n1" in out and (work / "HTC-02-n1").exists(), f"run: resumes: {err}")

    work = tmp / "handler-collect-fail"
    path = work / "HTS-06-n1" / "run.json"
    original = json.loads(path.read_text())
    args = real_args(screen_args(work, reuse, tasks, "--skip-existing"))
    for bad in ({**original, "totalTokens": 70000}, {**original, "tokenUsageKnown": True}):
        path.write_text(json.dumps(bad))
        with FakeRealRun({}):
            rc, _, err = run_cli(args)
        check(rc == 2 and "inconsistent" in err and not (work / "HTS-07-n1").exists(), "partial hand fix: resume refused")
        rc, _, err = run_cli(["screen-summarize", "--work-root", str(work), "--reuse-root", str(reuse)])
        check(rc == 2 and "inconsistent" in err, "partial hand fix: summary refused")
    run_work = tmp / "to-run"
    run_path = run_work / "HTC-01-n1" / "run.json"
    run_path.write_text(json.dumps({**json.loads(run_path.read_text()), "totalTokens": 70000}))
    rc, _, err = run_cli(["summarize", "--work-root", str(run_work)])
    check(rc == 2 and "inconsistent" in err, "run: partial hand fix refused by summarize")


class NonzeroExitRun(FakeRealRun):
    """Runs listed in `exits` end with that exit code; `no_usage` Runs leave a trace without token_count."""

    def __init__(self, exits: dict[str, int], success_at: dict[int, int] | None = None, no_usage: bool = False):
        super().__init__({}, success_at)
        self.exits, self.no_usage = exits, no_usage

    def container(self, args, rdir, _prompt, evidence, _on_launched=None):
        evidence["modelLaunched"] = True
        htc.fake_codex(args, rdir / "sessions")
        if self.no_usage and rdir.name in self.exits:
            trace = rdir / "sessions" / "rollout-dry-run.jsonl"
            trace.write_text("".join(ln + "\n" for ln in trace.read_text().splitlines() if "token_count" not in ln))
        return self.exits.get(rdir.name, 0), evidence


class NonzeroHandlerRun(TimeoutHandlerRun):
    """Keeps the real container_exec_codex; Codex ends with `code`; collection and docker stop behave as given."""

    def __init__(self, collect, stop=0, code=1, run_fails=False, popen_fails=False, communicate_fails=None):
        super().__init__(0, collect, 0, stop)
        self.code, self.run_fails, self.popen_fails = code, run_fails, popen_fails
        self.communicate_fails = communicate_fails  # the run.json path read at the moment communicate fails
        self.on_disk_at_failure = None

    def fake_docker(self, *a, stdin=None, check=True, timeout=None):
        if a[0] == "run" and self.run_fails:
            raise subprocess.CalledProcessError(125, "docker run")
        return super().fake_docker(*a, stdin=stdin, check=check, timeout=timeout)

    def __enter__(self):
        super().__enter__()
        runner = self

        class Exit:
            returncode = runner.code

            def __init__(self, *_a, **_k):
                if runner.popen_fails:
                    raise OSError("popen")

            def communicate(self, _prompt, timeout):
                if runner.communicate_fails:
                    runner.on_disk_at_failure = json.loads(runner.communicate_fails.read_text())
                    raise OSError("communicate")

        subprocess.Popen = Exit
        return self


def resolve_usage(path: Path) -> None:
    """Runbook §7 step 4: only totalTokens and tokenUsageKnown change."""
    path.write_text(json.dumps({**json.loads(path.read_text()), "totalTokens": 70000, "tokenUsageKnown": True}))


def test_screen_abort_keeps_record(tmp: Path, reuse: Path, tasks: Path) -> None:
    limits = {"run": "100000", "cand": "1000000", "budget": "10000000"}
    others = {o: 1 for o in range(7, 45)}

    work = tmp / "ab-stop"
    args = real_args(screen_args(work, reuse, tasks, **limits))
    with NonzeroHandlerRun("ok", stop="oserror"):
        rc, _, err = run_cli(args)
    path = work / "HTS-06-n1" / "run.json"
    record = json.loads(path.read_text())
    check(rc == 2 and record["status"] == "aborted-nonzero-exit" and record["modelLaunched"] is True
          and record["isolation"]["stopTrace"]["stopError"] == "OSError" and "docker stop" in err,
          f"stop failure after exit 1 is kept: {record}")
    with NonzeroExitRun({}, others):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 0 and (work / "HTS-07-n1").exists() and not (work / "HTS-06-n2").exists(), f"resumes: {err}")

    work = tmp / "ab-read"
    args = real_args(screen_args(work, reuse, tasks, **limits))
    saved = htc.read_trace

    def unreadable(_path, null_safe=False):
        raise OSError("read")

    htc.read_trace = unreadable
    try:
        with NonzeroExitRun({"HTS-06-n1": 1}):
            rc, _, err = run_cli(args)
    finally:
        htc.read_trace = saved
    path = work / "HTS-06-n1" / "run.json"
    record = json.loads(path.read_text())
    check(rc == 2 and "STOP" in err and record["status"] == "aborted-nonzero-exit" and record["modelLaunched"] is True
          and record["tokenUsageKnown"] is False and "totalTokens" not in record, f"unreadable trace: {record}")
    with NonzeroExitRun({}, others):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 2 and "unknown" in err, "unreadable trace: resume waits for the usage")
    resolve_usage(path)
    with NonzeroExitRun({}, others):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 0 and (work / "HTS-07-n1").exists() and not (work / "HTS-06-n2").exists(), f"runbook resume: {err}")

    work = tmp / "ab-zero-collect"
    args = real_args(screen_args(work, reuse, tasks, **limits))
    with NonzeroHandlerRun("fail", code=0):
        rc, _, err = run_cli(args)
    path = work / "HTS-06-n1" / "run.json"
    record = json.loads(path.read_text())
    check(rc == 2 and record["status"] == "aborted-trace-unavailable" and record["modelLaunched"] is True
          and record["tokenUsageKnown"] is False and record["codexExitCode"] == 0, f"exit 0 without a trace: {record}")
    resolve_usage(path)
    with NonzeroExitRun({}, others):
        rc, _, err = run_cli(args + ["--skip-existing"])
    rows = {r["order"]: r for r in htc.screen_summarize(work, reuse)["candidates"]}
    check(rc == 0 and rows[6]["outcome"] == "budget-excluded" and not (work / "HTS-06-n2").exists(), f"resumes: {err}")

    work = tmp / "ab-zero-stop"
    args = real_args(screen_args(work, reuse, tasks, **limits))
    with NonzeroHandlerRun("ok", stop="oserror", code=0):
        rc, _, err = run_cli(args)
    record = json.loads((work / "HTS-06-n1" / "run.json").read_text())
    check(rc == 2 and "docker stop failed" in err and record["status"] == "completed" and record["totalTokens"] == 68022
          and not (work / "HTS-06-n2").exists(), f"exit 0, stop failure: result kept, batch stops: {err}")
    with NonzeroExitRun({}, {6: 2, **others}):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 0 and json.loads((work / "HTS-06-n1" / "run.json").read_text()) == record
          and (work / "HTS-06-n2").exists(), f"exit 0, stop failure: resumes: {err}")

    work = tmp / "ab-grade"
    args = real_args(screen_args(work, reuse, tasks, **limits))
    with NonzeroExitRun({}):
        def hang(*_a):
            raise subprocess.TimeoutExpired("ac", 300)
        htc.grade = hang
        rc, _, err = run_cli(args)
    record = json.loads((work / "HTS-06-n1" / "run.json").read_text())
    check(rc == 2 and "STOP" in err and record["status"] == "grade-error" and record["modelLaunched"] is True
          and record["totalTokens"] == 68022, f"grade failure is recorded: {record}")
    with NonzeroExitRun({}, others):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 2 and "cannot classify" in err, "grade failure never becomes a result on resume")


def test_screen_post_launch_errors(tmp: Path, reuse: Path, tasks: Path) -> None:
    limits = {"run": "100000", "cand": "1000000", "budget": "10000000"}
    others = {o: 1 for o in range(7, 45)}

    work = tmp / "pl-communicate"
    args = real_args(screen_args(work, reuse, tasks, **limits))
    path = work / "HTS-06-n1" / "run.json"
    with NonzeroHandlerRun("ok", communicate_fails=path) as runner:
        rc, _, err = run_cli(args)
    check(runner.on_disk_at_failure["modelLaunched"] is True, "launch is on disk before communicate returns")
    record = json.loads(path.read_text())
    check(rc == 2 and "STOP" in err and record["status"] == "aborted-run-error" and record["modelLaunched"] is True
          and record["tokenUsageKnown"] is False and "totalTokens" not in record and "OSError" in record["stopReason"]
          and record["isolation"]["stopTrace"]["stopExitCode"] == 0, f"communicate failure: {record}")
    s = htc.screen_summarize(work, reuse)
    check(s["usageUnknownRuns"] == ["HTS-06-n1"] and s["budgetExcluded"][0]["order"] == 6, "communicate failure: summary")
    with NonzeroExitRun({}, others):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 2 and "unknown" in err and not (work / "HTS-07-n1").exists(), "communicate failure: resume refused")
    resolve_usage(path)
    with NonzeroExitRun({}, others):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 0 and (work / "HTS-07-n1").exists() and not (work / "HTS-06-n2").exists(), f"runbook resume: {err}")

    work = tmp / "pl-timeout-read"
    args = real_args(screen_args(work, reuse, tasks, **limits))
    path = work / "HTS-06-n1" / "run.json"
    saved = htc.read_trace

    def unreadable(_path, null_safe=False):
        raise OSError("read")

    htc.read_trace = unreadable
    try:
        with TimeoutHandlerRun(0, "ok"):
            rc, _, err = run_cli(args)
    finally:
        htc.read_trace = saved
    record = json.loads(path.read_text())
    check(rc == 2 and "unknown" in err and record["status"] == "aborted-timeout" and record["modelLaunched"] is True
          and record["tokenUsageKnown"] is False and "totalTokens" not in record, f"timeout read failure: {record}")
    with NonzeroExitRun({}, others):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 2 and "unknown" in err, "timeout read failure: resume refused")
    resolve_usage(path)
    with NonzeroExitRun({}, others):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 0 and (work / "HTS-07-n1").exists() and not (work / "HTS-06-n2").exists(), f"runbook resume: {err}")

    work = tmp / "pl-collect-hang"
    with NonzeroHandlerRun("hang", code=0) as runner:
        rc, _, err = run_cli(real_args(screen_args(work, reuse, tasks, **limits)))
    record = json.loads((work / "HTS-06-n1" / "run.json").read_text())
    check(rc == 2 and record["status"] == "aborted-trace-unavailable"
          and record["isolation"]["collectError"] == "TimeoutExpired" and htc.TIMEOUT_STEP_S in runner.bounds,
          f"normal-exit collection is bounded: {record}")

    for name, kwargs in (("run", {"run_fails": True}), ("popen", {"popen_fails": True})):
        work = tmp / f"pl-before-{name}"
        args = real_args(screen_args(work, reuse, tasks, **limits))
        with NonzeroHandlerRun("ok", **kwargs):
            rc, _, err = run_cli(args)
        record = json.loads((work / "HTS-06-n1" / "run.json").read_text())
        check(rc == 2 and "STOP" in err and record["status"] == "isolation-stop" and record["modelLaunched"] is False
              and record["stopReason"], f"{name}: pre-launch failure: {record}")
        with NonzeroExitRun({}, {6: 1, **others}):
            rc, out, err = run_cli(args + ["--skip-existing"])
        kept = work / "attempts" / "HTS-06-n1" / "attempt-1" / "run.json"
        check(rc == 0 and "retry HTS-06-n1" in out and json.loads(kept.read_text())["status"] == "isolation-stop"
              and json.loads((work / "HTS-06-n1" / "run.json").read_text())["status"] == "completed",
              f"{name}: retried: {err}")


def write_trace(rdir: Path, state: str, usage: bool, context: bool, model: str) -> None:
    args = types.SimpleNamespace(dry_run_model=model, dry_run_effort=htc.EFFORT, dry_run_tokens=68022)
    htc.fake_codex(args, rdir / "sessions")
    path = rdir / "sessions" / "rollout-dry-run.jsonl"
    if state == "missing":
        path.unlink()
    elif state == "corrupt":
        path.write_text("not json\n")
    else:
        dropped = ([] if usage else ["token_count"]) + ([] if context else ["turn_context"])
        path.write_text("".join(ln + "\n" for ln in path.read_text().splitlines() if not any(d in ln for d in dropped)))


class TraceTimeoutRun(TimeoutHandlerRun):
    """Real timeout handler; the collected trace is shaped as given."""

    def __init__(self, usage=True, context=True, model=htc.MODEL):
        super().__init__(0, "ok")
        self.usage, self.context, self.model = usage, context, model

    def fake_collect(self, _name, rdir, timeout=None):
        write_trace(rdir, "readable", self.usage, self.context, self.model)


BROKEN = "{broken"


def raw_trace(rdir: Path, cli: str | None, contexts: list) -> None:
    """A valid JSON trace with usage whose effective values are exactly the given ones."""
    lines = [json.dumps({"type": "session_meta", "payload": {"cli_version": cli}})]
    lines += [BROKEN if c == BROKEN else json.dumps({"type": "turn_context", "payload": {"model": c[0], "effort": c[1]}})
              for c in contexts]
    lines.append(json.dumps({"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {
        "input_tokens": 68022, "output_tokens": 0}}}}))
    (rdir / "sessions").mkdir(parents=True, exist_ok=True)
    (rdir / "sessions" / "rollout-raw.jsonl").write_text("".join(ln + "\n" for ln in lines))


class RawTimeoutRun(TimeoutHandlerRun):
    def __init__(self, cli, contexts):
        super().__init__(0, "ok")
        self.cli, self.contexts = cli, contexts

    def fake_collect(self, _name, rdir, timeout=None):
        raw_trace(rdir, self.cli, self.contexts)


class RawExitRun(NonzeroHandlerRun):
    def __init__(self, code, cli, contexts):
        super().__init__("ok", code=code)
        self.cli, self.contexts = cli, contexts

    def fake_collect(self, _name, rdir, timeout=None):
        raw_trace(rdir, self.cli, self.contexts)


GOOD_CLI = htc.RUNTIME_VERSION.split()[-1]
GOOD = (htc.MODEL, htc.EFFORT)
NULL_MODEL = (None, htc.EFFORT)
NULL_EFFORT = (htc.MODEL, None)


def null_mix_cases() -> list[tuple]:
    """(name, cli, contexts): a null line never hides an actual mismatch of another value."""
    return [("cli", "0.159.0", [NULL_MODEL, GOOD]),
            ("model", GOOD_CLI, [NULL_MODEL, GOOD, ("gpt-6-luna", htc.EFFORT)]),
            ("effort", GOOD_CLI, [NULL_EFFORT, GOOD, (htc.MODEL, "medium")]),
            ("same-line", GOOD_CLI, [GOOD, (None, "medium")]),
            ("array-cli", "0.159.0", [([], htc.EFFORT), GOOD]),
            ("array-effort", GOOD_CLI, [([], "medium")]),
            ("array-model", GOOD_CLI, [(htc.MODEL, ["high"]), ("gpt-6-luna", htc.EFFORT)]),
            ("broken-before", GOOD_CLI, [BROKEN, ("gpt-6-luna", htc.EFFORT)]),
            ("broken-after", GOOD_CLI, [("gpt-6-luna", htc.EFFORT), BROKEN]),
            ("broken-cli", "0.159.0", [BROKEN, GOOD])]


def check_null_mix_refused(tmp: Path, reuse: Path, tasks: Path, name: str, make) -> None:
    work = tmp / "null-mix" / name
    args = real_args(screen_args(work, reuse, tasks, run="100000", cand="1000000", budget="10000000"))
    with make():
        rc, _, err = run_cli(args)
    path = work / "HTS-06-n1" / "run.json"
    record = json.loads(path.read_text())
    check(rc == 2 and "control deviation" in err and record["status"] == "control-deviation"
          and "verifiedSuccess" not in record, f"{name}: mismatch found: {record['status']} {err}")
    resolve_usage(path)
    with NonzeroExitRun({}, {o: 1 for o in range(7, 45)}):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 2 and not (work / "HTS-07-n1").exists(), f"{name}: refused after runbook step 4: {err}")


def null_mix_runs() -> list[tuple]:
    return [(f"{name}-{kind}", (lambda c=cli, x=contexts, m=make: m(c, x)))
            for name, cli, contexts in null_mix_cases()
            for kind, make in (("exit0", lambda c, x: RawExitRun(0, c, x)), ("exit1", lambda c, x: RawExitRun(1, c, x)),
                               ("timeout", RawTimeoutRun))]


def test_screen_trace_null_mix(tmp: Path, reuse: Path, tasks: Path) -> None:
    for name, make in null_mix_runs():
        check_null_mix_refused(tmp, reuse, tasks, name, make)

    others = {o: 1 for o in range(7, 45)}
    for name, contexts, missing in (("model", [NULL_MODEL], "model"), ("effort", [NULL_EFFORT], "effort"),
                                    ("mixed", [NULL_MODEL, GOOD], "model")):
        work = tmp / "null-only" / name
        args = real_args(screen_args(work, reuse, tasks, run="100000", cand="1000000", budget="10000000"))
        with RawExitRun(1, GOOD_CLI, contexts):
            rc, _, err = run_cli(args)
        record = json.loads((work / "HTS-06-n1" / "run.json").read_text())
        check(rc == 2 and record["status"] == "aborted-nonzero-exit" and record["totalTokens"] == 68022
              and missing in record["traceControlsMissing"] and "verifiedSuccess" not in record,
              f"null {name} is missing: {record}")
        with NonzeroExitRun({}, others):
            rc, _, err = run_cli(args + ["--skip-existing"])
        check(rc == 0 and (work / "HTS-07-n1").exists(), f"null {name}: resumes: {err}")
        rows = {r["order"]: r for r in htc.screen_summarize(work, reuse)["candidates"]}
        check(rows[6]["outcome"] == "budget-excluded", f"null {name}: excluded")
    for name, contexts, missing in (("broken", [BROKEN, GOOD], "malformed-lines"), ("array", [([], htc.EFFORT)], "model")):
        for kind, make in (("exit0", lambda c, x: RawExitRun(0, c, x)), ("exit1", lambda c, x: RawExitRun(1, c, x)),
                           ("timeout", RawTimeoutRun)):
            work = tmp / "unusable" / f"{name}-{kind}"
            args = real_args(screen_args(work, reuse, tasks, run="100000", cand="1000000", budget="10000000"))
            with make(GOOD_CLI, contexts):
                rc, _, err = run_cli(args)
            path = work / "HTS-06-n1" / "run.json"
            record = json.loads(path.read_text())
            check(rc == 2 and record["status"] in htc.ABORTED_STATUSES and record["tokenUsageKnown"] is False
                  and "verifiedSuccess" not in record and missing in record["traceControlsMissing"],
                  f"{name}-{kind}: missing, not a mismatch: {record}")
            resolve_usage(path)
            with NonzeroExitRun({}, others):
                rc, _, err = run_cli(args + ["--skip-existing"])
            check(rc == 0 and (work / "HTS-07-n1").exists(), f"{name}-{kind}: resumes: {err}")

    work = tmp / "unusable" / "run-error"
    args = real_args(screen_args(work, reuse, tasks, run="100000", cand="1000000", budget="10000000"))
    saved = htc.screen_trace_state

    def raises(_rdir):
        raise RuntimeError("state")

    htc.screen_trace_state = raises
    try:
        with RawExitRun(1, "0.159.0", [GOOD]):
            rc, _, err = run_cli(args)
    finally:
        htc.screen_trace_state = saved
    record = json.loads((work / "HTS-06-n1" / "run.json").read_text())
    check(rc == 2 and "control deviation" in err and record["status"] == "control-deviation"
          and record["abortedAs"] == "aborted-run-error", f"run error keeps the mismatch check: {record}")

    work = tmp / "null-only" / "exit0"
    with RawExitRun(0, GOOD_CLI, [NULL_MODEL, GOOD]):
        rc, _, err = run_cli(real_args(screen_args(work, reuse, tasks, run="100000", cand="1000000", budget="10000000")))
    record = json.loads((work / "HTS-06-n1" / "run.json").read_text())
    check(rc == 2 and record["status"] == "aborted-trace-unavailable" and "verifiedSuccess" not in record,
          f"exit 0 with a null value is not graded: {record}")

    trace = tmp / "null-only" / "cal"
    raw_trace(trace, GOOD_CLI, [NULL_MODEL, GOOD])
    try:
        htc.read_trace(trace / "sessions" / "rollout-raw.jsonl")
    except TypeError:
        return
    raise AssertionError("read_trace default (used by calibration) changed for mixed null contexts")


class MatrixRun(NonzeroHandlerRun):
    """Real container_exec_codex; the exit code, collection, trace, usage, and AC result are all given."""

    def __init__(self, code, collect, trace, usage, context, success, model=htc.MODEL):
        super().__init__(collect, code=code)
        self.trace_state, self.usage, self.context, self.model = trace, usage, context, model
        self.success_at = {**{o: 1 for o in range(7, 45)}, **({6: 1} if success else {})}
        self.graded: list[str] = []

    def grade(self, cand, ws, grade_dir, ac, py):
        self.graded.append(ws.parent.name)
        return super().grade(cand, ws, grade_dir, ac, py)

    def fake_collect(self, _name, rdir, timeout=None):
        write_trace(rdir, self.trace_state, self.usage, self.context, self.model)
        if self.collect_mode == "fail":
            raise subprocess.CalledProcessError(1, "tar")
        if self.collect_mode == "hang":
            raise subprocess.TimeoutExpired("tar", timeout)


def matrix_cases() -> list[tuple]:
    return [(code, collect, trace, usage, context, success)
            for code in (0, 1) for collect in ("ok", "fail", "hang") for trace in ("readable", "missing", "corrupt")
            for usage in (True, False) for context in (True, False) for success in (True, False)]


def check_matrix_case(tmp: Path, reuse: Path, tasks: Path, case: tuple) -> None:
    code, collect, trace, usage, context, success = case
    label = f"code={code} collect={collect} trace={trace} usage={usage} context={context} success={success}"
    work = tmp / "matrix" / label.replace(" ", "_").replace("=", "-")
    args = real_args(screen_args(work, reuse, tasks, run="100000", cand="1000000", budget="10000000"))
    with MatrixRun(code, collect, trace, usage, context, success) as runner:
        rc, _, err = run_cli(args)
    path = work / "HTS-06-n1" / "run.json"
    record = json.loads(path.read_text())
    intact = collect == "ok" and trace == "readable" and usage
    if code == 0 and intact and context:
        check(record["status"] == "completed" and record["verifiedSuccess"] is success and record["totalTokens"] == 68022
              and runner.graded.count("HTS-06-n1") == 1, f"{label}: only the fully normal Run is graded once: {record}")
        return
    expected = "aborted-nonzero-exit" if code else "aborted-trace-unavailable"
    check(rc == 2 and record["status"] == expected and runner.graded == [] and "verifiedSuccess" not in record
          and "acExitCode" not in record and record["modelLaunched"] is True, f"{label}: {expected}: {record} {err}")
    check(record["tokenUsageKnown"] is intact and ("totalTokens" in record) is intact, f"{label}: usage: {record}")
    check(("traceControlsMissing" in record) is (trace == "corrupt" or (trace == "readable" and not context)),
          f"{label}: evidence: {record}")
    check(not (work / "HTS-06-n2").exists() and not (work / "HTS-07-n1").exists(), f"{label}: stops at the first Run")

    def excluded() -> None:
        s = htc.screen_summarize(work, reuse)
        check(6 not in s["selectedZero"] and 6 not in s["truncated"] and s["budgetExcluded"][0]["order"] == 6,
              f"{label}: neither a success nor 0/3: {s['budgetExcluded']}")

    excluded()
    others = {o: 1 for o in range(7, 45)}
    if not intact:
        check(htc.screen_summarize(work, reuse)["screeningTokens"] == 0, f"{label}: no partial usage in the budget")
        with NonzeroExitRun({}, others):
            rc, _, err = run_cli(args + ["--skip-existing"])
        check(rc == 2 and "unknown" in err and not (work / "HTS-07-n1").exists(), f"{label}: resume refused: {err}")
        excluded()
        resolve_usage(path)
    with NonzeroExitRun({}, others):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 0 and (work / "HTS-07-n1").exists() and not (work / "HTS-06-n2").exists(), f"{label}: resumes: {err}")
    excluded()


def test_screen_abort_matrix(tmp: Path, reuse: Path, tasks: Path) -> None:
    for case in matrix_cases():
        check_matrix_case(tmp, reuse, tasks, case)


def test_screen_trace_controls(tmp: Path, reuse: Path, tasks: Path) -> None:
    limits = {"run": "100000", "cand": "1000000", "budget": "10000000"}
    others = {o: 1 for o in range(7, 45)}

    work = tmp / "tc-timeout-missing"
    args = real_args(screen_args(work, reuse, tasks, **limits))
    with TraceTimeoutRun(context=False):
        rc, _, err = run_cli(args)
    record = json.loads((work / "HTS-06-n1" / "run.json").read_text())
    check(rc == 0 and record["status"] == "aborted-timeout" and record["totalTokens"] == 68022
          and "turn_context" in record["traceControlsMissing"], f"timeout without turn_context stays a timeout: {err}")
    s = htc.screen_summarize(work, reuse)
    check(s["budgetExcluded"][0]["order"] == 6 and s["budgetExcluded"][0]["tokens"] == 68022, "counted as excluded")

    work = tmp / "tc-timeout-missing-no-usage"
    args = real_args(screen_args(work, reuse, tasks, **limits))
    path = work / "HTS-06-n1" / "run.json"
    with TraceTimeoutRun(usage=False, context=False):
        rc, _, err = run_cli(args)
    record = json.loads(path.read_text())
    check(rc == 2 and "unknown" in err and record["status"] == "aborted-timeout" and record["tokenUsageKnown"] is False
          and record["traceControlsMissing"], f"no usage either: {record}")
    resolve_usage(path)
    with NonzeroExitRun({}, others):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 0 and (work / "HTS-07-n1").exists(), f"runbook resume: {err}")

    cases = (("timeout", lambda: TraceTimeoutRun(model="gpt-6-luna")),
             ("timeout-no-usage", lambda: TraceTimeoutRun(usage=False, model="gpt-6-luna")),
             ("exit1", lambda: MatrixRun(1, "ok", "readable", True, True, False, model="gpt-6-luna")),
             ("exit1-no-usage", lambda: MatrixRun(1, "ok", "readable", False, True, False, model="gpt-6-luna")),
             ("exit0", lambda: MatrixRun(0, "ok", "readable", True, True, True, model="gpt-6-luna")),
             ("cli-exit0", lambda: RawExitRun(0, "0.159.0", [GOOD])),
             ("cli-exit1", lambda: RawExitRun(1, "0.159.0", [GOOD])),
             ("cli-timeout", lambda: RawTimeoutRun("0.159.0", [GOOD])),
             ("effort-exit0", lambda: RawExitRun(0, GOOD_CLI, [(htc.MODEL, "medium")])),
             ("effort-exit1", lambda: RawExitRun(1, GOOD_CLI, [(htc.MODEL, "medium")])),
             ("effort-timeout", lambda: RawTimeoutRun(GOOD_CLI, [(htc.MODEL, "medium")])))
    for name, make in cases:
        work = tmp / f"tc-mismatch-{name}"
        args = real_args(screen_args(work, reuse, tasks, **limits))
        with make() as runner:
            rc, _, err = run_cli(args)
        record = json.loads((work / "HTS-06-n1" / "run.json").read_text())
        check(rc == 2 and "control deviation" in err and record["status"] == "control-deviation"
              and "verifiedSuccess" not in record and not getattr(runner, "graded", []), f"{name}: mismatch stops: {record}")
        with NonzeroExitRun({}, others):
            rc, _, err = run_cli(args + ["--skip-existing"])
        check(rc == 2 and not (work / "HTS-07-n1").exists(), f"{name}: resume refused: {err}")


def test_screen_before_launch(tmp: Path, reuse: Path, tasks: Path) -> None:
    limits = {"run": "100000", "cand": "1000000", "budget": "10000000"}
    others = {o: 1 for o in range(7, 45)}

    def fail_prepare(_cand, _ws, _mirror):
        raise subprocess.CalledProcessError(128, "git clone")

    real_sha = htc.sha256_file

    def bad_prompt_sha(path):
        return "0" * 64 if path.name == "prompt.md" else real_sha(path)

    for name, patch, value in (("prepare", "prepare_workspace", fail_prepare), ("sha", "sha256_file", bad_prompt_sha)):
        work = tmp / f"before-{name}"
        args = real_args(screen_args(work, reuse, tasks, **limits))
        with NonzeroExitRun({}):
            setattr(htc, patch, value)
            try:
                rc, _, err = run_cli(args)
            finally:
                htc.sha256_file = real_sha
        record = json.loads((work / "HTS-06-n1" / "run.json").read_text())
        check(rc == 2 and "STOP" in err and record["status"] == "isolation-stop" and record["modelLaunched"] is False
              and record["stopReason"], f"{name}: saved as never launched: {record}")
        with NonzeroExitRun({}, {6: 1, **others}):
            rc, out, err = run_cli(args + ["--skip-existing"])
        check(rc == 0 and "retry HTS-06-n1" in out and (work / "attempts" / "HTS-06-n1" / "attempt-1").exists(),
              f"{name}: retried: {err}")

    work = tmp / "before-started"
    args = real_args(screen_args(work, reuse, tasks, **limits))
    with NonzeroExitRun({}):
        run_cli(args + ["--dry-run-success", "6"])
    path = work / "HTS-06-n1" / "run.json"
    record = json.loads(path.read_text())
    record.update(status="started", modelLaunched=False)
    record.pop("totalTokens")
    path.write_text(json.dumps(record))
    with NonzeroExitRun({}, others):
        rc, out, err = run_cli(args + ["--skip-existing"])
    check(rc == 2 and "retry" not in out and "no totalTokens" in err, "a leftover started record is not retried")


def test_screen_abort_accounting(tmp: Path, reuse: Path, tasks: Path) -> None:
    work = tmp / "acct"
    with NonzeroExitRun({"HTS-06-n1": 1}):
        run_cli(real_args(screen_args(work, reuse, tasks, run="100000", cand="1000000")))
    with NonzeroExitRun({}):
        rc, out, err = run_cli(real_args(screen_args(work, reuse, tasks, "--skip-existing", run="100000", cand="1000000",
                                                     budget="168021")))
    check(rc == 2 and "68022" in out and "budget" in err and not (work / "HTS-07-n1").exists(),
          f"aborted usage counts against the budget on resume: {err}")
    with NonzeroExitRun({}, {o: 1 for o in range(8, 45)}):
        rc, _, err = run_cli(real_args(screen_args(work, reuse, tasks, "--skip-existing", run="100000", cand="1000000",
                                                   budget="168022")))
    check((work / "HTS-07-n1").exists(), f"exactly the remaining budget starts the next Run: {err}")

    work = tmp / "twelve"
    args = real_args(screen_args(work, reuse, tasks))
    with NonzeroExitRun({"HTS-06-n1": 1}):
        run_cli(args)
    with NonzeroExitRun({}):
        rc, out, err = run_cli(args + ["--skip-existing"])
    s = htc.screen_summarize(work, reuse)
    check(rc == 0 and "target-reached" in out and s["selectedCount"] == 12 and 6 not in s["selectedZero"]
          and s["selectedZero"][-1] == 19 and not (work / "HTS-20-n1").exists(), f"12 without the aborted one: {s['selectedZero']}")


def test_screen_nonzero_exit(tmp: Path, reuse: Path, tasks: Path) -> None:
    limits = {"run": "100000", "cand": "1000000", "budget": "10000000"}
    others = {o: 1 for o in range(7, 45)}

    work = tmp / "nz-usage"
    args = real_args(screen_args(work, reuse, tasks, **limits))
    with NonzeroExitRun({"HTS-06-n1": 1}):
        rc, _, err = run_cli(args)
    check(rc == 2 and "exited 1" in err, f"non-zero exit stops the batch: {err}")
    check(not (work / "HTS-06-n2").exists() and not (work / "HTS-07-n1").exists(), "no further Run after the abort")
    path = work / "HTS-06-n1" / "run.json"
    record = json.loads(path.read_text())
    check(record["status"] == "aborted-nonzero-exit" and record["codexExitCode"] == 1 and record["totalTokens"] == 68022
          and record["tokenUsageKnown"] is True and "verifiedSuccess" not in record and "acExitCode" not in record,
          f"aborted, not graded: {record}")
    s = htc.screen_summarize(work, reuse)
    excluded = s["budgetExcluded"][0]
    check(excluded["order"] == 6 and 6 not in s["selectedZero"] and "exit code 1" in excluded["reason"]
          and excluded["tokens"] == 68022, f"budget-excluded with a reason: {excluded}")
    with NonzeroExitRun({}, others):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 0 and json.loads(path.read_text()) == record and not (work / "HTS-06-n2").exists()
          and (work / "HTS-07-n1").exists(), f"resume keeps the abort and moves on: {err}")
    s = htc.screen_summarize(work, reuse)
    rows = {r["order"]: r for r in s["candidates"]}
    check(rows[6]["outcome"] == "budget-excluded" and 6 not in s["selectedZero"] and 6 not in s["truncated"],
          "abort does not become 0/3 or a success after resume")

    work = tmp / "nz-later"
    with NonzeroExitRun({"HTS-06-n2": 1}):
        rc, _, _ = run_cli(real_args(screen_args(work, reuse, tasks, **limits)))
    rows = {r["order"]: r for r in htc.screen_summarize(work, reuse)["candidates"]}
    check(rc == 2 and not (work / "HTS-06-n3").exists() and rows[6]["outcome"] == "budget-excluded"
          and [r["result"] for r in rows[6]["runs"]] == ["failure", "budget-excluded"], f"abort at n2: {rows[6]}")

    work = tmp / "nz-no-usage"
    args = real_args(screen_args(work, reuse, tasks, **limits))
    with NonzeroExitRun({"HTS-06-n1": 1}, no_usage=True):
        rc, _, err = run_cli(args)
    path = work / "HTS-06-n1" / "run.json"
    record = json.loads(path.read_text())
    check(rc == 2 and "unknown" in err and record["status"] == "aborted-nonzero-exit"
          and record["tokenUsageKnown"] is False and "totalTokens" not in record, f"usage is not guessed: {record}")
    with NonzeroExitRun({}, others):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 2 and "unknown" in err and not (work / "HTS-07-n1").exists(), "resume waits for the usage")
    path.write_text(json.dumps({**record, "totalTokens": 70000}))
    with NonzeroExitRun({}, others):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 2 and "inconsistent" in err, "partial hand fix refused")
    path.write_text(json.dumps({**record, "totalTokens": 70000, "tokenUsageKnown": True}))
    with NonzeroExitRun({}, others):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 0 and (work / "HTS-07-n1").exists() and not (work / "HTS-06-n2").exists(), f"resolved: resumes: {err}")

    work = tmp / "nz-no-trace"
    args = real_args(screen_args(work, reuse, tasks, **limits))
    with NonzeroHandlerRun("fail"):
        rc, _, err = run_cli(args)
    record = json.loads((work / "HTS-06-n1" / "run.json").read_text())
    check(rc == 2 and "STOP" in err and record["status"] == "aborted-nonzero-exit"
          and record["isolation"]["collectError"] == "CalledProcessError" and "totalTokens" not in record,
          f"no trace: STOP, not a crash: {err}")
    s = htc.screen_summarize(work, reuse)
    check(s["usageUnknownRuns"] == ["HTS-06-n1"] and s["budgetExcluded"][0]["order"] == 6, "no trace: summary")
    with NonzeroHandlerRun("ok"):
        rc, _, err = run_cli(args + ["--skip-existing"])
    check(rc == 2 and "unknown" in err and not (work / "HTS-07-n1").exists(), "no trace: resume refused")


def test_calibration_keeps_nonzero_exit() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d).resolve()
        prompt = tmp / "tasks"
        prompt.mkdir()
        for order in range(1, 6):
            (prompt / f"order-{order:02d}.md").write_text(f"Symptom-only description for candidate {order}.\n")
        work = tmp / "cal"
        with NonzeroExitRun({"HTC-01-n1": 1}):
            rc, _, err = run_cli(real_args(dry_args(work, prompt)))
        record = json.loads((work / "HTC-01-n1" / "run.json").read_text())
        check(rc == 0 and record["status"] == "completed" and record["codexExitCode"] == 1
              and record["verifiedSuccess"] is False and (work / "HTC-02-n1").exists(),
              f"calibration still grades a non-zero exit: {err}")
        cases = ((NonzeroHandlerRun("fail"), subprocess.CalledProcessError, "failed collection"),
                 (NonzeroHandlerRun("ok", run_fails=True), subprocess.CalledProcessError, "docker run failure"),
                 (NonzeroHandlerRun("ok", popen_fails=True), OSError, "Popen failure"))
        for i, (runner, expected, why) in enumerate(cases):
            cal = tmp / f"cal-{i}"
            try:
                with runner:
                    run_cli(real_args(dry_args(cal, prompt)))
            except expected:
                record = json.loads((cal / "HTC-01-n1" / "run.json").read_text())
                check(record["status"] == "started", f"calibration record unchanged: {why}")
                continue
            raise AssertionError(f"calibration handling of a {why} changed")
        cal = tmp / "cal-communicate"
        path = cal / "HTC-01-n1" / "run.json"
        try:
            with NonzeroHandlerRun("ok", communicate_fails=path) as runner:
                run_cli(real_args(dry_args(cal, prompt)))
        except OSError:
            check(runner.on_disk_at_failure["modelLaunched"] is False, "calibration does not persist the launch early")
            return
        raise AssertionError("calibration handling of a communicate failure changed")


def test_success_at_later_runs(tmp: Path, reuse: Path, tasks: Path) -> None:
    work = tmp / "later"
    with FakeRealRun({}, {6: 2, 7: 3, **{o: 1 for o in range(8, 45)}}):
        rc, _, err = run_cli(real_args(screen_args(work, reuse, tasks)))
    check(rc == 0, f"later successes: {err}")
    check((work / "HTS-06-n2").exists() and not (work / "HTS-06-n3").exists(), "success at n2 stops before n3")
    rows = {r["order"]: r for r in htc.screen_summarize(work, reuse)["candidates"]}
    check(rows[6]["outcome"] == "truncated" and [r["result"] for r in rows[6]["runs"]] == ["failure", "success"], "n2")
    check(rows[7]["outcome"] == "truncated" and [r["result"] for r in rows[7]["runs"]] == ["failure", "failure", "success"], "n3")


class AbsentStopRun(TimeoutHandlerRun):
    """docker stop exits 1; `docker ps` lists `containers` (independent of the query) or fails or hangs."""

    def __init__(self, ps, timeout=True, containers=()):
        super().__init__(0, "ok", 0, 1)
        self.ps_mode, self.timeout, self.containers = ps, timeout, containers
        self.ps_args: list[tuple] = []

    def fake_docker(self, *a, stdin=None, check=True, timeout=None):
        if a[0] == "ps":
            self.calls.append("ps")
            self.bounds.append(timeout)
            self.ps_args.append(a)
            if self.ps_mode == "hang":
                raise subprocess.TimeoutExpired("docker", timeout)
            listed = [c for c in self.containers if f"name=^/{c}$" in a]
            return subprocess.CompletedProcess(a, 1 if self.ps_mode == "fail" else 0,
                                               "".join(c + "\n" for c in listed), "")
        return super().fake_docker(*a, stdin=stdin, check=check, timeout=timeout)

    def __enter__(self):
        super().__enter__()
        if not self.timeout:
            class Exit:
                returncode = 1

                def __init__(self, *_a, **_k):
                    pass

                def communicate(self, _prompt, timeout):
                    pass

            subprocess.Popen = Exit
        return self


def test_screen_rehearsal_findings(tmp: Path, reuse: Path, tasks: Path) -> None:
    """#244 rehearsal: control-deviation summary, `--rm` container already gone, phase on stop paths."""
    limits = {"run": "100000", "cand": "1000000", "budget": "10000000"}
    others = {o: 1 for o in range(7, 45)}

    work = tmp / "rf-deviation"
    args = real_args(screen_args(work, reuse, tasks, **limits))
    path = work / "HTS-06-n1" / "run.json"
    with TraceTimeoutRun(model="gpt-6-luna"):
        run_cli(args)
    record = json.loads(path.read_text())
    check(record["status"] == "control-deviation" and "totalTokens" not in record and record["phase"] == "screening",
          f"deviation saved with phase: {record}")
    for name in ("no-usage", "usage-added", "marker"):
        if name == "usage-added":
            resolve_usage(path)
        if name == "marker":
            htc.write_marker(work, 6, "candidate budget")
        out = tmp / f"rf-summary-{name}.json"
        rc, _, err = run_cli(["screen-summarize", "--work-root", str(work), "--reuse-root", str(reuse),
                              "--output", str(out)])
        check(rc == 0 and out.exists(), f"{name}: summary saved: {err}")
        s = json.loads(out.read_text())
        deviation = s["controlDeviation"]
        check([d["runId"] for d in deviation] == ["HTS-06-n1"] and "control deviation" in deviation[0]["reason"]
              and {r["order"]: r for r in s["candidates"]}[6]["outcome"] == "control-deviation"
              and 6 not in s["selectedZero"] and not s["budgetExcluded"], f"{name}: shown as the stop reason: {s}")
        with NonzeroExitRun({}, others):
            rc, _, err = run_cli(args + ["--skip-existing"])
        check(rc == 2 and "control deviation" in err and "record its usage" not in err and "resolve it" not in err
              and not (work / "HTS-07-n1").exists(), f"{name}: resume refused without a usage hint: {err}")

    own = f"htc-hts-06-n1-{os.getpid()}"
    for name, ps, timeout, containers, absent in (
            ("timeout-absent", "ok", True, (), True), ("timeout-renamed", "ok", True, ("htc-other",), True),
            ("timeout-present", "ok", True, (own,), False), ("timeout-ps-fail", "fail", True, (), False),
            ("timeout-ps-hang", "hang", True, (), False), ("exit1-absent", "ok", False, (), True),
            ("exit1-present", "ok", False, (own,), False)):
        work = tmp / f"rf-{name}"
        with AbsentStopRun(ps, timeout, containers) as runner:
            rc, _, err = run_cli(real_args(screen_args(work, reuse, tasks, **limits)))
        record = json.loads((work / "HTS-06-n1" / "run.json").read_text())
        trace = record["isolation"]["timeoutTrace" if timeout else "stopTrace"]
        check(record["phase"] == "screening" and trace["stopExitCode"] == 1
              and runner.ps_args == [("ps", "-a", "--filter", f"name=^/{own}$", "--format", "{{.Names}}")]
              and all(b == htc.TIMEOUT_STEP_S for b in runner.bounds), f"{name}: {record} {runner.ps_args}")
        check(rc == 2 and "WARNING" in err and not (work / "HTS-07-n1").exists()
              and ("not found" in err and "daemon" in err) is absent and trace.get("containerAbsent", False) is absent,
              f"{name}: a failed stop always stops the batch: {err}")
        if timeout:
            check(record["status"] == "aborted-timeout" and "timed out and docker stop failed" in err, f"{name}: {err}")
        else:
            check(record["status"] == "aborted-nonzero-exit" and "codex exit code 1" in record["stopReason"]
                  and "codex exit code 1" in err, f"{name}: {record['status']} {err}")


def test_calibration_unchanged() -> None:
    rc, out, _ = run_cli(["plan"])
    check(rc == 0 and len(out.splitlines()) == 25 and all(ln.startswith("HTC-") for ln in out.splitlines()),
          "calibration plan unchanged")
    check(htc.PREREGISTRATION.name == "HARD_TASK_T0_T1_PREREGISTRATION.md"
          and htc.PREREGISTRATION_BLOB == "52b4a585044e00d52fea8db64f725c4b4f3258cd", "calibration blob unchanged")


def main() -> int:
    test_plan()
    test_calibration_unchanged()
    test_screen_constants()
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
        test_retry_never_launched(tmp, prompt)
        test_missing_launch_flag(tmp, prompt)
        test_container_isolation(tmp)
        test_workspace_and_grade(tmp)
        reuse = tmp / "reuse"
        write_reuse(reuse)
        screen_tasks = tmp / "screen-tasks"
        screen_tasks.mkdir()
        for cand in htc.screen_targets(htc.load_screen_candidates()):
            (screen_tasks / f"order-{cand['order']:02d}.md").write_text(f"Symptom-only description {cand['order']}.\n")
        test_screen_flow(tmp, reuse, screen_tasks)
        test_screen_limits(tmp, reuse, screen_tasks)
        test_screen_reuse_and_blobs(tmp, reuse, screen_tasks)
        test_screen_record_states(tmp, reuse, screen_tasks)
        test_timeout_reaches_aborted(tmp, reuse, screen_tasks)
        test_timeout_handler(tmp, reuse, screen_tasks)
        test_screen_nonzero_exit(tmp, reuse, screen_tasks)
        test_screen_abort_keeps_record(tmp, reuse, screen_tasks)
        test_screen_post_launch_errors(tmp, reuse, screen_tasks)
        test_screen_abort_matrix(tmp, reuse, screen_tasks)
        test_screen_trace_controls(tmp, reuse, screen_tasks)
        test_screen_trace_null_mix(tmp, reuse, screen_tasks)
        test_screen_before_launch(tmp, reuse, screen_tasks)
        test_screen_abort_accounting(tmp, reuse, screen_tasks)
        test_calibration_keeps_nonzero_exit()
        test_success_at_later_runs(tmp, reuse, screen_tasks)
        test_screen_rehearsal_findings(tmp, reuse, screen_tasks)
    print("test_hard_task_calibrate: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
