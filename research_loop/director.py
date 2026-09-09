"""Internal director operations, distinct from coding/maintenance operations.

Worker IDs are accountability labels in manual mode, not authenticated principals.
Provider/OS identity enforcement is required before unattended deployment.
"""
from .network import Network
from .improvement import ImprovementRegistry

WORKER_PROMPTS = frozenset({'researcher', 'data_auditor', 'reviewer'})


def propose_prompt(root, task_id, director_id, role, prompt, rationale):
    """Register a worker-prompt candidate from a completed director review.

    Never activates it. The maintainer owns director/controller/evaluator changes.
    """
    if role not in WORKER_PROMPTS:
        raise ValueError('Director may propose worker prompts only; maintainer owns director and evaluator policy')
    network = Network(root)
    task = network.get_task(task_id)
    if task['role'] != 'improvement_proposal' or task['state'] != 'completed':
        raise ValueError('A completed director improvement task is required')
    if task['worker_id'] != director_id:
        raise ValueError('Proposal must come from the owning director')
    if task['result']['decision'] != 'propose_improvement':
        raise ValueError('Task did not propose an improvement')
    registry = ImprovementRegistry(root)
    baseline = registry.active(role)
    if baseline is None:
        raise ValueError('Explicit initial baseline required before director improvement')
    return registry.register(role, prompt, baseline['id'], rationale,
        proposer_id=director_id,
        provenance={'task_id': task_id, 'cycle_id': task['cycle_id'],
                    'result_hash': task['result_hash'], 'packet_hash': task['packet_hash']})
