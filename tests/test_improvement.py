import tempfile
import unittest
from research_loop.improvement import ImprovementRegistry


class ImprovementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.r = ImprovementRegistry(self.tmp.name)
        self.r.initialize()
        self.base = self.r.register('researcher', 'Source every statement')['id']
        self.candidate = self.r.register('researcher', 'Source every statement and check dates', self.base)['id']
        self.r.bootstrap(self.base)
        self.suite = self.r.build_suite([
            dict(id='a', prompt='Unsupported claim', expected_decision='reject', critical=True),
            dict(id='b', prompt='Supported claim', expected_decision='accept', critical=False)])['id']
        self.good = [dict(case_id='a', decision='reject'), dict(case_id='b', decision='accept')]
        self.r.begin_comparison(self.candidate, self.base, self.suite)

    def evaluate_pair(self, candidate_answers=None, candidate_cost=9):
        self.r.evaluate(self.base, self.suite, self.good, 10, 'baseline-evaluator')
        self.r.evaluate(self.candidate, self.suite, candidate_answers or self.good, candidate_cost, 'candidate-evaluator')

    def test_promote_and_rollback_preserve_history(self):
        self.evaluate_pair()
        self.assertTrue(self.r.promote(self.candidate, self.base, self.suite, 'independent')['promoted'])
        self.assertEqual(self.r.active('researcher')['id'], self.candidate)
        self.assertEqual(self.r.rollback('researcher', 'Production review failure')['id'], self.base)
        self.assertEqual(len(self.r.status()['history']), 3)
        with self.assertRaises(ValueError):
            self.r.rollback('researcher', 'Repeated rollback')
        with self.assertRaises(ValueError):
            self.r.promote(self.candidate, self.base, self.suite, 'independent')

    def test_packet_withholds_all_labels(self):
        packet = self.r.packet(self.suite)
        self.assertEqual(set(packet['cases'][0]), {'id', 'prompt'})
        self.assertEqual(packet['id'], self.suite)

    def test_rejected_comparison_consumes_suite(self):
        self.evaluate_pair(candidate_cost=11)
        with self.assertRaises(ValueError):
            self.r.promote(self.candidate, self.base, self.suite, 'independent')
        self.assertFalse(self.r.status()['active']['researcher'] == self.candidate)
        with self.assertRaisesRegex(ValueError, 'already used'):
            self.r.promote(self.candidate, self.base, self.suite, 'independent')
        with self.assertRaises(ValueError):
            self.r.evaluate(self.candidate, self.suite, self.good, 0, 'new-evaluator')

    def test_reviewer_independence(self):
        self.evaluate_pair()
        with self.assertRaisesRegex(ValueError, 'independent'):
            self.r.promote(self.candidate, self.base, self.suite, 'candidate-evaluator')
        self.assertEqual(self.r.active('researcher')['id'], self.base)

    def test_critical_miss_cannot_be_bought_with_lower_cost(self):
        bad = [dict(case_id='a', decision='accept'), dict(case_id='b', decision='accept')]
        self.evaluate_pair(bad, 0)
        with self.assertRaises(ValueError):
            self.r.promote(self.candidate, self.base, self.suite, 'independent')

    def test_answers_must_be_complete_and_unique(self):
        for answers in (self.good[:1], self.good + self.good[:1], self.good + [dict(case_id='unknown', decision='accept')]):
            with self.assertRaises(ValueError):
                self.r.evaluate(self.candidate, self.suite, answers, 0, 'evaluator')
        first = self.r.evaluate(self.candidate, self.suite, self.good, 0, 'evaluator')
        self.assertEqual(first['accuracy'], 1.0)
        self.assertEqual(len(first['answers_hash']), 64)
        with self.assertRaises(ValueError):
            self.r.evaluate(self.candidate, self.suite, self.good, 0, 'evaluator')

    def test_input_bounds_and_role_scope(self):
        for cost in (True, -1, 1.5, float('nan'), 10**13):
            with self.assertRaises(ValueError):
                self.r.evaluate(self.candidate, self.suite, self.good, cost, 'evaluator')
        for role in ('controller', 'budget', 'risk', 'policy'):
            with self.assertRaises(ValueError):
                self.r.register(role, 'Change controller')
        with self.assertRaises(ValueError):
            self.r.bootstrap(self.candidate)
        with self.assertRaises(ValueError):
            self.r.register('reviewer', 'Different role', self.base)
        with self.assertRaises(ValueError):
            self.r.build_suite([])

    def test_suite_hash_prevents_renaming_identical_cases(self):
        cases = [dict(id='a', prompt='Unsupported claim', expected_decision='reject', critical=True),
                 dict(id='b', prompt='Supported claim', expected_decision='accept', critical=False)]
        self.assertEqual(self.r.build_suite(list(reversed(cases)))['id'], self.suite)
        self.evaluate_pair()
        self.r.promote(self.candidate, self.base, self.suite, 'independent')
        self.assertEqual(self.r.build_suite(cases)['id'], self.suite)

    def test_accuracy_gain_can_cost_more(self):
        partial = [dict(case_id='a', decision='reject'), dict(case_id='b', decision='reject')]
        self.r.evaluate(self.base, self.suite, partial, 1, 'baseline-evaluator')
        self.r.evaluate(self.candidate, self.suite, self.good, 100, 'candidate-evaluator')
        self.assertTrue(self.r.promote(self.candidate, self.base, self.suite, 'independent')['promoted'])

    def test_no_change_is_not_improvement(self):
        self.evaluate_pair(candidate_cost=10)
        with self.assertRaises(ValueError):
            self.r.promote(self.candidate, self.base, self.suite, 'independent')

    def test_inactive_baseline_and_missing_evaluations_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Baseline must be active'):
            self.r.promote(self.base, self.candidate, self.suite, 'independent')
        with self.assertRaisesRegex(ValueError, 'Unknown evaluation'):
            self.r.promote(self.candidate, self.base, self.suite, 'independent')
        self.evaluate_pair()
        self.assertTrue(self.r.promote(self.candidate, self.base, self.suite, 'independent')['promoted'])

    def test_only_frozen_pair_can_be_evaluated(self):
        third = self.r.register('researcher', 'A third prompt', self.base)['id']
        with self.assertRaisesRegex(ValueError, 'frozen comparison'):
            self.r.evaluate(third, self.suite, self.good, 0, 'third')
        with self.assertRaises(ValueError):
            self.r.begin_comparison(third, self.base, self.suite)
        suite = self.r.build_suite([dict(id='new', prompt='New evidence', expected_decision='accept', critical=True)])['id']
        with self.assertRaisesRegex(ValueError, 'frozen comparison'):
            self.r.evaluate(self.base, suite, [dict(case_id='new', decision='accept')], 0, 'base')

    def test_semantic_reuse_cannot_be_hidden_by_renaming_cases(self):
        suite = self.r.build_suite([
            dict(id='renamed-a', prompt='Unsupported claim', expected_decision='reject', critical=True),
            dict(id='renamed-b', prompt='Supported claim', expected_decision='accept', critical=False)])['id']
        self.assertNotEqual(suite, self.suite)
        with self.assertRaisesRegex(ValueError, 'semantic'):
            self.r.begin_comparison(self.candidate, self.base, suite)

    def test_lineage_changed_prompt_and_size_required(self):
        suite = self.r.build_suite([dict(id='new', prompt='Fresh evidence', expected_decision='accept', critical=True)])['id']
        for candidate in (self.r.register('researcher', 'No parent')['id'],
                          self.r.register('researcher', 'Source every statement', self.base)['id']):
            with self.assertRaises(ValueError):
                self.r.begin_comparison(candidate, self.base, suite)
        with self.assertRaises(ValueError):
            self.r.register('researcher', 'x' * 6001)

    def test_proposer_cannot_evaluate_or_approve_own_change(self):
        candidate = self.r.register('researcher', 'Proposed new prompt', self.base,
                                    proposer_id='director', provenance={'task_id': 'task-1'})['id']
        suite = self.r.build_suite([dict(id='new', prompt='Fresh evidence', expected_decision='accept', critical=True)])['id']
        self.r.begin_comparison(candidate, self.base, suite)
        answers = [dict(case_id='new', decision='accept')]
        with self.assertRaisesRegex(ValueError, 'independent of proposer'):
            self.r.evaluate(candidate, suite, answers, 0, 'director')
        self.r.evaluate(candidate, suite, answers, 0, 'candidate-evaluator')
        self.r.evaluate(self.base, suite, answers, 1, 'baseline-evaluator')
        with self.assertRaisesRegex(ValueError, 'independent'):
            self.r.promote(candidate, self.base, suite, 'director')


if __name__ == '__main__':
    unittest.main()
