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
for value in args.files:
    path = Path(value)
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data.get("kind") != "RunEvaluation":
        raise SystemExit(f"{path}: expected kind RunEvaluation")
    groups[data["metadata"]["condition"]].append(data)

def mean(values):
    return statistics.fmean(values) if values else None

result = {}
for condition, runs in sorted(groups.items()):
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
    result[condition] = {
        "runs": len(runs),
        "taskSuccessRate": mean([1 if r["outcome"]["taskSuccess"] else 0 for r in runs]),
        "regressionRate": mean([1 if r["outcome"]["regressionDetected"] else 0 for r in runs]),
        "meanHumanInterventions": mean([r["collaboration"]["humanInterventions"] for r in runs]),
        "meanTopologyAdherence": mean([r["collaboration"]["topologyAdherence"] for r in runs]),
        "meanEvidenceCompleteness": mean([r["evidence"]["completeness"] for r in runs]),
        "meanTotalTokens": mean(total_tokens),
        "meanWallClockMs": mean([r["efficiency"]["wallClockMs"] for r in runs]),
        "verifierFalseAcceptRate": mean([1 if v else 0 for v in false_accept_values])
        if false_accept_values else None,
    }

print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
