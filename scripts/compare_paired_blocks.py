#!/usr/bin/env python3
"""Compare a baseline and a candidate condition per paired block of RunEvaluation files.

Blocks are keyed by (experiment, scenario, blockId) as in docs/EXPERIMENTS.md and
scripts/validate_experiments.py. Missing values and zero denominators are reported
as null with a reason; they are never filled with 0 or estimates.
"""
from pathlib import Path
import argparse
import json
import statistics
import sys
from jsonschema import Draft202012Validator
import yaml

ROOT = Path(__file__).resolve().parents[1]
EVALUATION_SCHEMA = ROOT / "schemas" / "evaluation.schema.json"


def load(path):
    try:
        with Path(path).open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise ValueError(f"{path}: cannot read YAML: {error}") from error
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a YAML mapping")
    return data


def load_evaluation(path, validator):
    data = load(path)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if errors:
        details = "; ".join(f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in errors)
        raise ValueError(f"{path}: not a valid RunEvaluation: {details}")
    return data


def check_experiment_spec(spec, path):
    try:
        name = spec["metadata"]["name"]
        ids = [item["id"] for item in spec["spec"]["conditions"]]
        controls = spec["spec"]["controls"]
    except (KeyError, TypeError) as error:
        raise ValueError(f"{path}: missing experiment structure: {error!r}") from error
    if not isinstance(name, str) or not isinstance(controls, dict) or not all(isinstance(i, str) for i in ids):
        raise ValueError(f"{path}: invalid experiment metadata.name, spec.conditions, or spec.controls")
    return spec


def load_json_schema():
    with EVALUATION_SCHEMA.open(encoding="utf-8") as f:
        return json.load(f)


def find_experiment_spec(name):
    for path in sorted((ROOT / "experiments").glob("EXP-*/experiment.yaml")):
        if load(path)["metadata"]["name"] == name:
            return path
    return None


def total_tokens(evaluation):
    efficiency = evaluation["efficiency"]
    if "inputTokens" in efficiency and "outputTokens" in efficiency:
        return efficiency["inputTokens"] + efficiency["outputTokens"]
    return None


def metrics(evaluation):
    return {
        "taskSuccess": 1 if evaluation["outcome"]["taskSuccess"] else 0,
        "regressionDetected": 1 if evaluation["outcome"]["regressionDetected"] else 0,
        "humanInterventions": evaluation["collaboration"]["humanInterventions"],
        "boundaryViolations": evaluation["collaboration"]["boundaryViolations"],
        "totalTokens": total_tokens(evaluation),
        "wallClockMs": evaluation["efficiency"]["wallClockMs"],
    }


def ratio(numerator, denominator, label):
    if numerator is None or denominator is None:
        return None, f"{label}: value missing"
    if denominator == 0:
        return None, f"{label}: zero denominator"
    return numerator / denominator, None


def block_problems(runs, expected_conditions, controls):
    problems = []
    conditions = [r["metadata"]["condition"] for r in runs]
    duplicates = sorted({c for c in conditions if conditions.count(c) > 1})
    if duplicates:
        problems.append(f"duplicate conditions {duplicates}")
    if set(conditions) != expected_conditions:
        problems.append(f"conditions {sorted(set(conditions))}, expected {sorted(expected_conditions)}")
    contexts = [r["executionContext"] for r in runs]
    if controls.get("sameRuntime") and len({c["runtime"] for c in contexts}) != 1:
        problems.append("mixes runtimes")
    if controls.get("sameModel") and len({c["model"] for c in contexts}) != 1:
        problems.append("mixes models")
    if controls.get("sameEffort"):
        efforts = [c.get("effort") for c in contexts]
        if any(value is None for value in efforts):
            problems.append("requires effort values")
        elif len(set(efforts)) != 1:
            problems.append("mixes effort levels")
    return problems


def compare(evaluations, experiment_spec, baseline, candidate, exclusions):
    experiment = experiment_spec["metadata"]["name"]
    expected_conditions = {item["id"] for item in experiment_spec["spec"]["conditions"]}
    for condition in (baseline, candidate):
        if condition not in expected_conditions:
            raise ValueError(f"condition {condition!r} is not defined in {experiment}")
    if baseline == candidate:
        raise ValueError("baseline and candidate must differ")
    controls = experiment_spec["spec"]["controls"]

    blocks = {}
    for evaluation in evaluations:
        metadata = evaluation["metadata"]
        if metadata["experiment"] != experiment:
            raise ValueError(f"{metadata['runId']}: experiment {metadata['experiment']!r} is not {experiment!r}")
        key = (metadata["scenario"], metadata["blockId"])
        blocks.setdefault(key, []).append(evaluation)

    unknown = sorted(set(exclusions) - {block_id for _, block_id in blocks})
    if unknown:
        raise ValueError(f"excluded blocks not found in input: {unknown}")

    paired, invalid, excluded = [], [], []
    included_runs = {baseline: [], candidate: []}
    for (scenario, block_id), runs in sorted(blocks.items()):
        entry = {"scenario": scenario, "blockId": block_id, "runIds": sorted(r["metadata"]["runId"] for r in runs)}
        if block_id in exclusions:
            excluded.append({**entry, "reason": exclusions[block_id]})
            continue
        problems = block_problems(runs, expected_conditions, controls)
        if problems:
            invalid.append({**entry, "reasons": problems})
            continue
        by_condition = {r["metadata"]["condition"]: r for r in runs}
        base, cand = metrics(by_condition[baseline]), metrics(by_condition[candidate])
        included_runs[baseline].append(base)
        included_runs[candidate].append(cand)
        delta, nulls = {}, []
        for name in base:
            if base[name] is None or cand[name] is None:
                delta[name] = None
                nulls.append(f"delta.{name}: value missing")
            else:
                delta[name] = cand[name] - base[name]
        token_ratio, reason = ratio(cand["totalTokens"], base["totalTokens"], "totalTokensRatio")
        nulls += [reason] if reason else []
        wall_ratio, reason = ratio(cand["wallClockMs"], base["wallClockMs"], "wallClockMsRatio")
        nulls += [reason] if reason else []
        paired.append({
            **entry,
            "baseline": base,
            "candidate": cand,
            "delta": delta,
            "totalTokensRatio": token_ratio,
            "wallClockMsRatio": wall_ratio,
            "nullReasons": nulls,
        })

    def condition_means(rows):
        means, nulls = {}, []
        for name in ("taskSuccess", "regressionDetected", "humanInterventions", "boundaryViolations",
                     "totalTokens", "wallClockMs"):
            values = [row[name] for row in rows if row[name] is not None]
            means[name] = statistics.fmean(values) if values else None
            means[f"{name}Runs"] = len(values)
            if not values:
                nulls.append(f"{name}: no values")
        means["nullReasons"] = nulls
        return means

    base_means = condition_means(included_runs[baseline])
    cand_means = condition_means(included_runs[candidate])
    ratio_nulls = []
    mean_token_ratio, reason = ratio(cand_means["totalTokens"], base_means["totalTokens"], "meanTotalTokensRatio")
    ratio_nulls += [reason] if reason else []
    mean_wall_ratio, reason = ratio(cand_means["wallClockMs"], base_means["wallClockMs"], "meanWallClockMsRatio")
    ratio_nulls += [reason] if reason else []

    return {
        "experiment": experiment,
        "baseline": baseline,
        "candidate": candidate,
        "pairedBlockCount": len(paired),
        "invalidBlockCount": len(invalid),
        "excludedBlockCount": len(excluded),
        "status": "INCONCLUSIVE" if not paired else ("PARTIAL" if invalid else "PAIRED"),
        "conditionMeans": {baseline: base_means, candidate: cand_means},
        "meanTotalTokensRatio": mean_token_ratio,
        "meanWallClockMsRatio": mean_wall_ratio,
        "ratioNullReasons": ratio_nulls,
        "pairedBlocks": paired,
        "invalidBlocks": invalid,
        "excludedBlocks": excluded,
    }


def parse_exclusion(value):
    block_id, sep, reason = value.partition("=")
    if not sep or not block_id or not reason.strip():
        raise argparse.ArgumentTypeError("--exclude must be BLOCK_ID=REASON with a non-empty reason")
    return block_id, reason.strip()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", help="RunEvaluation YAML files of one experiment")
    parser.add_argument("--baseline", required=True, help="baseline condition id")
    parser.add_argument("--candidate", required=True, help="candidate condition id")
    parser.add_argument("--experiment-spec", help="experiment.yaml (default: found by name under experiments/)")
    parser.add_argument("--exclude", action="append", default=[], type=parse_exclusion,
                        metavar="BLOCK_ID=REASON", help="exclude a block; the reason is kept in the output")
    args = parser.parse_args(argv)

    try:
        validator = Draft202012Validator(load_json_schema())
        evaluations = [load_evaluation(value, validator) for value in args.files]
        names = {e["metadata"]["experiment"] for e in evaluations}
        if len(names) != 1:
            raise ValueError(f"input mixes experiments {sorted(names)}; compare one experiment at a time")
        spec_path = Path(args.experiment_spec) if args.experiment_spec else find_experiment_spec(next(iter(names)))
        if spec_path is None:
            raise ValueError(f"experiment spec for {next(iter(names))!r} not found; pass --experiment-spec")
        exclusions = dict(args.exclude)
        if len(exclusions) != len(args.exclude):
            raise ValueError("a block is excluded more than once")
        spec = check_experiment_spec(load(spec_path), spec_path)
        result = compare(evaluations, spec, args.baseline, args.candidate, exclusions)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
