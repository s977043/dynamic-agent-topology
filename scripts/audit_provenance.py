#!/usr/bin/env python3
"""Read-only, non-normative provenance consistency audit; never changes EXP-001 acceptance."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import yaml

MISSING = object()


def field(value: object, *keys: str) -> object:
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return MISSING
        value = value[key]
    return MISSING if value is None else value


def unique_worker_event(trace: dict, kind: str) -> object:
    events = trace.get("events")
    if not isinstance(events, list):
        return MISSING
    hits = [event for event in events if isinstance(event, dict)
            and event.get("type") == kind and event.get("actor") == "worker"]
    return hits[0] if len(hits) == 1 else MISSING


def instant(value: object) -> object:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return MISSING
    else:
        return MISSING
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return MISSING
    return parsed.astimezone(timezone.utc)


def compare(left: object, right: object, *, timestamp: bool = False) -> str:
    if timestamp:
        left, right = instant(left), instant(right)
    if left is MISSING or right is MISSING:
        return "UNKNOWN"
    if type(left) is not type(right) or isinstance(left, (dict, list)):
        return "UNKNOWN"
    return "PASS" if left == right else "FAIL"


def audit(attestation: dict, trace: dict, evaluation: dict) -> dict:
    spec = field(attestation, "spec")
    if not isinstance(spec, dict):
        spec = {}
    start, finish = unique_worker_event(trace, "start"), unique_worker_event(trace, "finish")
    checks = {
        "worker_session_id": compare(field(start, "details", "sessionId"), field(spec, "sessionId")),
        "fresh_session": compare(field(start, "details", "freshSession"), field(spec, "freshSession")),
        "cross_run_feedback": compare(field(start, "details", "crossRunFeedbackUsed"),
                                      field(spec, "crossRunFeedbackUsed")),
        "start_timestamp": compare(field(start, "timestamp"), field(spec, "startedAt"), timestamp=True),
        "finish_timestamp": compare(field(finish, "timestamp"), field(spec, "finishedAt"), timestamp=True),
        "input_tokens": compare(field(trace, "summary", "inputTokens"), field(evaluation, "efficiency", "inputTokens")),
        "output_tokens": compare(field(trace, "summary", "outputTokens"), field(evaluation, "efficiency", "outputTokens")),
        "wall_clock_ms": compare(field(trace, "summary", "wallClockMs"), field(evaluation, "efficiency", "wallClockMs")),
        "runtime": compare(field(trace, "runtime", "name"), field(spec, "runtime")),
        "model": compare(field(trace, "model", "id"), field(spec, "model")),
        "effort": compare(field(trace, "model", "effort"), field(spec, "effort")),
    }
    status = "FAIL" if "FAIL" in checks.values() else "UNKNOWN" if "UNKNOWN" in checks.values() else "PASS"
    return {"verdict": status, "checks": checks}


def audit_directory(directory: Path) -> dict:
    documents = []
    for name in ("execution-attestation.yaml", "trace.yaml", "evaluation.yaml"):
        path = directory / name
        if path.is_symlink():
            raise ValueError(f"symlink input disallowed: {name}")
        with path.open(encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
        if not isinstance(document, dict):
            raise ValueError(f"invalid YAML mapping: {name}")
        documents.append(document)
    result = audit(*documents)
    # Run identity in this report is a self-reported label, not independently verified provenance.
    run_id = field(documents[1], "metadata", "runId")
    result["runId"] = run_id if isinstance(run_id, str) else "UNKNOWN"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-dir", type=Path)
    group.add_argument("--artifact-root", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.run_dir:
            directories = [args.run_dir]
        else:
            directories = sorted(path for path in args.artifact_root.iterdir()
                                 if path.name.startswith("EXP-001-") and path.is_dir() and not path.is_symlink())
        if not directories:
            raise ValueError("no Run Artifact directories found")
        results = []
        for directory in directories:
            item = audit_directory(directory)
            item["directory"] = str(directory)
            results.append(item)
    except (OSError, yaml.YAMLError, ValueError) as error:
        print(f"Audit input error: {error}", file=sys.stderr)
        return 2
    counts = {key: sum(item["verdict"] == key for item in results)
              for key in ("PASS", "FAIL", "UNKNOWN")}
    print(json.dumps({"nonNormative": True, "counts": counts, "runs": results},
                     ensure_ascii=False, indent=2))
    # Exit=0 means the report was produced, NOT that the Run was accepted.
    # Exit=2 means malformed/unreadable input. Decisions belong to independent Reviewers/Humans.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
