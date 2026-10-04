#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]

def load(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)

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
    args = parser.parse_args()

    pilot_path = (ROOT / args.pilot).resolve() if not Path(args.pilot).is_absolute() else Path(args.pilot)
    matrix_path = (ROOT / args.matrix).resolve() if not Path(args.matrix).is_absolute() else Path(args.matrix)
    errors = []

    pilot = load(pilot_path)
    matrix = load(matrix_path)
    validate(pilot, ROOT / "schemas" / "pilot.schema.json", str(pilot_path), errors)

    experiment_name = pilot["metadata"]["experiment"]
    experiment_path = ROOT / "experiments" / "EXP-001-t0-vs-t1" / "experiment.yaml"
    experiment = load(experiment_path)
    if experiment["metadata"]["name"] != experiment_name:
        errors.append("pilot: experiment reference does not match experiment.yaml")

    if pilot["spec"]["runtime"] not in experiment["spec"]["runtimeScope"]:
        errors.append("pilot: runtime is not allowed by experiment runtimeScope")

    expected_conditions = [item["id"] for item in experiment["spec"]["conditions"]]
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

    if args.require_complete:
        artifact_root = (ROOT / pilot["spec"]["artifactRoot"]).resolve()
        trace_schema = ROOT / "schemas" / "execution-trace.schema.json"
        eval_schema = ROOT / "schemas" / "evaluation.schema.json"
        for item in expected:
            run_dir = artifact_root / item["runId"]
            required = ["trace.yaml", "evaluation.yaml", "patch.diff", "evidence.txt"]
            for filename in required:
                if not (run_dir / filename).is_file():
                    errors.append(f"{item['runId']}: missing {filename}")
            trace_path = run_dir / "trace.yaml"
            eval_path = run_dir / "evaluation.yaml"
            if trace_path.is_file():
                trace = load(trace_path)
                validate(trace, trace_schema, str(trace_path), errors)
                metadata = trace.get("metadata", {})
                for field in ("runId", "blockId", "scenario", "condition"):
                    if metadata.get(field) != item[field]:
                        errors.append(f"{trace_path}: {field} does not match matrix")
                if trace.get("runtime", {}).get("name") != pilot["spec"]["runtime"]:
                    errors.append(f"{trace_path}: runtime does not match pilot")
                if trace.get("model", {}).get("id") != pilot["spec"]["model"]:
                    errors.append(f"{trace_path}: model does not match pilot")
                if trace.get("model", {}).get("effort") != pilot["spec"]["effort"]:
                    errors.append(f"{trace_path}: effort does not match pilot")
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

    if errors:
        print("Pilot validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    mode = "complete artifacts" if args.require_complete else "plan/matrix"
    print(f"Pilot validation passed: {mode}, expected_runs={len(expected)}.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
