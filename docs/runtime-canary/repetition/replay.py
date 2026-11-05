"""Replay trusted saved canary code, never launch models. Standard library only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def replay(source, out):
    out.mkdir(parents=True, exist_ok=False)
    names = ["task.md", "evaluate.py", "initial.py", "t0-final.py", "t1-final.py"]
    before = {name: digest(source / name) for name in names}
    plan = Path(__file__).with_name("PLAN.md")
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).parent,
                              capture_output=True, text=True, check=False)
    manifest = {
        "evidenceClass": "offline-saved-output-replay",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "repositoryHead": revision.stdout.strip() if revision.returncode == 0 else None,
        "planSha256": digest(plan), "scriptSha256": digest(Path(__file__)),
        "sourceHashesBefore": before,
        "environment": {"python": platform.python_version(), "system": platform.system(),
                        "release": platform.release(), "machine": platform.machine()},
        "missingMetrics": {"model": None, "effort": None, "tokens": None,
                           "costUsd": None, "humanAttentionSeconds": None},
        "missingReason": "No model calls or human timing; subprocess duration is scoring time only.",
        "blinding": "Opaque labels only; shared filesystem/public hashes do not enforce blinding.",
        "timeoutSeconds": 30,
    }
    write(out / "manifest.json", manifest)
    schedule = [("b01", "q7", "initial.py", 6, 1),
                ("b01", "m2", "t0-final.py", 18, 0),
                ("b01", "x9", "t1-final.py", 18, 0),
                ("b02", "k4", "initial.py", 6, 1),
                ("b02", "r8", "t1-final.py", 18, 0),
                ("b02", "v3", "t0-final.py", 18, 0)]
    write(out / "mapping.json", [{"blockId": block, "label": label, "source": name}
                                  for block, label, name, _, _ in schedule])
    observations = []
    for block, label, name, expected_pass, expected_exit in schedule:
        started = time.monotonic_ns()
        observation = {"blockId": block, "label": label, "startedMonotonicNs": started,
                       "exitCode": None, "error": None, "stderr": "", "result": None}
        try:
            if any(value is None for value in before.values()):
                raise FileNotFoundError("Required source file missing; see manifest sourceHashesBefore")
            result = subprocess.run([sys.executable, "-B", str(source / "evaluate.py"),
                                     str(source / name)], capture_output=True, text=True,
                                    timeout=30, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            observation["exitCode"] = result.returncode
            observation["stderr"] = result.stderr
            observation["stdout"] = result.stdout
            observation["result"] = json.loads(result.stdout)
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            observation["error"] = type(exc).__name__
            if isinstance(exc, subprocess.TimeoutExpired):
                observation["stdout"] = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
                observation["stderr"] = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        ended = time.monotonic_ns()
        observation["endedMonotonicNs"] = ended
        observation["durationSeconds"] = (ended - started) / 1e9
        score = observation["result"]
        observation["expectedMatched"] = (
            observation["error"] is None and observation["exitCode"] == expected_exit
            and isinstance(score, dict) and score.get("passed") == expected_pass
            and score.get("total") == 18 and score.get("failed") == 18 - expected_pass
            and score.get("oracle_sha256") == before["evaluate.py"]
            and score.get("solution_sha256") == before[name])
        write(out / (label + ".json"), observation)
        observations.append(observation)
    after = {name: digest(source / name) for name in names}
    summary = {"evidenceClass": manifest["evidenceClass"], "scoringInvocations": len(observations),
               "matched": sum(item["expectedMatched"] for item in observations),
               "sourceHashesAfter": after, "sourcesUnchanged": before == after,
               "sourceComplete": all(value is not None for value in before.values()),
               "liveAgentRuns": 0, "topologyEffect": "NOT_TESTED"}
    summary["passed"] = summary["matched"] == 6 and summary["sourcesUnchanged"] and summary["sourceComplete"]
    write(out / "summary.json", summary)
    return 0 if summary["passed"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        return replay(args.source.resolve(), args.out.resolve())
    except FileExistsError:
        print("Refusing existing output directory", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
