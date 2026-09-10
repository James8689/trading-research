"""Manual, bounded research orchestration. No provider or broker dispatch."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import sqlite3
from contextlib import closing

from .network import Network
from .improvement import ImprovementRegistry
from .director import propose_prompt
from .budget import BudgetLedger


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".", help="Project root with research_state storage")
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Initialize once; existing caps cannot be reset")
    init.add_argument("--max-tasks", type=int)
    init.add_argument("--max-concurrent", type=int)
    sub.add_parser("status")
    sub.add_parser("brief", help="Bounded internal-director resume context")
    export = sub.add_parser("export", help="Private operator runtime backup; requires an idle network")
    export.add_argument("archive")
    restore = sub.add_parser("restore", help="Restore a verified private backup into empty state")
    restore.add_argument("archive")
    ingest = sub.add_parser("ingest", help="Import a UTF-8 source file; never downloads URLs")
    ingest.add_argument("source_id", help="Original source URL or stable identifier")
    ingest.add_argument("file")
    ingest.add_argument("--published-at")
    seed = sub.add_parser("seed-cef", help="Seed frozen CEF document-feasibility workflow")
    seed.add_argument("--evidence", nargs="*", default=[])
    nxt = sub.add_parser("next", help="Claim a packet for a named manual worker")
    nxt.add_argument("worker")
    nxt.add_argument("--role")
    task = sub.add_parser("task", help="Inspect saved task and packet after interruption")
    task.add_argument("task_id")
    submit = sub.add_parser("submit")
    submit.add_argument("task_id")
    submit.add_argument("worker")
    submit.add_argument("file", help="Structured result JSON")
    fail = sub.add_parser("fail")
    fail.add_argument("task_id")
    fail.add_argument("worker")
    fail.add_argument("reason")
    stop = sub.add_parser("stop")
    stop.add_argument("reason")
    sub.add_parser("resume")
    recover = sub.add_parser("recover", help="Explicitly reconcile an interrupted task; never redispatch")
    recover.add_argument("task_id")
    recover.add_argument("reason")
    improve = sub.add_parser("improve", help="Version, evaluate and promote role prompts only")
    actions = improve.add_subparsers(dest="action", required=True)
    actions.add_parser("status")
    propose = actions.add_parser("propose", help="Internal director proposes a worker prompt from completed work")
    propose.add_argument("task_id")
    propose.add_argument("director")
    propose.add_argument("role")
    propose.add_argument("prompt_file")
    propose.add_argument("--rationale", required=True)
    reg = actions.add_parser("register")
    reg.add_argument("role")
    reg.add_argument("prompt_file")
    reg.add_argument("--parent")
    reg.add_argument("--rationale", required=True)
    bootstrap = actions.add_parser("bootstrap")
    bootstrap.add_argument("version")
    suite = actions.add_parser("suite")
    suite.add_argument("file", help="Evaluator-owned JSON list of labelled cases")
    packet = actions.add_parser("packet")
    packet.add_argument("suite")
    compare = actions.add_parser("compare", help="Freeze a baseline/candidate pair before evaluations")
    compare.add_argument("candidate")
    compare.add_argument("baseline")
    compare.add_argument("suite")
    evaluate = actions.add_parser("evaluate")
    evaluate.add_argument("version")
    evaluate.add_argument("suite")
    evaluate.add_argument("answers")
    evaluate.add_argument("--cost-units", type=int, required=True)
    evaluate.add_argument("--evaluator", required=True)
    promote = actions.add_parser("promote")
    promote.add_argument("candidate")
    promote.add_argument("baseline")
    promote.add_argument("suite")
    promote.add_argument("--reviewer", required=True)
    rollback = actions.add_parser("rollback")
    rollback.add_argument("role")
    rollback.add_argument("reason")
    return p


def seed_cef(root, network, evidence):
    plan_path = root / "research_batch3/frozen_experiment_plans.json"
    raw = plan_path.read_bytes()
    receipt = read_json(root / "research_batch3/freeze_receipt.json")
    digest = hashlib.sha256(raw).hexdigest()
    if receipt["sha256"] != digest:
        raise ValueError("Frozen experiment hash mismatch; refusing to seed")
    question = (
        "B3-H1-v1 document feasibility only: can original CEF reinvestment terms "
        "establish a contract-fixed purchase route, contemporaneous NAV publication, "
        "known nonzero participation, and a purchase window continuing after entry? "
        "Read the frozen plan at research_batch3/frozen_experiment_plans.json and "
        "its sample_protocol before selecting sources. Preserve the first 30 ordered "
        "search hits, exclusions and missing fields; require at least 3 independent "
        "funds and 90% critical completeness for later feasibility review. Do not "
        "download prices, change rules, build a simulator or claim returns. "
        "The current packet is a bounded source-planning task when no original "
        "documents have been ingested. Missing sources mean blocked, not feasible."
    )
    cycle = network.create_cycle("B3-H1-v1", question, evidence, digest)
    from .families import FamilyRegistry
    families = FamilyRegistry(root)
    families.initialize()
    family = families.register(
        "B3-H1-v1",
        "CEF contractual reinvestment route switch: transfer-agent open-market buying around payment, not dividend capture.",
        digest,
        "feasibility_pending",
    )
    families.link_cycle(family["family_id"], cycle["cycle_id"])
    cycle["family_id"] = family["family_id"]
    return cycle


def initialize_runtime(root, max_tasks=None, max_concurrent=None):
    root = Path(root)
    network = Network(root)
    policy = {'max_tasks': 12, 'max_concurrent': 3}
    if network.path.exists():
        with closing(sqlite3.connect(network.path)) as db:
            if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='policy'").fetchone():
                row = db.execute('SELECT max_tasks,max_concurrent FROM policy WHERE id=1').fetchone()
                if row:
                    policy = dict(zip(('max_tasks', 'max_concurrent'), row))
    value = network.initialize(policy['max_tasks'] if max_tasks is None else max_tasks,
                               policy['max_concurrent'] if max_concurrent is None else max_concurrent)
    registry = ImprovementRegistry(root)
    registry.initialize()
    budget = BudgetLedger(root)
    if not budget.path.exists():
        budget.initialize('manual-no-spend', 0)
    from .families import FamilyRegistry
    FamilyRegistry(root).initialize()
    from .network import ROLES
    for role in ROLES:
        path = root / 'agents' / 'network' / (role + '.md')
        if path.exists() and registry.active(role) is None:
            version = registry.register(role, path.read_text(encoding='utf-8'), rationale='Maintainer-shipped initial baseline')
            registry.bootstrap(version['id'])
    value['prompts'] = registry.status()['active']
    return value


def main(argv=None):
    args = parser().parse_args(argv)
    root = Path(args.root).resolve()
    try:
        network = Network(root)
        if args.command == "init":
            value = initialize_runtime(root, args.max_tasks, args.max_concurrent)
        elif args.command == "status":
            value = network.status()
        elif args.command == "brief":
            value = network.director_brief()
        elif args.command == "export":
            from .snapshot import export_snapshot
            value = export_snapshot(root, args.archive)
        elif args.command == "restore":
            from .snapshot import restore_snapshot
            value = restore_snapshot(root, args.archive)
        elif args.command == "ingest":
            value = network.ingest(args.source_id, Path(args.file).read_text(encoding="utf-8-sig"), args.published_at)
        elif args.command == "seed-cef":
            value = seed_cef(root, network, args.evidence)
        elif args.command == "next":
            value = network.claim(args.worker, args.role)
        elif args.command == "task":
            value = network.get_task(args.task_id)
        elif args.command == "submit":
            value = network.submit(args.task_id, args.worker, read_json(args.file))
        elif args.command == "fail":
            value = network.fail(args.task_id, args.worker, args.reason)
        elif args.command == "stop":
            value = network.stop(args.reason)
        elif args.command == "resume":
            value = network.resume()
        elif args.command == "recover":
            value = network.recover(args.task_id, reason=args.reason)
        else:
            registry = ImprovementRegistry(root)
            if args.action == "status":
                value = registry.status()
            elif args.action == "propose":
                value = propose_prompt(root, args.task_id, args.director, args.role,
                    Path(args.prompt_file).read_text(encoding='utf-8-sig'), args.rationale)
            elif args.action == "compare":
                value = registry.begin_comparison(args.candidate, args.baseline, args.suite)
            elif args.action == "register":
                value = registry.register(args.role, Path(args.prompt_file).read_text(encoding="utf-8-sig"), args.parent, args.rationale)
            elif args.action == "bootstrap":
                value = registry.bootstrap(args.version)
            elif args.action == "suite":
                value = registry.build_suite(read_json(args.file))
            elif args.action == "packet":
                value = registry.packet(args.suite)
            elif args.action == "evaluate":
                value = registry.evaluate(args.version, args.suite, read_json(args.answers), args.cost_units, args.evaluator)
            elif args.action == "promote":
                value = registry.promote(args.candidate, args.baseline, args.suite, args.reviewer)
            else:
                value = registry.rollback(args.role, args.reason)
        print(json.dumps(value, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, RuntimeError, OSError, KeyError, sqlite3.DatabaseError) as exc:
        print(f"research_loop: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
