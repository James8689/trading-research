"""Manual, bounded research orchestration. No provider or broker dispatch."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from .network import Network
from .improvement import ImprovementRegistry


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".", help="Project root with research_state storage")
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Initialize once; existing caps cannot be reset")
    init.add_argument("--max-tasks", type=int, default=12)
    init.add_argument("--max-concurrent", type=int, default=3)
    sub.add_parser("status")
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
    return network.create_cycle("B3-H1-v1", question, evidence, digest)


def main(argv=None):
    args = parser().parse_args(argv)
    root = Path(args.root).resolve()
    try:
        network = Network(root)
        if args.command == "init":
            value = network.initialize(args.max_tasks, args.max_concurrent)
            ImprovementRegistry(root).initialize()
        elif args.command == "status":
            value = network.status()
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
            if args.action == "register":
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
    except (ValueError, RuntimeError, OSError, KeyError) as exc:
        print(f"research_loop: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
