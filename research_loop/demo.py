"""Repeatable synthetic smoke run. Fixture workers are NOT language models."""
from __future__ import annotations
import hashlib
import tempfile
from .network import Network, ROLES
from .improvement import ImprovementRegistry
from .director import propose_prompt
from .budget import BudgetLedger


def run_demo():
    with tempfile.TemporaryDirectory(prefix='research-demo-') as root:
        network = Network(root)
        network.initialize(12, 3)
        registry = ImprovementRegistry(root)
        registry.initialize()
        baseline = registry.register('researcher', 'Read the source and extract contractual clauses.',
                                     rationale='Synthetic baseline, not measured model behavior.')
        registry.bootstrap(baseline['id'])
        event = network.ingest('fixture:cef-contract',
            'SYNTHETIC TEST DOCUMENT. Purchases are optional. Publication time is unknown.')
        cycle = network.create_cycle('SYNTHETIC-NOT-B3', 'Check whether buying is mandatory.',
            [event['event_id']], hashlib.sha256(b'synthetic smoke plan v1').hexdigest())
        workers = ['director', 'reader', 'auditor', 'reviewer', 'director', 'director']
        dispositions = ['continue', 'reject', 'blocked', 'reject', 'reject', 'propose_improvement']
        for role, worker, decision in zip(ROLES, workers, dispositions):
            packet = network.claim(worker, role)
            if packet is None:
                raise RuntimeError(f'Demo could not claim {role}')
            network.submit(packet['task_id'], worker, {
                'summary': 'Synthetic document has optional purchases and no known publication time.',
                'decision': decision,
                'evidence': [{'source_id': event['event_id'], 'quote': 'Purchases are optional.'}],
                'uncertainty': 'Synthetic fixture only. No market claim or real research evaluation.',
                'next_action': 'Require explicit mandatory language and report missing knowledge time.',
                'memory': 'Synthetic optional-flow premise rejected. Preserve the missing timestamp.'})
        challenger = propose_prompt(root, cycle['tasks']['improvement_proposal'], 'director',
            'researcher', 'Extract clauses; reject optional flow as mandatory and flag unknown knowledge time.',
            'Director observed optional-flow and timing checks in the synthetic review.')
        suite = registry.build_suite([
            {'id': 'optional', 'prompt': 'Synthetic: optional buying proves mandatory demand?',
             'expected_decision': 'reject', 'critical': True},
            {'id': 'unknown-time', 'prompt': 'Synthetic: public availability time is unknown. Is timing established?',
             'expected_decision': 'blocked', 'critical': True}])
        registry.begin_comparison(challenger['id'], baseline['id'], suite['id'])
        registry.evaluate(baseline['id'], suite['id'],
            [{'case_id': 'optional', 'decision': 'continue'}, {'case_id': 'unknown-time', 'decision': 'blocked'}],
            10, 'fixture-evaluator-a')
        registry.evaluate(challenger['id'], suite['id'],
            [{'case_id': 'optional', 'decision': 'reject'}, {'case_id': 'unknown-time', 'decision': 'blocked'}],
            10, 'fixture-evaluator-b')
        comparison = registry.promote(challenger['id'], baseline['id'], suite['id'], 'independent-fixture-reviewer')
        registry.rollback('researcher', 'Demonstrate reversible promotion; retain baseline for smoke.')
        budget = BudgetLedger(root)
        budget.initialize('synthetic-only', 100)
        budget.reserve('fake-attempt', 60)
        budget.record_dispatch('fake-attempt', 'fake-provider-id')
        budget.settle('fake-attempt', None)
        unknown_blocked = budget.status()['blocked']
        budget.settle('fake-attempt', 40)
        state = network.status()
        return {
            'schema_version': 1,
            'mode': 'synthetic_offline_demo',
            'model_calls': 0, 'broker_calls': 0, 'real_money_spent': 0,
            'research_tasks_completed': sum(t['state'] == 'completed' for t in state['tasks']),
            'director_decision': 'reject',
            'director_owned_prompt_proposal': challenger['proposer_id'] == 'director',
            'synthetic_gate_promoted': comparison['promoted'],
            'rollback_restored_baseline': registry.active('researcher')['id'] == baseline['id'],
            'unknown_provider_outcome_blocked': unknown_blocked,
            'restart_preserves_attempts': Network(root).status()['attempts_used'] == 6,
            'meaning': 'Verifies controller plumbing with scripted answers, not agent improvement or trading alpha.'}
