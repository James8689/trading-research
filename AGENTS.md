# Trading research project instructions

## Mission

**Current scope (September 9, 2026): implement the bounded research orchestration network.** James subsequently requested code, director-managed prompt improvement, separated durable contexts and a repeatable GitHub checkout/start workflow. This supersedes the earlier design-only scope. Read `design/STATUS.md` first. Offline/manual implementation and synthetic tests are authorized; no paid provider allowance or live trading is implied. Existing research plans remain frozen.

Build an autonomous opportunity research and refinement engine whose terminal product is an implementation-ready opportunity blueprint for a separate builder system. Trading is the initial and likely primary domain; the core engine must support other plausibly automated online opportunities. Read `design/OPPORTUNITY_ENGINE.md` for the authoritative mission, creative/sanity separation, family memory, model preferences and roadmap. Preserve existing scientific controls. The modeled $2,500 account and approximately 25% drawdown ceiling remain constraints of the existing frozen trading experiments, not universal domain rules. No live trading or broker order submission is authorized by this repository.

## Research standards

- Generate original hypotheses from first principles. Do not merely copy or threshold-tune published moving-average, RSI, breakout, volume, momentum, or overnight rules.
- Explain the economic mechanism before inspecting results: forced flows, delayed information, participant constraints, or another reason the opportunity might persist.
- Use AI for hypothesis generation, feature construction, and falsification only when it adds measurable value. The eventual live rule should be deterministic and inexpensive.
- Freeze rules before viewing new results. Separate development data from an untouched validation period.
- Enforce point-in-time inputs, no lookahead, realistic spread/slippage/latency assumptions, cash and whole-share constraints, and concentration analysis.
- Preserve failed ideas. Never select a historical winner and call it validated.
- Score workers on correct scientific work, including rejection and falsification. Preserve mechanism-family lineage, blockers and evidence-based reopening reasons.
- Separate memory/context, prompt and routing improvement. Require recurring evidence before automatic prompt rewrites; keep independent evaluation/versioning gates. Do not conflate the coding maintainer with the internal portfolio director.
- Apply `design/EVIDENCE_LED_DEVELOPMENT.md`: complete a real bounded research cycle before expanding architecture, measure adaptation independently, and require builder feasibility review before marking a blueprint implementation-ready. These new gates are design contracts pending runtime enforcement.
- The operator dashboard (`python go.py --mode dashboard`, `docs/DASHBOARD.md`) may drive the manual network. It must not bypass `Network` methods, raise spend, or describe itself as autonomous model research.
- Run data-heavy work in Python and save compact JSON summaries. Do not paste raw data into the agent conversation.
- Update `HANDOFF.md` after each material batch and run `checkpoint.py --save` after updating it.
- After checkpointing, refresh `data_inventory.json`, verify it, commit and push the completed documentation batch to the authorized private GitHub repo. A local commit is not a remote backup. Report any push failure and the exact remaining commit. Never include credentials or raw model transcripts.

## Agent roles

When delegation is available, use bounded roles: hypothesis generator, data-availability auditor, adversarial falsifier, and result synthesizer. Agents must write their findings to files. The synthesizer reads summaries, not raw datasets. Parallel agents should work on independent hypotheses and must not silently change shared rules.

## Deployment gate

Research orchestration may now be built. No trading bot or order execution is authorized by this implementation task. Strategy implementation still requires reserved validation, cost stress tests, concentration checks, and 30–60 sessions of live quote or shadow-order testing. Robinhood read-only access succeeded in the conversation; no repository broker adapter has been tested.
