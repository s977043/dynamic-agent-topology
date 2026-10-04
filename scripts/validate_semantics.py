#!/usr/bin/env python3
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)

errors = []

role_files = sorted((ROOT / "roles").glob("*.yaml"))
roles = {load(p)["metadata"]["name"] for p in role_files}

topology_files = sorted((ROOT / "topologies" / "canonical").glob("*.yaml"))
topologies = {}
for path in topology_files:
    data = load(path)
    name = data["metadata"]["name"]
    topologies[name] = data
    nodes = data.get("nodes", [])
    node_ids = [n["id"] for n in nodes]
    if len(node_ids) != len(set(node_ids)):
        errors.append(f"{path}: duplicate node id")
    known_nodes = set(node_ids)
    for node in nodes:
        if node["role"] not in roles:
            errors.append(f"{path}: unknown role {node['role']!r}")
    for edge in data.get("edges", []):
        if edge["from"] not in known_nodes:
            errors.append(f"{path}: edge.from references unknown node {edge['from']!r}")
        if edge["to"] not in known_nodes:
            errors.append(f"{path}: edge.to references unknown node {edge['to']!r}")
    for constraint in data.get("constraints", []):
        for subject in constraint.get("subjects", []):
            if subject not in known_nodes:
                errors.append(f"{path}: constraint references unknown node {subject!r}")

routing_files = sorted((ROOT / "policies" / "routing").glob("*.yaml"))
routing_names = set()
for path in routing_files:
    data = load(path)
    routing_names.add(data["metadata"]["name"])
    for rule in data.get("rules", []):
        ref = rule["topology"]
        if ref not in topologies:
            errors.append(f"{path}: routing references unknown topology {ref!r}")

for path in sorted((ROOT / "policies" / "escalation").glob("*.yaml")):
    data = load(path)
    ref = data["spec"]["maxTopology"]
    if ref not in topologies:
        errors.append(f"{path}: maxTopology references unknown topology {ref!r}")

example_root = ROOT / "examples" / "brownfield" / ".dat"
project = load(example_root / "project.yaml")
supported = set(project["spec"].get("supportedTopologies", []))
default = project["spec"]["defaultTopology"]
if default not in topologies:
    errors.append(f"project binding: unknown defaultTopology {default!r}")
for ref in supported:
    if ref not in topologies:
        errors.append(f"project binding: unknown supported topology {ref!r}")

policy = load(example_root / "policy.yaml")
routing_ref = policy["spec"]["routingPolicy"]
if routing_ref not in routing_names:
    errors.append(f"project policy: unknown routingPolicy {routing_ref!r}")
max_topology = policy["spec"].get("escalation", {}).get("maxTopology")
if max_topology and max_topology not in topologies:
    errors.append(f"project policy: unknown maxTopology {max_topology!r}")

if errors:
    print("Semantic validation failed:")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print(f"Semantic validation passed: {len(roles)} roles, {len(topologies)} topologies, {len(routing_names)} routing policies.")
