import hashlib
import tempfile
import unittest
from pathlib import Path

from research_loop.families import FamilyRegistry
from research_loop.network import Network


class FamilyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.reg = FamilyRegistry(self.root)
        self.reg.initialize()

    def test_register_link_and_retrospective(self):
        family = self.reg.register('B3-H1-v1', 'Open-market CEF reinvestment buying.', 'a' * 64)
        again = self.reg.register('B3-H1-v1', 'ignored')
        self.assertTrue(again['duplicate'])
        self.assertEqual(again['family_id'], family['family_id'])
        link = self.reg.link_cycle(family['family_id'], 'cycle_fixture')
        self.assertFalse(link.get('duplicate'))
        self.assertTrue(self.reg.link_cycle(family['family_id'], 'cycle_fixture')['duplicate'])
        retro = self.reg.record_retrospective(family['family_id'], 'Missing original filings.', 'cycle_fixture', ['task_1'])
        status = self.reg.status()
        self.assertEqual(len(status['families']), 1)
        self.assertEqual(status['retrospectives'][0]['retro_id'], retro['retro_id'])

    def test_role_report_does_not_include_packet_body(self):
        net = Network(self.root)
        net.initialize()
        net.create_cycle('fixture', 'Question.', [], hashlib.sha256(b'p').hexdigest())
        report = net.role_report('director_plan')
        self.assertEqual(report['role'], 'director_plan')
        self.assertNotIn('packet', report['tasks'][0])
        self.assertEqual(report['open_task']['state'], 'pending')
