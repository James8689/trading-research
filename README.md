# Trading research and orchestration

This private repository preserves the research archive and a runnable, bounded research-agent network. No strategy is validated.

The long-term mission is a domain-general **opportunity blueprint factory**: discover, reject, refine and validate opportunities for automated online systems, then hand implementation-ready blueprints to a separate builder. Trading is the initial focus. Read [the authoritative direction](design/OPPORTUNITY_ENGINE.md); the autonomous discovery and multi-provider layers are still future work.

## Run from a fresh checkout

With Python 3.11 or newer, no extra packages needed for the network:

```sh
python go.py
python go.py --mode check
python go.py --mode start
```

The default runs a complete **synthetic offline demonstration**. `check` runs tests and archive verification. `start` prepares the real CEF document-feasibility queue with durable state; it does not start a model process. On Windows you can use `py -3` instead of `python`.

The network has an internal director, independent researcher/data auditor/reviewer roles, candidate-scoped memory, immutable packets, prompt-improvement evaluations and rollback. The internal director owns worker-prompt proposals; the coding maintainer owns controller and evaluator code. Automatic provider dispatch, paid inference and brokerage execution are not implemented in the supported runtime.

Read [the operating guide](docs/ORCHESTRATION.md) for commands, context ownership, prompt promotion, interruption recovery and private runtime backups. Read [START_HERE.md](START_HERE.md) to resume as a new coding agent.

- [Current status](design/STATUS.md) and [handoff](HANDOFF.md).
- [Design specification](design/README.md): broader intended architecture and future acceptance criteria.
- [Research synthesis](research_batch3/SYNTHESIS.md) and [frozen plans](research_batch3/frozen_experiment_plans.json).
- [Historical reproduction](docs/REPRODUCIBILITY.md) and [data catalog](docs/DATA_CATALOG.md).

The archived runner at `research_loop/runner.py` is superseded; its provider path is explicitly disabled. Use `python -m research_loop` for supported operations. Synthetic tests establish controller behavior, not trading returns or measured model improvement.
