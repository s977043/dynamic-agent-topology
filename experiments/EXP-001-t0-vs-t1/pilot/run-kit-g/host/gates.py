#!/usr/bin/env python3
"""Host-side checks for run-kit-g (read-only). Each subcommand prints PASS/values or exits non-zero with STOP."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
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


def cmd_comment_body(args) -> None:
    body = sys.stdin.read()
    lines = body.splitlines()
    if not any(re.fullmatch(args.line_pattern, line.strip()) for line in lines):
        raise Stop("comment does not contain the required judgment line")
    for needle in args.contains or []:
        if needle not in body:
            raise Stop("comment does not mention the required identifier")
    print("PASS: judgment line present")


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
    p = sub.add_parser("comment-body"); p.add_argument("--line-pattern", required=True); p.add_argument("--contains", action="append")
    p.set_defaults(func=cmd_comment_body)
    args = parser.parse_args()
    try:
        args.func(args)
    except Stop as exc:
        print(f"STOP: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
