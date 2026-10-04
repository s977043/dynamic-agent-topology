#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def safe_repo_path(value: str, label: str):
    path = (ROOT / value).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"{label}: path escapes repository: {value!r}") from exc
    return path


def find_scenario(experiment, scenario_id: str):
    for item in experiment["spec"]["scenarioSets"]:
        scenario_set = load(ROOT / item["path"])
        for scenario in scenario_set["spec"]["scenarios"]:
            if scenario["id"] == scenario_id:
                return scenario, item["split"]
    raise ValueError(f"unknown scenario {scenario_id!r}")


def render_prompt(base_template: str, topology_contract: str, scenario: dict) -> str:
    acceptance = "\n".join(f"- {value}" for value in scenario["acceptanceCriteria"])
    evidence = "\n".join(f"- `{value}`" for value in scenario["evidenceCommands"])
    return (
        base_template.replace("{{topology_contract}}", topology_contract.strip())
        .replace("{{instruction}}", scenario["instruction"])
        .replace("{{acceptance_criteria}}", acceptance)
        .replace("{{evidence_commands}}", evidence)
    )


def existing_workspace_ids(artifact_root: Path):
    workspace_ids = set()
    if not artifact_root.exists():
        return workspace_ids
    for path in artifact_root.glob("*/run-meta.yaml"):
        try:
            data = load(path)
        except Exception as exc:
            raise ValueError(f"cannot read existing preparation metadata {path}: {exc}") from exc
        workspace_id = data.get("spec", {}).get("workspaceId")
        if workspace_id:
            workspace_ids.add(workspace_id)
    return workspace_ids


def run_validator(pilot_path: Path, matrix_path: Path, *extra_args: str):
    validator = ROOT / "scripts" / "validate_pilot.py"
    result = subprocess.run(
        [
            sys.executable,
            str(validator),
            "--pilot",
            str(pilot_path),
            "--matrix",
            str(matrix_path),
            *extra_args,
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        raise ValueError("pilot validation failed:\n" + result.stdout)


def assert_valid_plan(pilot_path: Path, matrix_path: Path):
    run_validator(pilot_path, matrix_path)


def prepare_run(
    pilot_path: Path,
    matrix_path: Path,
    run_id: str,
    workspace: Path,
    workspace_id: str,
):
    assert_valid_plan(pilot_path, matrix_path)
    pilot = load(pilot_path)
    matrix = load(matrix_path)

    declared_matrix = safe_repo_path(pilot["spec"]["matrixPath"], "pilot.matrixPath")
    if declared_matrix != matrix_path.resolve():
        raise ValueError("--matrix does not match pilot spec.matrixPath")

    entries = {item["runId"]: item for item in matrix["spec"]["runs"]}
    if run_id not in entries:
        raise ValueError(f"unknown runId {run_id!r}")
    item = entries[run_id]

    try:
        workspace.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise ValueError(
            f"workspace must be outside the DAT repository to isolate runs: {workspace}"
        )

    if workspace.exists():
        raise ValueError(f"workspace must not already exist: {workspace}")

    artifact_root = safe_repo_path(pilot["spec"]["artifactRoot"], "pilot.artifactRoot")
    run_dir = artifact_root / run_id
    if run_dir.exists():
        raise ValueError(f"run artifact directory already exists: {run_dir}")

    workspaces = existing_workspace_ids(artifact_root)
    if workspace_id in workspaces:
        raise ValueError(f"workspaceId already used by another run: {workspace_id!r}")

    experiment_path = ROOT / "experiments" / "EXP-001-t0-vs-t1" / "experiment.yaml"
    experiment = load(experiment_path)
    scenario, split = find_scenario(experiment, item["scenario"])
    if split != item["split"]:
        raise ValueError("matrix split does not match scenario set")

    fixture = safe_repo_path(scenario["fixturePath"], "scenario.fixturePath")
    if not fixture.is_dir():
        raise ValueError(f"fixture does not exist: {fixture}")

    prompt_dir = ROOT / "experiments" / "EXP-001-t0-vs-t1" / "pilot" / "prompts"
    base_prompt_path = prompt_dir / "BASE.md"
    prompt_path = prompt_dir / f"{item['condition']}.md"
    if not base_prompt_path.is_file():
        raise ValueError("base prompt template does not exist")
    if not prompt_path.is_file():
        raise ValueError(f"prompt template does not exist for condition {item['condition']!r}")

    if item["executionOrder"] > 1:
        prior = next(
            (
                value for value in matrix["spec"]["runs"]
                if value["blockId"] == item["blockId"]
                and value["executionOrder"] == item["executionOrder"] - 1
            ),
            None,
        )
        if prior is None:
            raise ValueError("matrix is missing prior executionOrder within paired block")
        prior_dir = artifact_root / prior["runId"]
        prior_required = ("run-meta.yaml", "prompt.md", "execution-attestation.yaml", "trace.yaml", "evaluation.yaml", "patch.diff", "evidence.txt")
        missing_prior = [
            name for name in prior_required
            if not (prior_dir / name).is_file()
            or (name in {"trace.yaml", "evaluation.yaml", "patch.diff", "evidence.txt"}
                and (prior_dir / name).stat().st_size == 0)
        ]
        if missing_prior:
            raise ValueError(
                f"prior run {prior['runId']!r} must have result artifacts before executionOrder "
                f"{item['executionOrder']}; missing/empty={missing_prior!r}"
            )
        run_validator(pilot_path, matrix_path, "--run-id", prior["runId"])

    base_template = base_prompt_path.read_text(encoding="utf-8")
    topology_contract = prompt_path.read_text(encoding="utf-8")
    prompt = render_prompt(base_template, topology_contract, scenario)
    header = (
        f"<!-- runId: {item['runId']} -->\n"
        f"<!-- blockId: {item['blockId']} -->\n"
        f"<!-- executionOrder: {item['executionOrder']} -->\n\n"
    )
    rendered_prompt = header + prompt
    prompt_sha256 = hashlib.sha256(rendered_prompt.encode("utf-8")).hexdigest()

    shutil.copytree(fixture, workspace)
    run_dir.mkdir(parents=True)

    run_meta = {
        "apiVersion": "dat/v1alpha1",
        "kind": "PilotRunMetadata",
        "metadata": {
            "runId": item["runId"],
            "blockId": item["blockId"],
            "scenario": item["scenario"],
            "condition": item["condition"],
        },
        "spec": {
            "repetition": item["repetition"],
            "executionOrder": item["executionOrder"],
            "workspaceId": workspace_id,
            "freshWorkspace": True,
            "promptSha256": prompt_sha256,
        },
    }
    (run_dir / "run-meta.yaml").write_text(
        yaml.safe_dump(run_meta, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    (run_dir / "prompt.md").write_text(rendered_prompt, encoding="utf-8")

    print(f"Prepared {run_id}")
    print(f"Workspace: {workspace}")
    print(f"Artifacts: {run_dir}")
    print(f"Condition: {item['condition']} (executionOrder={item['executionOrder']})")
    print("Next: start a fresh Codex session using prompt.md, then create execution-attestation.yaml from observed execution facts.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare one EXP-001 pilot run without launching Codex.")
    parser.add_argument("--pilot", required=True)
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--workspace-id", required=True, help="Opaque, non-secret ID unique to this prepared workspace.")
    args = parser.parse_args()

    pilot_path = (ROOT / args.pilot).resolve() if not Path(args.pilot).is_absolute() else Path(args.pilot).resolve()
    matrix_path = (ROOT / args.matrix).resolve() if not Path(args.matrix).is_absolute() else Path(args.matrix).resolve()
    workspace = Path(args.workspace).resolve()

    if not args.workspace_id.strip():
        print("workspace-id must be non-empty", file=sys.stderr)
        return 1

    try:
        prepare_run(
            pilot_path,
            matrix_path,
            args.run_id,
            workspace,
            args.workspace_id.strip(),
        )
    except Exception as exc:
        print(f"Prepare pilot run failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
