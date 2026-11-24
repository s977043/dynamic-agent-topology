#!/usr/bin/env python3
"""Offline positive, negative, and malformed-policy checks for routing audit."""

import tempfile
import unittest
from pathlib import Path

from audit_routing_states import ROOT, OTHER, audit, load_rules, select_first_match


BASE = [
    {"when": {"complexity": "low", "ambiguity": "low"}, "topology": "T0"},
    {"when": {"risk": "high"}, "topology": "T2"},
]


class RoutingAuditTests(unittest.TestCase):
    def test_first_match_is_preserved(self):
        self.assertEqual(
            select_first_match(BASE, {"complexity": "low", "ambiguity": "low", "risk": "high"}),
            (0, "T0"),
        )
        self.assertEqual(
            select_first_match(BASE, {"complexity": OTHER, "ambiguity": "low", "risk": "high"}),
            (1, "T2"),
        )

    def test_candidate_counterexample_is_detected(self):
        result = audit(BASE)
        self.assertEqual(result["states_checked"], 2 * 2 * 2)
        self.assertEqual(result["candidate_invariant"]["status"], "COUNTEREXAMPLE_FOUND")
        self.assertEqual(len(result["candidate_invariant"]["counterexamples"]), 1)

    def test_high_risk_first_has_no_counterexample_in_abstraction(self):
        result = audit([BASE[1], BASE[0]])
        self.assertEqual(result["candidate_invariant"]["status"], "NO_COUNTEREXAMPLE_IN_FINITE_ABSTRACTION")
        self.assertEqual(result["candidate_invariant"]["counterexamples"], [])

    def test_missing_explicit_candidate_is_undecidable_not_pass(self):
        result = audit(BASE[:1])
        self.assertEqual(result["candidate_invariant"]["status"], "NOT_EVALUATED")

    def test_repository_r0_policy_can_be_audited_without_fixing_outcome(self):
        result = audit(load_rules(ROOT / "policies/routing/R0_dynamic.yaml"))
        self.assertGreater(result["states_checked"], 0)
        self.assertEqual(sum(result["selection_counts"].values()), result["states_checked"])

    def test_invalid_policy_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.yaml"
            path.write_text("rules:\n  - when: {}\n    topology: T0\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nonempty"):
                load_rules(path)


if __name__ == "__main__":
    unittest.main()
