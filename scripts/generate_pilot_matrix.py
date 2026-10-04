#!/usr/bin/env python3
from pathlib import Path
import argparse
import yaml

ROOT = Path(__file__).resolve().parents[1]

parser = argparse.ArgumentParser(description="Generate the deterministic run matrix for a DAT pilot.")
parser.add_argument("--pilot", required=True)
args = parser.parse_args()

pilot_path = (ROOT / args.pilot).resolve() if not Path(args.pilot).is_absolute() else Path(args.pilot)
with pilot_path.open(encoding="utf-8") as f:
    pilot = yaml.safe_load(f)

runs = []
for scenario in pilot["spec"]["scenarios"]:
    for repetition in range(1, pilot["spec"]["repetitions"] + 1):
        block_id = f"EXP-001-{scenario['id']}-r{repetition:02d}"
        for condition in pilot["spec"]["conditions"]:
            runs.append({
                "runId": f"{block_id}-{condition}",
                "blockId": block_id,
                "scenario": scenario["id"],
                "split": scenario["split"],
                "condition": condition,
                "repetition": repetition,
            })

result = {
    "apiVersion": "dat/v1alpha1",
    "kind": "PilotRunMatrix",
    "metadata": {
        "name": pilot["metadata"]["name"],
        "experiment": pilot["metadata"]["experiment"],
    },
    "spec": {"expectedRuns": len(runs), "runs": runs},
}
print(yaml.safe_dump(result, sort_keys=False, allow_unicode=True), end="")
