#!/usr/bin/env python3
"""Host-side checks for run-kit-g (read-only). Each subcommand prints PASS/values or exits non-zero with STOP."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import pwd
import re
import subprocess
import sys
from pathlib import Path

import yaml

PRIOR_REQUIRED = ("run-meta.yaml", "prompt.md", "execution-attestation.yaml", "trace.yaml",
                  "evaluation.yaml", "patch.diff", "evidence.txt")
PILOT = "experiments/EXP-001-t0-vs-t1/pilot"
ARTIFACT_ROOT = "experiments/EXP-001-t0-vs-t1/runs/pilot-codex"
FAILURE_ROOT = "experiments/EXP-001-t0-vs-t1/runs/infrastructure-failures"
EXPECT_COLUMNS = ("scenario", "fixturePath", "ran", "failedLine", "kind", "test", "assertType", "assertMsg")


class Stop(Exception):
    pass


def load(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expectation(table: Path, scenario: str) -> dict[str, str]:
    rows = []
    for line in table.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) != len(EXPECT_COLUMNS):
            raise Stop(f"malformed expectation row: {cols[0]!r}")
        rows.append(dict(zip(EXPECT_COLUMNS, cols)))
    hits = [row for row in rows if row["scenario"] == scenario]
    if len(hits) != 1:
        raise Stop(f"expected exactly 1 expectation row for scenario {scenario!r}, found {len(hits)}")
    return hits[0]


def matrix_runs(root: Path):
    return load(root / PILOT / "run-matrix.yaml")["spec"]["runs"]


def cmd_matrix_order(args) -> None:
    root = Path(args.root)
    runs = matrix_runs(root)
    ids = [run["runId"] for run in runs]
    if args.run_id not in ids:
        raise Stop(f"runId {args.run_id!r} is not in the run matrix")
    idx = ids.index(args.run_id)
    if idx == 0:
        raise Stop("first matrix run is not handled by this kit")
    art = root / ARTIFACT_ROOT
    for run_id in ids[:idx]:
        d = art / run_id
        missing = [n for n in PRIOR_REQUIRED if not (d / n).is_file() or (d / n).stat().st_size == 0]
        if missing:
            raise Stop(f"earlier matrix run {run_id} lacks result artifacts: {missing}")
    for run_id in ids[idx:]:
        if (art / run_id).exists():
            raise Stop(f"matrix run {run_id} at or after the target already has a run directory")
        if (root / FAILURE_ROOT / run_id).exists():
            raise Stop(f"matrix run {run_id} has an infrastructure-failure archive (needs a reviewed disposition)")
    print(ids[idx - 1])


def cmd_workspace_id(args) -> None:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{7,95}", args.workspace_id):
        raise Stop("workspaceId must be an opaque lower-case id ([a-z0-9-], 8-96 chars)")
    used = set()
    for path in (Path(args.root) / ARTIFACT_ROOT).glob("*/run-meta.yaml"):
        used.add(load(path).get("spec", {}).get("workspaceId"))
    for path in (Path(args.root) / FAILURE_ROOT).glob("*/*/run-meta.yaml"):
        used.add(load(path).get("spec", {}).get("workspaceId"))
    if args.workspace_id in used:
        raise Stop("workspaceId already used by an existing or archived run")
    print("PASS: workspaceId is unique")


def scenario_fixture(root: Path, scenario_id: str) -> str:
    experiment = load(root / "experiments/EXP-001-t0-vs-t1/experiment.yaml")
    for item in experiment["spec"]["scenarioSets"]:
        for scenario in load(root / item["path"])["spec"]["scenarios"]:
            if scenario["id"] == scenario_id:
                return scenario["fixturePath"]
    raise Stop(f"scenario {scenario_id!r} not found in experiment scenario sets")


def cmd_meta(args) -> None:
    meta = load(Path(args.run_meta))
    prompt_sha = sha256(Path(args.prompt))
    spec, md = meta.get("spec", {}), meta.get("metadata", {})
    if prompt_sha != spec.get("promptSha256"):
        raise Stop("Gate 7: prompt SHA-256 differs from run-meta promptSha256")
    if md.get("runId") != args.run_id:
        raise Stop("Gate 8: run-meta runId differs")
    if spec.get("workspaceId") != args.workspace_id:
        raise Stop("Gate 8: run-meta workspaceId differs")
    if spec.get("freshWorkspace") is not True:
        raise Stop("Gate 8: run-meta freshWorkspace is not true")
    scenario = md.get("scenario")
    row = expectation(Path(args.expectations), scenario)
    if row["fixturePath"] != args.fixture:
        raise Stop("Gate 8: --fixture differs from the expectation table fixturePath for this scenario")
    if args.mode == "real":
        root = Path(args.root)
        entry = next((r for r in matrix_runs(root) if r["runId"] == args.run_id), None)
        if entry is None:
            raise Stop("Gate 8: runId not in matrix")
        for key in ("blockId", "scenario", "condition"):
            if md.get(key) != entry[key]:
                raise Stop(f"Gate 8: run-meta metadata.{key} differs from matrix")
        for key in ("repetition", "executionOrder"):
            if spec.get(key) != entry[key]:
                raise Stop(f"Gate 8: run-meta spec.{key} differs from matrix")
        if scenario_fixture(root, scenario) != args.fixture:
            raise Stop("Gate 8: --fixture differs from the frozen scenario fixturePath")
        header = f"<!-- runId: {args.run_id} -->\n"
        if not Path(args.prompt).read_text(encoding="utf-8").startswith(header):
            raise Stop("Gate 7: prompt header runId differs")
    elif not args.run_id.startswith("PRACTICE-") or not scenario.startswith("practice-"):
        raise Stop("practice mode requires a PRACTICE- runId and a practice- scenario")
    print(f"scenario={scenario}")
    print(f"promptSha256={prompt_sha}")


def cmd_expect(args) -> None:
    row = expectation(Path(args.expectations), args.scenario)
    print(f"RAN={row['ran']}")
    print(f"FAILED_LINE={row['failedLine']}")
    print(f"KIND={row['kind']}")
    print(f"TEST={row['test']}")
    print(f"ASSERT_TYPE={row['assertType']}")
    print(f"ASSERT_MSG={row['assertMsg']}")


def cmd_fixture_hashes(args) -> None:
    want = []
    for line in Path(args.table).read_text(encoding="utf-8").splitlines():
        parts = line.split("  ")
        if len(parts) == 3 and parts[0] == args.scenario:
            want.append(f"{parts[1]}  {parts[2]}")
    if not want:
        raise Stop(f"no fixture hashes recorded for scenario {args.scenario!r}")
    got = Path(args.observed).read_text(encoding="utf-8").splitlines()
    if got != want:
        raise Stop("file set / SHA-256 differs from the recorded fixture hashes")
    print(f"PASS: {len(got)} files match recorded fixture hashes for {args.scenario}")


def cmd_codex_package(args) -> None:
    data = json.loads((Path(args.dir) / "codex-package.json").read_text(encoding="utf-8"))
    if data.get("version") != args.version or data.get("target") != args.target or data.get("entrypoint") != "bin/codex":
        raise Stop("codex-package.json version/target/entrypoint mismatch")
    print(f"PASS: codex package {data['version']} {data['target']}")


def cmd_bind_audit(args) -> None:
    # Reuse the unchanged repository audit; only its hard-coded T1 r01 prompt SHA is replaced by this Run's value.
    script = Path(args.root) / "scripts" / "audit_exp001_g_bind_sources.py"
    spec = importlib.util.spec_from_file_location("audit_exp001_g_bind_sources", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    problems = module.audit_sources(Path(args.workspace), Path(args.prompt), Path(args.codex_dir),
                                    Path(args.seccomp), Path(args.auth_file))
    problems = [p for p in problems if p != "prompt: frozen SHA-256 mismatch"]
    if sha256(Path(args.prompt)) != args.prompt_sha:
        problems.append("prompt: SHA-256 differs from run-meta promptSha256")
    if problems:
        raise Stop("; ".join(problems))
    print("PASS: candidate G host bind sources (static; prompt SHA-256 = run-meta promptSha256)")


def cmd_practice_meta(args) -> None:
    # Practice stand-in for prepare_pilot_run.py: the reviewed template plus this attempt's workspaceId.
    out = Path(args.out)
    if out.exists():
        raise Stop(f"{out} already exists")
    meta = load(Path(args.template))
    if not meta["metadata"]["runId"].startswith("PRACTICE-") or "workspaceId" in meta["spec"]:
        raise Stop("practice run-meta template must have a PRACTICE- runId and no workspaceId")
    meta["spec"]["workspaceId"] = args.workspace_id
    out.write_text(yaml.safe_dump(meta, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"PASS: practice run-meta written for {meta['metadata']['runId']}")


def body_lines() -> list[str]:
    return [line.strip() for line in sys.stdin.read().splitlines()]


def require_line(lines: list[str], line: str, what: str) -> None:
    if line not in lines:
        raise Stop(f"{what}: required line {line!r} not found")


REPO_URL = r"https://github\.com/s977043/dynamic-agent-topology/\S+"
# AGENT_HARNESS.md 自律境界: an independent Reviewer's record names runtime, model and session ID.
REVIEWER = re.compile(r"Reviewer:.*\bruntime:\s*\S+.*\bmodel:\s*\S+.*\bsession:.*[0-9A-Za-z_-]{8,}")


EVIDENCE = re.compile(r"evidence: https://github\.com/s977043/dynamic-agent-topology/(pull|issues)/[0-9]+\S*")


def require_evidence(lines: list[str], what: str) -> None:
    # Syntax only: links to the review grounds. It does not prove the Reviewer exists or is independent.
    found = [line for line in lines if line.startswith("evidence:")]
    if not found:
        raise Stop(f"{what}: no 'evidence: <pull/issue link>' line")
    bad = [line for line in found if not EVIDENCE.fullmatch(line)]
    if bad:
        raise Stop(f"{what}: malformed evidence line(s): {len(bad)}")


def require_reviewer(lines: list[str], what: str) -> None:
    if not any(REVIEWER.match(line) for line in lines):
        raise Stop(f"{what}: no 'Reviewer:' line with runtime, model and session ID")


def cmd_env_judgment(args) -> None:
    # Record format (README「環境 Judgment の記録フォーマット」): unconditional ACCEPT, the merged kit, and evidence per condition.
    lines = body_lines()
    if any(re.search(r"environment disposition:\s*CONDITIONAL", line) for line in lines):
        raise Stop("environment Judgment is CONDITIONAL (conditions not recorded as satisfied)")
    require_line(lines, "EXP-001 r02+ environment disposition: ACCEPT", "environment Judgment")
    require_reviewer(lines, "environment Judgment")
    kits = [m for m in (re.fullmatch(r"kit: PR #[0-9]+ merge ([0-9a-f]{40})", line) for line in lines) if m]
    if len(kits) != 1:
        raise Stop("environment Judgment must name exactly one 'kit: PR #<n> merge <40-hex sha>' line")
    sha = kits[0].group(1)
    links = []
    for n in (1, 2, 3):
        hits = [line for line in lines if re.fullmatch(rf"condition-{n}: {REPO_URL}", line)]
        if len(hits) != 1:
            raise Stop(f"environment Judgment must have exactly one 'condition-{n}: <repository link>' line")
        links.append(hits[0].split(": ", 1)[1])
    if len(set(links)) != 3:
        raise Stop("environment Judgment: condition-1..3 must link to three different URLs")
    git = ["git", "-C", args.repo]
    if subprocess.run(git + ["merge-base", "--is-ancestor", sha, args.main_ref], capture_output=True).returncode != 0:
        raise Stop(f"kit merge {sha} is not contained in {args.main_ref}")
    judged = subprocess.run(git + ["show", f"{sha}:{args.kitrel}/SHA256SUMS"], capture_output=True)
    if judged.returncode != 0 or judged.stdout != (Path(args.kit_dir) / "SHA256SUMS").read_bytes():
        raise Stop("the kit judged by the environment Judgment differs from this kit (SHA256SUMS)")
    print(f"PASS: unconditional environment Judgment for kit {sha}")


def cmd_run_acceptance(args) -> None:
    lines = body_lines()
    require_line(lines, "EXP-001 Run acceptance: ACCEPT", "Run acceptance")
    require_line(lines, f"runId: {args.run_id}", "Run acceptance")
    require_reviewer(lines, "Run acceptance")
    require_evidence(lines, "Run acceptance")
    if any(re.fullmatch(r"runId: \S+", line) and line != f"runId: {args.run_id}" for line in lines):
        raise Stop("Run acceptance names another runId")
    print(f"PASS: Run acceptance for {args.run_id}")


def cmd_slot_disposition(args) -> None:
    lines = body_lines()
    require_line(lines, "EXP-001 slot disposition: NEW-ATTEMPT", "slot disposition")
    require_line(lines, f"runId: {args.run_id}", "slot disposition")
    require_line(lines, f"attempt: {args.attempt}", "slot disposition")
    require_reviewer(lines, "slot disposition")
    require_evidence(lines, "slot disposition")
    if not any(re.fullmatch(r"reason: \S.{9,}", line) for line in lines):
        raise Stop("slot disposition: no 'reason:' line (why a new attempt of this slot is allowed)")
    print(f"PASS: slot disposition allows attempt {args.attempt} of {args.run_id}")


def attempts(registry: Path, run_id: str) -> list[int]:
    d = registry / run_id
    if not d.exists():
        return []
    found = []
    for entry in d.iterdir():
        m = re.fullmatch(r"attempt-([1-9][0-9]*)", entry.name)
        if not m or not entry.is_dir():
            raise Stop(f"unexpected entry in attempt registry: {entry.name}")
        found.append(int(m.group(1)))
    return sorted(found)


def check_registry(path: Path) -> None:
    try:
        st = path.stat()
    except FileNotFoundError as exc:
        raise Stop(f"attempt registry {path} not found (create it once: mkdir -p -m 700 {path})") from exc
    except OSError as exc:
        raise Stop(f"attempt registry {path} cannot be read: {exc}") from exc
    if not path.is_dir() or path.is_symlink():
        raise Stop(f"attempt registry {path} is not a directory")
    if st.st_uid != os.getuid() or (st.st_mode & 0o777) != 0o700:
        raise Stop(f"attempt registry {path} must be owned by the operator with mode 700")
    if not os.access(path, os.R_OK | os.W_OK | os.X_OK):
        raise Stop(f"attempt registry {path} is not readable/writable")


def cmd_registry_path(args) -> None:
    # The registry follows the OS user database, not the caller's $HOME (prevents an accidental second ledger).
    db_home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    env_home = os.environ.get("HOME", "")
    if not env_home or os.path.realpath(env_home) != os.path.realpath(db_home):
        raise Stop(f"HOME ({env_home or 'unset'}) differs from the user database home ({db_home})")
    path = db_home / ".exp001-run-kit-g" / "attempts"
    check_registry(path)
    print(path)


def cmd_check_registry(args) -> None:
    check_registry(Path(args.path))
    print(f"PASS: attempt registry {args.path}")


def cmd_attempt_count(args) -> None:
    check_registry(Path(args.registry))
    print(len(attempts(Path(args.registry), args.run_id)))


def cmd_reserve_attempt(args) -> None:
    # One attempt per invocation, reserved atomically (mkdir). Records are never removed by the kit.
    if not re.fullmatch(r"EXP-001-[a-z]+-[a-z-]+-r0[1-3]-T[01]", args.run_id):
        raise Stop("attempt registry is for matrix runIds only")
    registry = Path(args.registry)
    check_registry(registry)
    (registry / args.run_id).mkdir(mode=0o700, exist_ok=True)
    existing = attempts(registry, args.run_id)
    if existing != list(range(1, len(existing) + 1)):
        raise Stop(f"attempt registry for {args.run_id} is not contiguous: {existing}")
    if len(existing) != args.expect_existing:
        raise Stop(f"{args.run_id} has {len(existing)} recorded attempt(s), expected {args.expect_existing}")
    target = registry / args.run_id / f"attempt-{len(existing) + 1}"
    try:
        target.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise Stop(f"{target.name} was reserved concurrently") from exc
    print(target)


def cmd_legacy_acceptance(args) -> None:
    # Only for the T1 r01 acceptance comment, which predates the record format and has no runId line.
    require_line(body_lines(), "EXP-001 Run acceptance: ACCEPT", "Run acceptance")
    print("PASS: legacy Run acceptance line present")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("matrix-order"); p.add_argument("--root", required=True); p.add_argument("--run-id", required=True)
    p.set_defaults(func=cmd_matrix_order)
    p = sub.add_parser("workspace-id"); p.add_argument("--root", required=True); p.add_argument("--workspace-id", required=True)
    p.set_defaults(func=cmd_workspace_id)
    p = sub.add_parser("meta")
    for name in ("--root", "--run-meta", "--prompt", "--run-id", "--workspace-id", "--fixture", "--expectations"):
        p.add_argument(name, required=True)
    p.add_argument("--mode", choices=("real", "practice"), required=True)
    p.set_defaults(func=cmd_meta)
    p = sub.add_parser("expect"); p.add_argument("--expectations", required=True); p.add_argument("--scenario", required=True)
    p.set_defaults(func=cmd_expect)
    p = sub.add_parser("fixture-hashes")
    for name in ("--table", "--scenario", "--observed"):
        p.add_argument(name, required=True)
    p.set_defaults(func=cmd_fixture_hashes)
    p = sub.add_parser("codex-package")
    for name in ("--dir", "--version", "--target"):
        p.add_argument(name, required=True)
    p.set_defaults(func=cmd_codex_package)
    p = sub.add_parser("bind-audit")
    for name in ("--root", "--workspace", "--prompt", "--codex-dir", "--seccomp", "--auth-file", "--prompt-sha"):
        p.add_argument(name, required=True)
    p.set_defaults(func=cmd_bind_audit)
    p = sub.add_parser("practice-meta")
    for name in ("--template", "--workspace-id", "--out"):
        p.add_argument(name, required=True)
    p.set_defaults(func=cmd_practice_meta)
    p = sub.add_parser("env-judgment")
    for name in ("--repo", "--main-ref", "--kitrel", "--kit-dir"):
        p.add_argument(name, required=True)
    p.set_defaults(func=cmd_env_judgment)
    p = sub.add_parser("run-acceptance"); p.add_argument("--run-id", required=True)
    p.set_defaults(func=cmd_run_acceptance)
    p = sub.add_parser("slot-disposition"); p.add_argument("--run-id", required=True)
    p.add_argument("--attempt", type=int, required=True)
    p.set_defaults(func=cmd_slot_disposition)
    p = sub.add_parser("registry-path")
    p.set_defaults(func=cmd_registry_path)
    p = sub.add_parser("check-registry"); p.add_argument("--path", required=True)
    p.set_defaults(func=cmd_check_registry)
    p = sub.add_parser("attempt-count"); p.add_argument("--registry", required=True); p.add_argument("--run-id", required=True)
    p.set_defaults(func=cmd_attempt_count)
    p = sub.add_parser("reserve-attempt"); p.add_argument("--registry", required=True); p.add_argument("--run-id", required=True)
    p.add_argument("--expect-existing", type=int, required=True)
    p.set_defaults(func=cmd_reserve_attempt)
    p = sub.add_parser("legacy-acceptance")
    p.set_defaults(func=cmd_legacy_acceptance)
    args = parser.parse_args()
    try:
        args.func(args)
    except Stop as exc:
        print(f"STOP: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
