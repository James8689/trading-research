import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from research_loop.budget import BudgetLedger


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ledger = BudgetLedger(self.temp.name)

    def test_no_implicit_allowance_and_immutable_policy(self):
        self.assertEqual(self.ledger.status()["available_microusd"], 0)
        with self.assertRaises(RuntimeError):
            self.ledger.reserve("unapproved", 1)
        self.ledger.initialize("simulation", 10)
        self.ledger.initialize("simulation", 10)
        for period, limit in [("next", 10), ("simulation", 20)]:
            with self.assertRaises(ValueError):
                self.ledger.initialize(period, limit)

    def test_concurrent_final_budget_contention(self):
        self.ledger.initialize("simulation", 10)
        gate = Barrier(2)

        def compete(attempt):
            ledger = BudgetLedger(self.temp.name)
            gate.wait()
            try:
                ledger.reserve(attempt, 10)
                return True
            except RuntimeError:
                return False

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(compete, ["a", "b"]))
        self.assertEqual(sum(results), 1)
        self.assertEqual(self.ledger.status()["reserved_microusd"], 10)

    def test_timeout_unknown_survives_restart_and_resume(self):
        self.ledger.initialize("simulation", 100)
        self.ledger.reserve("a", 30)
        self.ledger.record_dispatch("a", "receipt")
        self.ledger.settle("a", None)
        restarted = BudgetLedger(self.temp.name)
        self.assertEqual(restarted.status()["reserved_microusd"], 30)
        restarted.stop("operator pause")
        self.assertTrue(restarted.resume()["blocked"])
        with self.assertRaises(RuntimeError):
            restarted.reserve("b", 1)
        restarted.settle("a", 12)
        self.assertEqual(restarted.status()["available_microusd"], 88)
        restarted.reserve("b", 88)

    def test_crash_before_receipt_keeps_reservation(self):
        self.ledger.initialize("simulation", 10)
        self.ledger.reserve("a", 10)
        restarted = BudgetLedger(self.temp.name)
        with self.assertRaises(RuntimeError):
            restarted.reserve("retry", 1)

    def test_duplicate_and_conflicting_calls(self):
        self.ledger.initialize("simulation", 10)
        self.assertEqual(self.ledger.reserve("a", 10), self.ledger.reserve("a", 10))
        with self.assertRaises(ValueError):
            self.ledger.reserve("a", 9)
        self.assertEqual(self.ledger.record_dispatch("a", "r"), self.ledger.record_dispatch("a", "r"))
        with self.assertRaises(ValueError):
            self.ledger.record_dispatch("a", "other")
        self.assertEqual(self.ledger.settle("a", 5), self.ledger.settle("a", 5))
        for value in [6, None]:
            with self.assertRaises(ValueError):
                self.ledger.settle("a", value)
        self.assertEqual(self.ledger.status()["spent_microusd"], 5)

    def test_overrun_records_truth_and_blocks(self):
        self.ledger.initialize("simulation", 10)
        self.ledger.reserve("a", 5)
        self.ledger.settle("a", 12)
        status = self.ledger.status()
        self.assertEqual(status["spent_microusd"], 12)
        self.assertTrue(status["over_budget"])
        self.assertTrue(self.ledger.resume()["blocked"])
        with self.assertRaises(RuntimeError):
            self.ledger.reserve("b", 0)

    def test_stop_prevents_admission_and_dispatch_but_allows_accounting(self):
        self.ledger.initialize("simulation", 10)
        self.ledger.reserve("a", 5)
        self.ledger.stop("pause")
        with self.assertRaises(RuntimeError):
            self.ledger.reserve("b", 1)
        with self.assertRaises(RuntimeError):
            self.ledger.record_dispatch("a", "r")
        self.ledger.settle("a", 3)
        self.assertFalse(self.ledger.resume()["blocked"])

    def test_invalid_money(self):
        for value in [-1, True, False, 1.5, "1", 2**63]:
            with self.assertRaises(ValueError):
                self.ledger.initialize("simulation", value)
        self.ledger.initialize("simulation", 10)
        self.ledger.reserve("a", 5)
        for value in [-1, True, False, 1.5, "1", 2**63]:
            with self.assertRaises(ValueError):
                self.ledger.reserve("b", value)
            with self.assertRaises(ValueError):
                self.ledger.settle("a", value)


if __name__ == "__main__":
    unittest.main()
