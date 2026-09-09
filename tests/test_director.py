import tempfile
import unittest
from research_loop.director import propose_prompt
from research_loop.improvement import ImprovementRegistry
from research_loop.network import Network, ROLES


class DirectorTests(unittest.TestCase):
    def test_director_owns_proposals_but_cannot_activate_or_rewrite_self(self):
        with tempfile.TemporaryDirectory() as root:
            net = Network(root)
            net.initialize()
            reg = ImprovementRegistry(root)
            reg.initialize()
            baseline = reg.register('researcher', 'Extract exact source clauses.')
            reg.bootstrap(baseline['id'])
            event = net.ingest('fixture:source', 'Synthetic source evidence.')['event_id']
            cycle = net.create_cycle('fixture', 'Check synthetic evidence.', [event], 'a' * 64)
            workers = ['director', 'worker-a', 'worker-b', 'reviewer', 'director', 'director']
            for role, worker in zip(ROLES, workers):
                packet = net.claim(worker, role)
                net.submit(packet['task_id'], worker, {
                    'summary': 'Synthetic check.',
                    'decision': 'propose_improvement' if role == 'improvement_proposal' else 'continue',
                    'evidence': [{'source_id': event, 'quote': 'Synthetic source evidence.'}],
                    'uncertainty': 'Synthetic only.', 'next_action': 'Check source dates.', 'memory': ''})
            task = cycle['tasks']['improvement_proposal']
            candidate = propose_prompt(root, task, 'director', 'researcher',
                                       'Extract exact clauses and check publication dates.', 'Observed missing timing check.')
            self.assertEqual(candidate['proposer_id'], 'director')
            self.assertEqual(candidate['provenance']['task_id'], task)
            self.assertEqual(reg.active('researcher')['id'], baseline['id'])
            with self.assertRaises(ValueError):
                propose_prompt(root, task, 'worker-a', 'researcher', 'Bad ownership.', 'reason')
            with self.assertRaises(ValueError):
                propose_prompt(root, task, 'director', 'director_decision', 'Rewrite myself.', 'reason')


if __name__ == '__main__':
    unittest.main()
