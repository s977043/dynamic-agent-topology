"""Synthetic fixtures only: no agents, credentials, network, or real-run metrics."""

import unittest
from itertools import permutations
from dataclasses import replace

from subagent_folding_oracle import Case, Event, evaluate


CASE = Case("order-demo", 3)
RUN_ID = "synthetic-run"


def golden(actor: str = "main") -> tuple[Event, ...]:
    return (
        Event(RUN_ID, "lookup_order", CASE.order_id, actor=actor),
        Event(RUN_ID, "lookup_eta", CASE.order_id, CASE.eta_days, actor=actor),
        Event(RUN_ID, "respond", CASE.order_id, CASE.eta_days),
    )


def judge(events, *, case=CASE, run_id=RUN_ID, trace_complete=True):
    return evaluate(case, events, run_id=run_id, trace_complete=trace_complete)


class FoldingOracleTests(unittest.TestCase):
    def test_complete_chain_passes(self):
        self.assertEqual(judge(golden()).verdict, "PASS")

    def test_correct_answer_without_eta_lookup_fails(self):
        self.assertEqual(judge((golden()[0], golden()[2])).verdict, "FAIL")

    def test_correct_answer_without_order_lookup_fails(self):
        self.assertEqual(judge(golden()[1:]).verdict, "FAIL")

    def test_wrong_final_answer_fails(self):
        events = golden()[:2] + (replace(golden()[2], eta_days=7),)
        self.assertEqual(judge(events).verdict, "FAIL")

    def test_eta_before_order_fails(self):
        order, eta, response = golden()
        self.assertEqual(judge((eta, order, response)).verdict, "FAIL")

    def test_checks_after_first_response_do_not_repair_it(self):
        order, eta, response = golden()
        self.assertEqual(judge((response, order, eta, response)).verdict, "FAIL")

    def test_other_order_access_fails(self):
        events = (replace(golden()[0], order_id="other-order"),) + golden()
        self.assertEqual(judge(events).verdict, "FAIL")

    def test_unknown_event_is_not_silently_ignored(self):
        events = (replace(golden()[0], kind="unrecognized"),) + golden()
        self.assertEqual(judge(events).verdict, "INCONCLUSIVE")

    def test_incomplete_or_unknown_trace_is_inconclusive(self):
        for complete in (False, None):
            with self.subTest(complete=complete):
                self.assertEqual(judge(golden(), trace_complete=complete).verdict,
                                 "INCONCLUSIVE")

    def test_cross_run_results_are_inconclusive(self):
        order, eta, response = golden()
        events = (order, replace(eta, run_id="other-run"), response)
        self.assertEqual(judge(events).verdict, "INCONCLUSIVE")

    def test_failed_eta_call_does_not_count_as_confirmation(self):
        order, eta, response = golden()
        events = (order, replace(eta, succeeded=False), response)
        self.assertEqual(judge(events).verdict, "FAIL")

    def test_failed_order_call_does_not_count_as_confirmation(self):
        order, eta, response = golden()
        events = (replace(order, succeeded=False), eta, response)
        self.assertEqual(judge(events).verdict, "FAIL")

    def test_missing_final_response_fails(self):
        self.assertEqual(judge(golden()[:2]).verdict, "FAIL")

    def test_empty_complete_trace_fails(self):
        self.assertEqual(judge(()).verdict, "FAIL")

    def test_incomplete_empty_trace_is_not_counted_as_failure(self):
        self.assertEqual(judge((), trace_complete=False).verdict, "INCONCLUSIVE")

    def test_string_success_is_not_truthy_success(self):
        order, eta, response = golden()
        events = (order, replace(eta, succeeded="false"), response)
        self.assertEqual(judge(events).verdict, "INCONCLUSIVE")

    def test_boolean_eta_is_not_an_integer_measurement(self):
        order, eta, response = golden()
        events = (order, replace(eta, eta_days=True), replace(response, eta_days=True))
        self.assertEqual(judge(events, case=Case(CASE.order_id, 1)).verdict,
                         "INCONCLUSIVE")

    def test_invalid_evaluator_truth_raises(self):
        for case in (Case("", 3), Case(CASE.order_id, True), Case(CASE.order_id, -1)):
            with self.subTest(case=case), self.assertRaises(ValueError):
                judge(golden(), case=case)

    def test_actor_names_do_not_bias_topology(self):
        self.assertEqual(judge(golden("main")), judge(golden("specialist")))
        self.assertEqual(judge(golden("specialist")).verdict, "PASS")

    def test_retry_before_response_can_recover(self):
        order, eta, response = golden()
        failed = replace(eta, succeeded=False, eta_days=None)
        self.assertEqual(judge((order, failed, eta, response)).verdict, "PASS")

    def test_wrong_eta_result_cannot_be_hidden_by_answer(self):
        order, eta, response = golden()
        self.assertEqual(judge((order, replace(eta, eta_days=7), response)).verdict,
                         "FAIL")

    def test_only_valid_order_of_three_events_passes(self):
        for events in permutations(golden()):
            with self.subTest(kinds=tuple(e.kind for e in events)):
                expected = "PASS" if events == golden() else "FAIL"
                self.assertEqual(judge(events).verdict, expected)

    def test_deleting_any_required_event_fails(self):
        for index in range(3):
            with self.subTest(index=index):
                events = golden()[:index] + golden()[index + 1:]
                self.assertEqual(judge(events).verdict, "FAIL")

    def test_consistent_run_relabel_does_not_change_result(self):
        events = tuple(replace(e, run_id="another-synthetic-run") for e in golden())
        self.assertEqual(judge(events, run_id="another-synthetic-run"), judge(golden()))

    def test_zero_day_eta_is_valid(self):
        order, eta, response = golden()
        events = (order, replace(eta, eta_days=0), replace(response, eta_days=0))
        self.assertEqual(judge(events, case=Case(CASE.order_id, 0)).verdict, "PASS")

    def test_empty_run_id_is_inconclusive(self):
        self.assertEqual(judge(golden(), run_id="").verdict, "INCONCLUSIVE")

    def test_untyped_completeness_does_not_pass(self):
        for value in ("true", 1):
            with self.subTest(value=value):
                self.assertEqual(judge(golden(), trace_complete=value).verdict,
                                 "INCONCLUSIVE")

    def test_missing_successful_eta_result_is_inconclusive(self):
        order, eta, response = golden()
        self.assertEqual(judge((order, replace(eta, eta_days=None), response)).verdict,
                         "INCONCLUSIVE")

    def test_malformed_event_fields_are_inconclusive(self):
        for change in ({"kind": []}, {"order_id": ""}, {"succeeded": 1},
                       {"eta_days": 3.0}, {"eta_days": "3"}, {"eta_days": -1}):
            with self.subTest(change=change):
                order, eta, response = golden()
                self.assertEqual(judge((order, replace(eta, **change), response)).verdict,
                                 "INCONCLUSIVE")

    def test_duplicate_response_fails(self):
        self.assertEqual(judge(golden() + (golden()[2],)).verdict, "FAIL")

    def test_failed_response_is_not_task_completion(self):
        events = golden()[:2] + (replace(golden()[2], succeeded=False),)
        self.assertEqual(judge(events).verdict, "FAIL")

    def test_trace_completeness_argument_is_required(self):
        with self.assertRaises(TypeError):
            evaluate(CASE, golden(), run_id=RUN_ID)

    def test_no_events_after_response(self):
        self.assertEqual(judge(golden() + (golden()[0],)).verdict, "FAIL")

    def test_answer_alone_is_not_completion(self):
        self.assertEqual(judge((golden()[2],)).verdict, "FAIL")

if __name__ == "__main__":
    unittest.main(verbosity=2)
