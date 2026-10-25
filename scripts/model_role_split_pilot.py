#!/usr/bin/env python3
"""Pilot kit for the #220 model role split comparison (runbook steps 11-12, preregistration §6 / §8).

Subcommands:
  plan       print the 2 pilot Runs (order 2, arm A then arm B)
  run        execute them sequentially with Claude Code CLI 2.1.310, --effort high; --dry-run never launches a model
  summarize  per-Run activation / trace completeness / token checks, m vs EXP-001 T0, and a proposed pilot judgment

Each Run gets a fresh workspace (scripts/model_role_split_fixture.py prepare) and a fresh non-persistent session
(`claude -p --output-format stream-json`) in --restricted / --safe-mode with a per-Run settings file that enables the
Bash sandbox and an allowlist. The stream is checked while it runs: a wrong init (version, model, permission mode,
tools, MCP), a wrong responding model, a tool input that touches credentials or the network, the token limit, or the
wall clock stops the Run. Grading reuses the fixture's verify (network denied by sandbox-exec). The Operator launches
`run` without --dry-run; agents use --dry-run only.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import datetime as dt
import errno
import hashlib
import json
import os
import queue
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import model_role_split_fixture as fx  # noqa: E402

PREREGISTRATION = ROOT / "docs/MODEL_ROLE_SPLIT_PREREGISTRATION.md"
PREREGISTRATION_BLOB = "5e7576393641dcdd0d70f60a1282fe3ff497172a"
RUNTIME_VERSION = "2.1.310"
ARMS = (("A", "claude-opus-5-5"), ("B", "claude-sonnet-5-5"))
EFFORT = "high"
PILOT_ORDER = 2
T0_TOKENS_EXP001 = 68022.0
LOCK_NAME = ".pilot.lock"
TOOLS = ("Bash", "Read", "Edit", "Write", "Glob", "Grep")
PERMISSION_MODE = "dontAsk"
# Host variables that would open an API-key / third-party billing path (U4-1) or override the Effort.
FORBIDDEN_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_BASE_URL",
                 "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
                 "CLAUDE_CODE_EFFORT_LEVEL", "ANTHROPIC_MODEL")
PASS_ENV = ("PATH", "HOME", "USER", "LOGNAME", "SHELL", "TMPDIR", "LANG", "TERM")
# Items no model-free check can confirm; the Operator must acknowledge them explicitly before a real Run.
NOT_TESTED = ("bash-sandbox-denies-credential-read", "bash-sandbox-denies-network", "keychain-ipc-from-sandbox",
              "settings-file-applied", "effort-visible-in-trace")
# Tool inputs (Bash commands, Read/Glob/Grep paths) that touch credentials or the network stop the Run.
CREDENTIAL_PATTERN = re.compile(r"\.claude|keychain|(^|[;&|(]\s*)security\s|credential|auth\.json|printenv|"
                                r"(^|[;&|(]\s*)env\b|/proc/|environ|anthropic_|oauth|\.ssh|\.netrc|\.config/gh", re.I)
NETWORK_PATTERN = re.compile(r"(^|[;&|(]\s*)(curl|wget|nc|ncat|ssh|scp|rsync|telnet|ftp)\b|"
                             r"git\s+(push|fetch|pull|clone|remote)|pip\d*(\.\d+)?\s+install|https?://", re.I)


class Stop(Exception):
    """Stop the batch; the message is the reason recorded for the Operator."""


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_pilot() -> dict:
    cands = fx.load_candidates()
    pilots = [c for c in cands.values() if c.get("pilot")]
    if [c["order"] for c in pilots] != [PILOT_ORDER]:
        raise Stop(f"candidate table pilot Tasks {[c['order'] for c in pilots]} != [{PILOT_ORDER}]")
    return pilots[0]


def plan() -> list[dict]:
    """Block 1 is odd, so A then B (preregistration §8 counterbalance rule)."""
    return [{"runId": f"MRS-P{PILOT_ORDER:02d}-{arm}", "arm": arm, "model": model} for arm, model in ARMS]


def bash_allow(cand: dict) -> list[str]:
    """allowedCommands as permission rules; the read-only shell phrase maps to ls / cat / grep."""
    rules = []
    for entry in cand["permissions"]["allowedCommands"]:
        if entry.startswith("読み取り専用のシェルコマンド"):
            rules += ["Bash(ls)", "Bash(ls *)", "Bash(cat *)", "Bash(grep *)"]
        elif any(ord(ch) > 127 for ch in entry):
            raise Stop(f"cannot map allowedCommands entry {entry!r}")
        else:
            rules.append(f"Bash({entry})")
    return rules


def settings(cand: dict) -> dict:
    """Identical for both arms; written outside the workspace so the agent cannot edit it."""
    return {
        "permissions": {
            "defaultMode": PERMISSION_MODE,
            "allow": ["Read", "Glob", "Grep", "Edit", "Write", *bash_allow(cand)],
            "deny": ["Read(~/.claude/**)", "Read(~/.claude.json)", "Read(~/Library/Keychains/**)", "Read(~/.ssh/**)",
                     "Read(~/.config/**)", "Bash(security *)", "Bash(env)", "Bash(printenv *)", "Bash(curl *)",
                     "Bash(wget *)", "Bash(git push *)", "WebFetch", "WebSearch"],
        },
        "sandbox": {"enabled": True, "allowUnsandboxedCommands": False, "autoAllowBashIfSandboxed": False,
                    "network": {"allowedDomains": []}},
    }


def claude_command(claude_bin: str, model: str, settings_path: Path, session_id: str) -> list[str]:
    return [claude_bin, "-p", "--output-format", "stream-json", "--verbose", "--model", model, "--effort", EFFORT,
            "--restricted", "--safe-mode", "--strict-mcp-config", "--disable-slash-commands",
            "--settings", str(settings_path), "--tools", ",".join(TOOLS), "--permission-mode", PERMISSION_MODE,
            "--permission-prompts", "none", "--no-session-persistence", "--session-id", session_id]


def child_env() -> dict:
    env = {k: os.environ[k] for k in PASS_ENV if k in os.environ}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


# ---------------------------------------------------------------- stream checks (live and after the Run)

def find_effort(obj) -> list:
    """Every value under a key containing 'effort' (the field name in stream-json is not documented)."""
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if "effort" in k.lower() and not isinstance(v, (dict, list)):
                found.append(v)
            found += find_effort(v)
    elif isinstance(obj, list):
        for v in obj:
            found += find_effort(v)
    return found


def tool_inputs(msg: dict) -> list[tuple[str, str, dict]]:
    out = []
    for block in (msg.get("message") or {}).get("content") or []:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            out.append((block.get("id"), block.get("name"), block.get("input") or {}))
    return out


def policy_violation(name: str, inp: dict) -> str | None:
    """Credential / network access in a Bash command or a Read/Glob/Grep path (Edit content is not scanned)."""
    if name == "Bash":
        text = str(inp.get("command", ""))
    elif name in ("Read", "Glob", "Grep"):
        text = " ".join(str(inp.get(k, "")) for k in ("file_path", "path", "pattern"))
    else:
        text = str(inp.get("file_path", ""))
    for label, pattern in (("credential", CREDENTIAL_PATTERN), ("network", NETWORK_PATTERN)):
        if name in ("Edit", "Write") and label == "network":
            continue
        if pattern.search(text):
            return f"{label} access in {name}: {text[:200]}"
    return None


def usage_total(usage: dict) -> int:
    return sum(int(usage.get(k) or 0) for k in
               ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))


class Monitor:
    """Checks each stream-json event as it arrives; returns a (status, reason) to stop the Run, or None."""

    def __init__(self, model: str, max_tokens: int):
        self.model, self.max_tokens = model, max_tokens
        self.init_seen = False
        self.usage_by_message: dict[str, int] = {}

    def check_init(self, ev: dict) -> tuple[str, str] | None:
        problems = []
        if ev.get("claude_code_version") != RUNTIME_VERSION:
            problems.append(f"version {ev.get('claude_code_version')!r}")
        if ev.get("model") != self.model:
            problems.append(f"model {ev.get('model')!r}")
        if ev.get("permissionMode") != PERMISSION_MODE:
            problems.append(f"permissionMode {ev.get('permissionMode')!r}")
        if sorted(ev.get("tools") or []) != sorted(TOOLS):
            problems.append(f"tools {ev.get('tools')!r}")
        if ev.get("mcp_servers"):
            problems.append(f"mcp_servers {ev.get('mcp_servers')!r}")
        return ("control-deviation", "init: " + ", ".join(problems)) if problems else None

    def feed(self, ev: dict) -> tuple[str, str] | None:
        kind = ev.get("type")
        if kind == "system" and ev.get("subtype") == "init":
            if self.init_seen:
                return "control-deviation", "second init event (not a single fresh session)"
            self.init_seen = True
            return self.check_init(ev)
        if kind == "assistant":
            msg = ev.get("message") or {}
            if msg.get("model") != self.model:
                return "control-deviation", f"responding model {msg.get('model')!r} != {self.model!r}"
            for _, name, inp in tool_inputs(ev):
                reason = policy_violation(name, inp)
                if reason:
                    return "policy-stop", reason
            if msg.get("usage"):
                self.usage_by_message[msg.get("id") or str(len(self.usage_by_message))] = usage_total(msg["usage"])
                if sum(self.usage_by_message.values()) > self.max_tokens:
                    return "token-limit", f"running total {sum(self.usage_by_message.values())} > {self.max_tokens}"
        return None


def read_stream(path: Path) -> dict:
    """Post-run summary of a saved stream: activation, effort, tool call completeness, usage."""
    events, bad = [], 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except ValueError:
            bad += 1
    inits = [e for e in events if e.get("type") == "system" and e.get("subtype") == "init"]
    results = [e for e in events if e.get("type") == "result"]
    models = sorted({(e.get("message") or {}).get("model") for e in events if e.get("type") == "assistant"},
                    key=str)
    uses, results_for = [], []
    for e in events:
        if e.get("type") == "assistant":
            uses += [tid for tid, _, _ in tool_inputs(e)]
        if e.get("type") == "user":
            for block in (e.get("message") or {}).get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    results_for.append(block.get("tool_use_id"))
    problems = []
    if bad:
        problems.append(f"{bad} non-JSON lines")
    if len(inits) != 1:
        problems.append(f"{len(inits)} init events")
    if len(results) != 1 or events[-1:] != results[-1:]:
        problems.append("stream does not end with exactly one result event")
    if len(set(uses)) != len(uses) or None in uses:
        problems.append("tool_use ids missing or duplicated")
    if sorted(uses, key=str) != sorted(results_for, key=str):
        problems.append(f"tool_use without matching tool_result: {sorted(set(uses) ^ set(results_for), key=str)}")
    result = results[-1] if results else {}
    usage = result.get("usage") or None
    init = inits[0] if inits else {}
    return {
        "events": len(events), "initModel": init.get("model"), "initVersion": init.get("claude_code_version"),
        "initPermissionMode": init.get("permissionMode"), "initTools": init.get("tools"),
        "sessionId": init.get("session_id"), "respondingModels": models,
        "effortValues": sorted({str(v) for v in find_effort(events)}),
        "toolCalls": len(uses), "toolResults": len(results_for), "complete": not problems, "problems": problems,
        "resultSubtype": result.get("subtype"), "resultIsError": result.get("is_error"),
        "durationMs": result.get("duration_ms"), "numTurns": result.get("num_turns"), "usage": usage,
        "modelUsage": result.get("modelUsage"), "totalTokens": usage_total(usage) if usage else None,
    }


# ---------------------------------------------------------------- launching

def launch(cmd: list[str], cwd: Path, env: dict, prompt: str, stream_path: Path, stderr_path: Path,
           monitor: Monitor, timeout_s: int) -> tuple[str | None, str | None, int | None]:
    """Run one session in its own process group; returns (stop status, reason, exit code)."""
    with stream_path.open("w", encoding="utf-8") as out, stderr_path.open("w", encoding="utf-8") as err:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err,
                                text=True, start_new_session=True)
        lines: queue.Queue = queue.Queue()
        threading.Thread(target=lambda: [lines.put(ln) for ln in proc.stdout] + [lines.put(None)], daemon=True).start()
        proc.stdin.write(prompt)
        proc.stdin.close()
        deadline = time.monotonic() + timeout_s
        stop = None
        while True:
            try:
                line = lines.get(timeout=max(0.0, deadline - time.monotonic()))
            except queue.Empty:
                stop = ("aborted-timeout", f"wall clock over {timeout_s}s")
                break
            if line is None:
                break
            out.write(line)
            out.flush()
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            stop = monitor.feed(ev)
            if stop:
                break
        if stop:
            kill_group(proc)
        try:
            rc = proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            kill_group(proc)
            rc = proc.wait()
    return (stop[0], stop[1], rc) if stop else (None, None, rc)


def kill_group(proc: subprocess.Popen) -> None:
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            continue


def fake_claude() -> int:
    """Dry-run stand-in for `claude`: synthetic stream-json on stdout. No model is launched."""
    sys.stdin.read()
    model, effort = os.environ["MRS_FAKE_MODEL"], os.environ.get("MRS_FAKE_EFFORT", "")
    tokens, scenario = int(os.environ["MRS_FAKE_TOKENS"]), os.environ.get("MRS_FAKE_SCENARIO", "ok")
    if scenario == "sleep":
        time.sleep(30)
    init = {"type": "system", "subtype": "init", "session_id": "dry-run", "model": model,
            "permissionMode": PERMISSION_MODE, "tools": list(TOOLS), "mcp_servers": [],
            "claude_code_version": RUNTIME_VERSION}
    if effort:
        init["effort"] = effort
    command = "cat ~/.claude/.credentials.json" if scenario == "credential" else "git status"
    half = tokens // 2
    use = {"input_tokens": 10, "cache_creation_input_tokens": 0, "cache_read_input_tokens": half - 20,
           "output_tokens": 10}
    events = [init,
              {"type": "assistant", "message": {"id": "m1", "model": model, "usage": use, "content": [
                  {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": command}}]}}]
    if scenario != "missing-result":
        events.append({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1"}]}})
    last = {"input_tokens": 10, "cache_creation_input_tokens": 0, "cache_read_input_tokens": tokens - half - 20,
            "output_tokens": 10}
    events.append({"type": "assistant", "message": {"id": "m2", "model": model, "usage": last,
                                                    "content": [{"type": "text", "text": "done"}]}})
    total = {k: use[k] + last[k] for k in use}
    events.append({"type": "result", "subtype": "success", "is_error": False, "duration_ms": 1, "num_turns": 2,
                   "usage": total, "modelUsage": {model: {"inputTokens": total["input_tokens"]}}})
    for ev in events:
        print(json.dumps(ev), flush=True)
    return 0


# ---------------------------------------------------------------- preflight

NET_PROBE = """import errno, socket, sys
s = socket.socket()
s.settimeout(5)
try:
    s.connect(("127.0.0.1", int(sys.argv[1])))
except OSError as exc:
    print("ERRNO", errno.errorcode.get(exc.errno, exc.errno))
    sys.exit(0)
print("CONNECTED")
"""


def probe_grading_sandbox(ac_python: str) -> dict:
    """Control check for the fixture's grading sandbox: a local listener is reachable outside, denied inside."""
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(4)
    port = str(listener.getsockname()[1])
    try:
        with tempfile.TemporaryDirectory() as d:
            prefix, denied = fx.sandbox_prefix(d)
            if not denied:
                raise Stop("sandbox-exec not available: the AC cannot run with network denied")
            control = subprocess.run([ac_python, "-c", NET_PROBE, port], capture_output=True, text=True,
                                     timeout=30, check=False)
            boxed = subprocess.run([*prefix, ac_python, "-c", NET_PROBE, port], capture_output=True, text=True,
                                   timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Stop(f"grading network probe could not run: {exc}")
    finally:
        listener.close()
    result = {"control": control.stdout.strip(), "sandboxed": boxed.stdout.strip()}
    if control.returncode != 0 or result["control"] != "CONNECTED":
        raise Stop(f"grading network probe control could not connect: {result}")
    if boxed.returncode != 0 or result["sandboxed"] not in (f"ERRNO {errno.errorcode[errno.EPERM]}",
                                                           f"ERRNO {errno.errorcode[errno.EACCES]}"):
        raise Stop(f"grading network probe: sandbox denial not confirmed: {result}")
    return result


def preflight(args, runs: list[dict]) -> dict:
    """Model-free checks; any failure stops before a session starts. Returns evidence for run.json."""
    evidence = {}
    if not args.skip_blob_check and fx.blob_sha(PREREGISTRATION.read_bytes()) != PREREGISTRATION_BLOB:
        raise Stop(f"{PREREGISTRATION.name} blob differs from {PREREGISTRATION_BLOB}")
    work_root = Path(args.work_root).resolve()
    if work_root == ROOT or ROOT in work_root.parents:
        raise Stop("work root must be outside the DAT repository")
    for name in ("timeout_s", "max_run_tokens", "budget_tokens"):
        if getattr(args, name) <= 0:
            raise Stop(f"--{name.replace('_', '-')} must be positive")
    if args.max_run_tokens > args.budget_tokens:
        raise Stop("--max-run-tokens exceeds --budget-tokens")
    existing = [r["runId"] for r in runs if (work_root / r["runId"]).exists()]
    if existing and not args.skip_existing:
        raise Stop(f"result directories already exist (refusing to overwrite): {', '.join(existing)}")
    present = [k for k in FORBIDDEN_ENV if os.environ.get(k)]
    if present:
        raise Stop(f"environment sets {present} (API-key / provider billing path or Effort override)")
    evidence["forbiddenEnvAbsent"] = list(FORBIDDEN_ENV)
    if args.dry_run:
        return evidence
    acked = sorted(x for x in (args.acknowledge_not_tested or "").split(",") if x)
    if acked != sorted(NOT_TESTED):
        raise Stop(f"--acknowledge-not-tested must list exactly {','.join(NOT_TESTED)} (got {acked})")
    evidence["acknowledgedNotTested"] = acked
    if sys.platform != "darwin" or not shutil.which("sandbox-exec"):
        raise Stop("macOS sandbox-exec is required (Claude Code Bash sandbox and the grading sandbox)")
    try:
        version = subprocess.run([args.claude_bin, "--version"], capture_output=True, text=True, timeout=60,
                                 env=child_env(), check=False).stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Stop(f"claude --version failed: {exc}")
    evidence["claudeVersion"] = version
    if version.split()[:1] != [RUNTIME_VERSION]:
        raise Stop(f"claude --version {version!r} is not {RUNTIME_VERSION}")
    evidence["gradingProbe"] = probe_grading_sandbox(args.ac_python)
    return evidence


# ---------------------------------------------------------------- batch

def read_record(rdir: Path) -> dict:
    path = rdir / "run.json"
    record = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if not isinstance(record.get("modelLaunched"), bool):
        raise Stop(f"{path} has no boolean modelLaunched; cannot tell whether the model ran")
    return record


def never_launched(record: dict) -> bool:
    return record.get("status") == "isolation-stop" and record.get("modelLaunched") is False


def preserve_attempt(work_root: Path, rdir: Path) -> Path:
    base = work_root / "attempts" / rdir.name
    base.mkdir(parents=True, exist_ok=True)
    n = 1
    while (base / f"attempt-{n}").exists():
        n += 1
    dest = base / f"attempt-{n}"
    rdir.rename(dest)
    return dest


def spent_by_existing(work_root: Path, runs: list[dict]) -> int:
    spent = 0
    for run in runs:
        rdir = work_root / run["runId"]
        if not rdir.exists():
            continue
        record = read_record(rdir)
        if never_launched(record):
            continue
        if not isinstance(record.get("totalTokens"), int):
            raise Stop(f"{run['runId']} has no totalTokens; record its usage before resuming")
        spent += record["totalTokens"]
    return spent


def acquire_lock(work_root: Path) -> Path:
    work_root.mkdir(parents=True, exist_ok=True)
    lock = work_root / LOCK_NAME
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise Stop(f"lock exists: {lock} (another batch may be running; remove it only after confirming none is)")
    with os.fdopen(fd, "w") as fh:
        fh.write(json.dumps({"pid": os.getpid(), "startedAt": now()}))
    return lock


def write_record(rdir: Path, record: dict) -> None:
    (rdir / "run.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def will_grade(args) -> bool:
    return not args.dry_run or args.dry_run_grade


def run_one(args, run: dict, cand: dict, work_root: Path, prompt: str, evidence: dict) -> dict:
    rdir = work_root / run["runId"]
    rdir.mkdir(mode=0o700)
    session_id = str(uuid.uuid4())
    settings_path = rdir / "settings.json"
    settings_path.write_text(json.dumps(settings(cand), indent=2) + "\n", encoding="utf-8")
    cmd = claude_command(args.claude_bin, run["model"], settings_path, session_id)
    record = {"runId": run["runId"], "arm": run["arm"], "order": cand["order"], "condition": "T0",
              "repo": cand["repo"], "revision": cand["revision"], "dryRun": args.dry_run,
              "declared": {"runtime": RUNTIME_VERSION, "model": run["model"], "effort": EFFORT},
              "limits": {"timeoutS": args.timeout_s, "maxRunTokens": args.max_run_tokens,
                         "budgetTokens": args.budget_tokens, "autoContinue": 0},
              "promptSha256": sha256_bytes(prompt.encode("utf-8")),
              "settingsSha256": sha256_bytes(settings_path.read_bytes()), "sessionId": session_id,
              "command": cmd, "preflight": evidence, "notTested": list(NOT_TESTED),
              "status": "started", "modelLaunched": False, "startedAt": now()}
    write_record(rdir, record)
    ws = rdir / "workspace"
    try:
        if will_grade(args):
            fx.prepare(cand, ws, args.cache)
        else:
            ws.mkdir()
    except (subprocess.CalledProcessError, OSError, SystemExit) as exc:
        record.update(status="isolation-stop", stopReason=f"workspace preparation failed: {exc}")
        write_record(rdir, record)
        raise Stop(f"{run['runId']}: workspace preparation failed: {exc}")
    (rdir / "prompt.md").write_text(prompt, encoding="utf-8")
    env = child_env()
    launched = cmd
    if args.dry_run:
        launched = [sys.executable, str(Path(__file__).resolve()), "_fake_claude"]
        env.update(MRS_FAKE_MODEL=args.dry_run_model or run["model"], MRS_FAKE_EFFORT=args.dry_run_effort,
                   MRS_FAKE_TOKENS=str(args.dry_run_tokens), MRS_FAKE_SCENARIO=args.dry_run_scenario)
    record["launchedCommand"] = launched
    record["modelLaunched"] = True  # simulated in dry-run
    write_record(rdir, record)
    monitor = Monitor(run["model"], args.max_run_tokens)
    started = time.monotonic()
    try:
        stop_status, reason, rc = launch(launched, ws, env, prompt, rdir / "stream.jsonl", rdir / "stderr.log",
                                         monitor, args.timeout_s)
    except OSError as exc:
        record.update(status="runtime-error", stopReason=f"launch failed: {exc}", modelLaunched=False)
        write_record(rdir, record)
        raise Stop(f"{run['runId']}: launch failed: {exc}")
    record["wallClockMs"] = int((time.monotonic() - started) * 1000)
    record["exitCode"] = rc
    trace = read_stream(rdir / "stream.jsonl")
    record["trace"] = trace
    record["totalTokens"] = trace["totalTokens"]
    record["runningTotalTokens"] = sum(monitor.usage_by_message.values())
    if stop_status:
        record.update(status=stop_status, stopReason=reason)
    elif rc != 0 or not trace["complete"] or trace["resultIsError"]:
        record.update(status="runtime-error", stopReason=f"exit {rc}, problems {trace['problems']}")
    elif not will_grade(args):
        record["status"] = "dry-run-ungraded"
    else:
        record["status"] = "completed"
        try:
            record["grade"] = fx.verify(cand, ws, args.cache, args.ac_python)
        except (subprocess.CalledProcessError, OSError, SystemExit) as exc:
            record.update(status="grading-error", stopReason=str(exc))
    record["finishedAt"] = now()
    write_record(rdir, record)
    return record


def cmd_run(args) -> int:
    cand = load_pilot()
    runs = plan()
    evidence = preflight(args, runs)
    prompt = fx.load_task(cand["order"])["statement"]
    print(f"prompt order-{cand['order']:02d} statement sha256 {sha256_bytes(prompt.encode('utf-8'))}")
    work_root = Path(args.work_root).resolve()
    lock = acquire_lock(work_root)
    try:
        spent = spent_by_existing(work_root, runs)
        if spent:
            print(f"existing runs already used {spent} tokens (counted against --budget-tokens)")
        for run in runs:
            rdir = work_root / run["runId"]
            if rdir.exists():
                if not never_launched(read_record(rdir)):
                    print(f"skip existing {run['runId']}")
                    continue
                print(f"retry {run['runId']}: model was never launched; previous attempt kept at "
                      f"{preserve_attempt(work_root, rdir)}")
            if spent + args.max_run_tokens > args.budget_tokens:
                raise Stop(f"budget: spent {spent} + max per run {args.max_run_tokens} > {args.budget_tokens}")
            record = run_one(args, run, cand, work_root, prompt, evidence)
            if record["modelLaunched"] and not isinstance(record["totalTokens"], int):
                raise Stop(f"{run['runId']}: {record['status']} without a result usage (running total "
                           f"{record['runningTotalTokens']}); record totalTokens before resuming "
                           f"({record.get('stopReason')})")
            spent += record["totalTokens"] or 0
            print(f"{run['runId']}: {record['status']} tokens={record['totalTokens']} "
                  f"success={(record.get('grade') or {}).get('verifiedSuccess')}")
            if record["status"] not in ("completed", "dry-run-ungraded"):
                raise Stop(f"{run['runId']}: {record['status']}: {record.get('stopReason')}")
    except Stop as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2
    finally:
        lock.unlink()
    return 0


# ---------------------------------------------------------------- summary

def pilot_checks(rec: dict) -> dict:
    """Runbook step 12 items for one Run: PASS / FAIL / NOT_TESTED."""
    t = rec.get("trace") or {}
    model = rec["declared"]["model"]

    def pf(ok):
        return "PASS" if ok else "FAIL"

    usage = t.get("usage") or {}
    return {
        "activationModel": pf(t.get("initModel") == model and t.get("respondingModels") == [model]),
        "activationEffort": ("NOT_TESTED" if not t.get("effortValues")
                             else pf(t.get("effortValues") == [EFFORT])),
        "traceComplete": pf(bool(t.get("complete"))),
        "toolCallsRecorded": pf(t.get("toolCalls") is not None and t.get("toolCalls") == t.get("toolResults")),
        "tokens": pf(isinstance(rec.get("totalTokens"), int)),
        "cache": pf("cache_read_input_tokens" in usage and "cache_creation_input_tokens" in usage),
        "elapsed": pf(isinstance(rec.get("wallClockMs"), int)),
    }


def summarize(work_root: Path) -> dict:
    records = [read_record(p.parent) for p in sorted(work_root.glob("MRS-P*/run.json"))]
    rows = []
    for rec in records:
        checks = pilot_checks(rec)
        tokens = rec.get("totalTokens")
        rows.append({"runId": rec["runId"], "arm": rec["arm"], "model": rec["declared"]["model"],
                     "status": rec["status"], "modelLaunched": rec["modelLaunched"], "totalTokens": tokens,
                     "m": tokens / T0_TOKENS_EXP001 if isinstance(tokens, int) else None,
                     "wallClockMs": rec.get("wallClockMs"), "modelUsage": (rec.get("trace") or {}).get("modelUsage"),
                     "auxiliaryModels": sorted(set((rec.get("trace") or {}).get("modelUsage") or {})
                                               - {rec["declared"]["model"]}),
                     "verifiedSuccess": (rec.get("grade") or {}).get("verifiedSuccess"), "checks": checks})
    values = [v for r in rows for v in r["checks"].values()]
    complete = len(rows) == len(ARMS) and all(r["status"] in ("completed", "dry-run-ungraded") for r in rows)
    if any(r.get("dryRun") for r in records):
        judgment = "DRY_RUN"
    elif not complete or "FAIL" in values:
        judgment = "FAIL"
    elif "NOT_TESTED" in values:
        judgment = "NOT_TESTED"
    else:
        judgment = "PASS"
    tokens = [r["totalTokens"] for r in rows if r["modelLaunched"] and isinstance(r["totalTokens"], int)]
    mean = sum(tokens) / len(tokens) if tokens else None
    return {
        "runsFound": len(rows), "runsExpected": len(ARMS), "dryRun": any(r.get("dryRun") for r in records),
        "proposedPilotJudgment": judgment,
        "note": "proposal for runbook step 12; verifiedSuccess is not used for effect estimation",
        "totalTokensSpent": sum(tokens), "meanTotalTokens": mean, "t0TokensExp001": T0_TOKENS_EXP001,
        "m": None if mean is None else mean / T0_TOKENS_EXP001,
        "mainRunEstimateTokens": None if mean is None else 180 * mean,
        "runs": rows,
    }


def cmd_summarize(args) -> int:
    text = json.dumps(summarize(Path(args.work_root).resolve()), ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        out = Path(args.output)
        if out.exists():
            print(f"STOP: {out} exists (refusing to overwrite)", file=sys.stderr)
            return 2
        out.write_text(text + "\n", encoding="utf-8")
    return 0


def cmd_plan(_args) -> int:
    cand = load_pilot()
    for run in plan():
        print(f"{run['runId']}\tarm {run['arm']}\t{run['model']}\t--effort {EFFORT}\t{cand['repo']}@{cand['revision']}")
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan").set_defaults(func=cmd_plan)
    r = sub.add_parser("run")
    r.add_argument("--work-root", required=True, help="results directory outside the DAT repo")
    r.add_argument("--timeout-s", type=int, required=True, help="per-Run wall clock hard limit (no default)")
    r.add_argument("--max-run-tokens", type=int, required=True,
                   help="per-Run token limit, checked on every assistant message (no default)")
    r.add_argument("--budget-tokens", type=int, required=True, help="approved pilot budget (no default)")
    r.add_argument("--acknowledge-not-tested", help=f"comma list; must be exactly: {','.join(NOT_TESTED)}")
    r.add_argument("--cache", default=str(Path(tempfile.gettempdir()) / "mrs-cache"),
                   help="git cache for the fixture (outside the work root)")
    r.add_argument("--claude-bin", default="claude")
    r.add_argument("--ac-python", default="python3.12")
    r.add_argument("--skip-existing", action="store_true",
                   help="leave existing Run directories untouched, skip them, and count their tokens against the budget")
    r.add_argument("--skip-blob-check", action="store_true", help=argparse.SUPPRESS)
    r.add_argument("--dry-run", action="store_true", help="never launch claude; a synthetic stream stands in for it")
    r.add_argument("--dry-run-grade", action="store_true", help="dry-run: also prepare and grade the workspace")
    r.add_argument("--dry-run-model", help="dry-run: responding model (default: the arm's model)")
    r.add_argument("--dry-run-effort", default="", help="dry-run: effort value placed in the init event")
    r.add_argument("--dry-run-tokens", type=int, default=68022)
    r.add_argument("--dry-run-scenario", default="ok", choices=["ok", "credential", "missing-result", "sleep"],
                   help=argparse.SUPPRESS)
    r.set_defaults(func=cmd_run)
    s = sub.add_parser("summarize")
    s.add_argument("--work-root", required=True)
    s.add_argument("--output")
    s.set_defaults(func=cmd_summarize)
    return p


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["_fake_claude"]:
        return fake_claude()
    args = parser().parse_args(argv)
    try:
        return args.func(args)
    except Stop as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
