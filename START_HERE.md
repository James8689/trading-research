# Start here: maintainer and internal director handoff

James authorized implementation of the research orchestration network, director-managed worker prompts, separated durable context and repeatable startup. This supersedes the older design-only restriction. No paid provider allowance or live trading is implied.

Read:

1. `AGENTS.md` and `design/STATUS.md` for scope and verified state.
   Read `design/OPPORTUNITY_ENGINE.md` for the updated domain-general mission and implementation order; the existing CEF runtime is a first workflow, not the whole engine.
2. `docs/ORCHESTRATION.md` for the supported entry points and authority boundaries.
3. Latest `HANDOFF.md` entry; older entries are historical.
4. `research_batch3/SYNTHESIS.md` and frozen plan/receipt before research.

Run `python go.py` for the offline demonstration, `python go.py --mode check` for tests, or `python go.py --mode start` to prepare the first manual CEF cycle. This does not dispatch a model. Python 3.11+ and its standard library suffice.

## Context and ownership

The coding agent maintains software. The internal director owns research planning, evidence decisions and proposed worker-prompt changes. The controller enforces dependencies, source citations, immutable task inputs, prompt comparison gates and task limits. The director cannot change its own evaluator or controller policy through a worker result.

Runtime state is in ignored `research_state/network.sqlite3`, `improvement.sqlite3` and `budget.sqlite3`, not the old state.json. Use `python -m research_loop brief` for bounded director context and `task TASK_ID` for exact saved packets/results. Worker memory is separated by candidate and role; old versions remain available. Reviewers do not inherit prior interpretations. Existing leases survive restart without redispatch. Do not replace them or reset budgets to make progress.

Use the private export/restore commands to move idle runtime state. GitHub carries code and research artifacts, not raw runtime/evaluator databases. A downloaded repo can initialize from scratch without this chat. An interrupted research run resumes from its private snapshot.

## Next work

The manual network and synthetic gates are implemented. A future unattended provider adapter still needs bounded calls, real usage reconciliation, authenticated role separation and independently protected evaluation data. No API budget has been chosen. The first scientific task remains original-document feasibility for B3-H1-v1; sources have not been acquired by the implementation work. Keep both B3 plans frozen and preserve every missing/excluded observation.

Do not execute the superseded `research_loop/runner.py` provider path. Do not read raw market archives into model context. Update handoff/checkpoint/inventory, verify, commit and push after meaningful work so replacement agents can resume.
