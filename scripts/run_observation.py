#!/usr/bin/env python3
"""Save validated RunObservation records to a store, or summarize a store.

  python scripts/run_observation.py save <record.yaml> --store <dir>
  python scripts/run_observation.py sum --store <dir>

--store may be omitted when DAT_OBSERVATION_STORE is set. A store inside this
repository or any git working tree (a .git in the store or an ancestor) is
refused so that observation records are never committed.
Records are saved as <store>/<metadata.project>/<metadata.observationId>.yaml;
project and observationId must be single safe file-name elements.

Exit codes: save returns 0 when stored and 1 when refused. sum returns 0 when
every file was counted, 1 when tables were printed but invalid files were
skipped, and 2 when the store does not exist. Both return 2 on a bad --store.
"""
from collections import Counter
from pathlib import Path
import argparse
import os
import re
import sys

import yaml

import validate_run_observation as vro

ROOT = vro.ROOT
STORE_ENV = "DAT_OBSERVATION_STORE"
NOTICE = "Observational counts only; not evidence that a topology is better."
PATH_ELEMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def cell(value):
    return " ".join(str(value).splitlines()).replace("|", "\\|")


def resolve_store(value):
    value = value or os.environ.get(STORE_ENV)
    if not value:
        raise ValueError(f"--store or {STORE_ENV} is required")
    store = Path(value).expanduser().resolve()
    if store == ROOT or ROOT in store.parents:
        raise ValueError(f"store must be outside the DAT repository: {store}")
    if any((path / ".git").exists() for path in (store, *store.parents)):
        raise ValueError(f"store must be outside any git working tree: {store}")
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


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def construct_unique_mapping(loader, node, deep=False):
    keys = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            hash(key)
        except TypeError:
            raise yaml.constructor.ConstructorError(
                None, None, "mapping key must be a scalar", key_node.start_mark
            ) from None
        if key in keys:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r}", key_node.start_mark
            )
        keys.add(key)
    return loader.construct_mapping(node, deep=deep)


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_unique_mapping)


def load_record(path, validator):
    try:
        record = yaml.load(Path(path).read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
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
    bad = [key for key in ("project", "observationId") if not PATH_ELEMENT.fullmatch(meta[key])]
    if bad:
        print("NG")
        for key in bad:
            print(f"- metadata.{key}: must match {PATH_ELEMENT.pattern} to be used as a file name")
        return 1
    dest = store / meta["project"] / f"{meta['observationId']}.yaml"
    if store not in dest.resolve().parents:
        print(f"NG\n- destination resolves outside the store: {dest}")
        return 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(dest, "x", encoding="utf-8") as handle:
            handle.write(yaml.safe_dump(record, sort_keys=False, allow_unicode=True))
    except FileExistsError:
        print(f"NG\n- observationId already recorded: {dest}")
        return 1
    unknowns = list(unknown_fields(record))
    print(f"OK {meta['observationId']} -> {dest}")
    print(f"unknown: {', '.join(unknowns) if unknowns else 'none'}")
    return 0


def summarize(store):
    if not store.is_dir():
        print(f"NG\n- store does not exist: {store}")
        return 2
    validator = vro.load_validator()
    records = []
    skipped = 0
    for path in sorted(store.glob("*/*.yaml")):
        record, errors = load_record(path, validator)
        if errors:
            print(f"skipped invalid: {path.relative_to(store)}: {cell(errors[0])}")
            skipped += 1
            continue
        records.append(record)
    print(f"observations: {len(records)}")
    if records:
        by_project = Counter((r["metadata"]["project"], r["topologyEquivalent"]) for r in records)
        by_outcome = Counter((r["topologyEquivalent"], r["outcome"]) for r in records)
        print("\n| project | topology | waves |\n|---|---|---|")
        for (project, topology), count in sorted(by_project.items()):
            print(f"| {cell(project)} | {cell(topology)} | {count} |")
        print("\n| topology | outcome | waves |\n|---|---|---|")
        for (topology, outcome), count in sorted(by_outcome.items()):
            print(f"| {cell(topology)} | {cell(outcome)} | {count} |")
        print("\n| topology | known rework / waves | rework total |\n|---|---|---|")
        for topology in sorted({r["topologyEquivalent"] for r in records}):
            group = [r for r in records if r["topologyEquivalent"] == topology]
            known = [r["rework"]["count"] for r in group if isinstance(r["rework"]["count"], int)]
            print(f"| {cell(topology)} | {len(known)}/{len(group)} | {sum(known)} |")
    print(f"\n{NOTICE}")
    return 1 if skipped else 0


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
