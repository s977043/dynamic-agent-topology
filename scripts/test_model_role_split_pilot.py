#!/usr/bin/env python3
"""Model-free tests for the #220 pilot kit (dry-run with the synthetic stream only)."""
from __future__ import annotations

from pathlib import Path
import contextlib
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time

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
    cmd = mp.docker_run_command(Args, rdir, "c", "vol")
    binds = [cmd[i + 1] for i, a in enumerate(cmd) if a == "-v"]
    check(len(binds) == 4 and binds[-1] == f"vol:{mp.PROXY_SOCKET_DIR}:ro" and not any(".credentials" in b for b in binds),
          "three bind mounts and the socket volume (ro), no credential in the Run container")
    check(cmd[-4:] == ["python3", "-I", "-c", mp.RELAY], "Run container's main process is the loopback relay")
    pcmd = mp.proxy_run_command(Args, "p", "vol", "claude-opus-5-5")
    check(pcmd[-3:] == ["_proxy", "claude-opus-5-5", "300000"], "proxy gets the declared model and the Run limit")
    pbinds = [pcmd[i + 1] for i, a in enumerate(pcmd) if a == "-v"]
    check(any(b.startswith(os.path.realpath(Args.credentials_file) + ":") and b.endswith(f"{mp.PROXY_SECRET}:ro") for b in pbinds)
          and len(pbinds) == 3 and pbinds[-1] == f"vol:{mp.PROXY_SOCKET_DIR}", "credential mounted read-only into the proxy only")
    env = mp.container_env()
    check(env["ANTHROPIC_AUTH_TOKEN"] == mp.PLACEHOLDER_TOKEN and env["ANTHROPIC_BASE_URL"] == "http://127.0.0.1:3128",
          "Worker gets the relay URL and a placeholder")
    pexp = sorted(("bind", s, d, rw) for d, (s, rw) in mp.proxy_bind_sources(Args).items())
    pvol = {"Type": "volume", "Name": "vol", "Destination": mp.PROXY_SOCKET_DIR, "RW": True}
    pins = {"Mounts": [{"Type": t, "Source": s, "Destination": d, "RW": rw} for t, s, d, rw in pexp] + [pvol],
            "HostConfig": {}}
    mp.check_proxy_container(pins, Args, "vol")
    expect_stop(mp.check_proxy_container, {**pins, "HostConfig": {"PidMode": "host"}}, Args, "vol")
    expect_stop(mp.check_proxy_container, {**pins, "Mounts": pins["Mounts"][:1] + [pvol]}, Args, "vol")
    expect_stop(mp.check_proxy_container, {**pins, "Mounts": pins["Mounts"][:2]}, Args, "vol")
    expect_stop(mp.check_proxy_container, pins, Args, "other")
    check(cmd[cmd.index("--network") + 1] == "none" and "--cap-drop" in cmd and "--read-only" in cmd
          and f"seccomp={mp.SECCOMP}" in cmd, "no network and EXP-001 constraints")
    check(pcmd[pcmd.index("--network") + 1] == "bridge", "proxy alone has the outside route")
    check(any(b.endswith(":/work") for b in binds[:3]) and all(b.endswith(":ro") for b in binds if not b.endswith(":/work")),
          "only /work is writable")
    expected = mp.expected_mounts(Args, rdir)
    compact = json.dumps(json.loads(mp.SECCOMP.read_text(encoding="utf-8")), separators=(",", ":"))
    vol = ("volume", "vol", mp.PROXY_SOCKET_DIR, False)

    def inspect(mounts, **host):
        base = {"Privileged": False, "CapAdd": None, "CapDrop": ["ALL"], "ReadonlyRootfs": True, "NetworkMode": "none",
                "Tmpfs": {"/tmp": "", mp.CONFIG_DIR: "uid=1"}, "SecurityOpt": [f"seccomp={compact}", "no-new-privileges"]}
        return {"Mounts": [{"Type": t, "Source" if t == "bind" else "Name": s, "Destination": d, "RW": rw}
                           for t, s, d, rw in mounts],
                "HostConfig": {**base, **host}}

    evidence = mp.check_container(inspect(expected + [vol]), expected, work.resolve(), "vol")
    check(evidence["seccompMatchesLaunchedProfile"], "seccomp matches")
    rw_cc = [(t, s, d, True if d == "/cc" else rw) for t, s, d, rw in expected]
    bad_cases = [
        inspect(expected + [vol, ("bind", str(work / "MRS-P02-B"), "/past", False)]),
        inspect(expected + [vol, ("bind", Args.credentials_file, "/cc-home/.credentials.json", False)]),
        inspect(expected + [vol, ("volume", "v", "/data", True)]),
        inspect(expected),
        inspect(expected + [("volume", "vol", mp.PROXY_SOCKET_DIR, True)]),
        inspect(rw_cc + [vol]),
        inspect(expected + [vol], PidMode="container:p"),
        inspect(expected + [vol], Tmpfs={"/tmp": ""}),
        inspect(expected + [vol], NetworkMode="bridge"),
        inspect(expected + [vol], NetworkMode="container:p"),
        inspect(expected + [vol], Privileged=True),
        inspect(expected + [vol], SecurityOpt=["seccomp=unconfined", "no-new-privileges"]),
    ]
    for bad in bad_cases:
        try:
            mp.check_container(bad, expected, work.resolve(), "vol")
        except mp.Stop:
            continue
        raise AssertionError(f"container check accepted {bad}")
    mp.check_no_network({"NetworkSettings": {"Networks": {"none": {"IPAddress": "", "Gateway": ""}}}})
    for nets in ({"bridge": {"IPAddress": "172.17.0.3"}}, {"none": {}, "bridge": {}}, {}, {"none": {"IPAddress": "10.0.0.2"}}):
        expect_stop(mp.check_no_network, {"NetworkSettings": {"Networks": nets}})
    opts = {"type": "tmpfs", "device": "tmpfs", "o": mp.volume_mount_options()}
    mp.check_volume({"Name": "vol", "Driver": "local", "Options": opts}, "vol")
    expect_stop(mp.check_volume, {"Name": "vol", "Driver": "local", "Options": None}, "vol")
    expect_stop(mp.check_volume, {"Name": "vol", "Driver": "local", "Options": {**opts, "o": "mode=0777"}}, "vol")
    check(mp.volume_create_command("vol")[-1] == "vol" and "type=tmpfs" in mp.volume_create_command("vol"),
          "socket volume is tmpfs")


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
    good = ("PROBE_STARTED\nLOOPBACK CONNECTED\nROUTES v4=0 v6=0\nDIRECT ERRNO ENETUNREACH\nDIRECT_UDP ERRNO ENETUNREACH\n"
            "GATEWAY ERRNO EHOSTUNREACH\nGATEWAY_UDP ERRNO ENETUNREACH\nPROXY_IP ERRNO ENETUNREACH\n"
            "HOST_DOCKER_INTERNAL NORESOLVE\nPROXY_REACHABLE CONNECTED\n"
            "PROXY_CONNECT_DENY HTTP/1.0 403 Forbidden\nPROXY_ROUTE_DENY HTTP/1.0 403 Forbidden\n")
    mp.check_egress(0, good)
    mp.check_egress(0, good.replace("HOST_DOCKER_INTERNAL NORESOLVE", "HOST_DOCKER_INTERNAL ERRNO ENETUNREACH"))
    expect_stop(mp.check_egress, 0, good.replace("GATEWAY ERRNO EHOSTUNREACH", "GATEWAY ERRNO ECONNREFUSED"))
    expect_stop(mp.check_egress, 0, good.replace("HOST_DOCKER_INTERNAL NORESOLVE", "HOST_DOCKER_INTERNAL CONNECTED"))
    expect_stop(mp.check_egress, 0, good.replace("GATEWAY ERRNO EHOSTUNREACH\n", ""))
    expect_stop(mp.check_egress, 0, good.replace("ROUTES v4=0 v6=0", "ROUTES v4=1 v6=0"))
    expect_stop(mp.check_egress, 0, good.replace("GATEWAY_UDP ERRNO ENETUNREACH", "GATEWAY_UDP SENT"))
    expect_stop(mp.check_egress, 0, good.replace("PROXY_IP ERRNO ENETUNREACH", "PROXY_IP ERRNO ECONNREFUSED"))
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
    dup = b'{"model":"claude-haiku-5-5","model":"claude-opus-5-5"}'
    check(ledger.refuse("POST", "/v1/messages", Headers(), dup) == (403, "unreadable body"), "duplicate keys refused")
    check([mp.content_length(v) for v in (None, "0", "12")] == [0, 0, 12], "valid Content-Length")
    check(all(mp.content_length(v) is None for v in ("-1", "abc", "1e3", " 5", "\uff11", "9" * 13)),
          "negative or non-numeric Content-Length rejected")
    check(ledger.refuse("POST", "/v1/messages", Headers({"Transfer-Encoding": "chunked"}), body)[0] == 411,
          "chunked request refused")
    sse = mp.SseUsage()
    stream = (b'event: message_start\ndata: {"type":"message_start","message":{"id":"m","usage":{"input_tokens":20,'
              b'"cache_creation_input_tokens":300,"cache_read_input_tokens":400,"output_tokens":1}}}\n\n'
              b'event: content_block_delta\ndata: {"type":"content_block_delta","delta":{"text":"hi"}}\n\n'
              b'event: message_delta\r\ndata: {"type":"message_delta","usage":{"output_tokens":15}}\r\n\r\n'
              b'event: message_delta\ndata: {"type":"message_delta","usage":{"output_tokens":80}}\n\n'
              b'event: message_stop\ndata: {"type":"message_stop"}\n\n')
    for i in range(0, len(stream), 7):
        sse.feed(stream[i:i + 7])
    check(sse.total() == 20 + 300 + 400 + 80, f"SSE usage: start fields + cumulative delta ({sse.total()})")
    check(mp.SseUsage().total() is None, "no usage event is unmeasurable, not 0")
    cut = mp.SseUsage()
    cut.feed(stream[:stream.index(b"event: message_delta")])
    check(cut.total() is None, "a stream cut before message_stop is unmeasurable")
    cut.feed(stream[stream.index(b"event: message_delta"):stream.index(b"event: message_stop")])
    check(cut.total() is None, "message_delta without message_stop is still unmeasurable")
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
    check(blind.refuse("POST", "/v1/messages", Headers(), body) is None, "first billable request admitted")
    blind.add(None, True)
    check(blind.closed == "usage not measurable", "a billable response without usage (any status) closes the proxy")
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


def test_proxy_concurrency() -> None:
    body = json.dumps({"model": "m"}).encode()
    ledger = mp.ProxyLedger("m", 1000)
    start = threading.Barrier(20)
    results = []

    def send() -> None:
        start.wait()
        results.append(ledger.refuse("POST", "/v1/messages", Headers(), body))

    threads = [threading.Thread(target=send) for _ in range(20)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    admitted = [r for r in results if r is None]
    check(len(admitted) == 1 and all(r == (429, "concurrent billable request") for r in results if r),
          f"one billable request in flight at a time: {results}")
    check(ledger.refuse("GET", "/v1/models", Headers(), None) is None, "non-billable route not serialized")
    ledger.add(1100, True)
    check(ledger.refuse("POST", "/v1/messages", Headers(), body)[0] == 403, "next request sees the earlier usage")


class FakeUpstream:
    """Stands in for http.client.HTTPSConnection; `mode` picks the response."""
    mode = "json"
    release = threading.Event()  # "slow" holds the response until the test sets it

    def __init__(self, *_a, **_k):
        self.chunks: list[bytes] = []

    def request(self, *_a, **_k) -> None:
        pass

    def close(self) -> None:
        pass

    def getheaders(self) -> list:
        extra = [("X-Split", "a\r\nSet-Cookie: injected"), ("X-Nul\x00", "b")] if FakeUpstream.mode == "split" else []
        return [("Content-Type", self.ctype), *extra]

    def getheader(self, name: str, default=None):
        return self.ctype if name == "Content-Type" else default

    def read1(self, _n: int) -> bytes:
        return self.chunks.pop(0) if self.chunks else b""

    def getresponse(self):
        mode = FakeUpstream.mode
        if mode == "error":
            raise ValueError("unexpected")
        if mode == "slow":
            FakeUpstream.release.wait(10)
        self.status, self.ctype = (429, "application/json") if mode == "429" else (200, "application/json")
        self.chunks = [b'{"usage":{"input_tokens":100,"output_tokens":10}}'] if self.status == 200 else [b"{}"]
        if mode == "sse_cut":
            self.ctype = "text/event-stream"
            self.chunks = [b'data: {"type":"message_start","message":{"usage":{"input_tokens":5}}}\n\n']
        return self


@contextlib.contextmanager
def live_proxy(tmp: Path):
    """proxy_main on a Unix socket with FakeUpstream (no external network); yields (socket path, log)."""
    import http.client
    import socketserver
    servers = []
    real_server, real_conn = socketserver.UnixStreamServer, http.client.HTTPSConnection
    real_secret, real_socket = mp.PROXY_SECRET, mp.PROXY_SOCKET

    class LocalServer(real_server):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            servers.append(self)

    (tmp / "key").write_text("sk-test")
    sock_dir = tempfile.mkdtemp(dir="/tmp")  # AF_UNIX paths are limited to ~104 bytes
    log = io.StringIO()
    socketserver.UnixStreamServer, http.client.HTTPSConnection = LocalServer, FakeUpstream
    mp.PROXY_SECRET, mp.PROXY_SOCKET = str(tmp / "key"), os.path.join(sock_dir, "p.sock")
    try:
        with contextlib.redirect_stdout(log):
            threading.Thread(target=mp.proxy_main, args=(["m", "1000"],), daemon=True).start()
            end = time.monotonic() + 10
            while not servers:
                check(time.monotonic() < end, "proxy started")
                time.sleep(0.01)
            yield mp.PROXY_SOCKET, log
            servers[0].shutdown()
            servers[0].server_close()
    finally:
        socketserver.UnixStreamServer, http.client.HTTPSConnection = real_server, real_conn
        with contextlib.suppress(OSError):
            os.unlink(mp.PROXY_SOCKET)
        os.rmdir(sock_dir)
        mp.PROXY_SECRET, mp.PROXY_SOCKET = real_secret, real_socket


def unix_connect(path: str) -> socket.socket:
    s = socket.socket(socket.AF_UNIX)
    s.settimeout(10)
    s.connect(path)
    return s


def post(path: str, body: bytes = b'{"model":"m"}', length: int | None = None) -> int:
    with unix_connect(path) as s:
        s.sendall(b"POST /v1/messages HTTP/1.1\r\nHost: x\r\nContent-Length: %d\r\n\r\n"
                  % (len(body) if length is None else length) + body)
        return int(s.recv(64).split(b" ")[1])


def wait_logged(log: io.StringIO, n: int, deadline_s: float = 10) -> None:
    """Wait until the proxy has recorded n requests; it records after freeing the billable slot."""
    end = time.monotonic() + deadline_s
    while len(log.getvalue().splitlines()) < n:
        if time.monotonic() > end:
            raise AssertionError(f"proxy did not record {n} requests: {log.getvalue()!r}")
        time.sleep(0.01)


def test_proxy_handler(tmp: Path) -> None:
    for mode, first in (("sse_cut", 200), ("429", 429), ("error", 502)):
        FakeUpstream.mode = mode
        with live_proxy(tmp) as (port, log):
            check(post(port) == first, f"{mode}: relayed status")
            wait_logged(log, 1)
            check(post(port) == 403, f"{mode}: proxy closed (slot freed, not 429)")
            wait_logged(log, 2)
        reasons = [json.loads(line)["reason"] for line in log.getvalue().splitlines()]
        expected = "proxy error ValueError" if mode == "error" else "closed: usage not measurable"
        check(reasons[0] == expected and reasons[1] == expected.removeprefix("closed: "),
              f"{mode}: closure reason recorded: {reasons}")
    FakeUpstream.mode = "slow"
    with live_proxy(tmp) as (port, _log):
        start = threading.Barrier(5)
        statuses = []

        def send() -> None:
            start.wait()
            statuses.append(post(port))
            if statuses.count(429) == 4:
                FakeUpstream.release.set()

        threads = [threading.Thread(target=send) for _ in range(5)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        check(sorted(statuses) == [200, 429, 429, 429, 429], f"one billable request at a time: {statuses}")
    FakeUpstream.mode = "json"
    with live_proxy(tmp) as (port, log):
        head = b'{"model":"m","pad":"'
        exact = head + b"x" * (mp.MAX_BODY_BYTES - len(head) - 2) + b'"}'
        check(post(port, exact) == 200, "body of exactly MAX_BODY_BYTES forwarded")
        wait_logged(log, 1)
        check(post(port, b"", mp.MAX_BODY_BYTES + 1) == 413, "larger body refused before it is read")
        wait_logged(log, 2)
        check(post(port) == 200, "proxy still serves after a 413")
    check(json.loads(log.getvalue().splitlines()[1])["reason"] == "body too large", "413 recorded")
    FakeUpstream.mode = "split"
    with live_proxy(tmp) as (port, log):
        with unix_connect(port) as s:
            s.sendall(b'POST /v1/messages HTTP/1.1\r\nHost: x\r\nContent-Length: 13\r\n\r\n{"model":"m"}')
            raw = b""
            while chunk := s.recv(4096):
                raw += chunk
        wait_logged(log, 1)
    check(raw.startswith(b"HTTP/1.0 200") and b"Set-Cookie" not in raw and b"X-Split" not in raw,
          f"headers with CR/LF/NUL not relayed: {raw[:200]!r}")
    check("dropped unsafe headers ['X-Split', 'X-Nul\\x00']" in json.loads(log.getvalue())["reason"],
          "dropped headers recorded")


def test_relay_to_proxy(tmp: Path) -> None:
    FakeUpstream.mode = "json"
    with live_proxy(tmp) as (path, log):
        check(os.stat(path).st_mode & 0o777 == 0o600, f"proxy socket mode {oct(os.stat(path).st_mode & 0o777)}")
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(16)
        port = listener.getsockname()[1]
        bind_line = f'l = socket.socket(); l.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\nl.bind(("127.0.0.1", {mp.PROXY_PORT})); l.listen(16)'
        check(bind_line in mp.RELAY, "relay binds the fixed loopback port")
        relay = mp.RELAY.replace(repr(mp.PROXY_SOCKET_DIR + "/proxy.sock"), repr(path)).replace(
            bind_line, f"l = socket.socket(fileno={listener.fileno()})")  # already listening: no port race, no wait
        proc = subprocess.Popen([sys.executable, "-I", "-c", relay], pass_fds=(listener.fileno(),))
        listener.close()
        try:
            def relay_post(timeout: float = 10) -> bytes:
                with socket.create_connection(("127.0.0.1", port), timeout=timeout) as s:
                    s.sendall(b'POST /v1/messages HTTP/1.1\r\nHost: x\r\nContent-Length: 13\r\n\r\n{"model":"m"}')
                    raw = b""
                    while chunk := s.recv(4096):
                        raw += chunk
                    return raw

            raw = relay_post()
            check(raw.startswith(b"HTTP/1.0 200") and b"sk-test" not in raw, f"relayed through the proxy: {raw[:80]!r}")
            idle = [socket.create_connection(("127.0.0.1", port), timeout=5) for _ in range(mp.RELAY_MAX_CONNECTIONS)]
            try:
                relay_post(timeout=1)
            except socket.timeout:
                pass
            else:
                raise AssertionError("relay served more than RELAY_MAX_CONNECTIONS connections at once")
            for s in idle:
                s.close()
            wait_logged(log, 2)  # the queued request above is relayed (and answered) once a slot frees
            raw = relay_post()
            check(raw.startswith(b"HTTP/1.0 200"), f"relay serves again once slots are free: {raw[:80]!r}")
        finally:
            proc.kill()
            proc.wait()


def test_bind_source(tmp: Path) -> None:
    rdir = tmp / "iso" / "MRS-P02-A"
    expected = mp.expected_mounts(Args, rdir)
    compact = json.dumps(json.loads(mp.SECCOMP.read_text(encoding="utf-8")), separators=(",", ":"))
    host = {"Privileged": False, "CapAdd": None, "CapDrop": ["ALL"], "ReadonlyRootfs": True, "NetworkMode": "none",
            "Tmpfs": {"/tmp": "", mp.CONFIG_DIR: "uid=1"}, "SecurityOpt": [f"seccomp={compact}", "no-new-privileges"]}
    vol = {"Type": "volume", "Name": "vol", "Destination": mp.PROXY_SOCKET_DIR, "RW": False}

    def inspect(fn):
        return {"Mounts": [{"Type": "bind", "Source": fn(s, d), "Destination": d, "RW": rw} for _, s, d, rw in expected]
                + [vol], "HostConfig": host}

    work_root = (tmp / "iso").resolve()
    for desktop in (False, True):
        mp.check_container(inspect(lambda s, d: s), expected, work_root, "vol", desktop)
    mp.check_container(inspect(lambda s, d: mp.HOST_MNT + s), expected, work_root, "vol", True)
    mp.check_container(inspect(lambda s, d: mp.HOST_MNT + s if d == "/work" else s), expected, work_root, "vol", True)
    work = next(s for _, s, d, _ in expected if d == "/work")
    for desktop, fn in ((False, lambda s, d: mp.HOST_MNT + s),
                        (True, lambda s, d: "/host_mnt/other" if d == "/work" else s),
                        (True, lambda s, d: mp.HOST_MNT + s + "/x" if d == "/work" else s),
                        (True, lambda s, d: s + "/x" if d == "/work" else s),
                        (True, lambda s, d: mp.HOST_MNT + "/" + s if d == "/work" else s),
                        (True, lambda s, d: "/host_mnt/host_mnt" + s if d == "/work" else s),
                        (True, lambda s, d: s + "/" if d == "/work" else s),
                        (True, lambda s, d: s.replace("/MRS-P02-A/", "/MRS-P02-A/./") if d == "/work" else s),
                        (True, lambda s, d: work if d == "/run-input" else s)):
        expect_stop(mp.check_container, inspect(fn), expected, work_root, "vol", desktop)
    pexp = sorted(("bind", s, d, rw) for d, (s, rw) in mp.proxy_bind_sources(Args).items())
    pvol = {"Type": "volume", "Name": "vol", "Destination": mp.PROXY_SOCKET_DIR, "RW": True}

    def pins(fn):
        return {"Mounts": [{"Type": "bind", "Source": fn(s), "Destination": d, "RW": rw} for _, s, d, rw in pexp] + [pvol],
                "HostConfig": {}}

    mp.check_proxy_container(pins(lambda s: mp.HOST_MNT + s), Args, "vol", True)
    expect_stop(mp.check_proxy_container, pins(lambda s: mp.HOST_MNT + s), Args, "vol", False)
    expect_stop(mp.check_proxy_container, pins(lambda s: mp.HOST_MNT + s + "/x"), Args, "vol", True)


class FakeDocker:
    """Stands in for mp.docker in teardown: `stuck` names survive every removal."""

    def __init__(self, names: dict, stuck: set[str]):
        self.alive = {names["container"]: "running", names["proxy"]: "running", names["volume"]: "volume"}
        self.stuck, self.calls = stuck, []

    def __call__(self, *args, stdin=None, check=True):
        self.calls.append(args)
        out = ""
        if args[0] == "stop":
            for n in args[3:]:
                if n in self.alive:
                    self.alive[n] = "exited"
        elif args[0] == "rm" or args[:2] == ("volume", "rm"):
            for n in args[2:]:
                if n in self.alive and n not in self.stuck:
                    del self.alive[n]
        elif args[0] == "ps":
            name = args[args.index("--filter") + 1].removeprefix("name=^/").removesuffix("$")
            out = f"{name} {self.alive[name]}\n" if name in self.alive else ""
        elif args[:2] == ("volume", "ls"):
            name = args[args.index("--filter") + 1].removeprefix("name=^").removesuffix("$")
            out = f"{name}\n" if name in self.alive else ""
        return subprocess.CompletedProcess(args, 0, out, "")


def test_teardown(tmp: Path) -> None:
    names = {"container": "mrs-c", "proxy": "mrs-proxy-c", "volume": "mrs-sock-c", "containerStarted": True,
             "proxyStarted": True, "volumeCreated": True}
    real_docker, real_sleep = mp.docker, mp.time.sleep
    mp.time.sleep = lambda _s: None
    try:
        mp.docker = FakeDocker(names, set())
        check(mp.teardown(names) == [], "clean teardown leaves nothing")
        mp.docker = FakeDocker(names, {"mrs-proxy-c", "mrs-sock-c"})
        left = mp.teardown(names, attempts=3)
        check(left == [{"name": "mrs-proxy-c", "state": "exited"}, {"name": "mrs-sock-c", "state": "volume"}],
              f"leftover proxy and volume reported: {left}")
        mp.docker = FakeDocker(names, set())
        check(mp.teardown({**names, "containerStarted": False, "proxyStarted": False, "volumeCreated": False}) == []
              and mp.docker.calls == [], "nothing created, nothing removed")
        # run_one: an isolation stop followed by a failed teardown is recorded as teardown-failed with the leftovers.
        real_isolate, real_prepare = mp.isolate_and_check, mp.fx.prepare
        mp.docker = FakeDocker({"container": "", "proxy": "", "volume": ""}, set())

        def isolate(_args, _rdir, nm, _ev, _cand, _model):
            nm.update(proxyStarted=True)
            mp.docker = FakeDocker(nm, {nm["proxy"]})
            raise mp.Stop("gate failed")

        mp.isolate_and_check = isolate
        mp.fx.prepare = lambda _cand, ws, _cache: ws.mkdir()
        try:
            args = mp.parser().parse_args(["run", "--work-root", str(tmp), "--timeout-s", "60", "--max-run-tokens",
                                           "300000", "--budget-tokens", "600000"])
            run = mp.plan()[0]
            try:
                mp.run_one(args, run, mp.load_pilot(), tmp, "prompt", {})
            except mp.Stop as exc:
                check("teardown left" in str(exc), f"teardown failure stops the batch: {exc}")
            else:
                raise AssertionError("run_one succeeded with a leftover proxy")
            rec = json.loads((tmp / run["runId"] / "run.json").read_text())
            check(rec["status"] == "teardown-failed" and rec["modelLaunched"] is False
                  and rec["stopReasonBeforeTeardown"] == "gate failed"
                  and [x["name"] for x in rec["teardownLeftovers"]] == [rec["names"]["proxy"]],
                  f"leftovers recorded: {rec.get('status')} {rec.get('teardownLeftovers')}")
            check(not mp.never_launched(rec), "a Run with leftovers is not retried automatically")
        finally:
            mp.isolate_and_check, mp.fx.prepare = real_isolate, real_prepare
    finally:
        mp.docker, mp.time.sleep = real_docker, real_sleep


def main() -> int:
    tests = [test_plan_and_settings, test_policy, test_gates, test_proxy, test_proxy_concurrency]
    tmp_tests = [test_container_isolation, test_secret_quarantine, test_dry_run_and_summary, test_effort_not_visible, test_model_mismatch_stops,
                 test_credential_access_stops, test_token_limit_and_budget, test_incomplete_trace, test_egress_anomaly, test_timeout,
                 test_guards, test_never_launched_retry, test_proxy_handler, test_relay_to_proxy, test_bind_source,
                 test_teardown]
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
