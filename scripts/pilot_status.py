#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RESULT_FILES = ("trace.yaml", "evaluation.yaml", "patch.diff", "evidence.txt")


def load(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def safe_repo_path(value: str):
    path = (ROOT / value).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes repository: {value!r}") from exc
    return path


def status_for(run_dir: Path):
    if not run_dir.exists():
        return "planned"
    prepared = (run_dir / "run-meta.yaml").is_file() and (run_dir / "prompt.md").is_file()
    present = [name for name in RESULT_FILES if (run_dir / name).is_file()]
    if not prepared:
        return "invalid"
    if not present:
        return "prepared"
    if len(present) < len(RESULT_FILES):
        return "in-progress"
    if any((run_dir / name).stat().st_size == 0 for name in RESULT_FILES):
        return "invalid"
    return "artifacts-present"


def main() -> int:
    parser = argparse.ArgumentParser(description="Show EXP-001 pilot run progress without claiming semantic completeness.")
    parser.add_argument("--pilot", required=True)
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    pilot_path = (ROOT / args.pilot).resolve() if not Path(args.pilot).is_absolute() else Path(args.pilot)
    matrix_path = (ROOT / args.matrix).resolve() if not Path(args.matrix).is_absolute() else Path(args.matrix)
    pilot = load(pilot_path)
    matrix = load(matrix_path)
    artifact_root = safe_repo_path(pilot["spec"]["artifactRoot"])

    rows = []
    counts = {}
    for item in matrix["spec"]["runs"]:
        state = status_for(artifact_root / item["runId"])
        counts[state] = counts.get(state, 0) + 1
        rows.append({
            "executionOrder": item["executionOrder"],
            "runId": item["runId"],
            "scenario": item["scenario"],
            "condition": item["condition"],
            "state": state,
        })

    if args.json:
        print(json.dumps({"counts": counts, "runs": rows}, ensure_ascii=False, indent=2))
        return 0

    for row in rows:
        print(
            f"{row['executionOrder']}\t{row['state']:<17}\t"
            f"{row['condition']}\t{row['scenario']}\t{row['runId']}"
        )
    print("----")
    print(" ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    print("Note: artifacts-present is not semantic completion. Use validate_pilot.py --require-complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
