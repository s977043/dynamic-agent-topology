#!/usr/bin/env python3
"""Save validated RunObservation records to a store, or summarize a store.

  python scripts/run_observation.py save <record.yaml> --store <dir>
  python scripts/run_observation.py sum --store <dir> [--store <dir> ...]

--store may be omitted when DAT_OBSERVATION_STORE is set. sum with several
--store options counts them together and checks observationId across all of
them. A store inside this
repository or any git working tree (a .git in the store or an ancestor) is
refused so that observation records are never committed.
Records are saved as <store>/<metadata.project>/<metadata.observationId>.yaml;
project and observationId must be single safe file-name elements, and an
observationId already present anywhere in the store (as a file name or as a
stored metadata.observationId) is refused; save is also refused while any YAML
file in the store cannot be read or parsed. sum counts only
<store>/<project>/*.yaml and warns about YAML files at any other depth
(docs/OBSERVATION_MEASUREMENT.md).

Exit codes: save returns 0 when stored and 1 when refused. sum returns 0 when
every file was counted, 1 when tables were printed but invalid files were
skipped or when counted records share an observationId (no tables), and 2 when a store does not exist. Both return 2 on a bad --store.
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
SOURCES = ("spec-change", "human-return", "review-finding", "ci-failure", "self-correction", "unknown")
EXCLUSIONS = ("count unknown", "no breakdown (v1alpha1)", "no breakdown", "source counts unknown")


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


def stored_observation_id(path):
    """Return (observationId or None, read error or None) for a stored YAML file."""
    try:
        record = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        return None, " ".join(str(error).splitlines())
    metadata = record.get("metadata") if isinstance(record, dict) else None
    return (metadata.get("observationId") if isinstance(metadata, dict) else None), None


def save(path, store):
    record, errors = vro.load_record(path, vro.load_validator())
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
    resolved_dest = dest.resolve()
    if store not in resolved_dest.parents:
        print(f"NG\n- destination resolves outside the store: {dest}")
        return 1
    if any((path / ".git").exists() for path in resolved_dest.parents):
        print(f"NG\n- destination must be outside any git working tree: {dest}")
        return 1
    existing = []
    unreadable = []
    for stored in sorted(store.rglob("*.yaml")) if store.is_dir() else []:
        stored_id, error = stored_observation_id(stored)
        if error:
            unreadable.append(f"- cannot check for duplicate observationId: {stored}: {error}")
        elif stored.stem == meta["observationId"] or stored_id == meta["observationId"]:
            existing.append(stored)
    if unreadable:
        print("NG")
        print("\n".join(unreadable))
        return 1
    if existing:
        print(f"NG\n- observationId already recorded: {existing[0]}")
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
    for warning in vro.record_warnings(record):
        print(f"warning: {warning}")
    return 0


def source_breakdown(record):
    """Return (sources, None) when the breakdown is counted, or (None, exclusion reason).

    Rows of docs/RUN_OBSERVATION_DESIGN.md section 5.5.8 for a valid record.
    """
    rework = record["rework"]
    if rework["count"] == "unknown":
        return None, "count unknown"
    if rework["count"] == 0:
        return {}, None
    if record["apiVersion"] == "dat/v1alpha1":
        return None, "no breakdown (v1alpha1)"
    if "sources" not in rework:
        return None, "no breakdown"
    if "unknown" in rework["sources"].values():
        return None, "source counts unknown"
    return rework["sources"], None


def summarize(stores):
    missing = [store for store in stores if not store.is_dir()]
    if missing:
        print("NG")
        for store in missing:
            print(f"- store does not exist: {store}")
        return 2
    validator = vro.load_validator()

    def shown(store, path):
        relative = path.relative_to(store)
        return relative if len(stores) == 1 else store / relative

    records = []
    skipped = 0
    for store in stores:
        for path in sorted(store.rglob("*.yaml")):
            if len(path.relative_to(store).parts) != 2:
                print(f"warning: not counted (outside <project>/<observationId>.yaml): {cell(shown(store, path))}")
        for path in sorted(store.glob("*/*.yaml")):
            record, errors = vro.load_record(path, validator)
            if errors:
                print(f"skipped invalid: {shown(store, path)}: {cell(errors[0])}")
                skipped += 1
                continue
            records.append((shown(store, path), record))
    paths_by_id = {}
    for path, record in records:
        paths_by_id.setdefault(record["metadata"]["observationId"], []).append(path)
    duplicates = {key: paths for key, paths in paths_by_id.items() if len(paths) > 1}
    if duplicates:
        print("NG")
        for key, paths in sorted(duplicates.items()):
            print(f"- duplicate observationId {cell(key)}: {', '.join(cell(p) for p in paths)}")
        return 1
    records = [record for _, record in records]
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
        print("\nrework by source (all apiVersions, all periods; docs/RUN_OBSERVATION_DESIGN.md section 5.5.8)")
        print(
            "\n| topology | breakdown known / waves | "
            + " | ".join(f"excluded: {reason}" for reason in EXCLUSIONS)
            + " | "
            + " | ".join(f"source: {source}" for source in SOURCES)
            + " |\n|"
            + "---|" * (2 + len(EXCLUSIONS) + len(SOURCES))
        )
        for topology in sorted({r["topologyEquivalent"] for r in records}):
            group = [source_breakdown(r) for r in records if r["topologyEquivalent"] == topology]
            included = [sources for sources, _ in group if sources is not None]
            excluded = Counter(reason for _, reason in group if reason is not None)
            totals = [sum(sources.get(source, 0) for sources in included) for source in SOURCES]
            print(
                f"| {cell(topology)} | {len(included)}/{len(group)} | "
                + " | ".join(str(excluded[reason]) for reason in EXCLUSIONS)
                + " | "
                + " | ".join(str(total) for total in totals)
                + " |"
            )
        decisions = Counter(
            vro.normalize_decision(review["decision"])
            for r in records if r["reviews"] != "unknown" for review in r["reviews"]
        )
        print("\n| review decision (normalized) | reviews |\n|---|---|")
        for decision, count in sorted(decisions.items()):
            print(f"| {cell(decision)} | {count} |")
        print(f"\nendedAt unknown (cannot be placed in a period): {sum(r['endedAt'] == 'unknown' for r in records)}")
    print(f"\n{NOTICE}")
    return 1 if skipped else 0


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    save_parser = commands.add_parser("save", help="validate a record and store it")
    save_parser.add_argument("record")
    save_parser.add_argument("--store")
    sum_parser = commands.add_parser("sum", help="summarize stored records as Markdown tables")
    sum_parser.add_argument("--store", action="append")
    args = parser.parse_args(argv)
    try:
        if args.command == "save":
            store = resolve_store(args.store)
        else:
            stores = [resolve_store(value) for value in args.store or [None]]
    except ValueError as error:
        print(f"NG\n- {error}")
        return 2
    if args.command == "save":
        return save(args.record, store)
    return summarize(list(dict.fromkeys(stores)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
