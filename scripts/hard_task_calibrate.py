#!/usr/bin/env python3
"""Calibration kit for the hard-task T0/T1 comparison (#244, preregistration §6 / §9 step 6).

Subcommands:
  plan       print the 25 calibration Runs (first 5 initial candidates x n_cal 5)
  run        execute the Runs sequentially (T0, Codex / gpt-6.1-sol / high); --dry-run never launches a model
  summarize  aggregate per-candidate verified successes and m (token ratio vs EXP-001 T0)

The Operator launches `run` without --dry-run. Agents use --dry-run only.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

import yaml

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "docs/hard-task/CANDIDATES.yaml"
PREREGISTRATION = ROOT / "docs/HARD_TASK_T0_T1_PREREGISTRATION.md"
CANDIDATES_BLOB = "aad6f23629efaefdd266f0e21ca59248e4693c7b"
PREREGISTRATION_BLOB = "52b4a585044e00d52fea8db64f725c4b4f3258cd"

RUNTIME_VERSION = "codex-cli 0.160.1"
MODEL = "gpt-6.1-sol"
EFFORT = "high"
CANDIDATE_COUNT = 5
N_CAL = 5
P_MAX_SUCCESSES = 2
C = 44
T0_TOKENS_EXP001 = 68022.0
PROMPT_FIELDS = ("repo", "revision", "fixSubject")
LOCK_NAME = ".calibration.lock"


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


def render_prompt(template: str, cand: dict) -> str:
    out = template
    for field in PROMPT_FIELDS:
        out = out.replace("{" + field + "}", str(cand[field]))
    return out


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
    if not args.dry_run:
        version = subprocess.run([args.codex, "--version"], capture_output=True, text=True, check=False).stdout.strip()
        if version != RUNTIME_VERSION:
            raise Stop(f"runtime version {version!r} != {RUNTIME_VERSION!r}")


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


def codex_command(args, ws: Path) -> list[str]:
    return [args.codex, "exec", "--json", "--ignore-user-config", "--skip-git-repo-check",
            "-m", MODEL, "-c", f"model_reasoning_effort={EFFORT}", "-c", "approval_policy=never",
            "-s", "workspace-write", "-C", str(ws), "-"]


def fake_codex(args, ws: Path, sessions_dir: Path) -> int:
    """Dry-run stand-in: writes a synthetic session trace. No model is launched."""
    sessions_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        {"type": "session_meta", "payload": {"id": "dry-run", "cwd": str(ws), "cli_version": RUNTIME_VERSION.split()[-1]}},
        {"type": "turn_context", "payload": {"model": args.dry_run_model, "effort": args.dry_run_effort, "cwd": str(ws)}},
        {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {
            "input_tokens": args.dry_run_tokens, "cached_input_tokens": 0, "output_tokens": 0,
            "total_tokens": args.dry_run_tokens}}}},
    ]
    (sessions_dir / "rollout-dry-run.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
    return 0


def find_session(sessions_root: Path, ws: Path, since: float) -> Path:
    hits = []
    for path in sessions_root.rglob("rollout-*.jsonl"):
        if path.stat().st_mtime < since:
            continue
        with path.open(encoding="utf-8") as fh:
            first = json.loads(fh.readline() or "{}")
        if first.get("type") == "session_meta" and Path(first["payload"].get("cwd", "")).resolve() == ws.resolve():
            hits.append(path)
    if len(hits) != 1:
        raise Stop(f"expected exactly one session trace for {ws}, found {len(hits)}")
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
    """Overlay the fix commit's test files on a copy of the workspace and run the AC (Worker never sees them)."""
    shutil.copytree(ws, grade_dir, symlinks=True, ignore=shutil.ignore_patterns(".git"))
    for rel, blob in ac_files.items():
        target = grade_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
    cmd = shlex.split(cand["acceptanceCriteria"]["command"])
    cmd[0] = ac_python
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    ac = subprocess.run(cmd, cwd=grade_dir, capture_output=True, text=True, env=env, timeout=300, check=False)
    ids = [test_id(t) for t in cand["acceptanceCriteria"]["failingBeforeFix"]]
    oracle = subprocess.run([ac_python, "-m", "unittest", "-v", *ids], cwd=grade_dir, capture_output=True,
                            text=True, env=env, timeout=300, check=False)
    lines = oracle.stderr.splitlines()
    oracle_ok = oracle.returncode == 0 and all(any(f"({t}) ... ok" in ln for ln in lines) for t in ids)
    (grade_dir.parent / "ac-output.txt").write_text(ac.stdout + ac.stderr, encoding="utf-8")
    (grade_dir.parent / "oracle-output.txt").write_text(oracle.stdout + oracle.stderr, encoding="utf-8")
    return {"acExitCode": ac.returncode, "negativeOraclePassed": oracle_ok,
            "verifiedSuccess": ac.returncode == 0 and oracle_ok}


def run_one(args, run: dict, work_root: Path, template: str, prompt_sha: str, ac_files: dict[str, bytes]) -> dict:
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
    skip_ws = args.dry_run and args.mirror_dir is None
    if skip_ws:
        ws.mkdir()
    else:
        prepare_workspace(cand, ws, Path(args.mirror_dir) if args.mirror_dir else None)
    prompt = render_prompt(template, cand)
    (rdir / "prompt.md").write_text(prompt, encoding="utf-8")
    sessions_root = rdir / "dry-run-sessions" if args.dry_run else Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "sessions"
    cmd = codex_command(args, ws)
    record["command"] = cmd
    since = time.time() - 1
    started = time.monotonic()
    if args.dry_run:
        rc = fake_codex(args, ws, sessions_root)
        (rdir / "codex-events.jsonl").write_text("", encoding="utf-8")
    else:
        with (rdir / "codex-events.jsonl").open("w", encoding="utf-8") as out, \
                (rdir / "codex-stderr.log").open("w", encoding="utf-8") as err:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=out, stderr=err, text=True)
            try:
                proc.communicate(prompt, timeout=args.timeout_s)
                rc = proc.returncode
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                rc = None
    record["wallClockMs"] = int((time.monotonic() - started) * 1000)
    record["codexExitCode"] = rc
    session = find_session(sessions_root, ws, since)
    shutil.copy2(session, rdir / "session-trace.jsonl")
    trace = read_trace(session)
    record["trace"] = {"cliVersion": trace["cliVersion"], "contexts": [list(c) for c in trace["contexts"]],
                       "totalTokenUsage": trace["totalTokenUsage"]}
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
    elif skip_ws:
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
    template_path = Path(args.prompt)
    template = template_path.read_text(encoding="utf-8")
    prompt_sha = sha256_file(template_path)
    work_root = Path(args.work_root).resolve()
    lock = acquire_lock(work_root)
    spent = 0
    try:
        mirror = Path(args.mirror_dir) if args.mirror_dir else None
        ac_files = {} if args.dry_run and mirror is None else load_ac_files(candidates, mirror)
        for run in runs:
            if (work_root / run["runId"]).exists():
                print(f"skip existing {run['runId']}")
                continue
            if spent + args.max_run_tokens > args.budget_tokens:
                raise Stop(f"budget: spent {spent} + max per run {args.max_run_tokens} > {args.budget_tokens}")
            record = run_one(args, run, work_root, template, prompt_sha, ac_files.get(run["order"], {}))
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
    r.add_argument("--prompt", required=True, help=f"T0 prompt template; placeholders: {', '.join(PROMPT_FIELDS)}")
    r.add_argument("--timeout-s", type=int, required=True, help="per-Run wall clock hard limit (no default)")
    r.add_argument("--max-run-tokens", type=int, required=True, help="per-Run token limit, checked after the Run")
    r.add_argument("--budget-tokens", type=int, required=True, help="approved calibration budget for this batch")
    r.add_argument("--codex", default="codex")
    r.add_argument("--ac-python", default="python3.12")
    r.add_argument("--mirror-dir", help="local clones named after the repo (dry-run / offline tests)")
    r.add_argument("--skip-existing", action="store_true", help="leave existing Run directories untouched and skip them")
    r.add_argument("--skip-blob-check", action="store_true", help=argparse.SUPPRESS)
    r.add_argument("--dry-run", action="store_true", help="never launch a model; write a synthetic trace instead")
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
