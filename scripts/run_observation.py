#!/usr/bin/env python3
"""Save validated RunObservation records to a store, or summarize a store.

  python scripts/run_observation.py save <record.yaml> --store <dir>
  python scripts/run_observation.py sum --store <dir>

--store may be omitted when DAT_OBSERVATION_STORE is set. A store inside this
repository is refused so that observation records are never committed to DAT.
Records are saved as <store>/<metadata.project>/<metadata.observationId>.yaml.
"""
from collections import Counter
from pathlib import Path
import argparse
import os
import shutil
import sys

import yaml

import validate_run_observation as vro

ROOT = vro.ROOT
STORE_ENV = "DAT_OBSERVATION_STORE"
NOTICE = "Observational counts only; not evidence that a topology is better."


def resolve_store(value):
    value = value or os.environ.get(STORE_ENV)
    if not value:
        raise ValueError(f"--store or {STORE_ENV} is required")
    store = Path(value).expanduser().resolve()
    if store == ROOT or ROOT in store.parents:
        raise ValueError(f"store must be outside the DAT repository: {store}")
    return store


def unknown_fields(value, location=""):
    if value == "unknown":
        yield location or "$"
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from unknown_fields(item, f"{location}.{key}" if location else key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from unknown_fields(item, f"{location}[{index}]")


def load_record(path, validator):
    try:
        record = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        return None, [f"cannot read: {error}"]
    if not isinstance(record, dict):
        return None, ["record must be a mapping"]
    return record, vro.validate_record(record, validator)


def save(path, store):
    record, errors = load_record(path, vro.load_validator())
    if errors:
        print("NG")
        for error in errors:
            print(f"- {error}")
        return 1
    meta = record["metadata"]
    dest = store / meta["project"] / f"{meta['observationId']}.yaml"
    if dest.exists():
        print(f"NG\n- observationId already recorded: {dest}")
        return 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, dest)
    unknowns = list(unknown_fields(record))
    print(f"OK {meta['observationId']} -> {dest}")
    print(f"unknown: {', '.join(unknowns) if unknowns else 'none'}")
    return 0


def summarize(store):
    validator = vro.load_validator()
    records = []
    for path in sorted(store.glob("*/*.yaml")):
        record, errors = load_record(path, validator)
        if errors:
            print(f"skipped invalid: {path.relative_to(store)}: {errors[0]}")
            continue
        records.append(record)
    print(f"observations: {len(records)}")
    if records:
        by_project = Counter((r["metadata"]["project"], r["topologyEquivalent"]) for r in records)
        by_outcome = Counter((r["topologyEquivalent"], r["outcome"]) for r in records)
        print("\n| project | topology | waves |\n|---|---|---|")
        for (project, topology), count in sorted(by_project.items()):
            print(f"| {project} | {topology} | {count} |")
        print("\n| topology | outcome | waves |\n|---|---|---|")
        for (topology, outcome), count in sorted(by_outcome.items()):
            print(f"| {topology} | {outcome} | {count} |")
        print("\n| topology | known rework / waves | rework total |\n|---|---|---|")
        for topology in sorted({r["topologyEquivalent"] for r in records}):
            group = [r for r in records if r["topologyEquivalent"] == topology]
            known = [r["rework"]["count"] for r in group if isinstance(r["rework"]["count"], int)]
            print(f"| {topology} | {len(known)}/{len(group)} | {sum(known)} |")
    print(f"\n{NOTICE}")
    return 0


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    save_parser = commands.add_parser("save", help="validate a record and store it")
    save_parser.add_argument("record")
    save_parser.add_argument("--store")
    sum_parser = commands.add_parser("sum", help="summarize stored records as Markdown tables")
    sum_parser.add_argument("--store")
    args = parser.parse_args(argv)
    try:
        store = resolve_store(args.store)
    except ValueError as error:
        print(f"NG\n- {error}")
        return 2
    if args.command == "save":
        return save(args.record, store)
    return summarize(store)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
