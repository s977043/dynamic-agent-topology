#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect drift in artifacts frozen for an active DAT experiment."
    )
    parser.add_argument(
        "--manifest",
        default="experiments/EXP-001-t0-vs-t1/pilot/freeze.yaml",
    )
    args = parser.parse_args()

    manifest_path = (ROOT / args.manifest).resolve()
    try:
        manifest_path.relative_to(ROOT.resolve())
    except ValueError:
        print("Freeze validation failed: manifest escapes repository", file=sys.stderr)
        return 1

    with manifest_path.open(encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    if manifest.get("kind") != "ExperimentFreeze":
        print("Freeze validation failed: kind must be ExperimentFreeze", file=sys.stderr)
        return 1

    metadata = manifest.get("metadata", {})
    status = metadata.get("status")
    revision = metadata.get("revision")
    if status not in {"active", "completed"}:
        print(
            f"Freeze validation failed: unsupported status {status!r}; "
            "expected 'active' or 'completed'",
            file=sys.stderr,
        )
        return 1
    if not isinstance(revision, int) or revision < 1:
        print("Freeze validation failed: metadata.revision must be >= 1", file=sys.stderr)
        return 1
    if status == "completed":
        print(f"Freeze completed: revision={revision}")
        return 0

    errors = []
    seen = set()
    for item in manifest.get("spec", {}).get("files", []):
        value = item.get("path")
        expected = item.get("gitBlobSha")
        if not value or not expected:
            errors.append(f"invalid freeze entry: {item!r}")
            continue
        if value in seen:
            errors.append(f"duplicate frozen path: {value}")
            continue
        seen.add(value)

        path = (ROOT / value).resolve()
        try:
            path.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"frozen path escapes repository: {value!r}")
            continue

        if not path.is_file():
            errors.append(f"frozen artifact missing: {value}")
            continue

        actual = git_blob_sha(path)
        if actual != expected:
            errors.append(
                f"frozen artifact drift: {value} expected={expected} actual={actual}"
            )

    if not seen:
        errors.append("freeze manifest contains no files")

    if errors:
        print("EXP-001 feature freeze validation failed:")
        for error in errors:
            print(f"- {error}")
        print(
            "If this is a blocking defect, stop #15 and follow "
            "experiments/EXP-001-t0-vs-t1/pilot/FREEZE.md."
        )
        return 1

    print(f"EXP-001 feature freeze intact: {len(seen)} artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
