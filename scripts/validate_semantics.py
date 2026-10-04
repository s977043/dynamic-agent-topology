#!/usr/bin/env python3
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)

errors = []

def index_named(paths, kind):
    indexed = {}
    for path in sorted(paths):
        data = load(path)
        name = data["metadata"]["name"]
        if name in indexed:
            errors.append(f"{path}: duplicate {kind} name {name!r}; first defined in {indexed[name]['path']}")
            continue
        indexed[name] = {"path": path, "data": data}
    return indexed

roles_index = index_named((ROOT / "roles").glob("*.yaml"), "role")
roles = set(roles_index)

topologies_index = index_named((ROOT / "topologies" / "canonical").glob("*.yaml"), "topology")
topologies = set(topologies_index)

for name, item in topologies_index.items():
    path = item["path"]
    data = item["data"]
    nodes = data.get("nodes", [])
    node_ids = [n["id"] for n in nodes]
    if len(node_ids) != len(set(node_ids)):
        errors.append(f"{path}: duplicate node id")
    known_nodes = set(node_ids)

    for node in nodes:
        if node["role"] not in roles:
            errors.append(f"{path}: unknown role {node['role']!r}")

    seen_edges = set()
    for edge in data.get("edges", []):
        key = (edge["from"], edge["to"], edge["relation"])
        if key in seen_edges:
            errors.append(f"{path}: duplicate edge {key!r}")
        seen_edges.add(key)
        if edge["from"] not in known_nodes:
            errors.append(f"{path}: edge.from references unknown node {edge['from']!r}")
        if edge["to"] not in known_nodes:
            errors.append(f"{path}: edge.to references unknown node {edge['to']!r}")

    for constraint in data.get("constraints", []):
        for subject in constraint.get("subjects", []):
            if subject not in known_nodes:
                errors.append(f"{path}: constraint references unknown node {subject!r}")

routing_index = index_named((ROOT / "policies" / "routing").glob("*.yaml"), "routing policy")
for name, item in routing_index.items():
    path = item["path"]
    data = item["data"]
    for rule in data.get("rules", []):
        ref = rule["topology"]
        if ref not in topologies:
            errors.append(f"{path}: routing references unknown topology {ref!r}")

escalation_index = index_named((ROOT / "policies" / "escalation").glob("*.yaml"), "escalation policy")
for name, item in escalation_index.items():
    path = item["path"]
    data = item["data"]
    ref = data["spec"]["maxTopology"]
    if ref not in topologies:
        errors.append(f"{path}: maxTopology references unknown topology {ref!r}")

runtime_index = {}
for path in sorted((ROOT / "adapters").glob("*/capabilities.yaml")):
    data = load(path)
    runtime = data["metadata"]["runtime"]
    if runtime in runtime_index:
        errors.append(f"{path}: duplicate runtime manifest {runtime!r}")
    runtime_index[runtime] = path

example_root = ROOT / "examples" / "brownfield" / ".dat"
project = load(example_root / "project.yaml")
supported = set(project["spec"].get("supportedTopologies", []))
default = project["spec"]["defaultTopology"]

if default not in topologies:
    errors.append(f"project binding: unknown defaultTopology {default!r}")
if supported and default not in supported:
    errors.append(f"project binding: defaultTopology {default!r} is not in supportedTopologies")
for ref in supported:
    if ref not in topologies:
        errors.append(f"project binding: unknown supported topology {ref!r}")
for runtime in project["spec"].get("runtimes", []):
    if runtime not in runtime_index:
        errors.append(f"project binding: unknown runtime {runtime!r}")

policy = load(example_root / "policy.yaml")
policy_spec = policy["spec"]
routing_ref = policy_spec.get("routingPolicy")
if routing_ref and routing_ref not in routing_index:
    errors.append(f"project policy: unknown routingPolicy {routing_ref!r}")

escalation_ref = policy_spec.get("escalationPolicy")
if escalation_ref and escalation_ref not in escalation_index:
    errors.append(f"project policy: unknown escalationPolicy {escalation_ref!r}")

max_topology = policy_spec.get("escalation", {}).get("maxTopology")
if max_topology and max_topology not in topologies:
    errors.append(f"project policy: unknown maxTopology {max_topology!r}")
if max_topology and supported and max_topology not in supported:
    errors.append(f"project policy: maxTopology {max_topology!r} is not supported by project")

if routing_ref and routing_ref in routing_index and supported:
    targets = {r["topology"] for r in routing_index[routing_ref]["data"].get("rules", [])}
    unsupported_targets = sorted(targets - supported)
    if unsupported_targets:
        errors.append(
            f"project policy: routingPolicy {routing_ref!r} can select unsupported topologies {unsupported_targets!r}"
        )

if errors:
    print("Semantic validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print(
    "Semantic validation passed: "
    f"{len(roles)} roles, {len(topologies)} topologies, "
    f"{len(routing_index)} routing policies, {len(escalation_index)} escalation policies, "
    f"{len(runtime_index)} runtime manifests."
)
