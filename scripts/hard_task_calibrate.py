#!/usr/bin/env python3
"""Calibration kit for the hard-task T0/T1 comparison (#244, preregistration §6 / §9 step 6).

Subcommands:
  plan       print the 25 calibration Runs (first 5 initial candidates x n_cal 5)
  run        execute the Runs sequentially (T0, Codex / gpt-6.1-sol / high); --dry-run never launches a model
  summarize  aggregate per-candidate verified successes and m (token ratio vs EXP-001 T0)

Screening (second-edition preregistration §3 / §3.1 and addendum 1; HTS-<order>-n<k> Runs):
  screen-plan       print how each initial candidate 1..44 is handled (reuse / pre-excluded / up to k=3 Runs)
  screen            T0 screening: reuse n1..n3 of orders 1..5, stop a candidate at its first verified success,
                    stop when 12 candidates are 0/3; --dry-run never launches a model
  screen-summarize  per-candidate n1..nk results, truncated / pre-excluded / budget-excluded, selected 0/3

Each real Run executes Codex in its own Docker container that bind-mounts only that Run's workspace, the
prompt, the Codex binary directory, and auth.json (the EXP-001 run-kit-g constraints). The AC runs on the
host under sandbox-exec with network denied. The Operator launches `run` without --dry-run; agents use
--dry-run only.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import datetime as dt
import hashlib
import io
import json
import os
import shlex
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time

import yaml

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "docs/hard-task/CANDIDATES.yaml"
PREREGISTRATION = ROOT / "docs/HARD_TASK_T0_T1_PREREGISTRATION.md"
CANDIDATES_BLOB = "aad6f23629efaefdd266f0e21ca59248e4693c7b"
PREREGISTRATION_BLOB = "52b4a585044e00d52fea8db64f725c4b4f3258cd"
# EXP-001 run-kit-g environment (experiments/EXP-001-t0-vs-t1/pilot/run-kit-g/environment.conf); read, not modified.
SECCOMP = ROOT / "experiments/EXP-001-t0-vs-t1/pilot/retry-t1-r01/codex-bwrap-seccomp.json"
SECCOMP_SHA256 = "085e468fa8e70d8c839a9abab4d74a1ab2abad74a8c26f15234ba62a8ac2e1e8"
IMAGE = "python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258"

RUNTIME_VERSION = "codex-cli 0.160.1"
MODEL = "gpt-6.1-sol"
EFFORT = "high"
CANDIDATE_COUNT = 5
N_CAL = 5
P_MAX_SUCCESSES = 2
C = 44
T0_TOKENS_EXP001 = 68022.0
LOCK_NAME = ".calibration.lock"
TIMEOUT_STEP_S = 30
ABORTED_NONZERO = "aborted-nonzero-exit"
ABORTED_STATUSES = ("aborted-timeout", ABORTED_NONZERO)
CODEX_HOME = "/tmp/codex-home"
# Same profile as EXP-001 config-never.sh: workspace-write equivalent, CODEX_HOME hidden from sandboxed commands.
CONFIG_TOML = f"""model = "{MODEL}"
model_reasoning_effort = "{EFFORT}"
approval_policy = "never"
default_permissions = "t1-workspace"

[permissions.t1-workspace]
description = "workspace-write equivalent; CODEX_HOME (auth.json) hidden from sandboxed commands"
extends = ":workspace"

[permissions.t1-workspace.filesystem]
"{CODEX_HOME}" = "deny"

[projects."/work"]
trust_level = "trusted"
"""


class Stop(Exception):
    """Stop the batch; the message is the reason recorded for the Operator."""


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_candidates(path: Path = CANDIDATES) -> list[dict]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    initial = [c for c in doc["candidates"] if c["set"] == "initial"]
    initial.sort(key=lambda c: c["order"])
    picked = initial[:CANDIDATE_COUNT]
    if [c["order"] for c in picked] != list(range(1, CANDIDATE_COUNT + 1)):
        raise Stop("candidate table does not start with initial orders 1..5")
    return picked


def plan(candidates: list[dict]) -> list[dict]:
    """Rep-major order (n1 of every candidate, then n2, ...) so time drift spreads across candidates."""
    runs = []
    for k in range(1, N_CAL + 1):
        for cand in candidates:
            runs.append({"runId": f"HTC-{cand['order']:02d}-n{k}", "order": cand["order"], "calRep": k, "candidate": cand})
    return runs


def task_file(task_dir: Path, order: int) -> Path:
    return task_dir / f"order-{order:02d}.md"


def load_task_descriptions(task_dir: Path, candidates: list[dict]) -> dict[int, tuple[str, str]]:
    """Per-candidate symptom descriptions, passed verbatim as the T0 prompt. Returns {order: (text, sha256)}.

    Mechanical leak guard only: the fix commit hash and the fix subject must not appear. The review for
    hints about cause or fix location happens in a separate PR before calibration.
    """
    out = {}
    for cand in candidates:
        path = task_file(task_dir, cand["order"])
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            raise Stop(f"missing or empty task description: {path}")
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        if cand["fixCommit"][:7] in lowered or cand["fixSubject"].lower() in lowered:
            raise Stop(f"{path.name} contains the fix commit hash or subject")
        if "{" + "fixSubject" + "}" in text:
            raise Stop(f"{path.name} uses the removed {{fixSubject}} placeholder")
        out[cand["order"]] = (text, sha256_file(path))
    return out


# ---------------------------------------------------------------- AC sandbox (host, network denied)

def ac_sandbox_prefix(grade_dir: Path) -> list[str]:
    """sandbox-exec profile used when the candidate table was built: no network, writes only under grade_dir."""
    profile = ("(version 1)(allow default)(deny network*)(deny file-write*)"
               f'(allow file-write* (subpath "{grade_dir.resolve()}") (subpath "/private/var/folders")'
               ' (subpath "/private/tmp") (literal "/dev/null"))')
    return ["/usr/bin/sandbox-exec", "-p", profile]


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


def probe_ac_sandbox(ac_python: str) -> dict:
    """Controlled check against a local listener: reachable outside the sandbox, EPERM/EACCES inside it.

    Anything else (timeout, refused, other errno, probe crash) is not evidence of sandbox denial and stops.
    """
    if not Path("/usr/bin/sandbox-exec").exists():
        raise Stop("sandbox-exec not found: cannot run the AC with network denied")
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(4)
    port = str(listener.getsockname()[1])
    try:
        with tempfile.TemporaryDirectory() as d:
            control = subprocess.run([ac_python, "-c", NET_PROBE, port], capture_output=True, text=True,
                                     timeout=30, check=False)
            boxed = subprocess.run([*ac_sandbox_prefix(Path(d)), ac_python, "-c", NET_PROBE, port],
                                   capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Stop(f"AC network probe could not run: {exc}")
    finally:
        listener.close()
    result = {"control": control.stdout.strip(), "sandboxed": boxed.stdout.strip()}
    if control.returncode != 0 or result["control"] != "CONNECTED":
        raise Stop(f"AC network probe control could not connect to the local listener: {result}")
    if boxed.returncode != 0 or result["sandboxed"] not in ("ERRNO EPERM", "ERRNO EACCES"):
        raise Stop(f"AC network probe: sandbox denial not confirmed: {result}")
    return result


# ---------------------------------------------------------------- container isolation (real Runs)

TMPFS_ALLOWED = ("/tmp", CODEX_HOME)


def bind_sources(args, rdir: Path) -> dict[str, tuple[str, bool]]:
    """The only host paths a Run's container may see: container path -> (realpath of host path, writable)."""
    return {"/work": (os.path.realpath(rdir / "workspace"), True),
            "/run-input/prompt.md": (os.path.realpath(rdir / "prompt.md"), False),
            "/cx": (os.path.realpath(args.codex_dir) if args.codex_dir else "<codex-dir>", False),
            f"{CODEX_HOME}/auth.json": (os.path.realpath(Path(args.auth_file).expanduser()), False)}


def expected_mounts(args, rdir: Path) -> list[tuple[str, str, str, bool]]:
    return sorted(("bind", src, dest, rw) for dest, (src, rw) in bind_sources(args, rdir).items())


def docker_run_command(args, rdir: Path, name: str) -> list[str]:
    binds = bind_sources(args, rdir)
    uid, gid = os.getuid(), os.getgid()
    cmd = ["docker", "run", "--rm", "-d", "--name", name, "--platform", "linux/arm64",
           "--security-opt", f"seccomp={SECCOMP}", "--security-opt", "no-new-privileges", "--cap-drop", "ALL",
           "--user", f"{uid}:{gid}", "--read-only", "--tmpfs", "/tmp",
           "--tmpfs", f"{CODEX_HOME}:uid={uid},gid={gid},mode=700",
           "-e", "HOME=/tmp/home", "-e", f"CODEX_HOME={CODEX_HOME}"]
    for target, (source, rw) in binds.items():
        cmd += ["-v", f"{source}:{target}" + ("" if rw else ":ro")]
    return cmd + ["-w", "/work", IMAGE, "sleep", "infinity"]


def check_container(inspect: dict, expected: list[tuple[str, str, str, bool]], work_root: Path) -> dict:
    """Stop unless every mount, the tmpfs set, and the EXP-001 constraints match exactly (run-kit-g host-mounts)."""
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
    evidence = {"mounts": [list(b) for b in sorted(binds)], "hostTmpfs": host_tmpfs,
                "seccompLaunchedSha256": sha256_file(SECCOMP),
                "seccompInspectSha256": hashlib.sha256(seccomp[0].encode()).hexdigest(),
                "seccompMatchesLaunchedProfile": matches}
    if not matches:
        raise Stop(f"inspected seccomp profile does not match the launched profile: {evidence}")
    return evidence


def docker(*args: str, stdin: str | None = None, check: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], input=stdin, capture_output=True, text=True, check=check, timeout=timeout)


def preflight_container(args) -> None:
    if shutil.which("docker") is None:
        raise Stop("docker not found: cannot isolate Runs")
    if docker("info", "--format", "{{.ServerVersion}}", check=False).returncode != 0:
        raise Stop("docker daemon not reachable: cannot isolate Runs")
    if docker("image", "inspect", IMAGE, check=False).returncode != 0:
        raise Stop(f"image {IMAGE} not present (pull it before the batch)")
    if sha256_file(SECCOMP) != SECCOMP_SHA256:
        raise Stop("seccomp profile SHA-256 mismatch")
    if not args.codex_dir or not (Path(args.codex_dir) / "bin/codex").is_file():
        raise Stop("--codex-dir must contain bin/codex (Linux build for the container)")
    auth = Path(args.auth_file).expanduser()
    if not auth.is_file() or auth.stat().st_size == 0:
        raise Stop(f"auth file missing or empty: {args.auth_file}")


# Same probe as EXP-001 retry-t1-r01 preflight-d.sh: liveness marker, then a deny result of a known error class.
AUTH_PROBE = f"""set -euo pipefail
echo SANDBOX_ALIVE
command -v cat >/dev/null || {{ echo "UNKNOWN: cat missing"; exit 4; }}
if err=$(cat {CODEX_HOME}/auth.json 2>&1 >/dev/null); then echo "BLOCK: sandbox can read auth file"; exit 3; fi
case $err in *"Permission denied"*|*"No such file or directory"*) echo AUTH_DENIED ;; *) echo "UNKNOWN: unexpected error class"; exit 4 ;; esac
"""


def check_auth_probe(rc: int, output: str) -> None:
    """The probe must have started inside the sandbox, reported the expected deny, and exited 0 — each separately."""
    lines = output.splitlines()
    if "SANDBOX_ALIVE" not in lines:
        raise Stop("auth probe did not run inside the Codex sandbox")
    if "AUTH_DENIED" not in lines:
        raise Stop(f"auth probe did not report AUTH_DENIED: {[ln for ln in lines if ln != 'SANDBOX_ALIVE'][:3]}")
    if rc != 0:
        raise Stop(f"auth probe exited {rc}")


def codex_exec_command(name: str) -> list[str]:
    return ["docker", "exec", "-i", name, "/cx/bin/codex", "exec", "--json", "--skip-git-repo-check",
            "-m", MODEL, "-c", f"model_reasoning_effort={EFFORT}", "-c", "approval_policy=never", "-C", "/work", "-"]


def container_exec_codex(args, rdir: Path, prompt: str, evidence: dict) -> tuple[int | None, dict]:
    """One fresh container per Run; fills `evidence` as checks pass. Returns (exit code or None on timeout, evidence)."""
    name = f"htc-{rdir.name.lower()}-{os.getpid()}"  # same name as recorded in run.json
    evidence["container"] = name
    started = False
    stop_bound = None
    try:
        docker(*docker_run_command(args, rdir, name)[1:])
        started = True
        inspect = json.loads(docker("inspect", name).stdout)[0]
        evidence.update(check_container(inspect, expected_mounts(args, rdir), Path(args.work_root).resolve()))
        if docker("exec", name, "test", "-s", f"{CODEX_HOME}/auth.json", check=False).returncode != 0:
            raise Stop("auth.json is not mounted in the container (missing or empty)")
        docker("exec", "-i", name, "sh", "-c", f'mkdir -p /tmp/home && cat > "{CODEX_HOME}/config.toml"', stdin=CONFIG_TOML)
        version = docker("exec", name, "/cx/bin/codex", "--version").stdout.strip()
        evidence["codexVersion"] = version
        if version != RUNTIME_VERSION:
            raise Stop(f"runtime version {version!r} != {RUNTIME_VERSION!r}")
        probe = docker("exec", name, "/cx/bin/codex", "sandbox", "-P", "t1-workspace", "-C", "/work", "--",
                       "bash", "-c", AUTH_PROBE, check=False)
        evidence["authProbe"] = {"exitCode": probe.returncode, "lines": probe.stdout.splitlines()[:3]}
        check_auth_probe(probe.returncode, probe.stdout)
        cmd = codex_exec_command(name)
        with (rdir / "codex-events.jsonl").open("w", encoding="utf-8") as out, \
                (rdir / "codex-stderr.log").open("w", encoding="utf-8") as err:
            evidence["modelLaunched"] = True
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=out, stderr=err, text=True)
            try:
                proc.communicate(prompt, timeout=args.timeout_s)
                rc = proc.returncode
            except subprocess.TimeoutExpired:
                stop_bound = TIMEOUT_STEP_S
                evidence["timeoutTrace"] = stop_after_timeout(name, proc, rdir)
                return None, evidence
        try:
            collect_sessions(name, rdir)
        except (subprocess.CalledProcessError, tarfile.TarError, OSError) as exc:
            if not screen_abort(args, rc):
                raise
            evidence["collectError"] = type(exc).__name__
        return rc, evidence
    finally:
        if started:
            if stop_bound is None:
                docker("stop", "-t", "5", name, check=False)
            else:
                record_timeout_stop(name, evidence.setdefault("timeoutTrace", {}))


def record_timeout_stop(name: str, trace: dict) -> None:
    """A failed stop must not lose the timeout record; it is kept as evidence and shown to the Operator."""
    trace["stopExitCode"] = None
    try:
        trace["stopExitCode"] = docker("stop", "-t", "5", name, check=False, timeout=TIMEOUT_STEP_S).returncode
    except (subprocess.TimeoutExpired, OSError) as exc:
        trace["stopError"] = type(exc).__name__
    if trace["stopExitCode"] != 0:
        print(f"WARNING: docker stop {name} failed after a timeout (exit {trace['stopExitCode']}, "
              f"{trace.get('stopError')}); confirm the container stopped", file=sys.stderr)


def stop_after_timeout(name: str, proc: subprocess.Popen, rdir: Path) -> dict:
    """End Codex first, then collect the trace (it dies with the tmpfs). Every step is bounded; failures force-kill."""
    result = {"killExitCode": None, "collectedAfterKill": False, "forceKillExitCode": None}
    try:
        result["killExitCode"] = docker("exec", name, "sh", "-c", "kill -s KILL -- -1", check=False,
                                        timeout=TIMEOUT_STEP_S).returncode
    except (subprocess.TimeoutExpired, OSError) as exc:
        result["killError"] = type(exc).__name__
    proc.kill()
    try:
        proc.wait(timeout=TIMEOUT_STEP_S)
    except subprocess.TimeoutExpired:
        result["clientWaitTimedOut"] = True
    if result["killExitCode"] == 0:
        try:
            collect_sessions(name, rdir, timeout=TIMEOUT_STEP_S)
            result["collectedAfterKill"] = True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, tarfile.TarError, OSError) as exc:
            result["collectError"] = type(exc).__name__
    if not result["collectedAfterKill"]:
        try:
            result["forceKillExitCode"] = docker("kill", name, check=False, timeout=TIMEOUT_STEP_S).returncode
        except (subprocess.TimeoutExpired, OSError) as exc:
            result["forceKillError"] = type(exc).__name__
    return result


def collect_sessions(name: str, rdir: Path, timeout: int | None = None) -> None:
    tar = subprocess.run(["docker", "exec", name, "tar", "-C", CODEX_HOME, "-cf", "-", "sessions"],
                         capture_output=True, check=True, timeout=timeout).stdout
    with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
        members = [m for m in tf.getmembers() if m.isfile() and m.name.startswith("sessions/")]
        if any("auth.json" in m.name for m in members):
            raise Stop("auth.json found in collected evidence")
        tf.extractall(rdir, members=members, filter="data")


def timeout_usage_known(rdir: Path, timeout_trace: dict) -> bool:
    """Only a clean kill, a post-kill collection, and a token_count in that trace count; nothing is estimated."""
    if timeout_trace.get("killExitCode") != 0 or timeout_trace.get("collectedAfterKill") is not True:
        return False
    return trace_has_usage(rdir)


def trace_has_usage(rdir: Path) -> bool:
    try:
        return bool(read_trace(find_session(rdir / "sessions"))["totalTokenUsage"])
    except (Stop, ValueError):
        return False


def screen_abort(args, rc: int | None) -> bool:
    """Screening only: a non-zero Codex exit is conservatively treated as an environment abort, never graded."""
    return args.cmd == "screen" and rc not in (0, None)


def fake_codex(args, sessions_dir: Path) -> int:
    """Dry-run stand-in: writes a synthetic session trace. No model is launched."""
    sessions_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        {"type": "session_meta", "payload": {"id": "dry-run", "cwd": "/work", "cli_version": RUNTIME_VERSION.split()[-1]}},
        {"type": "turn_context", "payload": {"model": args.dry_run_model, "effort": args.dry_run_effort, "cwd": "/work"}},
        {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {
            "input_tokens": args.dry_run_tokens, "cached_input_tokens": 0, "output_tokens": 0,
            "total_tokens": args.dry_run_tokens}}}},
    ]
    (sessions_dir / "rollout-dry-run.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
    return 0


# ---------------------------------------------------------------- preflight, workspace, trace

def preflight(args, runs: list[dict]) -> None:
    if not args.skip_blob_check:
        for path, expected in ((CANDIDATES, CANDIDATES_BLOB), (PREREGISTRATION, PREREGISTRATION_BLOB)):
            actual = git_blob_sha(path)
            if actual != expected:
                raise Stop(f"blob mismatch for {path.name}: {actual} != {expected}")
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
    if will_grade(args):
        probe_ac_sandbox(args.ac_python)
    if not args.dry_run:
        preflight_container(args)


def will_grade(args) -> bool:
    return not args.dry_run or args.mirror_dir is not None


def read_record(rdir: Path) -> dict:
    path = rdir / "run.json"
    record = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if not isinstance(record.get("modelLaunched"), bool):
        raise Stop(f"{path} has no boolean modelLaunched; cannot tell whether the model ran")
    if record.get("status") in ABORTED_STATUSES:
        known, has_tokens = record.get("tokenUsageKnown"), isinstance(record.get("totalTokens"), int)
        if not ((known is True and has_tokens) or (known is False and "totalTokens" not in record)):
            raise Stop(f"{path}: tokenUsageKnown {known!r} and totalTokens are inconsistent; not treated as resolved")
    return record


def never_launched(record: dict) -> bool:
    """A Run stopped by the isolation checks before the model started; it is retried, not counted."""
    return record.get("status") == "isolation-stop" and record.get("modelLaunched") is False


def preserve_attempt(work_root: Path, rdir: Path) -> Path:
    """Move a never-launched Run directory to attempts/<runId>/attempt-<N> (never overwrites)."""
    base = work_root / "attempts" / rdir.name
    base.mkdir(parents=True, exist_ok=True)
    n = 1
    while (base / f"attempt-{n}").exists():
        n += 1
    dest = base / f"attempt-{n}"
    rdir.rename(dest)
    return dest


def spent_by_existing(work_root: Path, runs: list[dict]) -> int:
    """Tokens already used by existing Run directories that launched the model; unknown usage cannot be bounded."""
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


def prepare_workspace(cand: dict, ws: Path, mirror_dir: Path | None) -> None:
    source = cand["repo"]
    if mirror_dir is not None:
        source = str(mirror_dir / cand["repo"].rstrip("/").split("/")[-1])
    subprocess.run(["git", "clone", "--quiet", "--no-checkout", source, str(ws)], check=True)
    subprocess.run(["git", "-C", str(ws), "checkout", "--quiet", "--detach", cand["revision"]], check=True)
    subprocess.run(["git", "-C", str(ws), "remote", "remove", "origin"], check=True)
    # Drop history after the revision so the fix commit is not reachable from the workspace.
    subprocess.run(["git", "-C", str(ws), "reflog", "expire", "--expire=now", "--all"], check=True)
    for ref in subprocess.run(["git", "-C", str(ws), "for-each-ref", "--format=%(refname)"],
                              capture_output=True, text=True, check=True).stdout.split():
        subprocess.run(["git", "-C", str(ws), "update-ref", "-d", ref], check=True)
    subprocess.run(["git", "-C", str(ws), "gc", "--quiet", "--prune=now"], check=True)
    reach = subprocess.run(["git", "-C", str(ws), "cat-file", "-e", cand["fixCommit"] + "^{commit}"],
                           capture_output=True, check=False)
    if reach.returncode == 0:
        raise Stop(f"fix commit still present in workspace for {cand['repo']}")


def find_session(sessions_root: Path) -> Path:
    """Each Run has its own CODEX_HOME, so exactly one session trace is expected."""
    hits = sorted(sessions_root.rglob("rollout-*.jsonl"))
    if len(hits) != 1:
        raise Stop(f"expected exactly one session trace under {sessions_root}, found {len(hits)}")
    return hits[0]


def read_trace(path: Path) -> dict:
    meta, contexts, usage = {}, [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        payload = rec.get("payload") or {}
        if rec.get("type") == "session_meta":
            meta = payload
        elif rec.get("type") == "turn_context":
            contexts.append((payload.get("model"), payload.get("effort")))
        elif rec.get("type") == "event_msg" and payload.get("type") == "token_count":
            usage = (payload.get("info") or {}).get("total_token_usage") or usage
    return {"cliVersion": meta.get("cli_version"), "contexts": sorted(set(contexts)), "totalTokenUsage": usage}


def check_trace(trace: dict) -> None:
    if trace["contexts"] != [(MODEL, EFFORT)]:
        raise Stop(f"control deviation: trace model/effort {trace['contexts']} != [({MODEL!r}, {EFFORT!r})]")
    if trace["cliVersion"] != RUNTIME_VERSION.split()[-1]:
        raise Stop(f"control deviation: trace cli_version {trace['cliVersion']!r}")
    if not trace["totalTokenUsage"]:
        raise Stop("trace has no total_token_usage")


# ---------------------------------------------------------------- grading

def test_id(entry: str) -> str:
    return entry.rsplit("(", 1)[1].rstrip(")") if "(" in entry else entry


def load_ac_files(candidates: list[dict], mirror_dir: Path | None) -> dict[int, dict[str, bytes]]:
    """Read the fix commit's AC test files into memory before any Run, so no clone holding them stays on disk."""
    files: dict[int, dict[str, bytes]] = {}
    for cand in candidates:
        name = cand["repo"].rstrip("/").split("/")[-1]
        tmp = None
        if mirror_dir is not None:
            source = mirror_dir / name
        else:
            tmp = Path(tempfile.mkdtemp(prefix="htc-oracle-"))
            source = tmp / f"{name}.git"
            subprocess.run(["git", "clone", "--quiet", "--bare", cand["repo"], str(source)], check=True)
        try:
            files[cand["order"]] = {
                rel: subprocess.run(["git", "-C", str(source), "show", f"{cand['fixCommit']}:{rel}"],
                                    capture_output=True, check=True).stdout
                for rel in cand["acceptanceCriteria"]["testFilesFromFixCommit"]}
        finally:
            if tmp is not None:
                shutil.rmtree(tmp)
    return files


def grade(cand: dict, ws: Path, grade_dir: Path, ac_files: dict[str, bytes], ac_python: str) -> dict:
    """Overlay the fix commit's test files on a copy of the workspace and run the AC with network denied."""
    shutil.copytree(ws, grade_dir, symlinks=True, ignore=shutil.ignore_patterns(".git"))
    for rel, blob in ac_files.items():
        target = grade_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
    sandbox = ac_sandbox_prefix(grade_dir)
    cmd = shlex.split(cand["acceptanceCriteria"]["command"])
    cmd[0] = ac_python
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    ac = subprocess.run([*sandbox, *cmd], cwd=grade_dir, capture_output=True, text=True, env=env, timeout=300, check=False)
    ids = [test_id(t) for t in cand["acceptanceCriteria"]["failingBeforeFix"]]
    oracle = subprocess.run([*sandbox, ac_python, "-m", "unittest", "-v", *ids], cwd=grade_dir, capture_output=True,
                            text=True, env=env, timeout=300, check=False)
    lines = oracle.stderr.splitlines()
    oracle_ok = oracle.returncode == 0 and all(any(f"({t}) ... ok" in ln for ln in lines) for t in ids)
    (grade_dir.parent / "ac-output.txt").write_text(ac.stdout + ac.stderr, encoding="utf-8")
    (grade_dir.parent / "oracle-output.txt").write_text(oracle.stdout + oracle.stderr, encoding="utf-8")
    return {"acExitCode": ac.returncode, "acNetwork": "denied (sandbox-exec)", "negativeOraclePassed": oracle_ok,
            "verifiedSuccess": ac.returncode == 0 and oracle_ok}


# ---------------------------------------------------------------- batch

def run_one(args, run: dict, work_root: Path, prompt: str, prompt_sha: str, ac_files: dict[str, bytes]) -> dict:
    cand = run["candidate"]
    rdir = work_root / run["runId"]
    rdir.mkdir(mode=0o700)
    record = {"runId": run["runId"], "order": run["order"], "calRep": run["calRep"], "condition": "T0",
              "repo": cand["repo"], "revision": cand["revision"], "dryRun": args.dry_run,
              "declared": {"runtime": RUNTIME_VERSION, "model": MODEL, "effort": EFFORT},
              "limits": {"timeoutS": args.timeout_s, "maxRunTokens": args.max_run_tokens},
              "promptSha256": prompt_sha, "status": "started", "modelLaunched": False, "startedAt": now()}
    write_record(rdir, record)
    ws = rdir / "workspace"
    if will_grade(args):
        prepare_workspace(cand, ws, Path(args.mirror_dir) if args.mirror_dir else None)
    else:
        ws.mkdir()
    (rdir / "prompt.md").write_text(prompt, encoding="utf-8")
    if sha256_file(rdir / "prompt.md") != prompt_sha:
        raise Stop(f"{run['runId']}: prompt copy SHA-256 differs from the task description")
    name = f"htc-{run['runId'].lower()}-{os.getpid()}"
    record["containerCommand"] = docker_run_command(args, rdir, name)
    record["command"] = codex_exec_command(name)
    write_record(rdir, record)
    started = time.monotonic()
    if args.dry_run:
        rc = fake_codex(args, rdir / "sessions")
        record["modelLaunched"] = True  # simulated
    else:
        record["isolation"] = {}
        try:
            rc, _ = container_exec_codex(args, rdir, prompt, record["isolation"])
            record["modelLaunched"] = True
        except Stop as exc:
            record["status"] = "isolation-stop"
            record["stopReason"] = str(exc)
            record["modelLaunched"] = bool(record["isolation"].get("modelLaunched"))
            write_record(rdir, record)
            raise
    record["wallClockMs"] = int((time.monotonic() - started) * 1000)
    record["codexExitCode"] = rc
    if rc is None:
        record.update(status="aborted-timeout", modelLaunched=True, finishedAt=now(),
                      stopReason=f"wall clock limit: exceeded --timeout-s {args.timeout_s}")
        timeout_trace = record["isolation"].get("timeoutTrace") or {}
        record["tokenUsageKnown"] = timeout_usage_known(rdir, timeout_trace)
        write_record(rdir, record)
        if not record["tokenUsageKnown"]:
            raise Stop(f"{run['runId']} timed out and its token usage is unknown ({timeout_trace}); confirm the "
                       "container stopped and resolve the usage before resuming")
        record["tokenUsageBasis"] = ("cumulative value observed in the trace collected after the kill; a lower bound "
                                     "that excludes usage not recorded before the stop")
    aborted = screen_abort(args, rc)
    if aborted:
        record.update(status=ABORTED_NONZERO, modelLaunched=True, finishedAt=now(),
                      stopReason=f"codex exit code {rc}: conservatively treated as an environment abort")
        record["tokenUsageKnown"] = trace_has_usage(rdir)
        write_record(rdir, record)
        if not record["tokenUsageKnown"]:
            raise Stop(f"{run['runId']} exited {rc} and its token usage is unknown; confirm the cause and resolve "
                       "the usage before resuming")
        record["tokenUsageBasis"] = "cumulative value observed in the trace; a lower bound if usage went unrecorded"
    session = find_session(rdir / "sessions")
    trace = read_trace(session)
    record["trace"] = {"file": str(session.relative_to(rdir)), "cliVersion": trace["cliVersion"],
                       "contexts": [list(c) for c in trace["contexts"]], "totalTokenUsage": trace["totalTokenUsage"]}
    try:
        check_trace(trace)
    except Stop as exc:
        record["status"] = "control-deviation"
        record["stopReason"] = str(exc)
        write_record(rdir, record)
        raise
    usage = trace["totalTokenUsage"]
    record["totalTokens"] = int(usage["input_tokens"]) + int(usage["output_tokens"])
    if rc is None:
        record["status"] = "aborted-timeout"
    elif aborted:
        record["status"] = ABORTED_NONZERO
    elif not will_grade(args):
        record["status"] = "dry-run-ungraded"
    else:
        record.update(grade(cand, ws, rdir / "grade", ac_files, args.ac_python))
        record["status"] = "completed"
    if record["totalTokens"] > args.max_run_tokens:
        record["tokenLimitExceeded"] = True
    record["finishedAt"] = now()
    write_record(rdir, record)
    if rc is None and timeout_trace.get("stopExitCode") != 0:
        raise Stop(f"{run['runId']} timed out and docker stop failed ({timeout_trace}); confirm the container "
                   "stopped, then resume with --skip-existing")
    if aborted:
        raise Stop(f"{run['runId']} exited {rc}; the candidate is budget-excluded. Confirm the cause, then resume "
                   "with --skip-existing")
    return record


def write_record(rdir: Path, record: dict) -> None:
    (rdir / "run.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_run(args) -> int:
    candidates = load_candidates()
    runs = plan(candidates)
    preflight(args, runs)
    tasks = load_task_descriptions(Path(args.task_dir), candidates)
    for order, (_, sha) in sorted(tasks.items()):
        print(f"task description order-{order:02d}.md sha256 {sha} (must match the hash recorded in #244)")
    work_root = Path(args.work_root).resolve()
    lock = acquire_lock(work_root)
    try:
        spent = spent_by_existing(work_root, runs)
        if spent:
            print(f"existing runs already used {spent} tokens (counted against --budget-tokens)")
        mirror = Path(args.mirror_dir) if args.mirror_dir else None
        ac_files = load_ac_files(candidates, mirror) if will_grade(args) else {}
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
            text, sha = tasks[run["order"]]
            record = run_one(args, run, work_root, text, sha, ac_files.get(run["order"], {}))
            spent += record["totalTokens"]
            print(f"{run['runId']}: {record['status']} tokens={record['totalTokens']} "
                  f"success={record.get('verifiedSuccess')}")
            if record.get("tokenLimitExceeded"):
                raise Stop(f"{run['runId']} exceeded --max-run-tokens ({record['totalTokens']})")
    except Stop as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2
    finally:
        lock.unlink()
    return 0


def summarize(work_root: Path) -> dict:
    records = [read_record(p.parent) for p in sorted(work_root.glob("HTC-*/run.json"))]
    per = {}
    for rec in records:
        row = per.setdefault(rec["order"], {"order": rec["order"], "repo": rec["repo"], "revision": rec["revision"],
                                            "runs": 0, "completed": 0, "verifiedSuccesses": 0, "other": []})
        row["runs"] += 1
        if rec["status"] == "completed":
            row["completed"] += 1
            row["verifiedSuccesses"] += int(bool(rec.get("verifiedSuccess")))
        else:
            row["other"].append(f"{rec['runId']}:{rec['status']}")
    for row in per.values():
        if row["completed"] != N_CAL:
            row["band"] = "INCOMPLETE"
        elif row["verifiedSuccesses"] == 0:
            row["band"] = "zero (excluded from main set)"
        elif row["verifiedSuccesses"] <= P_MAX_SUCCESSES:
            row["band"] = "hard"
        else:
            row["band"] = "not-hard"
    tokens = [r["totalTokens"] for r in records
              if r.get("modelLaunched") is True and isinstance(r.get("totalTokens"), int)]
    mean = sum(tokens) / len(tokens) if tokens else None
    m = mean / T0_TOKENS_EXP001 if mean is not None else None
    return {
        "runsFound": len(records), "runsExpected": CANDIDATE_COUNT * N_CAL,
        "dryRun": any(r.get("dryRun") for r in records),
        "meanTotalTokens": mean, "m": m, "t0TokensExp001": T0_TOKENS_EXP001,
        "totalTokensSpent": sum(tokens),
        "updatedCalibrationEstimate": None if m is None else N_CAL * C * T0_TOKENS_EXP001 * m,
        "remainingCalibrationEstimate": None if m is None else N_CAL * (C - CANDIDATE_COUNT) * T0_TOKENS_EXP001 * m,
        "candidates": [per[k] for k in sorted(per)],
    }


def cmd_summarize(args) -> int:
    result = summarize(Path(args.work_root).resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        out = Path(args.output)
        if out.exists():
            print(f"STOP: {out} exists (refusing to overwrite)", file=sys.stderr)
            return 2
        out.write_text(text + "\n", encoding="utf-8")
    return 0


def cmd_plan(_args) -> int:
    for run in plan(load_candidates()):
        cand = run["candidate"]
        print(f"{run['runId']}\t{cand['repo']}@{cand['revision']}")
    return 0


# ---------------------------------------------------------------- screening (second edition §3 / §3.1, addendum 1)

SCREEN_BLOBS = {
    ROOT / "docs/HARD_TASK_T0_FAIL_T1_PREREGISTRATION.md": "57007effd1fd502c86ea7e63029352df902670d0",
    ROOT / "docs/HARD_TASK_T0_FAIL_T1_PREREGISTRATION_ADDENDUM_1.md": "b1e6d473bb875fbcab139cce3cabf25ba8b0b924",
    CANDIDATES: CANDIDATES_BLOB,
}
SCREEN_K = 3
SCREEN_TARGET = 12
SCREEN_C = 44
REUSE_ORDERS = (1, 2, 3, 4, 5)
# Addendum 1 §2: excluded before screening; never run, not counted as failure, 0/3, or budget-excluded.
PRE_EXCLUDED = (10, 11, 16, 26, 28, 32, 38)
SCREEN_LOG = "screen-log.jsonl"


def load_screen_candidates(path: Path = CANDIDATES) -> list[dict]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    initial = sorted((c for c in doc["candidates"] if c["set"] == "initial"), key=lambda c: c["order"])
    if [c["order"] for c in initial] != list(range(1, SCREEN_C + 1)):
        raise Stop(f"candidate table initial orders are not exactly 1..{SCREEN_C}")
    return initial


def screen_targets(candidates: list[dict]) -> list[dict]:
    return [c for c in candidates if c["order"] not in REUSE_ORDERS and c["order"] not in PRE_EXCLUDED]


def screen_run_id(order: int, k: int) -> str:
    return f"HTS-{order:02d}-n{k}"


def marker_path(work_root: Path, order: int) -> Path:
    return work_root / f"HTS-{order:02d}.budget-excluded.json"


def load_reuse(reuse_root: Path, candidates: list[dict]) -> dict[int, dict]:
    """§3.1: only n1..n3 of each of the first 5 candidates, read from the calibration results; never guessed."""
    out = {}
    for cand in candidates:
        if cand["order"] not in REUSE_ORDERS:
            continue
        runs = []
        for k in range(1, SCREEN_K + 1):
            path = reuse_root / f"HTC-{cand['order']:02d}-n{k}" / "run.json"
            try:
                rec = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise Stop(f"reuse: cannot read {path}: {exc}")
            trace = rec.get("trace") or {}
            if (rec.get("runId") != path.parent.name or rec.get("order") != cand["order"] or rec.get("calRep") != k
                    or rec.get("repo") != cand["repo"] or rec.get("revision") != cand["revision"]
                    or rec.get("dryRun") is not False or rec.get("modelLaunched") is not True
                    or rec.get("status") != "completed" or not isinstance(rec.get("verifiedSuccess"), bool)
                    or not isinstance(rec.get("totalTokens"), int)
                    or trace.get("contexts") != [[MODEL, EFFORT]]
                    or trace.get("cliVersion") != RUNTIME_VERSION.split()[-1]):
                raise Stop(f"reuse: {path} is not a completed real {RUNTIME_VERSION} {MODEL}/{EFFORT} Run of this "
                           "candidate with verifiedSuccess and totalTokens")
            runs.append({"k": k, "runId": rec["runId"], "status": rec["status"],
                         "success": rec["verifiedSuccess"], "tokens": rec["totalTokens"]})
        outcome = "truncated" if any(r["success"] for r in runs) else "zero"
        out[cand["order"]] = {"outcome": outcome, "runs": runs, "tokens": sum(r["tokens"] for r in runs)}
    return out


def run_outcome(rec: dict) -> str:
    """success / failure / budget-excluded for one launched screening Run; anything else cannot be classified."""
    if rec.get("tokenLimitExceeded"):
        return "budget-excluded"
    status = rec.get("status")
    if status in ABORTED_STATUSES:
        return "budget-excluded"
    if status == "completed":
        if not isinstance(rec.get("verifiedSuccess"), bool):
            raise Stop(f"{rec.get('runId')} is completed without a boolean verifiedSuccess")
        return "success" if rec["verifiedSuccess"] else "failure"
    if status == "dry-run-ungraded":
        return "success" if rec.get("dryRunSuccess") is True else "failure"
    raise Stop(f"{rec.get('runId')} has status {status!r}; cannot classify the screening Run")


def screen_records(work_root: Path, order: int) -> list[dict]:
    """Launched screening Runs of one candidate in Run-number order (never-launched attempts are not Runs)."""
    recs = []
    for k in range(1, SCREEN_K + 1):
        rdir = work_root / screen_run_id(order, k)
        if not rdir.exists():
            continue
        rec = read_record(rdir)
        if never_launched(rec):
            continue
        if not isinstance(rec.get("totalTokens"), int) and rec.get("status") not in ABORTED_STATUSES:
            raise Stop(f"{rdir.name} has no totalTokens; record its usage before resuming")
        recs.append(rec)
    return recs


def exclusion_reason(rec: dict) -> str:
    if rec.get("tokenLimitExceeded") and rec.get("status") != ABORTED_NONZERO:
        return (f"token limit:{rec['runId']} used {rec['totalTokens']} tokens "
                f"> --max-run-tokens {rec['limits']['maxRunTokens']}")
    tokens = rec.get("totalTokens")
    return f"{rec.get('stopReason')}: {rec['runId']} used {'unknown' if tokens is None else tokens} tokens"


def classify(work_root: Path, order: int) -> dict:
    recs = screen_records(work_root, order)
    runs, outcome, reason = [], "not-started" if not recs else "incomplete", None
    for rec in recs:
        result = run_outcome(rec)
        runs.append({"k": rec["calRep"], "runId": rec["runId"], "status": rec["status"], "result": result,
                     "tokens": rec.get("totalTokens")})
        if result in ("success", "budget-excluded"):
            outcome = "truncated" if result == "success" else "budget-excluded"
            if result == "budget-excluded":
                reason = exclusion_reason(rec)
            break
    else:
        if len(runs) == SCREEN_K:
            outcome = "zero"
    marker = marker_path(work_root, order)
    if marker.exists():
        outcome = "budget-excluded"
        reason = json.loads(marker.read_text(encoding="utf-8")).get("reason")
    return {"outcome": outcome, "runs": runs, "tokens": sum(r["tokens"] or 0 for r in runs), "reason": reason,
            "usageUnknown": [r["runId"] for r in runs if r["tokens"] is None]}


def write_marker(work_root: Path, order: int, reason: str) -> None:
    marker_path(work_root, order).write_text(json.dumps({"order": order, "reason": reason, "at": now()}) + "\n",
                                             encoding="utf-8")


def log_screen(work_root: Path, event: dict) -> None:
    with (work_root / SCREEN_LOG).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": now(), **event}, ensure_ascii=False) + "\n")


def preflight_screen(args) -> None:
    for path, expected in SCREEN_BLOBS.items():
        actual = git_blob_sha(path)
        if actual != expected:
            raise Stop(f"blob mismatch for {path.name}: {actual} != {expected}")
    work_root = Path(args.work_root).resolve()
    if work_root == ROOT or ROOT in work_root.parents:
        raise Stop("work root must be outside the DAT repository")
    if work_root == Path(args.reuse_root).expanduser().resolve():
        raise Stop("work root must differ from the reuse root")
    for name in ("timeout_s", "max_run_tokens", "max_candidate_tokens", "budget_tokens"):
        if getattr(args, name) <= 0:
            raise Stop(f"--{name.replace('_', '-')} must be positive")
    if args.max_run_tokens > args.max_candidate_tokens or args.max_run_tokens > args.budget_tokens:
        raise Stop("--max-run-tokens exceeds --max-candidate-tokens or --budget-tokens")
    existing = sorted(p.name for p in work_root.glob("HTS-*")) if work_root.exists() else []
    if existing and not args.skip_existing:
        raise Stop(f"screening results already exist (refusing to overwrite): {', '.join(existing)}")
    if will_grade(args):
        probe_ac_sandbox(args.ac_python)
    if not args.dry_run:
        preflight_container(args)


def screen_candidate(args, cand: dict, work_root: Path, spent: int, task: tuple[str, str],
                     ac_files: dict[str, bytes]) -> tuple[str, int]:
    """Up to k T0 Runs; stops the candidate at the first verified success. Returns (outcome, screening spend)."""
    order = cand["order"]
    for k in range(1, SCREEN_K + 1):
        state = classify(work_root, order)
        if state["outcome"] in ("truncated", "zero", "budget-excluded"):
            return state["outcome"], spent
        rdir = work_root / screen_run_id(order, k)
        if rdir.exists():
            if not never_launched(read_record(rdir)):
                print(f"skip existing {rdir.name}")
                continue
            print(f"retry {rdir.name}: model was never launched; previous attempt kept at "
                  f"{preserve_attempt(work_root, rdir)}")
        if spent + args.max_run_tokens > args.budget_tokens:
            raise Stop(f"budget: spent {spent} + max per run {args.max_run_tokens} > {args.budget_tokens}")
        if state["tokens"] + args.max_run_tokens > args.max_candidate_tokens:
            reason = (f"candidate budget: spent {state['tokens']} + max per run {args.max_run_tokens} "
                      f"> {args.max_candidate_tokens}")
            write_marker(work_root, order, reason)
            print(f"order-{order:02d}: budget-excluded ({reason})")
            return "budget-excluded", spent
        run = {"runId": rdir.name, "order": order, "calRep": k, "candidate": cand}
        record = run_one(args, run, work_root, task[0], task[1], ac_files)
        record["phase"] = "screening"
        if args.dry_run:
            record["dryRunSuccess"] = order in args.dry_run_success
        write_record(rdir, record)
        spent += record["totalTokens"]
        cand_spent = state["tokens"] + record["totalTokens"]
        print(f"{rdir.name}: {record['status']} tokens={record['totalTokens']} "
              f"success={record.get('verifiedSuccess', record.get('dryRunSuccess'))}")
        if record.get("tokenLimitExceeded"):
            raise Stop(f"{rdir.name} exceeded --max-run-tokens ({record['totalTokens']})")
        if cand_spent > args.max_candidate_tokens:
            reason = f"candidate spend {cand_spent} exceeded --max-candidate-tokens after {rdir.name}"
            write_marker(work_root, order, reason)
            raise Stop(reason)
        if spent > args.budget_tokens:
            raise Stop(f"screening spend {spent} exceeded --budget-tokens after {rdir.name}")
    return classify(work_root, order)["outcome"], spent


def cmd_screen(args) -> int:
    candidates = load_screen_candidates()
    preflight_screen(args)
    reused = load_reuse(Path(args.reuse_root).expanduser().resolve(), candidates)
    targets = screen_targets(candidates)
    tasks = load_task_descriptions(Path(args.task_dir), targets)
    for order, (_, sha) in sorted(tasks.items()):
        print(f"task description order-{order:02d}.md sha256 {sha} (must match the hash recorded in #244)")
    work_root = Path(args.work_root).resolve()
    lock = acquire_lock(work_root)
    try:
        for path in sorted(work_root.glob("HTS-*/run.json")):
            if json.loads(path.read_text(encoding="utf-8")).get("dryRun") is not args.dry_run:
                raise Stop(f"{path} was written in a different dry-run mode; synthetic and real Runs must not mix")
        states = [classify(work_root, c["order"]) for c in targets]
        unknown = [run_id for s in states for run_id in s["usageUnknown"]]
        if unknown:
            raise Stop(f"token usage is unknown for {', '.join(unknown)}; resolve it before resuming")
        spent = sum(s["tokens"] for s in states)
        if spent:
            print(f"existing screening runs already used {spent} tokens (counted against --budget-tokens)")
        mirror = Path(args.mirror_dir) if args.mirror_dir else None
        ac_files = load_ac_files(targets, mirror) if will_grade(args) else {}
        zeros = sum(1 for r in reused.values() if r["outcome"] == "zero")
        reason = "candidates-exhausted"
        for cand in targets:
            if zeros >= SCREEN_TARGET:
                reason = "target-reached"
                break
            outcome, spent = screen_candidate(args, cand, work_root, spent, tasks[cand["order"]],
                                              ac_files.get(cand["order"], {}))
            zeros += outcome == "zero"
        else:
            if zeros >= SCREEN_TARGET:
                reason = "target-reached"
        log_screen(work_root, {"event": "end", "reason": reason, "zeros": zeros, "spent": spent})
        print(f"screening ended: {reason} (0/{SCREEN_K} candidates: {zeros})")
    except Stop as exc:
        log_screen(work_root, {"event": "stop", "reason": str(exc)})
        print(f"STOP: {exc}", file=sys.stderr)
        return 2
    finally:
        lock.unlink()
    return 0


def screen_summarize(work_root: Path, reuse_root: Path) -> dict:
    candidates = load_screen_candidates()
    reused = load_reuse(reuse_root, candidates)
    rows = []
    for cand in candidates:
        order = cand["order"]
        row = {"order": order, "repo": cand["repo"], "revision": cand["revision"]}
        if order in PRE_EXCLUDED:
            row.update(source="addendum-1", outcome="pre-excluded", runs=[], tokens=0)
        elif order in reused:
            row.update(source="reuse (calibration n1..n3)", **reused[order])
        else:
            row.update(source="screening", **classify(work_root, order))
        rows.append(row)
    stops = []
    log = work_root / SCREEN_LOG
    if log.exists():
        stops = [json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()]
    screened = [r for r in rows if r["source"] == "screening"]
    launched = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(work_root.glob("HTS-*/run.json"))]
    zero = [r["order"] for r in rows if r["outcome"] == "zero"]
    return {
        "k": SCREEN_K, "target": SCREEN_TARGET,
        "dryRun": any(r.get("dryRun") for r in launched),
        "selectedZero": zero, "selectedCount": len(zero),
        "feasibilityOnly": len(zero) < SCREEN_TARGET,
        "truncated": [r["order"] for r in rows if r["outcome"] == "truncated"],
        "preExcluded": list(PRE_EXCLUDED),
        "budgetExcluded": [{"order": r["order"], "reason": r["reason"], "tokens": r["tokens"],
                            "usageUnknown": r["usageUnknown"]} for r in rows if r["outcome"] == "budget-excluded"],
        "screeningTokens": sum(r["tokens"] for r in screened),
        "usageUnknownRuns": [run_id for r in screened for run_id in r["usageUnknown"]],
        "reusedTokensNotCounted": sum(r["tokens"] for r in rows if r["source"].startswith("reuse")),
        "stopReason": stops[-1]["reason"] if stops else None,
        "stopLog": stops,
        "candidates": rows,
    }


def cmd_screen_summarize(args) -> int:
    result = screen_summarize(Path(args.work_root).resolve(), Path(args.reuse_root).expanduser().resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        out = Path(args.output)
        if out.exists():
            print(f"STOP: {out} exists (refusing to overwrite)", file=sys.stderr)
            return 2
        out.write_text(text + "\n", encoding="utf-8")
    return 0


def cmd_screen_plan(_args) -> int:
    for cand in load_screen_candidates():
        order = cand["order"]
        if order in PRE_EXCLUDED:
            action = "pre-excluded (addendum 1; no Run, not counted)"
        elif order in REUSE_ORDERS:
            action = f"reuse HTC-{order:02d}-n1..n{SCREEN_K} (no new Run)"
        else:
            action = f"{screen_run_id(order, 1)}..n{SCREEN_K} (stop at first verified success)"
        print(f"{order:02d}\t{action}\t{cand['repo']}@{cand['revision']}")
    print(f"stop when {SCREEN_TARGET} candidates are 0/{SCREEN_K} (reuse included)")
    return 0


def orders(value: str) -> set[int]:
    return {int(x) for x in value.split(",") if x.strip()}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan").set_defaults(func=cmd_plan)
    sub.add_parser("screen-plan").set_defaults(func=cmd_screen_plan)
    sc = sub.add_parser("screen")
    sc.add_argument("--work-root", required=True, help="screening results directory outside the DAT repo")
    sc.add_argument("--reuse-root", required=True, help="calibration results with HTC-01..05-n1..n3 (read only)")
    sc.add_argument("--task-dir", required=True, help="directory with order-NN.md for the screened candidates")
    sc.add_argument("--timeout-s", type=int, required=True, help="per-Run wall clock hard limit (no default)")
    sc.add_argument("--max-run-tokens", type=int, required=True, help="per-Run token limit, checked after the Run")
    sc.add_argument("--max-candidate-tokens", type=int, required=True, help="per-candidate screening token limit")
    sc.add_argument("--budget-tokens", type=int, required=True, help="approved screening budget (reuse not counted)")
    sc.add_argument("--codex-dir", help="Linux Codex vendor directory with bin/codex (mounted read-only at /cx)")
    sc.add_argument("--auth-file", default="~/.codex/auth.json", help="mounted read-only; contents are not read")
    sc.add_argument("--ac-python", default="python3.12")
    sc.add_argument("--mirror-dir", help="local clones named after the repo (dry-run / offline tests)")
    sc.add_argument("--skip-existing", action="store_true",
                    help="leave existing Run directories untouched, skip them, and count their tokens against the budget")
    sc.add_argument("--dry-run", action="store_true", help="never launch a model or a container; write a synthetic trace")
    sc.add_argument("--dry-run-model", default=MODEL)
    sc.add_argument("--dry-run-effort", default=EFFORT)
    sc.add_argument("--dry-run-tokens", type=int, default=68022)
    sc.add_argument("--dry-run-success", type=orders, default=set(),
                    help="comma-separated orders whose dry-run Runs count as synthetic successes")
    sc.set_defaults(func=cmd_screen)
    ss = sub.add_parser("screen-summarize")
    ss.add_argument("--work-root", required=True)
    ss.add_argument("--reuse-root", required=True)
    ss.add_argument("--output")
    ss.set_defaults(func=cmd_screen_summarize)
    r = sub.add_parser("run")
    r.add_argument("--work-root", required=True, help="results directory outside the DAT repo")
    r.add_argument("--task-dir", required=True,
                   help="directory with order-01.md .. order-05.md: per-candidate symptom descriptions, passed verbatim")
    r.add_argument("--timeout-s", type=int, required=True, help="per-Run wall clock hard limit (no default)")
    r.add_argument("--max-run-tokens", type=int, required=True, help="per-Run token limit, checked after the Run")
    r.add_argument("--budget-tokens", type=int, required=True, help="approved calibration budget for this batch")
    r.add_argument("--codex-dir", help="Linux Codex vendor directory with bin/codex (mounted read-only at /cx)")
    r.add_argument("--auth-file", default="~/.codex/auth.json", help="mounted read-only; contents are not read")
    r.add_argument("--ac-python", default="python3.12")
    r.add_argument("--mirror-dir", help="local clones named after the repo (dry-run / offline tests)")
    r.add_argument("--skip-existing", action="store_true",
                   help="leave existing Run directories untouched, skip them, and count their tokens against the budget")
    r.add_argument("--skip-blob-check", action="store_true", help=argparse.SUPPRESS)
    r.add_argument("--dry-run", action="store_true", help="never launch a model or a container; write a synthetic trace")
    r.add_argument("--dry-run-model", default=MODEL)
    r.add_argument("--dry-run-effort", default=EFFORT)
    r.add_argument("--dry-run-tokens", type=int, default=68022)
    r.set_defaults(func=cmd_run)
    s = sub.add_parser("summarize")
    s.add_argument("--work-root", required=True)
    s.add_argument("--output")
    s.set_defaults(func=cmd_summarize)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.func(args)
    except Stop as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
