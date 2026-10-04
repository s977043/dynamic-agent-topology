#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import subprocess

import yaml
from jsonschema import Draft202012Validator, FormatChecker


STAGE_ORDER = {
    "A0-assess": 0,
    "A1-bind": 1,
    "A2-observe": 2,
    "A3-recommend": 3,
    "A4-canary": 4,
    "A5-dynamic": 5,
}


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def safe_project_path(project_root: Path, value: str):
    candidate = (project_root / value).resolve()
    try:
        candidate.relative_to(project_root.resolve())
    except ValueError:
        return None
    return candidate


def validate_schema(path: Path, schema_path: Path, errors: list[str]):
    try:
        data = load_yaml(path)
    except Exception as exc:
        errors.append(f"{path}: failed to parse YAML: {exc}")
        return None

    schema = load_yaml(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        location = ".".join(str(x) for x in error.path) or "<root>"
        errors.append(f"{path}: schema error at {location}: {error.message}")
    return data


def index_named(paths, key_path):
    result = {}
    for path in sorted(paths):
        data = load_yaml(path)
        value = data
        for key in key_path:
            value = value[key]
        result[value] = {"path": path, "data": data}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an external repository's .dat project binding against a DAT checkout."
    )
    parser.add_argument("--project", required=True, help="Path to the adopting project root.")
    parser.add_argument(
        "--dat-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Path to the Dynamic Agent Topology repository checkout.",
    )
    args = parser.parse_args()

    project_root = Path(args.project).resolve()
    dat_root = Path(args.dat_root).resolve()
    dat_dir = project_root / ".dat"

    errors: list[str] = []
    warnings: list[str] = []

    if not dat_dir.is_dir():
        print(f"ERROR: {dat_dir} does not exist.", file=sys.stderr)
        return 1

    required_dat_paths = [
        dat_root / "schemas",
        dat_root / "topologies" / "canonical",
        dat_root / "adapters",
        dat_root / "CITATION.cff",
    ]
    missing_dat_paths = [str(path) for path in required_dat_paths if not path.exists()]
    if missing_dat_paths:
        print("DAT checkout is incomplete:", file=sys.stderr)
        for path in missing_dat_paths:
            print(f"- ERROR: missing {path}", file=sys.stderr)
        return 1

    required_base = {
        "project.yaml": "project-binding.schema.json",
        "runtimes.yaml": "runtime-binding.schema.json",
        "dat.lock.yaml": "dat-lock.schema.json",
    }

    docs = {}
    for filename, schema_name in required_base.items():
        path = dat_dir / filename
        if not path.is_file():
            errors.append(f"{path}: required adoption artifact is missing")
            continue
        docs[filename] = validate_schema(path, dat_root / "schemas" / schema_name, errors)

    policy_path = dat_dir / "policy.yaml"
    if policy_path.is_file():
        docs["policy.yaml"] = validate_schema(
            policy_path, dat_root / "schemas" / "project-policy.schema.json", errors
        )

    evidence_path = dat_dir / "evidence.yaml"
    if evidence_path.is_file():
        docs["evidence.yaml"] = validate_schema(
            evidence_path, dat_root / "schemas" / "evidence-profile.schema.json", errors
        )

    if errors:
        print("DAT project validation failed:")
        for error in errors:
            print(f"- ERROR: {error}")
        return 1

    project = docs["project.yaml"]
    runtime_binding = docs["runtimes.yaml"]
    lock = docs["dat.lock.yaml"]
    policy = docs.get("policy.yaml")
    evidence = docs.get("evidence.yaml")

    if policy:
        stage = policy["spec"]["rolloutStage"]
    elif evidence:
        stage = "A1-bind"
    else:
        stage = "A0-assess"
    stage_value = STAGE_ORDER[stage]

    if stage_value >= STAGE_ORDER["A1-bind"] and evidence is None:
        errors.append(f"{dat_dir / 'evidence.yaml'}: required from A1 onward")
    if stage_value >= STAGE_ORDER["A3-recommend"] and policy is None:
        errors.append(f"{policy_path}: required from A3 onward")

    topologies = index_named(
        (dat_root / "topologies" / "canonical").glob("*.yaml"), ["metadata", "name"]
    )
    routing = index_named(
        (dat_root / "policies" / "routing").glob("*.yaml"), ["metadata", "name"]
    )
    escalation = index_named(
        (dat_root / "policies" / "escalation").glob("*.yaml"), ["metadata", "name"]
    )
    manifests = index_named(
        (dat_root / "adapters").glob("*/capabilities.yaml"), ["metadata", "runtime"]
    )

    default_topology = project["spec"]["defaultTopology"]
    supported_values = project["spec"].get("supportedTopologies")
    supported = set(supported_values) if supported_values else {default_topology}

    if default_topology not in topologies:
        errors.append(f"project.yaml: unknown defaultTopology {default_topology!r}")
    if default_topology not in supported:
        errors.append("project.yaml: defaultTopology must be included in supportedTopologies")
    for topology in sorted(supported):
        if topology not in topologies:
            errors.append(f"project.yaml: unknown supported topology {topology!r}")

    project_runtimes = set(project["spec"].get("runtimes", []))
    bindings = runtime_binding["spec"]["bindings"]
    binding_names = [item["runtime"] for item in bindings]
    if len(binding_names) != len(set(binding_names)):
        errors.append("runtimes.yaml: duplicate runtime binding")

    binding_set = set(binding_names)
    missing_bindings = sorted(project_runtimes - binding_set)
    if missing_bindings:
        errors.append(f"runtimes.yaml: missing bindings for project runtimes {missing_bindings!r}")

    extra_bindings = sorted(binding_set - project_runtimes)
    if extra_bindings:
        warnings.append(f"runtimes.yaml: bindings not listed in project.yaml: {extra_bindings!r}")

    for binding in bindings:
        runtime = binding["runtime"]
        if binding["mode"] == "generated":
            errors.append(
                f"runtimes.yaml: mode='generated' is not implemented in DAT v0.2.1; use mode='manual'"
            )
        if runtime not in manifests:
            errors.append(f"runtimes.yaml: unknown runtime {runtime!r}")
            continue

        manifest = manifests[runtime]["data"]
        capabilities = manifest.get("capabilities", {})
        for capability in binding.get("requiredCapabilities", []):
            entry = capabilities.get(capability)
            if entry is None:
                errors.append(
                    f"runtimes.yaml: runtime {runtime!r} does not declare required capability {capability!r}"
                )
                continue
            status = entry["status"]
            if status in {"unsupported", "unknown"}:
                errors.append(
                    f"runtimes.yaml: required capability {capability!r} for {runtime!r} is {status}"
                )
            elif status in {"experimental", "emulated", "degraded"}:
                warnings.append(
                    f"runtimes.yaml: required capability {capability!r} for {runtime!r} is {status}"
                )

        config_path = binding.get("configPath")
        if config_path:
            resolved = safe_project_path(project_root, config_path)
            if resolved is None:
                errors.append(f"runtimes.yaml: configPath escapes project root: {config_path!r}")
            elif binding["mode"] == "manual" and not resolved.exists():
                warnings.append(
                    f"runtimes.yaml: manual configPath does not exist yet: {config_path!r}"
                )

    if policy:
        spec = policy["spec"]
        routing_ref = spec.get("routingPolicy")
        escalation_ref = spec.get("escalationPolicy")

        if routing_ref:
            if routing_ref not in routing:
                errors.append(f"policy.yaml: unknown routingPolicy {routing_ref!r}")
            else:
                targets = {
                    rule["topology"] for rule in routing[routing_ref]["data"].get("rules", [])
                }
                unsupported = sorted(targets - supported)
                if unsupported:
                    errors.append(
                        f"policy.yaml: routingPolicy can select unsupported topologies {unsupported!r}"
                    )

        if escalation_ref:
            if escalation_ref not in escalation:
                errors.append(f"policy.yaml: unknown escalationPolicy {escalation_ref!r}")

        max_topology = spec.get("escalation", {}).get("maxTopology")
        if max_topology and max_topology not in supported:
            errors.append(
                f"policy.yaml: escalation.maxTopology {max_topology!r} is not supported by project"
            )

    dat_lock = lock["spec"]["dat"]
    citation_path = dat_root / "CITATION.cff"
    if citation_path.is_file():
        citation = load_yaml(citation_path)
        current_version = str(citation.get("version", ""))
        if current_version and dat_lock["version"] != current_version:
            errors.append(
                f"dat.lock.yaml: version {dat_lock['version']!r} does not match DAT checkout "
                f"version {current_version!r}"
            )

    if dat_lock["pinMode"] == "floating":
        warnings.append(
            "dat.lock.yaml: pinMode is floating; use a commit SHA or tag for reproducible CI"
        )
    else:
        revision = dat_lock["revision"]
        head_result = subprocess.run(
            ["git", "-C", str(dat_root), "rev-parse", "HEAD"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        revision_result = subprocess.run(
            ["git", "-C", str(dat_root), "rev-parse", f"{revision}^{{commit}}"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if head_result.returncode != 0:
            errors.append("dat.lock.yaml: pinned mode requires dat-root to be a Git checkout")
        elif revision_result.returncode != 0:
            errors.append(
                f"dat.lock.yaml: pinned revision {revision!r} cannot be resolved in DAT checkout"
            )
        elif head_result.stdout.strip() != revision_result.stdout.strip():
            errors.append(
                f"dat.lock.yaml: pinned revision {revision!r} does not match checked-out DAT HEAD "
                f"{head_result.stdout.strip()!r}"
            )

    gitignore_path = project_root / ".gitignore"
    if gitignore_path.is_file():
        ignored = gitignore_path.read_text(encoding="utf-8")
        for entry in (".dat/generated/", ".dat/state/"):
            if entry not in ignored:
                warnings.append(f".gitignore: recommended entry is missing: {entry}")
    else:
        warnings.append(".gitignore: file not found; .dat/generated/ and .dat/state/ should not be committed")

    if evidence:
        # Commands are declarative only. This validator intentionally never executes them.
        if not evidence.get("gates"):
            warnings.append("evidence.yaml: no evidence gates declared")

    if warnings:
        print("DAT project validation warnings:")
        for warning in warnings:
            print(f"- WARNING: {warning}")

    if errors:
        print("DAT project validation failed:")
        for error in errors:
            print(f"- ERROR: {error}")
        return 1

    print(
        "DAT project validation passed: "
        f"stage={stage}, topologies={len(supported)}, runtimes={len(binding_set)}, "
        f"evidence_gates={len(evidence.get('gates', [])) if evidence else 0}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
