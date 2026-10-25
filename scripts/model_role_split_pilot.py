#!/usr/bin/env python3
"""Pilot kit for the #220 model role split comparison (runbook steps 11-12, preregistration §6 / §8).

Subcommands:
  plan       print the 2 pilot Runs (order 2, arm A then arm B)
  run        execute them sequentially with Claude Code CLI 2.1.310, --effort high; --dry-run never launches a model
  summarize  per-Run activation / trace completeness / token checks, m vs EXP-001 T0, and a proposed pilot judgment

Each real Run executes the Linux Claude Code binary in its own Docker container (the #244 / EXP-001 run-kit-g
constraints: pinned image digest, cap-drop ALL, read-only rootfs, no-new-privileges, the EXP-001 seccomp profile,
uid:gid, tmpfs, exact mount check). The container sits on an internal Docker network whose only exit is an allowlist
CONNECT proxy container (api.anthropic.com:443). Every isolation gate (mounts, version, binary hash, sandbox posture,
egress probes, credential probe) is checked before the model starts; any gate that fails or cannot be confirmed
stops the Run with modelLaunched false. Grading reuses the fixture's verify (network denied by sandbox-exec).
The Operator launches `run` without --dry-run; agents use --dry-run only.
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
import select
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    import model_role_split_fixture as fx  # noqa: E402
except ImportError:  # the proxy container mounts this file alone and only runs `_proxy`
    fx = None

PREREGISTRATION = ROOT / "docs/MODEL_ROLE_SPLIT_PREREGISTRATION.md"
PREREGISTRATION_BLOB = "5e7576393641dcdd0d70f60a1282fe3ff497172a"
# EXP-001 seccomp profile (allows bwrap user namespaces); read, not modified.
SECCOMP = ROOT / "experiments/EXP-001-t0-vs-t1/pilot/retry-t1-r01/codex-bwrap-seccomp.json"
SECCOMP_SHA256 = "085e468fa8e70d8c839a9abab4d74a1ab2abad74a8c26f15234ba62a8ac2e1e8"
RUNTIME_VERSION = "2.1.310"
# npm @anthropic-ai/claude-code-linux-arm64@2.1.310 (shasum a4422178456dd0bc485451c99609cf1e629e4ee7), file `claude`.
CLAUDE_LINUX_SHA256 = "9c64d9a7442436b65fcd7cc02c1aa0051bb5a7041e7788576ed3b5f29c447d54"
ARMS = (("A", "claude-opus-5-5"), ("B", "claude-sonnet-5-5"))
EFFORT = "high"
PILOT_ORDER = 2
T0_TOKENS_EXP001 = 68022.0
LOCK_NAME = ".pilot.lock"
TOOLS = ("Bash", "Read", "Edit", "Write", "Glob", "Grep")
PERMISSION_MODE = "dontAsk"
CONFIG_DIR = "/cc-home"
CREDENTIALS = f"{CONFIG_DIR}/.credentials.json"
TMPFS_ALLOWED = ("/tmp", CONFIG_DIR)
API_HOST, API_PORT, PROXY_PORT = "api.anthropic.com", 443, 3128
# Host variables that would open an API-key / third-party billing path (U4-1) or override the Effort.
FORBIDDEN_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_BASE_URL",
                 "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
                 "CLAUDE_CODE_EFFORT_LEVEL", "ANTHROPIC_MODEL")
# Early anomaly detection on tool inputs (not a security boundary: a script written by Write and run later is not seen).
CREDENTIAL_PATTERN = re.compile(r"\.claude|cc-home|keychain|(^|[;&|(]\s*)security\s|credential|auth\.json|printenv|"
                                r"(^|[;&|(]\s*)env\b|/proc/|environ|anthropic_|oauth|\.ssh|\.netrc|\.config/gh", re.I)
NETWORK_PATTERN = re.compile(r"(^|[;&|(]\s*)(curl|wget|nc|ncat|ssh|scp|rsync|telnet|ftp)\b|"
                             r"git\s+(push|fetch|pull|clone|remote)|pip\d*(\.\d+)?\s+install|https?://", re.I)
# Credential-shaped strings; a hit quarantines the Run directory.
SECRET_PATTERN = re.compile(rb"sk-ant-[A-Za-z0-9_\-]{16,}|\"(accessToken|refreshToken)\"\s*:|"
                            rb"Bearer\s+[A-Za-z0-9._\-]{20,}|CLAUDE_CODE_OAUTH_TOKEN=\S+")


class Stop(Exception):
    """Stop the batch; the message is the reason recorded for the Operator."""


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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
    """User settings in the Run's fresh CLAUDE_CONFIG_DIR; identical for both arms."""
    return {
        "permissions": {
            "defaultMode": PERMISSION_MODE,
            "allow": ["Read(/work/**)", "Glob(/work/**)", "Grep(/work/**)", "Edit(/work/**)", "Write(/work/**)",
                      *bash_allow(cand)],
            "deny": [f"Read({CONFIG_DIR}/**)", "Read(/proc/**)", "WebFetch", "WebSearch"],
        },
        "sandbox": {"enabled": True, "allowUnsandboxedCommands": False, "autoAllowBashIfSandboxed": False,
                    "network": {"allowedDomains": []}, "filesystem": {"denyRead": [CONFIG_DIR]}},
    }


def claude_args(model: str, session_id: str) -> list[str]:
    return ["-p", "--output-format", "stream-json", "--verbose", "--model", model, "--effort", EFFORT,
            "--setting-sources", "user", "--strict-mcp-config", "--disable-slash-commands",
            "--tools", ",".join(TOOLS), "--permission-mode", PERMISSION_MODE, "--permission-prompts", "none",
            "--no-session-persistence", "--session-id", session_id]


def container_env(proxy: str) -> dict:
    return {"HOME": "/tmp/home", "CLAUDE_CONFIG_DIR": CONFIG_DIR, "HTTPS_PROXY": f"http://{proxy}:{PROXY_PORT}",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "PYTHONDONTWRITEBYTECODE": "1"}


# ---------------------------------------------------------------- stream checks (early anomaly detection)

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
    """Credential / network reference in a Bash command or a tool path (Edit / Write content is not scanned)."""
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
            return f"{label} reference in {name}: {text[:200]}"
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


# ---------------------------------------------------------------- secrets in saved artifacts

def scan_secrets(rdir: Path) -> list[str]:
    """Files under the Run directory holding credential-shaped strings (relative paths only, never the match)."""
    hits = []
    for path in sorted(rdir.rglob("*")):
        if path.is_file() and not path.is_symlink() and ".git" not in path.relative_to(rdir).parts:
            if SECRET_PATTERN.search(path.read_bytes()):
                hits.append(path.relative_to(rdir).as_posix())
    return hits


def quarantine(work_root: Path, rdir: Path) -> Path:
    base = work_root / "quarantine"
    base.mkdir(mode=0o700, exist_ok=True)
    dest = base / f"{rdir.name}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    rdir.rename(dest)
    os.chmod(dest, 0o700)
    return dest


# ---------------------------------------------------------------- container isolation (real Runs)

def bind_sources(args, rdir: Path) -> dict[str, tuple[str, bool]]:
    """The only host paths a Run's container may see: container path -> (realpath of host path, writable)."""
    return {"/work": (os.path.realpath(rdir / "workspace"), True),
            "/run-input": (os.path.realpath(rdir / "input"), False),
            "/cc": (os.path.realpath(args.claude_dir) if args.claude_dir else "<claude-dir>", False),
            CREDENTIALS: (os.path.realpath(Path(args.credentials_file).expanduser())
                          if args.credentials_file else "<credentials-file>", False)}


def expected_mounts(args, rdir: Path) -> list[tuple[str, str, str, bool]]:
    return sorted(("bind", src, dest, rw) for dest, (src, rw) in bind_sources(args, rdir).items())


def docker_run_command(args, rdir: Path, name: str, network: str) -> list[str]:
    uid, gid = os.getuid(), os.getgid()
    cmd = ["docker", "run", "--rm", "-d", "--name", name, "--platform", "linux/arm64", "--network", network,
           "--security-opt", f"seccomp={SECCOMP}", "--security-opt", "no-new-privileges", "--cap-drop", "ALL",
           "--user", f"{uid}:{gid}", "--read-only", "--tmpfs", "/tmp",
           "--tmpfs", f"{CONFIG_DIR}:uid={uid},gid={gid},mode=700"]
    for target, (source, rw) in bind_sources(args, rdir).items():
        cmd += ["-v", f"{source}:{target}" + ("" if rw else ":ro")]
    return cmd + ["-w", "/work", args.image, "sleep", "infinity"]


def proxy_run_command(args, name: str, network: str) -> list[str]:
    script = os.path.realpath(__file__)
    return ["docker", "run", "--rm", "-d", "--name", name, "--platform", "linux/arm64", "--network", network,
            "--security-opt", "no-new-privileges", "--cap-drop", "ALL", "--user", f"{os.getuid()}:{os.getgid()}",
            "--read-only", "--tmpfs", "/tmp", "-v", f"{script}:/proxy/kit.py:ro", args.image,
            "python3", "-I", "/proxy/kit.py", "_proxy"]


def check_container(inspect: dict, expected: list[tuple[str, str, str, bool]], work_root: Path,
                    network: str) -> dict:
    """Stop unless every mount, the tmpfs set, the network, and the EXP-001 constraints match exactly."""
    host = inspect.get("HostConfig", {})
    binds, tmpfs = [], []
    for m in inspect.get("Mounts", []):
        kind = m.get("Type")
        if kind == "bind":
            binds.append(("bind", os.path.realpath(m.get("Source", "")), m.get("Destination"), bool(m.get("RW"))))
        elif kind == "tmpfs":
            tmpfs.append(m.get("Destination"))
        else:
            raise Stop(f"mount of unexpected type {kind!r} at {m.get('Destination')}")
    if sorted(binds) != sorted(expected):
        raise Stop(f"mounts {sorted(binds)} != expected {sorted(expected)}")
    if tmpfs and sorted(tmpfs) != sorted(TMPFS_ALLOWED):
        raise Stop(f"tmpfs in Mounts {tmpfs} is not exactly {TMPFS_ALLOWED}")
    host_tmpfs = sorted((host.get("Tmpfs") or {}).keys())
    if host_tmpfs != sorted(TMPFS_ALLOWED):
        raise Stop(f"HostConfig.Tmpfs {host_tmpfs} is not exactly {TMPFS_ALLOWED}")
    if host.get("NetworkMode") != network:
        raise Stop(f"NetworkMode {host.get('NetworkMode')!r} != {network!r}")
    rdir = Path(next(src for _, src, dest, _ in expected if dest == "/work")).parent
    for _, src, _, _ in expected:
        p = Path(src)
        if p == work_root or (work_root in p.parents and rdir != p and rdir not in p.parents):
            raise Stop(f"bind {src} exposes another Run under the work root")
    if host.get("Privileged") or host.get("CapAdd") or host.get("CapDrop") != ["ALL"] or not host.get("ReadonlyRootfs"):
        raise Stop("container constraints differ from EXP-001 (privileged / caps / read-only rootfs)")
    opts = host.get("SecurityOpt") or []
    seccomp = [o.split("=", 1)[1] for o in opts if o.startswith("seccomp=")]
    if "no-new-privileges" not in opts or len(seccomp) != 1 or any("unconfined" in o for o in opts):
        raise Stop(f"container security options differ from EXP-001: {[o[:40] for o in opts]}")
    try:
        matches = json.loads(seccomp[0]) == json.loads(SECCOMP.read_text(encoding="utf-8"))
    except ValueError:
        matches = False
    evidence = {"mounts": [list(b) for b in sorted(binds)], "hostTmpfs": host_tmpfs, "network": network,
                "seccompLaunchedSha256": sha256_file(SECCOMP),
                "seccompInspectSha256": hashlib.sha256(seccomp[0].encode()).hexdigest(),
                "seccompMatchesLaunchedProfile": matches}
    if not matches:
        raise Stop(f"inspected seccomp profile does not match the launched profile: {evidence}")
    return evidence


def check_network(inspect: dict) -> None:
    if inspect.get("Internal") is not True:
        raise Stop(f"network {inspect.get('Name')!r} is not internal (it would have a route outside)")


def check_sandbox_status(output: str) -> dict:
    """`claude sandbox status` (model-free): the settings file is the source and the Linux sandbox can run."""
    try:
        status = json.loads(output.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise Stop(f"sandbox status is not JSON: {output[:200]!r}")
    want = {"enabled": True, "enabledSource": "settings", "unavailableReason": None, "strictMode": True,
            "filesystemPolicy": "strict", "autoAllowBashIfSandboxed": False}
    bad = {k: status.get(k) for k, v in want.items() if status.get(k, "<missing>") != v}
    if bad:
        raise Stop(f"sandbox status differs from the required posture: {bad}")
    return {k: status[k] for k in want}


# Run inside the Run container as its uid. Each line is a separate finding; anything unexpected is UNKNOWN.
EGRESS_PROBE = """import errno, socket, sys
def tcp(host, port):
    s = socket.socket(); s.settimeout(10)
    try:
        s.connect((host, port)); s.close(); return "CONNECTED"
    except OSError as exc:
        return "ERRNO " + str(errno.errorcode.get(exc.errno, exc.errno))
def connect_via_proxy(proxy, target):
    s = socket.create_connection((proxy, %d), timeout=10)
    s.sendall(("CONNECT %%s HTTP/1.1\\r\\nHost: %%s\\r\\n\\r\\n" %% (target, target)).encode())
    line = s.recv(64).split(b"\\r\\n")[0].decode(); s.close(); return line
print("PROBE_STARTED")
l = socket.socket(); l.bind(("127.0.0.1", 0)); l.listen(1)
print("LOOPBACK", tcp("127.0.0.1", l.getsockname()[1]))
print("DIRECT", tcp("1.1.1.1", 443))
print("PROXY_DENY", connect_via_proxy(sys.argv[1], "example.com:443"))
print("PROXY_ALLOW", connect_via_proxy(sys.argv[1], "%s:%d"))
""" % (PROXY_PORT, API_HOST, API_PORT)


def check_egress(rc: int, output: str) -> dict:
    """Loopback control connects; a direct external IP is unreachable; the proxy refuses other hosts and opens the API."""
    found = dict(ln.split(" ", 1) for ln in output.splitlines() if " " in ln)
    if "PROBE_STARTED" not in output.splitlines():
        raise Stop("egress probe did not start in the Run container")
    expected = {"LOOPBACK": lambda v: v == "CONNECTED",
                "DIRECT": lambda v: v in ("ERRNO ENETUNREACH", "ERRNO EHOSTUNREACH"),
                "PROXY_DENY": lambda v: v.split()[1:2] == ["403"],
                "PROXY_ALLOW": lambda v: v.split()[1:2] == ["200"]}
    bad = {k: found.get(k) for k, ok in expected.items() if k not in found or not ok(found[k])}
    if bad or rc != 0:
        raise Stop(f"egress not confirmed (exit {rc}): {bad}")
    return {k: found[k] for k in expected}


# Same shape as the #244 auth probe. Claude Code 2.1.310 has no model-free way to run a command inside its Bash
# sandbox (`claude sandbox` only prints status), so the probe runs as the Run's uid outside that sandbox: the worst
# case if the sandbox fails open. The credential file must not be readable there.
AUTH_PROBE = f"""set -u
echo PROBE_STARTED
command -v cat >/dev/null || {{ echo "UNKNOWN: cat missing"; exit 4; }}
if err=$(cat {CREDENTIALS} 2>&1 >/dev/null); then echo "BLOCK: worker uid can read the credential file"; exit 3; fi
case $err in *"Permission denied"*|*"No such file or directory"*) echo AUTH_DENIED ;; *) echo "UNKNOWN: unexpected error class"; exit 4 ;; esac
"""


def check_auth_probe(rc: int, output: str) -> None:
    lines = output.splitlines()
    if "PROBE_STARTED" not in lines:
        raise Stop("credential probe did not start in the Run container")
    if "AUTH_DENIED" not in lines:
        raise Stop(f"credential probe did not report AUTH_DENIED: {[ln for ln in lines if ln != 'PROBE_STARTED'][:3]}")
    if rc != 0:
        raise Stop(f"credential probe exited {rc}")


def docker(*args: str, stdin: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], input=stdin, capture_output=True, text=True, check=check)


def preflight_container(args) -> dict:
    if shutil.which("docker") is None:
        raise Stop("docker not found: cannot isolate Runs")
    if docker("info", "--format", "{{.ServerVersion}}", check=False).returncode != 0:
        raise Stop("docker daemon not reachable: cannot isolate Runs")
    if not args.image or "@sha256:" not in args.image:
        raise Stop("--image must be pinned by digest (name@sha256:...)")
    if docker("image", "inspect", args.image, check=False).returncode != 0:
        raise Stop(f"image {args.image} not present (build or pull it before the batch)")
    if sha256_file(SECCOMP) != SECCOMP_SHA256:
        raise Stop("seccomp profile SHA-256 mismatch")
    binary = Path(args.claude_dir or "") / "claude"
    if not args.claude_dir or not binary.is_file():
        raise Stop("--claude-dir must contain the Linux `claude` binary")
    digest = sha256_file(binary)
    if digest != CLAUDE_LINUX_SHA256:
        raise Stop(f"claude binary SHA-256 {digest} != {CLAUDE_LINUX_SHA256}")
    cred = Path(args.credentials_file or "").expanduser()
    if not args.credentials_file or not cred.is_file() or cred.stat().st_size == 0:
        raise Stop(f"credentials file missing or empty: {args.credentials_file}")
    return {"image": args.image, "claudeSha256": digest}


def isolate_and_check(args, rdir: Path, names: dict, evidence: dict, cand: dict) -> None:
    """Create the network, proxy, and Run container, then every gate; fills `evidence` as gates pass."""
    docker("network", "create", "--internal", names["network"])
    names["networkCreated"] = True
    check_network(json.loads(docker("network", "inspect", names["network"]).stdout)[0])
    docker(*proxy_run_command(args, names["proxy"], names["network"])[1:])
    names["proxyStarted"] = True
    docker("network", "connect", "bridge", names["proxy"])
    docker(*docker_run_command(args, rdir, names["container"], names["network"])[1:])
    names["containerStarted"] = True
    inspect = json.loads(docker("inspect", names["container"]).stdout)[0]
    evidence.update(check_container(inspect, expected_mounts(args, rdir), Path(args.work_root).resolve(),
                                    names["network"]))
    docker("exec", "-i", names["container"], "sh", "-c", f'mkdir -p /tmp/home && cat > "{CONFIG_DIR}/settings.json"',
           stdin=json.dumps(settings(cand), indent=2))
    version = docker("exec", names["container"], "/cc/claude", "--version").stdout.strip()
    evidence["claudeVersion"] = version
    if version.split()[:1] != [RUNTIME_VERSION]:
        raise Stop(f"container claude --version {version!r} is not {RUNTIME_VERSION}")
    status = docker("exec", "-e", f"CLAUDE_CONFIG_DIR={CONFIG_DIR}", "-e", "HOME=/tmp/home", names["container"],
                    "/cc/claude", "sandbox", "status", check=False)
    evidence["sandboxStatus"] = check_sandbox_status(status.stdout)
    egress = docker("exec", names["container"], "python3", "-I", "-c", EGRESS_PROBE, names["proxy"], check=False)
    evidence["egress"] = check_egress(egress.returncode, egress.stdout)
    probe = docker("exec", names["container"], "bash", "-c", AUTH_PROBE, check=False)
    evidence["authProbe"] = {"exitCode": probe.returncode, "lines": probe.stdout.splitlines()[:3]}
    check_auth_probe(probe.returncode, probe.stdout)


def teardown(names: dict) -> None:
    for key, cmd in (("containerStarted", ["stop", "-t", "5", names["container"]]),
                     ("proxyStarted", ["stop", "-t", "5", names["proxy"]]),
                     ("networkCreated", ["network", "rm", names["network"]])):
        if names.get(key):
            docker(*cmd, check=False)


def proxy_main() -> int:
    """Allowlist CONNECT proxy (runs in its own container): only api.anthropic.com:443, every request logged."""
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PROXY_PORT))
    srv.listen(16)

    def pipe(a: socket.socket, b: socket.socket) -> None:
        try:
            while True:
                r, _, _ = select.select([a, b], [], [], 300)
                if not r:
                    return
                for s in r:
                    data = s.recv(65536)
                    if not data:
                        return
                    (b if s is a else a).sendall(data)
        except OSError:
            return
        finally:
            a.close()
            b.close()

    def handle(c: socket.socket) -> None:
        head = b""
        while b"\r\n\r\n" not in head and len(head) < 8192:
            chunk = c.recv(1024)
            if not chunk:
                break
            head += chunk
        parts = head.split(b"\r\n", 1)[0].decode("latin-1").split()
        target = parts[1] if len(parts) >= 2 and parts[0] == "CONNECT" else None
        allowed = target == f"{API_HOST}:{API_PORT}"
        print(json.dumps({"at": now(), "request": parts[:2], "allowed": allowed}), flush=True)
        if not allowed:
            c.sendall(b"HTTP/1.1 403 Forbidden\r\n\r\n")
            c.close()
            return
        try:
            up = socket.create_connection((API_HOST, API_PORT), timeout=30)
        except OSError:
            c.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            c.close()
            return
        c.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        pipe(c, up)

    while True:
        conn, _ = srv.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


# ---------------------------------------------------------------- launching

def launch(cmd: list[str], env: dict | None, prompt: str, stream_path: Path, stderr_path: Path,
           monitor: Monitor, timeout_s: int, kill) -> tuple[str | None, str | None, int | None]:
    """Run one session; returns (stop status, reason, exit code). `kill` stops the session on a stop."""
    with stream_path.open("w", encoding="utf-8") as out, stderr_path.open("w", encoding="utf-8") as err:
        proc = subprocess.Popen(cmd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err, text=True)
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
            kill(proc)
        try:
            rc = proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            rc = proc.wait()
    return (stop[0], stop[1], rc) if stop else (None, None, rc)


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
    command = "cat /cc-home/.credentials.json" if scenario == "credential" else "git status"
    half = tokens // 2
    use = {"input_tokens": 10, "cache_creation_input_tokens": 0, "cache_read_input_tokens": half - 20,
           "output_tokens": 10}
    events = [init,
              {"type": "assistant", "message": {"id": "m1", "model": model, "usage": use, "content": [
                  {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": command}}]}}]
    if scenario != "missing-result":
        text = "Bearer " + "x" * 24 if scenario == "secret" else "ok"
        events.append({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": text}]}})
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
    """Model-free checks before any Run; any failure stops. Returns evidence for run.json."""
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
    evidence.update(preflight_container(args))
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
    if (work_root / "quarantine").exists() and any((work_root / "quarantine").iterdir()):
        raise Stop("quarantined Runs exist; resolve them (and record their usage) before resuming")
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
    tag = f"{run['runId'].lower()}-{os.getpid()}"
    names = {"container": f"mrs-{tag}", "proxy": f"mrs-proxy-{tag}", "network": f"mrs-net-{tag}"}
    exec_cmd = ["docker", "exec", "-i", "-w", "/work",
                *[a for k, v in container_env(names["proxy"]).items() for a in ("-e", f"{k}={v}")],
                names["container"], "/cc/claude", *claude_args(run["model"], session_id)]
    record = {"runId": run["runId"], "arm": run["arm"], "order": cand["order"], "condition": "T0",
              "repo": cand["repo"], "revision": cand["revision"], "dryRun": args.dry_run,
              "declared": {"runtime": RUNTIME_VERSION, "model": run["model"], "effort": EFFORT},
              "limits": {"timeoutS": args.timeout_s, "maxRunTokens": args.max_run_tokens,
                         "budgetTokens": args.budget_tokens, "autoContinue": 0},
              "promptSha256": sha256_bytes(prompt.encode("utf-8")),
              "settingsSha256": sha256_bytes(json.dumps(settings(cand), indent=2).encode("utf-8")),
              "sessionId": session_id, "names": names, "command": exec_cmd, "preflight": evidence,
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
    (rdir / "input").mkdir()
    (rdir / "input" / "prompt.md").write_text(prompt, encoding="utf-8")
    monitor = Monitor(run["model"], args.max_run_tokens)
    try:
        if args.dry_run:
            launched = [sys.executable, str(Path(__file__).resolve()), "_fake_claude"]
            env = {"PATH": os.environ.get("PATH", ""), "MRS_FAKE_MODEL": args.dry_run_model or run["model"],
                   "MRS_FAKE_EFFORT": args.dry_run_effort, "MRS_FAKE_TOKENS": str(args.dry_run_tokens),
                   "MRS_FAKE_SCENARIO": args.dry_run_scenario}

            def kill(proc):
                proc.kill()
        else:
            launched, env = exec_cmd, None
            record["isolation"] = {}
            try:
                isolate_and_check(args, rdir, names, record["isolation"], cand)
            except (Stop, subprocess.CalledProcessError, OSError, ValueError, IndexError) as exc:
                record.update(status="isolation-stop", stopReason=str(exc))
                write_record(rdir, record)
                raise Stop(f"{run['runId']}: isolation-stop (model not launched): {exc}")

            def kill(proc):
                docker("kill", names["container"], check=False)
                proc.kill()
        record["launchedCommand"] = launched
        record["modelLaunched"] = True  # simulated in dry-run
        write_record(rdir, record)
        started = time.monotonic()
        try:
            stop_status, reason, rc = launch(launched, env, prompt, rdir / "stream.jsonl", rdir / "stderr.log",
                                             monitor, args.timeout_s, kill)
        except OSError as exc:
            record.update(status="runtime-error", stopReason=f"launch failed: {exc}", modelLaunched=False)
            write_record(rdir, record)
            raise Stop(f"{run['runId']}: launch failed: {exc}")
        record["wallClockMs"] = int((time.monotonic() - started) * 1000)
        if not args.dry_run:
            (rdir / "proxy.log").write_text(docker("logs", names["proxy"], check=False).stdout, encoding="utf-8")
    finally:
        if not args.dry_run:
            teardown(names)
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
    hits = scan_secrets(rdir)
    if hits:
        record.update(status="secret-quarantined", secretFiles=hits, totalTokens=record["totalTokens"])
        write_record(rdir, record)
        dest = quarantine(work_root, rdir)
        raise Stop(f"{run['runId']}: credential-shaped strings in {hits}; Run moved to {dest} (do not commit or "
                   f"share it; revoke the credential if the string is real)")
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
        tokens = rec.get("totalTokens")
        usage_by_model = (rec.get("trace") or {}).get("modelUsage")
        rows.append({"runId": rec["runId"], "arm": rec["arm"], "model": rec["declared"]["model"],
                     "status": rec["status"], "modelLaunched": rec["modelLaunched"], "totalTokens": tokens,
                     "m": tokens / T0_TOKENS_EXP001 if isinstance(tokens, int) else None,
                     "wallClockMs": rec.get("wallClockMs"), "modelUsage": usage_by_model,
                     "auxiliaryModels": sorted(set(usage_by_model or {}) - {rec["declared"]["model"]}),
                     "verifiedSuccess": (rec.get("grade") or {}).get("verifiedSuccess"),
                     "checks": pilot_checks(rec)})
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
    quarantined = sorted(p.name for p in (work_root / "quarantine").glob("*")) if (work_root / "quarantine").exists() else []
    return {
        "runsFound": len(rows), "runsExpected": len(ARMS), "dryRun": any(r.get("dryRun") for r in records),
        "proposedPilotJudgment": judgment, "quarantined": quarantined,
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
    r.add_argument("--image", help="Run image pinned by digest (python 3.12 + bubblewrap + socat; see the runbook)")
    r.add_argument("--claude-dir", help="directory with the Linux `claude` 2.1.310 binary (mounted read-only at /cc)")
    r.add_argument("--credentials-file", help="Linux Claude Code .credentials.json (mounted read-only; not read)")
    r.add_argument("--cache", default=str(Path(tempfile.gettempdir()) / "mrs-cache"),
                   help="git cache for the fixture (outside the work root)")
    r.add_argument("--ac-python", default="python3.12")
    r.add_argument("--skip-existing", action="store_true",
                   help="leave existing Run directories untouched, skip them, and count their tokens against the budget")
    r.add_argument("--skip-blob-check", action="store_true", help=argparse.SUPPRESS)
    r.add_argument("--dry-run", action="store_true", help="never launch claude or a container; a synthetic stream")
    r.add_argument("--dry-run-grade", action="store_true", help="dry-run: also prepare and grade the workspace")
    r.add_argument("--dry-run-model", help="dry-run: responding model (default: the arm's model)")
    r.add_argument("--dry-run-effort", default="", help="dry-run: effort value placed in the init event")
    r.add_argument("--dry-run-tokens", type=int, default=68022)
    r.add_argument("--dry-run-scenario", default="ok",
                   choices=["ok", "credential", "missing-result", "sleep", "secret"], help=argparse.SUPPRESS)
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
    if argv[:1] == ["_proxy"]:
        return proxy_main()
    args = parser().parse_args(argv)
    try:
        return args.func(args)
    except Stop as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
