#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "yes", "1"}:
        return True
    if normalized in {"false", "no", "0"}:
        return False
    raise argparse.ArgumentTypeError("expected true/false")


def parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone offset")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Record post-run execution attestation from observed operator/runtime facts."
    )
    parser.add_argument("--pilot", required=True)
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--session-id", required=True, help="Opaque non-secret ID assigned to the actual runtime session.")
    parser.add_argument("--fresh-session", required=True, type=parse_bool)
    parser.add_argument("--cross-run-feedback-used", required=True, type=parse_bool)
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", required=True, choices=["low","medium","high","xhigh","max"])
    parser.add_argument("--started-at", required=True)
    parser.add_argument("--finished-at", required=True)
    args = parser.parse_args()

    pilot_path = (ROOT / args.pilot).resolve() if not Path(args.pilot).is_absolute() else Path(args.pilot).resolve()
    matrix_path = (ROOT / args.matrix).resolve() if not Path(args.matrix).is_absolute() else Path(args.matrix).resolve()

    try:
        pilot = load(pilot_path)
        matrix = load(matrix_path)
        started = parse_datetime(args.started_at)
        finished = parse_datetime(args.finished_at)
        if finished <= started:
            raise ValueError("finished-at must be later than started-at")

        entry = next((item for item in matrix["spec"]["runs"] if item["runId"] == args.run_id), None)
        if entry is None:
            raise ValueError(f"unknown runId {args.run_id!r}")

        artifact_root = (ROOT / pilot["spec"]["artifactRoot"]).resolve()
        artifact_root.relative_to(ROOT.resolve())
        run_dir = artifact_root / args.run_id
        meta_path = run_dir / "run-meta.yaml"
        prompt_path = run_dir / "prompt.md"
        attestation_path = run_dir / "execution-attestation.yaml"
        if not meta_path.is_file() or not prompt_path.is_file():
            raise ValueError("run must be prepared before execution can be attested")
        if attestation_path.exists():
            raise ValueError(f"execution attestation already exists: {attestation_path}")

        run_meta = load(meta_path)
        metadata = run_meta.get("metadata", {})
        for field in ("runId","blockId","scenario","condition"):
            if metadata.get(field) != entry[field]:
                raise ValueError(f"run-meta {field} does not match matrix")

        expected_prompt_hash = run_meta.get("spec", {}).get("promptSha256")
        actual_prompt_hash = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
        if expected_prompt_hash != actual_prompt_hash:
            raise ValueError("prompt hash does not match prepared run metadata")

        existing_sessions = set()
        for path in artifact_root.glob("*/execution-attestation.yaml"):
            data = load(path)
            session_id = data.get("spec", {}).get("sessionId")
            if session_id:
                existing_sessions.add(session_id)
        if args.session_id in existing_sessions:
            raise ValueError(f"sessionId already used by another run: {args.session_id!r}")

        attestation = {
            "apiVersion": "dat/v1alpha1",
            "kind": "PilotExecutionAttestation",
            "metadata": {
                "runId": entry["runId"],
                "blockId": entry["blockId"],
                "scenario": entry["scenario"],
                "condition": entry["condition"],
            },
            "spec": {
                "sessionId": args.session_id.strip(),
                "freshSession": args.fresh_session,
                "crossRunFeedbackUsed": args.cross_run_feedback_used,
                "runtime": args.runtime.strip(),
                "model": args.model.strip(),
                "effort": args.effort,
                "startedAt": args.started_at,
                "finishedAt": args.finished_at,
            },
        }
        if not attestation["spec"]["sessionId"]:
            raise ValueError("session-id must be non-empty")

        attestation_path.write_text(
            yaml.safe_dump(attestation, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        print(f"Recorded execution attestation for {args.run_id}")
        print(f"Attestation: {attestation_path}")
        return 0
    except Exception as exc:
        print(f"Attest pilot run failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
