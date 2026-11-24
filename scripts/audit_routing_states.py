#!/usr/bin/env python3
"""Report finite, fully-known R0 routing examples without changing the policy.

This is a diagnostic abstraction, not an authorization gate or proof of runtime code.
"""

import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
OTHER = "__OTHER_KNOWN_VALUE__"


def load_rules(path):
    with path.open(encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict) or not isinstance(data.get("rules"), list) or not data["rules"]:
        raise ValueError("routing policy must contain a nonempty rules list")
    rules = data["rules"]
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict) or not isinstance(rule.get("when"), dict) or not rule["when"]:
            raise ValueError(f"rule {i}: 'when' must be a nonempty object")
        if not isinstance(rule.get("topology"), str) or not rule["topology"]:
            raise ValueError(f"rule {i}: 'topology' must be a nonempty string")
        for field, value in rule["when"].items():
            if not isinstance(field, str) or not isinstance(value, str) or value == OTHER:
                raise ValueError(f"rule {i}: all when keys/values must be strings, excluding {OTHER}")
    return rules


def select_first_match(rules, task):
    """Apply the R0 dat-select procedure to a fully known representative input."""
    for index, rule in enumerate(rules):
        if all(task[field] == value for field, value in rule["when"].items()):
            return index, rule["topology"]
    return None, None


def audit(rules):
    fields = sorted({field for rule in rules for field in rule["when"]})
    domains = {
        field: sorted({rule["when"][field] for rule in rules if field in rule["when"]}) + [OTHER]
        for field in fields
    }
    # This candidate is *not* a DAT contract. A single explicit risk-only
    # rule is needed to identify the proposed high-risk target unambiguously.
    candidate_rules = [r for r in rules if r["when"] == {"risk": "high"}]
    candidate_target = candidate_rules[0]["topology"] if len(candidate_rules) == 1 else None
    counts = Counter()
    counterexamples = []
    checked = 0
    for values in product(*(domains[field] for field in fields)):
        task = dict(zip(fields, values))
        _, selected = select_first_match(rules, task)
        counts[selected if selected is not None else "<no-match>"] += 1
        checked += 1
        if candidate_target and task.get("risk") == "high" and selected != candidate_target:
            counterexamples.append({"input": task, "actual": selected, "candidate_expected": candidate_target})
    status = (
        "NOT_EVALUATED" if candidate_target is None else
        "COUNTEREXAMPLE_FOUND" if counterexamples else
        "NO_COUNTEREXAMPLE_IN_FINITE_ABSTRACTION"
    )
    return {
        "scope": "fully-known rule literals and one representative known nonmatch per field; unknowns excluded",
        "domains": domains,
        "states_checked": checked,
        "selection_counts": dict(sorted(counts.items())),
        "candidate_invariant": {
            "hypothesis": "risk=high selects the topology of the explicit {risk: high} rule",
            "adopted_as_policy": False,
            "status": status,
            "counterexamples": counterexamples,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=ROOT / "policies/routing/R0_dynamic.yaml")
    args = parser.parse_args(argv)
    try:
        result = audit(load_rules(args.policy))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"routing audit unavailable: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # A violation of an unadopted *candidate* is not a failing product gate.
    return 0


if __name__ == "__main__":
    sys.exit(main())
