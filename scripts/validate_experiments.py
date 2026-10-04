#!/usr/bin/env python3
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
errors = []

def load(path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)

def safe_repo_path(value, owner_path):
    path = (ROOT / value).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError:
        errors.append(f"{owner_path}: path escapes repository: {value!r}")
        return None
    return path

topologies = {
    load(path)["metadata"]["name"]: path
    for path in sorted((ROOT / "topologies" / "canonical").glob("*.yaml"))
}
runtimes = {
    load(path)["metadata"]["runtime"]: path
    for path in sorted((ROOT / "adapters").glob("*/capabilities.yaml"))
}

experiments = {}
scenario_ids_by_experiment = {}
condition_ids_by_experiment = {}
condition_topology_by_experiment = {}

for experiment_path in sorted((ROOT / "experiments").glob("EXP-*/experiment.yaml")):
    experiment = load(experiment_path)
    name = experiment["metadata"]["name"]
    if name in experiments:
        errors.append(f"{experiment_path}: duplicate experiment name {name!r}")
        continue
    experiments[name] = experiment_path

    conditions = experiment["spec"]["conditions"]
    condition_ids = [item["id"] for item in conditions]
    if len(condition_ids) != len(set(condition_ids)):
        errors.append(f"{experiment_path}: duplicate condition id")
    condition_ids_by_experiment[name] = set(condition_ids)
    condition_topology_by_experiment[name] = {
        item["id"]: item["topologyRef"] for item in conditions
    }

    for condition in conditions:
        if condition["topologyRef"] not in topologies:
            errors.append(
                f"{experiment_path}: condition {condition['id']!r} references unknown topology "
                f"{condition['topologyRef']!r}"
            )

    for runtime in experiment["spec"].get("runtimeScope", []):
        if runtime not in runtimes:
            errors.append(f"{experiment_path}: unknown runtime {runtime!r}")

    declared_splits = [item["split"] for item in experiment["spec"]["scenarioSets"]]
    if len(declared_splits) != len(set(declared_splits)):
        errors.append(f"{experiment_path}: duplicate scenario split")
    required_splits = {"train", "test", "regression"}
    missing_splits = required_splits - set(declared_splits)
    if missing_splits:
        errors.append(f"{experiment_path}: missing scenario splits {sorted(missing_splits)!r}")

    all_scenario_ids = set()
    for item in experiment["spec"]["scenarioSets"]:
        scenario_path = safe_repo_path(item["path"], experiment_path)
        if scenario_path is None:
            continue
        if not scenario_path.is_file():
            errors.append(f"{experiment_path}: scenario set does not exist: {item['path']!r}")
            continue
        scenario_set = load(scenario_path)
        if scenario_set["metadata"]["split"] != item["split"]:
            errors.append(
                f"{scenario_path}: split {scenario_set['metadata']['split']!r} does not match "
                f"experiment declaration {item['split']!r}"
            )
        for scenario in scenario_set["spec"]["scenarios"]:
            scenario_id = scenario["id"]
            if scenario_id in all_scenario_ids:
                errors.append(f"{scenario_path}: duplicate scenario id {scenario_id!r}")
            all_scenario_ids.add(scenario_id)
            fixture_path = safe_repo_path(scenario["fixturePath"], scenario_path)
            if fixture_path is not None and not fixture_path.is_dir():
                errors.append(
                    f"{scenario_path}: fixture path does not exist for {scenario_id!r}: "
                    f"{scenario['fixturePath']!r}"
                )
    scenario_ids_by_experiment[name] = all_scenario_ids

def validate_run_ref(path, data):
    metadata = data["metadata"]
    experiment = metadata["experiment"]
    if experiment not in experiments:
        errors.append(f"{path}: unknown experiment {experiment!r}")
        return
    scenario = metadata["scenario"]
    condition = metadata["condition"]
    if scenario not in scenario_ids_by_experiment[experiment]:
        errors.append(f"{path}: unknown scenario {scenario!r} for experiment {experiment!r}")
    if condition not in condition_ids_by_experiment[experiment]:
        errors.append(f"{path}: unknown condition {condition!r} for experiment {experiment!r}")

for path in sorted((ROOT / "examples" / "experiment-run").glob("*-trace.yaml")):
    data = load(path)
    validate_run_ref(path, data)
    experiment = data["metadata"]["experiment"]
    condition = data["metadata"]["condition"]
    if experiment in condition_topology_by_experiment and condition in condition_topology_by_experiment[experiment]:
        expected = condition_topology_by_experiment[experiment][condition]
        if data["topology"] != expected:
            errors.append(f"{path}: topology {data['topology']!r} does not match condition topology {expected!r}")
    sequences = [event["sequence"] for event in data["events"]]
    if sequences != sorted(set(sequences)):
        errors.append(f"{path}: event sequence must be unique and strictly increasing")

for path in sorted((ROOT / "examples" / "experiment-run").glob("*-evaluation.yaml")):
    data = load(path)
    validate_run_ref(path, data)
    outcome = data["outcome"]
    if outcome["acceptanceCriteriaPassed"] > outcome["acceptanceCriteriaTotal"]:
        errors.append(f"{path}: acceptanceCriteriaPassed exceeds acceptanceCriteriaTotal")
    evidence = data["evidence"]
    if evidence["passedGates"] > evidence["requiredGates"]:
        errors.append(f"{path}: passedGates exceeds requiredGates")

if errors:
    print("Experiment semantic validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print(
    "Experiment semantic validation passed: "
    f"{len(experiments)} experiments, "
    f"{sum(len(v) for v in scenario_ids_by_experiment.values())} scenarios."
)
