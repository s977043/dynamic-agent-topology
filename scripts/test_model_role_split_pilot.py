#!/usr/bin/env python3
"""Model-free tests for the #220 pilot kit (dry-run with the synthetic stream only)."""
from __future__ import annotations

from pathlib import Path
import contextlib
import io
import json
import os
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import model_role_split_pilot as mp  # noqa: E402


def check(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def run_cli(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = mp.main(argv)
    return rc, out.getvalue(), err.getvalue()


def dry_args(work: Path, *extra: str) -> list[str]:
    return ["run", "--dry-run", "--work-root", str(work), "--timeout-s", "60", "--max-run-tokens", "300000",
            "--budget-tokens", "600000", *extra]


def records(work: Path) -> dict[str, dict]:
    return {p.parent.name: json.loads(p.read_text()) for p in work.glob("MRS-P*/run.json")}


def judgment_as_real(work: Path) -> str:
    """Judge dry-run records as if real (a dry-run summary is always DRY_RUN)."""
    check(mp.summarize(work)["proposedPilotJudgment"] == "DRY_RUN", "dry-run is never judged")
    for p in work.glob("MRS-P*/run.json"):
        rec = json.loads(p.read_text())
        rec["dryRun"] = False
        p.write_text(json.dumps(rec))
    return mp.summarize(work)["proposedPilotJudgment"]


def test_plan_and_settings() -> None:
    cand = mp.load_pilot()
    check(cand["order"] == 2, "pilot is order 2")
    check([(r["runId"], r["model"]) for r in mp.plan()] ==
          [("MRS-P02-A", "claude-opus-5-5"), ("MRS-P02-B", "claude-sonnet-5-5")], "A then B, full model IDs")
    s = mp.settings(cand)
    check("Bash(python3.12 -m unittest tests/test_svcb.py)" in s["permissions"]["allow"], "AC command allowed")
    check(s["sandbox"]["enabled"] and s["sandbox"]["network"]["allowedDomains"] == [], "sandbox, no domains")
    a = mp.claude_command("claude", "claude-opus-5-5", Path("/x/settings.json"), "sid")
    b = mp.claude_command("claude", "claude-sonnet-5-5", Path("/x/settings.json"), "sid")
    diff = [(x, y) for x, y in zip(a, b) if x != y]
    check(len(a) == len(b) and diff == [("claude-opus-5-5", "claude-sonnet-5-5")], "arms differ only in model")
    check(a[a.index("--effort") + 1] == "high" and "--restricted" in a and "--no-session-persistence" in a,
          "effort high, restricted, fresh session")


def test_policy() -> None:
    check(mp.policy_violation("Bash", {"command": "cat ~/.claude/.credentials.json"}), "credential read")
    check(mp.policy_violation("Bash", {"command": "curl https://example.com"}), "network")
    check(mp.policy_violation("Read", {"file_path": "/Users/x/.ssh/id_ed25519"}), "ssh key read")
    check(mp.policy_violation("Bash", {"command": "ls && env"}), "env dump")
    check(not mp.policy_violation("Bash", {"command": "grep -rn socket dns/"}), "code grep allowed")
    check(not mp.policy_violation("Bash", {"command": "python3.12 -m unittest tests/test_svcb.py"}), "AC allowed")
    check(not mp.policy_violation("Edit", {"file_path": "dns/rdtypes/svcbbase.py", "new_string": "https://x"}),
          "edit content not scanned")


def test_dry_run_and_summary(tmp: Path) -> None:
    work = tmp / "ok"
    rc, out, err = run_cli(dry_args(work, "--dry-run-effort", "high"))
    check(rc == 0, f"dry-run rc {rc}: {err}")
    recs = records(work)
    check(sorted(recs) == ["MRS-P02-A", "MRS-P02-B"], "two runs")
    check(all(r["status"] == "dry-run-ungraded" and r["totalTokens"] == 68022 for r in recs.values()), "status")
    check(not (work / mp.LOCK_NAME).exists(), "lock released")
    summary = mp.summarize(work)
    check(summary["m"] == 1.0 and summary["totalTokensSpent"] == 2 * 68022, "m and spent")
    check(judgment_as_real(work) == "PASS", "all checks pass")
    rc, _, err = run_cli(dry_args(work))
    check(rc == 2 and "refusing to overwrite" in err, "existing results refused")
    rc, out, _ = run_cli(dry_args(work, "--skip-existing"))
    check(rc == 0 and out.count("skip existing") == 2, "skip-existing leaves runs untouched")
    rc, _, err = run_cli(dry_args(work, "--skip-existing", "--budget-tokens", "400000"))
    check(rc == 0, "nothing left to run, budget not needed")


def test_effort_not_visible(tmp: Path) -> None:
    work = tmp / "noeffort"
    check(run_cli(dry_args(work))[0] == 0, "runs")
    check(judgment_as_real(work) == "NOT_TESTED", "effort absent from trace is NOT_TESTED, not PASS")


def test_model_mismatch_stops(tmp: Path) -> None:
    work = tmp / "mismatch"
    rc, _, err = run_cli(dry_args(work, "--dry-run-model", "claude-haiku-5-5"))
    check(rc == 2 and "control-deviation" in err, f"mismatch stops: {err}")
    check(list(records(work)) == ["MRS-P02-A"], "batch stops after the first Run")


def test_credential_access_stops(tmp: Path) -> None:
    work = tmp / "cred"
    rc, _, err = run_cli(dry_args(work, "--dry-run-scenario", "credential"))
    check(rc == 2 and "policy-stop" in err, f"credential stops: {err}")
    rec = records(work)["MRS-P02-A"]
    check(rec["status"] == "policy-stop" and rec["totalTokens"] is None, "no result usage after the kill")
    rc, _, err = run_cli(dry_args(work, "--skip-existing"))
    check(rc == 2 and "no totalTokens" in err, "resume needs the usage recorded")


def test_token_limit_and_budget(tmp: Path) -> None:
    rc, _, err = run_cli(dry_args(tmp / "tok", "--max-run-tokens", "40000"))
    check(rc == 2 and "token-limit" in err, f"running token limit: {err}")
    rc, _, err = run_cli(dry_args(tmp / "bud", "--max-run-tokens", "300000", "--budget-tokens", "350000"))
    check(rc == 2 and "budget" in err and len(records(tmp / "bud")) == 1, "second Run exceeds the budget")
    rc, _, err = run_cli(dry_args(tmp / "bud2", "--budget-tokens", "1000"))
    check(rc == 2 and "exceeds --budget-tokens" in err, "per-run above budget")


def test_incomplete_trace(tmp: Path) -> None:
    rc, _, err = run_cli(dry_args(tmp / "inc", "--dry-run-scenario", "missing-result"))
    check(rc == 2 and "runtime-error" in err, f"missing tool_result stops: {err}")
    rec = records(tmp / "inc")["MRS-P02-A"]
    check(not rec["trace"]["complete"], "trace marked incomplete")


def test_timeout(tmp: Path) -> None:
    rc, _, err = run_cli(dry_args(tmp / "slow", "--dry-run-scenario", "sleep", "--timeout-s", "1"))
    check(rc == 2 and "aborted-timeout" in err, f"timeout stops: {err}")


def test_guards(tmp: Path) -> None:
    work = tmp / "lock"
    work.mkdir()
    (work / mp.LOCK_NAME).write_text("{}")
    rc, _, err = run_cli(dry_args(work))
    check(rc == 2 and "lock exists" in err, "duplicate launch refused")
    rc, _, err = run_cli(dry_args(ROOT / "tmp-inside"))
    check(rc == 2 and "outside the DAT repository" in err, "work root inside repo refused")
    os.environ["ANTHROPIC_API_KEY"] = "x"
    try:
        rc, _, err = run_cli(dry_args(tmp / "key"))
    finally:
        del os.environ["ANTHROPIC_API_KEY"]
    check(rc == 2 and "ANTHROPIC_API_KEY" in err, "API key path refused")
    rc, _, err = run_cli(["run", "--work-root", str(tmp / "real"), "--timeout-s", "1800", "--max-run-tokens",
                          "300000", "--budget-tokens", "600000", "--claude-bin", "/nonexistent/claude"])
    check(rc == 2 and "--acknowledge-not-tested" in err, "real Run needs the NOT_TESTED acknowledgement")
    check(not (tmp / "real").exists(), "nothing created before preflight passes")


def test_never_launched_retry(tmp: Path) -> None:
    work = tmp / "retry"
    rdir = work / "MRS-P02-A"
    rdir.mkdir(parents=True)
    (rdir / "run.json").write_text(json.dumps({"status": "isolation-stop", "modelLaunched": False}))
    rc, out, err = run_cli(dry_args(work, "--skip-existing"))
    check(rc == 0 and "retry MRS-P02-A" in out, f"never-launched Run retried: {err}")
    check((work / "attempts/MRS-P02-A/attempt-1/run.json").exists(), "previous attempt preserved")


def main() -> int:
    tests = [test_plan_and_settings, test_policy]
    tmp_tests = [test_dry_run_and_summary, test_effort_not_visible, test_model_mismatch_stops,
                 test_credential_access_stops, test_token_limit_and_budget, test_incomplete_trace, test_timeout,
                 test_guards, test_never_launched_retry]
    for t in tests:
        t()
        print(f"ok {t.__name__}")
    for t in tmp_tests:
        with tempfile.TemporaryDirectory() as d:
            t(Path(d))
        print(f"ok {t.__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
