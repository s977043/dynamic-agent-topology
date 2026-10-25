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
    check(s["sandbox"]["filesystem"]["denyRead"] == [mp.CONFIG_DIR], "config dir denied to the Bash sandbox")
    a = mp.claude_args("claude-opus-5-5", "sid")
    b = mp.claude_args("claude-sonnet-5-5", "sid")
    diff = [(x, y) for x, y in zip(a, b) if x != y]
    check(len(a) == len(b) and diff == [("claude-opus-5-5", "claude-sonnet-5-5")], "arms differ only in model")
    check(a[a.index("--effort") + 1] == "high" and a[a.index("--setting-sources") + 1] == "user"
          and "--no-session-persistence" in a, "effort high, fresh config only, fresh session")


class Args:
    image = "img@sha256:" + "0" * 64
    max_run_tokens = 300000
    claude_dir = "/opt/cc"
    credentials_file = "/home/op/mrs-auth/.credentials.json"


def test_container_isolation(tmp: Path) -> None:
    work = tmp / "iso"
    rdir = work / "MRS-P02-A"
    cmd = mp.docker_run_command(Args, rdir, "c", "net")
    binds = [cmd[i + 1] for i, a in enumerate(cmd) if a == "-v"]
    check(len(binds) == 3 and not any(".credentials" in b for b in binds),
          "three bind mounts, no credential in the Run container")
    pcmd = mp.proxy_run_command(Args, "p", "net", "claude-opus-5-5")
    check(pcmd[-3:] == ["_proxy", "claude-opus-5-5", "300000"], "proxy gets the declared model and the Run limit")
    pbinds = [pcmd[i + 1] for i, a in enumerate(pcmd) if a == "-v"]
    check(any(b.startswith(os.path.realpath(Args.credentials_file) + ":") and b.endswith(f"{mp.PROXY_SECRET}:ro") for b in pbinds)
          and len(pbinds) == 2, "credential mounted read-only into the proxy only")
    env = mp.container_env("p")
    check(env["ANTHROPIC_AUTH_TOKEN"] == mp.PLACEHOLDER_TOKEN and env["ANTHROPIC_BASE_URL"] == "http://p:3128",
          "Worker gets the proxy URL and a placeholder")
    pexp = sorted(("bind", s, d, rw) for d, (s, rw) in mp.proxy_bind_sources(Args).items())
    pins = {"Mounts": [{"Type": t, "Source": s, "Destination": d, "RW": rw} for t, s, d, rw in pexp], "HostConfig": {}}
    mp.check_proxy_container(pins, Args)
    expect_stop(mp.check_proxy_container, {**pins, "HostConfig": {"PidMode": "host"}}, Args)
    expect_stop(mp.check_proxy_container, {**pins, "Mounts": pins["Mounts"][:1]}, Args)
    check(cmd[cmd.index("--network") + 1] == "net" and "--cap-drop" in cmd and "--read-only" in cmd
          and f"seccomp={mp.SECCOMP}" in cmd, "internal network and EXP-001 constraints")
    check(any(b.endswith(":/work") for b in binds) and all(b.endswith(":ro") for b in binds if not b.endswith(":/work")),
          "only /work is writable")
    expected = mp.expected_mounts(Args, rdir)
    compact = json.dumps(json.loads(mp.SECCOMP.read_text(encoding="utf-8")), separators=(",", ":"))

    def inspect(mounts, **host):
        base = {"Privileged": False, "CapAdd": None, "CapDrop": ["ALL"], "ReadonlyRootfs": True, "NetworkMode": "net",
                "Tmpfs": {"/tmp": "", mp.CONFIG_DIR: "uid=1"}, "SecurityOpt": [f"seccomp={compact}", "no-new-privileges"]}
        return {"Mounts": [{"Type": t, "Source": s, "Destination": d, "RW": rw} for t, s, d, rw in mounts],
                "HostConfig": {**base, **host}}

    evidence = mp.check_container(inspect(expected), expected, work.resolve(), "net")
    check(evidence["seccompMatchesLaunchedProfile"], "seccomp matches")
    rw_cc = [(t, s, d, True if d == "/cc" else rw) for t, s, d, rw in expected]
    bad_cases = [
        inspect(expected + [("bind", str(work / "MRS-P02-B"), "/past", False)]),
        inspect(expected + [("bind", Args.credentials_file, "/cc-home/.credentials.json", False)]),
        inspect(expected + [("volume", "v", "/data", True)]),
        inspect(rw_cc),
        inspect(expected, PidMode="container:p"),
        inspect(expected, Tmpfs={"/tmp": ""}),
        inspect(expected, NetworkMode="bridge"),
        inspect(expected, Privileged=True),
        inspect(expected, SecurityOpt=["seccomp=unconfined", "no-new-privileges"]),
    ]
    for bad in bad_cases:
        try:
            mp.check_container(bad, expected, work.resolve(), "net")
        except mp.Stop:
            continue
        raise AssertionError(f"container check accepted {bad}")
    for net in ({"Name": "n", "Internal": False}, {"Name": "n"}):
        try:
            mp.check_network(net)
        except mp.Stop:
            continue
        raise AssertionError("non-internal network accepted")


def expect_stop(fn, *a) -> None:
    try:
        fn(*a)
    except mp.Stop:
        return
    raise AssertionError(f"{fn.__name__}{a} did not stop")


def test_gates() -> None:
    ok = ('{"enabled":true,"enabledSource":"settings","unavailableReason":null,"strictMode":true,'
          '"filesystemPolicy":"strict","autoAllowBashIfSandboxed":false}')
    mp.check_sandbox_status(ok)
    expect_stop(mp.check_sandbox_status, ok.replace('"unavailableReason":null', '"unavailableReason":"bwrap missing"'))
    expect_stop(mp.check_sandbox_status, ok.replace('"enabledSource":"settings"', '"enabledSource":"default"'))
    expect_stop(mp.check_sandbox_status, "not json")
    good = ("PROBE_STARTED\nLOOPBACK CONNECTED\nDIRECT ERRNO ENETUNREACH\nGATEWAY ERRNO EHOSTUNREACH\n"
            "HOST_DOCKER_INTERNAL NORESOLVE\nPROXY_REACHABLE CONNECTED\n"
            "PROXY_CONNECT_DENY HTTP/1.0 403 Forbidden\nPROXY_ROUTE_DENY HTTP/1.0 403 Forbidden\n")
    mp.check_egress(0, good)
    mp.check_egress(0, good.replace("HOST_DOCKER_INTERNAL NORESOLVE", "HOST_DOCKER_INTERNAL ERRNO ENETUNREACH"))
    expect_stop(mp.check_egress, 0, good.replace("GATEWAY ERRNO EHOSTUNREACH", "GATEWAY ERRNO ECONNREFUSED"))
    expect_stop(mp.check_egress, 0, good.replace("HOST_DOCKER_INTERNAL NORESOLVE", "HOST_DOCKER_INTERNAL CONNECTED"))
    expect_stop(mp.check_egress, 0, good.replace("GATEWAY ERRNO EHOSTUNREACH\n", ""))
    check(mp.network_gateway({"IPAM": {"Config": [{"Subnet": "172.30.0.0/16", "Gateway": "172.30.0.1"}]}})
          == "172.30.0.1", "gateway read from IPAM")
    expect_stop(mp.network_gateway, {"IPAM": {"Config": []}})
    image_env = ["PATH=/usr/bin", "LANG=C.UTF-8"]
    mp.check_container_env(list(reversed(image_env)), image_env)
    expect_stop(mp.check_container_env, image_env + ["ANTHROPIC_API_KEY=x"], image_env)
    expect_stop(mp.check_container_env, image_env[:1], image_env)
    expect_stop(mp.check_egress, 0, good.replace("ERRNO ENETUNREACH", "CONNECTED"))
    expect_stop(mp.check_egress, 0, good.replace("ERRNO ENETUNREACH", "ERRNO ETIMEDOUT"))
    expect_stop(mp.check_egress, 0, good.replace("LOOPBACK CONNECTED", "LOOPBACK ERRNO ECONNREFUSED"))
    expect_stop(mp.check_egress, 0, good.replace("CONNECT_DENY HTTP/1.0 403", "CONNECT_DENY HTTP/1.0 200"))
    expect_stop(mp.check_egress, 0, good.replace("ROUTE_DENY HTTP/1.0 403", "ROUTE_DENY HTTP/1.0 502"))
    expect_stop(mp.check_egress, 1, good)
    expect_stop(mp.check_egress, 0, good.replace("PROBE_STARTED\n", ""))
    mp.check_auth_probe(0, "PROBE_STARTED\nCREDENTIAL_ABSENT\n")
    expect_stop(mp.check_auth_probe, 3, "PROBE_STARTED\nBLOCK: path /proxy-secret\n")
    expect_stop(mp.check_auth_probe, 0, "CREDENTIAL_ABSENT\n")
    expect_stop(mp.check_auth_probe, 4, "PROBE_STARTED\nCREDENTIAL_ABSENT\n")
    soon = (mp.dt.datetime.now(mp.dt.timezone.utc) + mp.dt.timedelta(hours=2)).isoformat()
    check(mp.check_credential_record(soon, "USD 5")["limit"] == "USD 5", "short-lived, limited credential recorded")
    late = (mp.dt.datetime.now(mp.dt.timezone.utc) + mp.dt.timedelta(hours=48)).isoformat()
    past = (mp.dt.datetime.now(mp.dt.timezone.utc) - mp.dt.timedelta(hours=1)).isoformat()
    for bad in ((late, "USD 5"), (past, "USD 5"), (soon, " "), (None, "USD 5"), ("2026-10-26T10:00:00", "USD 5")):
        expect_stop(mp.check_credential_record, *bad)
    log = "\n".join(json.dumps({"request": r, "allowed": a, "status": s}) for r, a, s in
                    ((["CONNECT", "api.anthropic.com:443"], False, 403), (["GET", "/"], False, 403),
                     (["POST", "/v1/messages"], True, 200), (["POST", "/v1/messages"], True, 429),
                     (["GET", "/v2/x"], False, 403))) + "\nnot json\n"
    got = mp.proxy_requests(log, 2)
    check({k: got[k] for k in ("allowed", "denied", "statuses", "unparsed")} ==
          {"allowed": ["POST /v1/messages"] * 2, "denied": ["GET /v2/x"], "statuses": {"200": 1, "429": 1, "403": 1},
           "unparsed": 1}, f"only post-gate proxy entries are counted: {got}")
    check(mp.egress_anomaly(got), "denied request is an anomaly")
    ok = {"allowed": ["GET /v1/models", "POST /v1/messages"], "denied": [], "statuses": {}, "unparsed": 0}
    check(not mp.egress_anomaly(ok), "documented routes only")
    check(mp.egress_anomaly({**ok, "allowed": ["GET /v1/models"]}), "no Messages call is an anomaly")
    check(mp.egress_anomaly({**ok, "stderrBytes": 5}), "proxy stderr is an anomaly")
    log = "\n".join(json.dumps(e) for e in (
        {"request": ["POST", "/v1/messages"], "allowed": True, "status": 200, "reason": None, "usage": 100},
        {"request": ["POST", "/v1/messages/count_tokens"], "allowed": True, "status": 200, "reason": None,
         "usage": None},
        {"request": ["POST", "/v1/messages"], "allowed": False, "status": 403, "reason": "token-limit 101 > 100"}))
    got = mp.proxy_requests(log, 0, "boom")
    check(got["usageTokens"] == 100 and got["limitRefused"] and got["stderrBytes"] == 4, f"proxy ledger read: {got}")


class Headers(dict):
    def get(self, k, default=None):
        return next((v for key, v in self.items() if key.lower() == k.lower()), default)


def test_proxy() -> None:
    body = json.dumps({"model": "claude-opus-5-5", "messages": []}).encode()
    ledger = mp.ProxyLedger("claude-opus-5-5", 1000)
    check(ledger.refuse("POST", "/v1/messages", Headers(), body) is None, "declared model forwarded")
    check(ledger.refuse("GET", "/v1/models", Headers(), None) is None, "models list forwarded")
    check(ledger.refuse("GET", "/", Headers(), None) == (403, "route"), "other route refused")
    check(ledger.refuse("CONNECT", "api.anthropic.com:443", Headers(), None)[0] == 403, "CONNECT refused")
    other = json.dumps({"model": "claude-haiku-5-5"}).encode()
    check(ledger.refuse("POST", "/v1/messages", Headers(), other)[0] == 403, "other model refused")
    check(ledger.refuse("POST", "/v1/messages/count_tokens", Headers(), other)[0] == 403, "count_tokens model checked")
    check(ledger.refuse("POST", "/v1/messages", Headers(), b"not json")[0] == 403, "unreadable body refused")
    check(ledger.refuse("POST", "/v1/messages", Headers({"Transfer-Encoding": "chunked"}), body)[0] == 411,
          "chunked request refused")
    sse = mp.SseUsage()
    stream = (b'event: message_start\ndata: {"type":"message_start","message":{"id":"m","usage":{"input_tokens":20,'
              b'"cache_creation_input_tokens":300,"cache_read_input_tokens":400,"output_tokens":1}}}\n\n'
              b'event: content_block_delta\ndata: {"type":"content_block_delta","delta":{"text":"hi"}}\n\n'
              b'event: message_delta\r\ndata: {"type":"message_delta","usage":{"output_tokens":15}}\r\n\r\n'
              b'event: message_delta\ndata: {"type":"message_delta","usage":{"output_tokens":80}}\n\n')
    for i in range(0, len(stream), 7):
        sse.feed(stream[i:i + 7])
    check(sse.total() == 20 + 300 + 400 + 80, f"SSE usage: start fields + cumulative delta ({sse.total()})")
    check(mp.SseUsage().total() is None, "no usage event is unmeasurable, not 0")
    check(mp.json_usage(json.dumps({"usage": {"input_tokens": 5, "cache_read_input_tokens": 7,
                                              "output_tokens": 3}}).encode()) == 15, "JSON usage")
    check(mp.json_usage(b"{}") is None and mp.json_usage(b"<html>") is None, "missing usage is None")
    ledger.add(600, True)
    check(ledger.refuse("POST", "/v1/messages", Headers(), body) is None, "under the limit")
    ledger.add(500, True)
    refused = ledger.refuse("POST", "/v1/messages", Headers(), body)
    check(refused == (403, "token-limit 1100 > 1000"), f"over the limit refuses later requests: {refused}")
    check(ledger.refuse("GET", "/v1/models", Headers(), None)[0] == 403, "closed for every route")
    blind = mp.ProxyLedger("claude-opus-5-5", 1000)
    blind.add(None, False)
    check(blind.refuse("POST", "/v1/messages", Headers(), body) is None, "non-billable without usage is fine")
    blind.add(None, True)
    check(blind.refuse("POST", "/v1/messages", Headers(), body) == (403, "usage not measurable"),
          "a billed response without usage closes the proxy")
    fwd = mp.forward_headers([("Authorization", "Bearer p"), ("x-api-key", "w"), ("Proxy-Authorization", "x"),
                              ("X-Forwarded-For", "1.2.3.4"), ("Forwarded", "for=x"), ("Transfer-Encoding", "chunked"),
                              ("Host", "p"), ("anthropic-version", "2023-06-01"), ("Content-Type", "application/json")],
                             "real")
    check(fwd == {"anthropic-version": "2023-06-01", "Content-Type": "application/json", "x-api-key": "real"},
          f"only safe headers forwarded, credential replaced: {fwd}")


def test_secret_quarantine(tmp: Path) -> None:
    work = tmp / "secret"
    rc, _, err = run_cli(dry_args(work, "--dry-run-scenario", "secret"))
    check(rc == 2 and "credential-shaped" in err and "Bearer" not in err.split("credential-shaped", 1)[1],
          f"secret quarantined without echoing it: {err}")
    check(not (work / "MRS-P02-A").exists() and len(list((work / "quarantine").iterdir())) == 1, "moved to quarantine")
    check(mp.summarize(work)["quarantined"], "summary lists the quarantined Run")
    rc, _, err = run_cli(dry_args(work, "--skip-existing"))
    check(rc == 2 and "quarantined Runs exist" in err, "resume refused while quarantined")


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


def test_egress_anomaly(tmp: Path) -> None:
    rc, _, err = run_cli(dry_args(tmp / "egress", "--dry-run-scenario", "proxy-denied"))
    check(rc == 2 and "egress-anomaly" in err, f"proxy denial during the Run stops: {err}")
    rc, _, err = run_cli(dry_args(tmp / "usage", "--dry-run-scenario", "usage-mismatch"))
    check(rc == 2 and "usage-mismatch" in err, f"proxy usage differing from the stream stops: {err}")


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
    real = ["run", "--work-root", str(tmp / "real"), "--timeout-s", "1800", "--max-run-tokens", "300000",
            "--budget-tokens", "600000", "--image", "python:3.12"]
    rc, _, err = run_cli(real)
    check(rc == 2 and "--credential-expires-at" in err, f"real Run needs the credential expiry: {err}")
    soon = (mp.dt.datetime.now(mp.dt.timezone.utc) + mp.dt.timedelta(hours=2)).isoformat()
    rc, _, err = run_cli(real + ["--credential-expires-at", soon, "--credential-limit", "USD 5"])
    check(rc == 2 and "STOP:" in err and "credential" not in err, f"then the container preflight stops: {err}")
    check(not (tmp / "real").exists(), "nothing created before preflight passes")
    check(mp.PROXY_AUTH_PATH == "NOT_TESTED", "real Runs stop before the model until the proxy path is confirmed")


def test_never_launched_retry(tmp: Path) -> None:
    work = tmp / "retry"
    rdir = work / "MRS-P02-A"
    rdir.mkdir(parents=True)
    (rdir / "run.json").write_text(json.dumps({"status": "isolation-stop", "modelLaunched": False}))
    rc, out, err = run_cli(dry_args(work, "--skip-existing"))
    check(rc == 0 and "retry MRS-P02-A" in out, f"never-launched Run retried: {err}")
    check((work / "attempts/MRS-P02-A/attempt-1/run.json").exists(), "previous attempt preserved")


def main() -> int:
    tests = [test_plan_and_settings, test_policy, test_gates, test_proxy]
    tmp_tests = [test_container_isolation, test_secret_quarantine, test_dry_run_and_summary, test_effort_not_visible, test_model_mismatch_stops,
                 test_credential_access_stops, test_token_limit_and_budget, test_incomplete_trace, test_egress_anomaly, test_timeout,
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
