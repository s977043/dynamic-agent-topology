#!/usr/bin/env python3
"""Calibration kit for the hard-task T0/T1 comparison (#244, preregistration §6 / §9 step 6).

Subcommands:
  plan       print the 25 calibration Runs (first 5 initial candidates x n_cal 5)
  run        execute the Runs sequentially (T0, Codex / gpt-6.1-sol / high); --dry-run never launches a model
  summarize  aggregate per-candidate verified successes and m (token ratio vs EXP-001 T0)

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


def docker(*args: str, stdin: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], input=stdin, capture_output=True, text=True, check=check)


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
                docker("kill", name, check=False)
                proc.kill()
                proc.wait()
                return None, evidence
        tar = subprocess.run(["docker", "exec", name, "tar", "-C", CODEX_HOME, "-cf", "-", "sessions"],
                             capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
            members = [m for m in tf.getmembers() if m.isfile() and m.name.startswith("sessions/")]
            if any("auth.json" in m.name for m in members):
                raise Stop("auth.json found in collected evidence")
            tf.extractall(rdir, members=members, filter="data")
        return rc, evidence
    finally:
        if started:
            docker("stop", "-t", "5", name, check=False)


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


def spent_by_existing(work_root: Path, runs: list[dict]) -> int:
    """Tokens already used by existing Run directories; a Run without a token count cannot be bounded."""
    spent = 0
    for run in runs:
        rdir = work_root / run["runId"]
        if not rdir.exists():
            continue
        record_path = rdir / "run.json"
        record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.exists() else {}
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
              "promptSha256": prompt_sha, "status": "started", "startedAt": now()}
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
    else:
        record["isolation"] = {}
        try:
            rc, _ = container_exec_codex(args, rdir, prompt, record["isolation"])
        except Stop as exc:
            record["status"] = "isolation-stop"
            record["stopReason"] = str(exc)
            if not record["isolation"].get("modelLaunched"):
                record["totalTokens"] = 0
            write_record(rdir, record)
            raise
    record["wallClockMs"] = int((time.monotonic() - started) * 1000)
    record["codexExitCode"] = rc
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
    elif not will_grade(args):
        record["status"] = "dry-run-ungraded"
    else:
        record.update(grade(cand, ws, rdir / "grade", ac_files, args.ac_python))
        record["status"] = "completed"
    if record["totalTokens"] > args.max_run_tokens:
        record["tokenLimitExceeded"] = True
    record["finishedAt"] = now()
    write_record(rdir, record)
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
            if (work_root / run["runId"]).exists():
                print(f"skip existing {run['runId']}")
                continue
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
    records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(work_root.glob("HTC-*/run.json"))]
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
    tokens = [r["totalTokens"] for r in records if isinstance(r.get("totalTokens"), int)]
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


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan").set_defaults(func=cmd_plan)
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
