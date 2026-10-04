#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
from pathlib import Path
import sys

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]

def load(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)

def safe_repo_path(value: str, label: str, errors: list[str]):
    path = (ROOT / value).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError:
        errors.append(f"{label}: path escapes repository: {value!r}")
        return None
    return path

def validate(data, schema_path: Path, label: str, errors: list[str]):
    schema = load(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for error in sorted(validator.iter_errors(data), key=lambda e: tuple(str(p) for p in e.path)):
        location = ".".join(str(p) for p in error.path) or "<root>"
        errors.append(f"{label}: schema error at {location}: {error.message}")

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an EXP-001 pilot plan and optional run artifacts.")
    parser.add_argument("--pilot", required=True)
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument(
        "--run-id",
        help="Validate artifacts for one run only. Used by the Operator Kit order gate.",
    )
    args = parser.parse_args()

    pilot_path = (ROOT / args.pilot).resolve() if not Path(args.pilot).is_absolute() else Path(args.pilot)
    matrix_path = (ROOT / args.matrix).resolve() if not Path(args.matrix).is_absolute() else Path(args.matrix)
    errors = []

    pilot = load(pilot_path)
    matrix = load(matrix_path)
    validate(pilot, ROOT / "schemas" / "pilot.schema.json", str(pilot_path), errors)

    declared_matrix = safe_repo_path(pilot["spec"]["matrixPath"], "pilot.matrixPath", errors)
    if declared_matrix is not None and declared_matrix != matrix_path.resolve():
        errors.append("pilot: --matrix does not match spec.matrixPath")

    artifact_root_checked = safe_repo_path(pilot["spec"]["artifactRoot"], "pilot.artifactRoot", errors)

    experiment_name = pilot["metadata"]["experiment"]
    experiment_path = ROOT / "experiments" / "EXP-001-t0-vs-t1" / "experiment.yaml"
    experiment = load(experiment_path)
    if experiment["metadata"]["name"] != experiment_name:
        errors.append("pilot: experiment reference does not match experiment.yaml")

    if pilot["spec"]["runtime"] not in experiment["spec"]["runtimeScope"]:
        errors.append("pilot: runtime is not allowed by experiment runtimeScope")

    expected_conditions = [item["id"] for item in experiment["spec"]["conditions"]]
    execution_subject_by_condition = {
        item["id"]: item["executionRef"] for item in experiment["spec"]["conditions"]
    }
    if pilot["spec"]["conditions"] != expected_conditions:
        errors.append(f"pilot: conditions {pilot['spec']['conditions']!r} do not match experiment {expected_conditions!r}")

    minimum = experiment["spec"]["decisionPolicy"]["minimumRunsPerScenarioPerCondition"]
    if pilot["spec"]["repetitions"] < minimum:
        errors.append(f"pilot: repetitions must be >= experiment minimum {minimum}")

    known_scenarios = {}
    for item in experiment["spec"]["scenarioSets"]:
        scenario_set = load(ROOT / item["path"])
        for scenario in scenario_set["spec"]["scenarios"]:
            known_scenarios[scenario["id"]] = item["split"]

    plan_scenarios = pilot["spec"]["scenarios"]
    for scenario in plan_scenarios:
        if scenario["id"] not in known_scenarios:
            errors.append(f"pilot: unknown scenario {scenario['id']!r}")
        elif known_scenarios[scenario["id"]] != scenario["split"]:
            errors.append(f"pilot: split mismatch for scenario {scenario['id']!r}")

    expected = []
    conditions = pilot["spec"]["conditions"]
    if pilot["spec"]["orderPolicy"] != "counterbalanced-paired":
        errors.append("pilot: unsupported orderPolicy")
    for scenario_index, scenario in enumerate(plan_scenarios):
        for repetition in range(1, pilot["spec"]["repetitions"] + 1):
            block_id = f"EXP-001-{scenario['id']}-r{repetition:02d}"
            ordered = list(conditions)
            if (scenario_index + repetition) % 2 == 0:
                ordered.reverse()
            for execution_order, condition in enumerate(ordered, start=1):
                expected.append({
                    "runId": f"{block_id}-{condition}",
                    "blockId": block_id,
                    "scenario": scenario["id"],
                    "split": scenario["split"],
                    "condition": condition,
                    "repetition": repetition,
                    "executionOrder": execution_order,
                })

    if matrix.get("kind") != "PilotRunMatrix":
        errors.append("matrix: kind must be PilotRunMatrix")
    actual = matrix.get("spec", {}).get("runs", [])
    if matrix.get("spec", {}).get("expectedRuns") != len(expected):
        errors.append(f"matrix: expectedRuns must be {len(expected)}")
    if matrix.get("spec", {}).get("orderPolicy") != pilot["spec"]["orderPolicy"]:
        errors.append("matrix: orderPolicy does not match pilot")
    if actual != expected:
        errors.append("matrix: run list does not exactly match deterministic pilot matrix")

    run_ids = [item["runId"] for item in actual]
    if len(run_ids) != len(set(run_ids)):
        errors.append("matrix: duplicate runId")

    validate_artifacts = args.require_complete or args.run_id is not None
    items_to_validate = expected
    if args.run_id is not None:
        matches = [item for item in expected if item["runId"] == args.run_id]
        if not matches:
            errors.append(f"unknown runId for artifact validation: {args.run_id!r}")
            items_to_validate = []
        else:
            items_to_validate = matches

    if validate_artifacts:
        artifact_root = artifact_root_checked
        if artifact_root is None:
            artifact_root = ROOT / "__invalid_artifact_root__"
        trace_schema = ROOT / "schemas" / "execution-trace.schema.json"
        eval_schema = ROOT / "schemas" / "evaluation.schema.json"
        meta_schema = ROOT / "schemas" / "pilot-run-meta.schema.json"
        attestation_schema = ROOT / "schemas" / "pilot-execution-attestation.schema.json"
        workspace_ids = set()

        session_owners = {}
        for expected_item in expected:
            path = artifact_root / expected_item["runId"] / "execution-attestation.yaml"
            if path.is_file():
                try:
                    data = load(path)
                    session_id = data.get("spec", {}).get("sessionId")
                    if session_id:
                        session_owners.setdefault(session_id, []).append(expected_item["runId"])
                except Exception:
                    pass
        for session_id, owners in session_owners.items():
            if len(owners) > 1:
                errors.append(f"duplicate execution sessionId {session_id!r}: {owners!r}")

        for item in items_to_validate:
            run_dir = artifact_root / item["runId"]
            required = ["run-meta.yaml", "prompt.md", "execution-attestation.yaml", "trace.yaml", "evaluation.yaml", "patch.diff", "evidence.txt"]
            for filename in required:
                if not (run_dir / filename).is_file():
                    errors.append(f"{item['runId']}: missing {filename}")
            meta_path = run_dir / "run-meta.yaml"
            prompt_path = run_dir / "prompt.md"
            attestation_path = run_dir / "execution-attestation.yaml"
            trace_path = run_dir / "trace.yaml"
            eval_path = run_dir / "evaluation.yaml"
            if meta_path.is_file():
                run_meta = load(meta_path)
                validate(run_meta, meta_schema, str(meta_path), errors)
                metadata = run_meta.get("metadata", {})
                for field in ("runId", "blockId", "scenario", "condition"):
                    if metadata.get(field) != item[field]:
                        errors.append(f"{meta_path}: {field} does not match matrix")
                spec = run_meta.get("spec", {})
                for field in ("repetition", "executionOrder"):
                    if spec.get(field) != item[field]:
                        errors.append(f"{meta_path}: {field} does not match matrix")
                if prompt_path.is_file():
                    prompt_digest = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
                    if spec.get("promptSha256") != prompt_digest:
                        errors.append(f"{meta_path}: promptSha256 does not match prompt.md")
                workspace_id = spec.get("workspaceId")
                if workspace_id in workspace_ids:
                    errors.append(f"{meta_path}: workspaceId must be unique across runs")
                elif workspace_id:
                    workspace_ids.add(workspace_id)

            attestation = None
            if attestation_path.is_file():
                attestation = load(attestation_path)
                validate(attestation, attestation_schema, str(attestation_path), errors)
                metadata = attestation.get("metadata", {})
                for field in ("runId", "blockId", "scenario", "condition"):
                    if metadata.get(field) != item[field]:
                        errors.append(f"{attestation_path}: {field} does not match matrix")
                attested = attestation.get("spec", {})
                if attested.get("freshSession") is not True:
                    errors.append(f"{attestation_path}: freshSession must be true for a valid pilot run")
                if attested.get("crossRunFeedbackUsed") is not False:
                    errors.append(f"{attestation_path}: crossRunFeedbackUsed must be false for a valid pilot run")
                if attested.get("runtime") != pilot["spec"]["runtime"]:
                    errors.append(f"{attestation_path}: runtime does not match pilot")
                if attested.get("model") != pilot["spec"]["model"]:
                    errors.append(f"{attestation_path}: model does not match pilot")
                if attested.get("effort") != pilot["spec"]["effort"]:
                    errors.append(f"{attestation_path}: effort does not match pilot")
                try:
                    started = datetime.fromisoformat(attested.get("startedAt", "").replace("Z", "+00:00"))
                    finished = datetime.fromisoformat(attested.get("finishedAt", "").replace("Z", "+00:00"))
                    if finished <= started:
                        errors.append(f"{attestation_path}: finishedAt must be later than startedAt")
                except ValueError:
                    pass

            if trace_path.is_file():
                trace = load(trace_path)
                validate(trace, trace_schema, str(trace_path), errors)
                metadata = trace.get("metadata", {})
                for field in ("runId", "blockId", "scenario", "condition"):
                    if metadata.get(field) != item[field]:
                        errors.append(f"{trace_path}: {field} does not match matrix")
                expected_subject = execution_subject_by_condition[item["condition"]]
                subject = trace.get("executionSubject", {})
                if subject.get("kind") != expected_subject["kind"] or subject.get("name") != expected_subject["name"]:
                    errors.append(f"{trace_path}: executionSubject does not match experiment condition")
                sequences = [event.get("sequence") for event in trace.get("events", [])]
                if sequences != sorted(set(sequences)):
                    errors.append(f"{trace_path}: event sequence must be unique and strictly increasing")
                if trace.get("runtime", {}).get("name") != pilot["spec"]["runtime"]:
                    errors.append(f"{trace_path}: runtime does not match pilot")
                if trace.get("model", {}).get("id") != pilot["spec"]["model"]:
                    errors.append(f"{trace_path}: model does not match pilot")
                if trace.get("model", {}).get("effort") != pilot["spec"]["effort"]:
                    errors.append(f"{trace_path}: effort does not match pilot")
                if attestation is not None:
                    attested = attestation.get("spec", {})
                    if trace.get("runtime", {}).get("name") != attested.get("runtime"):
                        errors.append(f"{trace_path}: runtime does not match execution attestation")
                    if trace.get("model", {}).get("id") != attested.get("model"):
                        errors.append(f"{trace_path}: model does not match execution attestation")
                    if trace.get("model", {}).get("effort") != attested.get("effort"):
                        errors.append(f"{trace_path}: effort does not match execution attestation")
            if eval_path.is_file():
                evaluation = load(eval_path)
                validate(evaluation, eval_schema, str(eval_path), errors)
                metadata = evaluation.get("metadata", {})
                for field in ("runId", "blockId", "scenario", "condition"):
                    if metadata.get(field) != item[field]:
                        errors.append(f"{eval_path}: {field} does not match matrix")
                context = evaluation.get("executionContext", {})
                if context.get("runtime") != pilot["spec"]["runtime"]:
                    errors.append(f"{eval_path}: runtime does not match pilot")
                if context.get("model") != pilot["spec"]["model"]:
                    errors.append(f"{eval_path}: model does not match pilot")
                if context.get("effort") != pilot["spec"]["effort"]:
                    errors.append(f"{eval_path}: effort does not match pilot")
                if attestation is not None:
                    attested = attestation.get("spec", {})
                    if context.get("runtime") != attested.get("runtime"):
                        errors.append(f"{eval_path}: runtime does not match execution attestation")
                    if context.get("model") != attested.get("model"):
                        errors.append(f"{eval_path}: model does not match execution attestation")
                    if context.get("effort") != attested.get("effort"):
                        errors.append(f"{eval_path}: effort does not match execution attestation")
                outcome = evaluation.get("outcome", {})
                if outcome.get("acceptanceCriteriaPassed", 0) > outcome.get("acceptanceCriteriaTotal", 0):
                    errors.append(f"{eval_path}: acceptanceCriteriaPassed exceeds acceptanceCriteriaTotal")
                evidence = evaluation.get("evidence", {})
                if evidence.get("passedGates", 0) > evidence.get("requiredGates", 0):
                    errors.append(f"{eval_path}: passedGates exceeds requiredGates")
            if trace_path.is_file() and eval_path.is_file():
                trace = load(trace_path)
                evaluation = load(eval_path)
                trace_summary = trace.get("summary", {})
                efficiency = evaluation.get("efficiency", {})
                collaboration = evaluation.get("collaboration", {})
                for field in ("agentInvocations", "coordinationTransitions", "wallClockMs"):
                    if field in trace_summary and efficiency.get(field) != trace_summary[field]:
                        errors.append(f"{eval_path}: efficiency.{field} does not match trace summary")
                if collaboration.get("humanInterventions") != trace_summary.get("humanInterventions"):
                    errors.append(f"{eval_path}: humanInterventions does not match trace summary")
            for filename in ("prompt.md", "execution-attestation.yaml", "patch.diff", "evidence.txt"):
                artifact = run_dir / filename
                if artifact.is_file() and artifact.stat().st_size == 0:
                    errors.append(f"{item['runId']}: {filename} must not be empty")

    if errors:
        print("Pilot validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    if args.run_id is not None:
        mode = f"single run {args.run_id}"
    elif args.require_complete:
        mode = "complete artifacts"
    else:
        mode = "plan/matrix"
    print(f"Pilot validation passed: {mode}, expected_runs={len(expected)}.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
