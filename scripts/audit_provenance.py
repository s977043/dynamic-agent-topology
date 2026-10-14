#!/usr/bin/env python3
"""Read-only, non-normative cross-artifact provenance audit for DAT (#57).

This audit does not replace validate_pilot.py, authenticate an attestation,
authorize a run, or change EXP-001 acceptance/evaluation decisions.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
PASS, FAIL, UNKNOWN = "PASS", "FAIL", "UNKNOWN"
REQUIRED = ("execution-attestation.yaml", "trace.yaml", "evaluation.yaml")


def load_artifact(path: Path) -> dict[str, Any] | None:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, yaml.YAMLError, UnicodeError):
        return None


def at(value: Any, *keys: str) -> Any:
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def compare(*values: Any) -> str:
    # Distinguish missing/invalid observations from a measured zero/false.
    if any(value is None or isinstance(value, (dict, list)) for value in values):
        return UNKNOWN
    if any(type(value) is not type(values[0]) for value in values):
        return FAIL
    return PASS if all(value == values[0] for value in values[1:]) else FAIL


def instant(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo is not None and parsed.utcoffset() is not None else None
    except (ValueError, OverflowError):
        return None


def compare_instants(left: Any, right: Any) -> str:
    a, b = instant(left), instant(right)
    if a is None or b is None:
        return UNKNOWN
    return PASS if a == b else FAIL


def single_event(trace: dict[str, Any] | None, event_type: str) -> dict[str, Any] | None:
    events = at(trace, "events")
    if not isinstance(events, list):
        return None
    found = [event for event in events if isinstance(event, dict) and event.get("type") == event_type]
    return found[0] if len(found) == 1 else None


def audit(attestation: dict[str, Any] | None, trace: dict[str, Any] | None,
          evaluation: dict[str, Any] | None) -> dict[str, str]:
    checks: dict[str, str] = {}
    start = single_event(trace, "start")
    finish = single_event(trace, "finish")

    for field in ("runId", "blockId", "scenario", "condition"):
        checks["metadata." + field] = compare(
            at(attestation, "metadata", field),
            at(trace, "metadata", field),
            at(evaluation, "metadata", field),
        )
    for field, trace_path, evaluation_path in (
        ("runtime", ("runtime", "name"), ("executionContext", "runtime")),
        ("model", ("model", "id"), ("executionContext", "model")),
        ("effort", ("model", "effort"), ("executionContext", "effort")),
    ):
        checks["environment." + field] = compare(
            at(attestation, "spec", field),
            at(trace, *trace_path),
            at(evaluation, *evaluation_path),
        )

    for field in ("sessionId", "freshSession", "crossRunFeedbackUsed"):
        checks["start." + field] = compare(at(attestation, "spec", field), at(start, "details", field))

    for name, att_field, event in (
        ("start.timestamp", "startedAt", start),
        ("finish.timestamp", "finishedAt", finish),
    ):
        checks[name] = compare_instants(at(attestation, "spec", att_field), at(event, "timestamp"))

    for field in ("inputTokens", "outputTokens", "wallClockMs"):
        checks["summary." + field] = compare(
            at(trace, "summary", field), at(evaluation, "efficiency", field)
        )

    return checks


def overall(checks: dict[str, str]) -> str:
    if FAIL in checks.values():
        return FAIL
    if UNKNOWN in checks.values() or not checks:
        return UNKNOWN
    return PASS


def audit_directory(directory: Path) -> dict[str, str]:
    return audit(*(load_artifact(directory / name) for name in REQUIRED))


def directories(args: argparse.Namespace) -> list[Path]:
    found = [Path(path).resolve() for path in args.run_dir]
    if args.runs_root:
        found.extend(sorted(path for path in Path(args.runs_root).resolve().iterdir() if path.is_dir()))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Independent, read-only DAT provenance comparison")
    parser.add_argument("--run-dir", action="append", default=[], help="Run artifact directory; repeatable")
    parser.add_argument("--runs-root", help="Root of multiple run directories")
    args = parser.parse_args()
    try:
        run_dirs = directories(args)
    except OSError as exc:
        parser.error(f"cannot list runs: {exc}")
    if not run_dirs:
        parser.error("provide --run-dir or --runs-root containing Run directories")

    totals = {PASS: 0, FAIL: 0, UNKNOWN: 0}
    for run_dir in run_dirs:
        checks = audit_directory(run_dir)
        verdict = overall(checks)
        totals[verdict] += 1
        print(f"{run_dir.name}: {verdict}")
        for name, result in checks.items():
            print(f"  {name}: {result}")
    print(f"SUMMARY PASSED={totals[PASS]} FAILED={totals[FAIL]} UNKNOWN={totals[UNKNOWN]}")
    print("OBSERVATIONAL ONLY: matching self-reported artifacts is not independent attestation.")
    # Exit code is not a pilot acceptance gate. UNKNOWN is visible, not silently PASS.
    return 1 if totals[FAIL] else 0


if __name__ == "__main__":
    raise SystemExit(main())
