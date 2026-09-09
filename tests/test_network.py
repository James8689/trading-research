import concurrent.futures
import hashlib
import tempfile
import unittest
from pathlib import Path

from research_loop.network import Network

PLAN = hashlib.sha256(b'frozen synthetic plan').hexdigest()
SOURCE = 'SYNTHETIC FIXTURE: The plan must buy existing shares during the stated window.'


def result(source, decision='continue'):
    return dict(summary='Synthetic evidence check only.', decision=decision,
                evidence=[{'source_id': source, 'quote': 'must buy existing shares'}],
                uncertainty='This fixture is not market evidence.',
                next_action='Review the original source.', memory='Fixture checked; not a strategy result.')


class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.net = Network(self.root)
        self.net.initialize()
        self.source = self.net.ingest('fixture:contract', SOURCE, '2026-01-01T00:00:00Z')['event_id']
        self.cycle = self.net.create_cycle('fixture-v1', 'Check contractual language.', [self.source], PLAN)

    def complete(self, role, worker, decision='continue'):
        packet = self.net.claim(worker, role)
        self.assertIsNotNone(packet, role)
        self.net.submit(packet['task_id'], worker, result(self.source, decision))
        return packet

    def test_end_to_end_and_reviewer_blinding(self):
        self.complete('director_plan', 'director')
        self.complete('researcher', 'researcher')
        self.complete('data_auditor', 'auditor')
        packet = self.complete('reviewer', 'reviewer')
        self.assertTrue(packet['sources'])
        self.assertTrue(all(set(d['result']) == {'evidence'} for d in packet['dependencies']))
        self.complete('director_decision', 'director')
        self.complete('improvement_proposal', 'improver', 'propose_improvement')
        self.assertEqual(self.net.status()['attempts_used'], 6)
        self.assertTrue(all(t['state'] == 'completed' for t in self.net.status()['tasks']))
        self.assertIsNone(self.net.claim('another-worker'))

    def test_duplicate_source_revision_and_cycle(self):
        same = self.net.ingest('fixture:contract', SOURCE, '2026-01-01T00:00:00Z')
        self.assertEqual(self.source, same['event_id'])
        revised = self.net.ingest('fixture:contract', SOURCE + ' Revised.', '2026-01-02T00:00:00Z')
        self.assertNotEqual(self.source, revised['event_id'])
        self.assertEqual(revised['revision'], 2)
        same_cycle = self.net.create_cycle('fixture-v1', 'Check contractual language.', [self.source], PLAN)
        self.assertEqual(self.cycle['cycle_id'], same_cycle['cycle_id'])

    def test_claim_is_atomic_and_lease_survives_restart(self):
        def claim(i):
            return Network(self.root).claim(f'worker-{i}', 'director_plan')
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            packets = list(executor.map(claim, range(4)))
        selected = [p for p in packets if p]
        self.assertEqual(len(selected), 1)
        restarted = Network(self.root)
        self.assertIsNone(restarted.claim('retry', 'director_plan'))
        task = restarted.get_task(selected[0]['task_id'])
        self.assertEqual(task['packet'], selected[0])
        self.assertEqual(len(task['attempts']), 1)

    def test_independent_worker_identities(self):
        self.complete('director_plan', 'director')
        self.complete('researcher', 'worker')
        self.assertIsNone(self.net.claim('worker', 'data_auditor'))
        self.complete('data_auditor', 'auditor')
        self.assertIsNone(self.net.claim('worker', 'reviewer'))
        self.assertIsNone(self.net.claim('auditor', 'reviewer'))
        self.complete('reviewer', 'reviewer')
        self.assertIsNone(self.net.claim('reviewer', 'director_decision'))

    def test_fabricated_evidence_rejected_without_losing_lease(self):
        packet = self.net.claim('director', 'director_plan')
        bad = result(self.source)
        bad['evidence'][0]['quote'] = 'guaranteed profit'
        with self.assertRaises(ValueError):
            self.net.submit(packet['task_id'], 'director', bad)
        self.assertEqual(self.net.get_task(packet['task_id'])['state'], 'leased')
        with self.assertRaises(ValueError):
            self.net.submit(packet['task_id'], 'imposter', result(self.source))
        self.net.submit(packet['task_id'], 'director', result(self.source))
        with self.assertRaises(ValueError):
            self.net.submit(packet['task_id'], 'director', result(self.source))

    def test_rejection_reaches_director_and_improvement(self):
        self.complete('director_plan', 'director')
        self.complete('researcher', 'researcher')
        self.complete('data_auditor', 'auditor', 'reject')
        self.complete('reviewer', 'reviewer', 'reject')
        packet = self.net.claim('director', 'director_decision')
        with self.assertRaises(ValueError):
            self.net.submit(packet['task_id'], 'director', result(self.source))
        self.net.submit(packet['task_id'], 'director', result(self.source, 'reject'))
        self.complete('improvement_proposal', 'improver', 'propose_improvement')

    def test_failure_propagates_and_preserves_attempt(self):
        packet = self.net.claim('director', 'director_plan')
        self.net.recover(packet['task_id'], reason='Operator confirmed interrupted manual task.')
        states = [t['state'] for t in self.net.status()['tasks']]
        self.assertEqual(states.count('failed'), 1)
        self.assertEqual(states.count('blocked'), 5)
        self.assertIsNone(self.net.claim('retry'))
        self.assertEqual(self.net.get_task(packet['task_id'])['attempts'][0]['outcome'], 'failed')

    def test_stop_resume_and_caps_do_not_reset(self):
        self.net.stop('Pause for review.')
        self.assertIsNone(Network(self.root).claim('director'))
        self.net.resume()
        self.assertIsNotNone(self.net.claim('director'))
        with self.assertRaises(ValueError):
            Network(self.root).initialize(999, 99)
        self.assertEqual(Network(self.root).status()['attempts_used'], 1)

    def test_packet_size_and_timestamp_validation(self):
        with self.assertRaises(ValueError):
            self.net.ingest('x', 'text', '2026-01-01T12:00:00')
        a = self.net.ingest('a', 'a' * 15000)['event_id']
        b = self.net.ingest('b', 'b' * 15000)['event_id']
        with self.assertRaises(ValueError):
            self.net.create_cycle('too-large', 'question', [a, b], PLAN)
        self.assertEqual(len(self.net.status()['cycles']), 1)

    def test_empty_source_packet_can_report_blocked(self):
        cycle = self.net.create_cycle('missing', 'Find source documents.', [], PLAN)
        self.complete('director_plan', 'first-director')
        packet = self.net.claim('second-director', 'director_plan')
        self.assertEqual(packet['task_id'], cycle['tasks']['director_plan'])
        value = result(self.source, 'blocked')
        value['evidence'] = []
        self.net.submit(packet['task_id'], 'second-director', value)


if __name__ == '__main__':
    unittest.main()
