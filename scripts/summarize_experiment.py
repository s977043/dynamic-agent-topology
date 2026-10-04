#!/usr/bin/env python3
from collections import defaultdict
from pathlib import Path
import argparse
import json
import statistics
import yaml

parser = argparse.ArgumentParser(description="Summarize DAT RunEvaluation YAML files by condition.")
parser.add_argument("files", nargs="+")
args = parser.parse_args()

groups = defaultdict(list)
contexts = defaultdict(set)
for value in args.files:
    path = Path(value)
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data.get("kind") != "RunEvaluation":
        raise SystemExit(f"{path}: expected kind RunEvaluation")
    experiment = data["metadata"]["experiment"]
    condition = data["metadata"]["condition"]
    context = data["executionContext"]
    context_key = (context["runtime"], context["model"], context.get("effort"))
    contexts[experiment].add(context_key)
    key = (experiment, condition)
    groups[key].append(data)

for experiment, values in contexts.items():
    if len(values) != 1:
        raise SystemExit(
            f"{experiment}: multiple execution contexts detected {sorted(values)!r}; "
            "summarize each runtime/model/effort context separately"
        )

def mean(values):
    return statistics.fmean(values) if values else None

result = {}
for (experiment, condition), runs in sorted(groups.items()):
    total_tokens = [
        r["efficiency"]["inputTokens"] + r["efficiency"]["outputTokens"]
        for r in runs
        if "inputTokens" in r["efficiency"] and "outputTokens" in r["efficiency"]
    ]
    false_accept_values = [
        r["evidence"].get("verifierFalseAccept")
        for r in runs
        if r["evidence"].get("verifierFalseAccept") is not None
    ]
    adherence_values = [
        r["collaboration"]["topologyAdherence"]
        for r in runs
        if r["collaboration"]["topologyAdherence"] is not None
    ]
    runtime, model, effort = next(iter(contexts[experiment]))
    experiment_result = result.setdefault(
        experiment,
        {
            "executionContext": {"runtime": runtime, "model": model, "effort": effort},
            "conditions": {},
        },
    )
    experiment_result["conditions"][condition] = {
        "runs": len(runs),
        "taskSuccessRate": mean([1 if r["outcome"]["taskSuccess"] else 0 for r in runs]),
        "regressionRate": mean([1 if r["outcome"]["regressionDetected"] else 0 for r in runs]),
        "meanHumanInterventions": mean([r["collaboration"]["humanInterventions"] for r in runs]),
        "meanTopologyAdherence": mean(adherence_values),
        "meanEvidenceCompleteness": mean([r["evidence"]["completeness"] for r in runs]),
        "meanTotalTokens": mean(total_tokens),
        "meanWallClockMs": mean([r["efficiency"]["wallClockMs"] for r in runs]),
        "verifierFalseAcceptRate": mean([1 if v else 0 for v in false_accept_values])
        if false_accept_values else None,
    }

print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
