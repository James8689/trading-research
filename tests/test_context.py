import json
import tempfile
import unittest
from pathlib import Path

from research_loop.network import Network


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.net = Network(self.root)
        self.net.initialize(max_tasks=60)
        self.event = self.net.ingest('source', 'SECRET_EVIDENCE original text')['event_id']

    def cycle(self, candidate, question):
        return self.net.create_cycle(candidate, question, [self.event], 'a' * 64)

    def complete(self, role, worker, memory='isolated interpretation'):
        packet = self.net.claim(worker, role)
        self.assertIsNotNone(packet)
        result = {'summary': 'SECRET_SUMMARY', 'decision': 'continue',
                  'evidence': [{'source_id': self.event, 'quote': 'SECRET_EVIDENCE'}],
                  'uncertainty': 'SECRET_LABEL', 'next_action': 'Human review', 'memory': memory}
        self.net.submit(packet['task_id'], worker, result)
        return packet

    def test_candidate_memory_isolation_and_history(self):
        first = self.cycle('A', 'First')
        self.complete('director_plan', 'director', 'A memory v1')
        self.cycle('B', 'Other')
        packet_b = self.complete('director_plan', 'director', 'B memory')
        self.assertEqual(packet_b['memory'], '')
        self.assertIsNone(packet_b['memory_provenance'])
        self.cycle('A', 'Second')
        packet_a = self.complete('director_plan', 'director', 'A memory v2')
        self.assertEqual(packet_a['memory'], 'A memory v1')
        self.assertEqual(packet_a['memory_provenance']['task_id'], first['tasks']['director_plan'])
        self.assertEqual(packet_a['memory_provenance']['version'], 1)
        with self.net._db() as db:
            versions = db.execute("SELECT version,memory FROM memory_history WHERE candidate_id='A' ORDER BY version").fetchall()
        self.assertEqual([tuple(r) for r in versions], [(1, 'A memory v1'), (2, 'A memory v2')])

    def test_packet_frozen_across_prompt_and_memory_changes(self):
        directory = self.root / 'agents' / 'network'
        directory.mkdir(parents=True)
        prompt_file = directory / 'director_plan.md'
        prompt_file.write_text('Initial prompt', encoding='utf-8')
        cycle = self.cycle('A', 'One')
        packet = self.net.claim('one', 'director_plan')
        prompt_file.write_text('Updated prompt', encoding='utf-8')
        self.cycle('A', 'Two')
        newer = self.complete('director_plan', 'two', 'newer memory')
        self.assertEqual(newer['prompt'], 'Updated prompt')
        self.assertEqual(self.net.get_task(cycle['tasks']['director_plan'])['packet'], packet)
        self.assertEqual(packet['memory'], '')
        self.assertEqual(packet['prompt'], 'Initial prompt')

    def test_reviewer_blinding_and_director_improvement_ownership(self):
        for index in range(2):
            self.cycle('A', str(index))
            self.complete('director_plan', 'director')
            self.complete('researcher', 'researcher')
            self.complete('data_auditor', 'auditor')
            packet = self.complete('reviewer', 'reviewer')
            self.assertEqual(packet['memory'], '')
            self.assertIsNone(packet['memory_provenance'])
            self.assertTrue(all(set(d['result']) == {'evidence'} for d in packet['dependencies']))
            self.complete('director_decision', 'director')
            self.assertIsNone(self.net.claim('maintainer', 'improvement_proposal'))
            improvement = self.complete('improvement_proposal', 'director')
            self.assertEqual({d['role'] for d in improvement['dependencies']}, {'director_plan', 'researcher', 'data_auditor', 'reviewer', 'director_decision'})

    def test_maximal_results_remain_dispatchable(self):
        directory = self.root / 'agents' / 'network'
        directory.mkdir(parents=True)
        for role in ('director_plan', 'researcher', 'data_auditor', 'reviewer', 'director_decision', 'improvement_proposal'):
            (directory / (role + '.md')).write_text('P' * 6000, encoding='utf-8')
        event = self.net.ingest('large', 'E' * 4000)['event_id']
        self.net.create_cycle('large', 'Q' * 2000, [event], 'a' * 64)
        for role, worker in [('director_plan', 'director'), ('researcher', 'researcher'), ('data_auditor', 'auditor'), ('reviewer', 'reviewer'), ('director_decision', 'director'), ('improvement_proposal', 'director')]:
            packet = self.net.claim(worker, role)
            self.assertIsNotNone(packet)
            self.assertLessEqual(len(json.dumps(packet, ensure_ascii=False, separators=(',', ':'))), 20000)
            result = {'summary': 'S' * 4000, 'decision': 'continue',
                      'evidence': [{'source_id': event, 'quote': 'E' * 4000}],
                      'uncertainty': 'U' * 2000, 'next_action': 'N' * 2000, 'memory': 'M' * 4000}
            self.net.submit(packet['task_id'], worker, result)
            for dependency in packet['dependencies']:
                self.assertNotIn('memory', dependency['result'])
                self.assertEqual(len(dependency['result_hash']), 64)
        self.assertEqual(len(packet['dependencies']), 5)

    def test_director_brief_contains_actionable_final_decision(self):
        self.cycle('A', 'Question')
        for role, worker in [('director_plan', 'director'), ('researcher', 'researcher'), ('data_auditor', 'auditor'), ('reviewer', 'reviewer'), ('director_decision', 'director')]:
            self.complete(role, worker)
        brief = self.net.director_brief()
        final = brief['latest_decisions'][0]
        self.assertEqual(final['role'], 'director_decision')
        self.assertEqual(final['summary'], 'SECRET_SUMMARY')
        self.assertEqual(final['next_action'], 'Human review')
        self.assertEqual(len(final['result_hash']), 64)
        self.assertNotIn('SECRET_EVIDENCE', json.dumps(brief))
        self.assertNotIn('SECRET_LABEL', json.dumps(brief))

    def test_rejected_submission_preserves_bounded_error_lineage(self):
        self.cycle('A', 'Question')
        packet = self.net.claim('director', 'director_plan')
        result = {'summary': 'bad', 'decision': 'continue',
                  'evidence': [{'source_id': self.event, 'quote': 'fabricated content'}],
                  'uncertainty': 'Unknown', 'next_action': 'Review', 'memory': ''}
        with self.assertRaises(ValueError):
            self.net.submit(packet['task_id'], 'director', result)
        task = self.net.get_task(packet['task_id'])
        self.assertEqual(task['state'], 'leased')
        self.assertEqual(task['submission_errors'][0]['code'], 'evidence_rejected')
        self.assertEqual(len(task['submission_errors'][0]['payload_hash']), 64)
        self.assertNotIn('fabricated content', json.dumps(task['submission_errors']))
        with self.assertRaises(ValueError):
            self.net.submit(packet['task_id'], 'unowned', result)
        self.assertEqual(len(self.net.get_task(packet['task_id'])['submission_errors']), 1)

    def test_director_brief_is_bounded_and_has_no_research_context(self):
        self.cycle('A', 'SECRET_QUESTION')
        self.complete('director_plan', 'director')
        for index in range(12):
            self.cycle('A', str(index))
        brief = self.net.director_brief(1600)
        encoded = json.dumps(brief, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        self.assertLessEqual(len(encoded), 1600)
        self.assertNotIn('SECRET_', encoded)
        self.assertNotIn('isolated interpretation', encoded)
        self.assertGreater(brief['counts']['pending_and_leased_omitted'], 0)
        self.assertEqual(brief['context_owner'], 'internal_research_director')


if __name__ == '__main__':
    unittest.main()
