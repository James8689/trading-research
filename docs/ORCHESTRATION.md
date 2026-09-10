# Research orchestration: runnable manual v1

The network is a standard-library Python application. It has no provider adapter, background service or brokerage endpoint. The offline demo exercises the complete control flow with scripted workers. Assisted mode creates real research packets for named agents or people to process. It does not start an autonomous model by itself.

## Download and run

Clone the private GitHub repository with an authorized GitHub account. Install Python 3.11 or newer, then from the repository root run:

```sh
python go.py
```

On Windows, `py -3 go.py` works when Python is registered with the launcher. The research network needs no pip installation, API keys, previous chat or historical-report dependencies. `requirements.txt` belongs to the older research/report scripts, not this entry point.

The default is a repeatable synthetic demonstration in temporary storage: six tasks, a rejected premise, a director-authored worker prompt, frozen evaluation comparison, promotion, rollback and uncertain-cost reconciliation. Its result is a controller test, not a model-quality or trading result.

```sh
python go.py --mode check
python go.py --mode start
python go.py --mode dashboard
python -m research_loop brief
python -m research_loop next director --role director_plan
```

`check` runs unit tests and verifies archived data/frozen-plan hashes. `start` initializes persistent state, bootstraps the six shipped role prompts and seeds the frozen CEF document-feasibility question. Repeating it does not reset budgets, prompts or create duplicate cycles. It leaves packets unclaimed until `next`. With no original documents ingested, this is a source-planning queue, not evidence of feasibility. Runtime defaults allow 12 lifetime task claims and 3 concurrent leases; raising limits requires an explicit controller change, not restarting.

`dashboard` serves the single-operator UI on port 8787 (see `docs/DASHBOARD.md`). It is a browser for the same SQLite records plus a persistent director console. It is not an unattended model loop. Set `DASHBOARD_PASSWORD` and keep `research_state/` on durable storage if the process should survive a host restart.

## Three distinct actors

**Coding maintainer:** changes code, controller invariants, schemas, shipped baseline prompts and tests through reviewed commits. This is the coding agent's role during construction. It is not an invisible decision step in normal research.

**Internal director:** runs director_plan, director_decision and improvement_proposal with one stable identity for the latter two. It defines bounded work, reads evidence/reviews and proposes improvements to researcher, data_auditor and reviewer prompts. It sees durable packets and a bounded resume brief, not this chat history. It cannot approve its own prompt changes, rewrite the evaluator, expand budget or change scientific gates through a result.

**Deterministic controller:** leases tasks, validates result shapes/citations, records hashes/history and enforces the graph and improvement gate. No model decides whether duplicate dispatch, reset budgets or missing evaluations are acceptable.

The workflow is director_plan -> researcher and independent data_auditor -> blinded reviewer -> director_decision -> director-owned improvement_proposal. The reviewer receives original sources and cited evidence without upstream interpretations. The director receives all relevant outcomes. A final continue means ready for human feasibility review; it does not declare the complete B3 sample adequate or validate a strategy.

## Evidence and task protocol

```sh
python -m research_loop ingest https://original.example/filing source.txt --published-at 2026-09-01T15:00:00Z
python -m research_loop seed-cef --evidence SOURCE_EVENT_ID
python -m research_loop next reader-a --role researcher
python -m research_loop submit TASK_ID reader-a result.json
python -m research_loop task TASK_ID
```

The URL is a source identifier; ingest never downloads it. Supply an original source or an explicitly bounded excerpt with trustworthy provenance. Unknown publication time stays null. The supplied publication timestamp is operator metadata, not independently authenticated by the controller. Content is capped at 16,000 characters; split documents deliberately rather than dropping trailing clauses. Cycles bind immutable source events and a verified plan hash. New evidence creates a new cycle rather than changing leased packets.

Results have exactly six fields:

```json
{
  "summary": "The document does not establish mandatory participation.",
  "decision": "blocked",
  "evidence": [],
  "uncertainty": "Original contractual source has not been supplied.",
  "next_action": "Obtain and independently verify the original terms.",
  "memory": "Participation remains unknown; this is not a failed return test."
}
```

Evidence entries use `source_id` equal to an ingested event ID and `quote` equal to an exact nonempty source substring. Quotes are checked mechanically; whether they support the conclusion still requires independent review. Empty evidence is permitted only for blocked/inconclusive results. All completed decisions, including rejection and blocked findings, reach review and director stages. A runtime failure instead blocks dependent tasks and preserves the failed attempt for explicit recovery.

## Context separation and refresh

The shared database is already implemented: `network.sqlite3` is the research record, `improvement.sqlite3` holds version/evaluation records, and `budget.sqlite3` holds accounting. Logical separation makes ownership explicit; it does not hide data from a process with the same filesystem permissions. Agents submit through the controller's API/CLI. They should not issue arbitrary SQL or update another worker's memory directly.

- Canonical records: immutable source events, frozen packets/results, decisions, prompt versions and attempts in SQLite.
- Working memory: separate candidate-and-role history with a current pointer, source task ID and hash. Each accepted result advances only that context. Old versions remain available.
- Reviewer: no prior interpretive working memory; original sources and bounded citations only.
- Director: `brief` provides a small resume index; `task ID` retrieves the exact detailed packet/result when needed. The improvement task receives the cycle's reports.
- Evaluation: packets exclude answer labels; paired versions and suite content are frozen before answers are scored. No answer keys enter normal research packets.

Packets are capped at 20,000 characters and stored memory at 4,000. Cycle admission reserves downstream capacity and never truncates source text or hard constraints. Dependency reports and working memory can be explicitly labelled excerpts with hashes and references to full saved artifacts; nothing is silently dropped. Already leased packets keep their exact prompt and memory even after a new version is promoted. The next claim picks up the newly active prompt. Replacing the coding session or director process does not erase state.

Manual worker names are accountability labels, not authentication. A same-user process can read or edit local databases; prompt boundaries are not OS isolation. A future provider deployment needs separate worker/evaluator identities, filesystem capabilities and secret-free packet delivery. This v1 does not claim sealed holdouts or adversarial containment.

## When the director acts and how work stays aligned

The dependency graph is the readiness signal. A task claim transaction checks whether all required predecessors completed and whether identity/capacity rules permit dispatch. Researcher and data auditor work independently after planning; their completion unlocks review; review unlocks a director decision; that decision unlocks the same director's improvement task. Rejection and missing-evidence results still reach the director. Runtime failures remain visible as failed/blocked tasks rather than being retried silently.

In manual mode, `next director --role director_decision` claims the ready decision packet. Nothing continuously polls or wakes a model. A future provider adapter will consume those ready packets and return results; the graph and durable record already define when it should act. The controller, not the worker, determines readiness.

Every task in a cycle inherits the same candidate ID, bounded question, frozen-plan hash, original source IDs and research constraints. Role prompts define complementary responsibilities against that shared question. The shipped first question is CEF document feasibility, and seed-cef verifies the experiment receipt before creating it. Workers cannot replace the cycle question or plan through a result. Changing the mission or scientific rules is an explicit new version, not a memory rewrite. This aligns work toward trustworthy evidence and a reproducible decision, including a useful rejection, rather than rewarding agreeable answers or short-term P&L.

## Director-managed prompt improvement

After completing improvement_proposal, the director can register its proposed worker prompt:

```sh
python -m research_loop improve propose IMPROVEMENT_TASK director researcher revised.md --rationale "The audit found omitted timing checks."
```

The controller verifies task ownership, completed proposal status and eligible target role. It stores parent prompt, proposer, task/result/packet hashes and rationale. The prompt remains a candidate.

An independent evaluator prepares a fresh suite of `id`, `prompt`, `expected_decision`, `critical` cases. Freeze one baseline/challenger pair before evaluation:

```sh
python -m research_loop improve suite cases.json
python -m research_loop improve compare CANDIDATE_ID BASELINE_ID SUITE_ID
python -m research_loop improve packet SUITE_ID
python -m research_loop improve evaluate BASELINE_ID SUITE_ID baseline-answers.json --cost-units 100 --evaluator evaluator-a
python -m research_loop improve evaluate CANDIDATE_ID SUITE_ID candidate-answers.json --cost-units 90 --evaluator evaluator-b
python -m research_loop improve promote CANDIDATE_ID BASELINE_ID SUITE_ID --reviewer independent-reviewer
python -m research_loop improve rollback researcher "Regression found in subsequent source work."
```

Answers contain one `case_id` and `decision` per case. Cost units are explicitly arbitrary evaluation units, not inferred dollars. Operator-reported answers/costs are inputs; this version does not run models or authenticate provider telemetry. The proposer cannot evaluate or approve its own change. Promotion requires zero critical misses, no accuracy loss and an accuracy or cost improvement. The same semantic suite cannot be reused under renamed case IDs. Rejected comparisons and rollbacks are retained.

This is an evaluation mechanism, not proof that prompts have improved. The included small synthetic suites test software behavior. Real prompt adoption requires representative independently held cases, grounded reasoning checks and measured usage. Director/evaluator policy changes remain maintainer work, outside the director proposal interface.

## Stop, interruption and backups

```sh
python -m research_loop stop "Pause before another packet"
python -m research_loop status
python -m research_loop task TASK_ID
python -m research_loop recover TASK_ID "Confirmed interrupted; retain as failed"
python -m research_loop resume
python -m research_loop export private-runtime.zip
```

Restart never reissues a leased task. Submit its retained result, or explicitly mark it failed with recover. No automatic retry is made. Stopping blocks new claims but permits result reconciliation. Resume does not reset task caps. BudgetLedger separately implements atomic reservations, unresolved-charge blocking and truthful overrun accounting for a future provider; the supported entry point initializes a zero-dollar ledger and makes no paid calls.

GitHub stores code, prompts, tests, design and research artifacts. Runtime databases and raw packets stay local and are ignored by Git. For transfer, stop work and export an idle private runtime snapshot; restore it into an empty runtime with `python -m research_loop --root DESTINATION restore private-runtime.zip`. Backups contain evaluator answer keys and must not be handed to workers. Each database is copied consistently with SQLite backup; there is no cross-database transaction snapshot, so operators must keep the system idle during export. Historical checkpoint.py excludes runtime state and uses this dedicated path instead.

## Next engineering boundary

Before real unattended research: implement and test a single provider adapter with authenticated role identity, bounded packet delivery, real usage reconciliation and evaluator isolation. Choose spending mode and a finite allowance, then run one real CEF document cycle and independently assess its evidence. No background scheduler, provider subscription, source download or trading integration was activated by this implementation.
