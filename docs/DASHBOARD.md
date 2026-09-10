# Operator dashboard

Single-operator web console for the research network. It does not dispatch models or brokers. Python 3.11+ and the standard library are enough.

## Run locally

```sh
export DASHBOARD_PASSWORD='choose-a-long-password'
python go.py --mode dashboard
```

Equivalent: `python -m dashboard`. The process listens on `0.0.0.0:8787` by default (`DASHBOARD_HOST`, `DASHBOARD_PORT`). If `DASHBOARD_PASSWORD` is unset on a fresh `research_state/`, a password is generated and printed once.

Open the printed URL, sign in, and keep the process running. Sign-in cookies last 30 days and are stored in `research_state/ui.sqlite3`, so a restart of the same volume keeps you logged in only after you sign in again on that browser; the **messages, ideas, jobs, families and research queues** survive the restart.

## What persists

All of this is gitignored under `research_state/`:

| File | Contents |
|------|----------|
| `network.sqlite3` | Sources, cycles, tasks, leases, memory, decisions |
| `improvement.sqlite3` | Prompt versions and gates |
| `budget.sqlite3` | Fail-closed spend ledger |
| `families.sqlite3` | Minimal opportunity-family registry |
| `ui.sqlite3` | Sessions, orchestrator transcript, ideas, jobs, API-key aliases, audit log |

GitHub still does not carry runtime databases. Back them up by copying `research_state/` or (for the original three research DBs) `python -m research_loop export archive.zip` while the network is idle.

## Cloud / internet access

Run the same command on a host you control (Fly, Railway, a VPS, this machine with a reverse proxy). Put TLS in front of it. Set:

```sh
DASHBOARD_PASSWORD=...
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8787
DASHBOARD_SECURE=1   # optional; sets the Secure cookie flag behind HTTPS
```

Mount `/app/research_state` as a persistent volume. A Dockerfile is in the repo root. There is no public signup; whoever knows the password is the operator. Treat the password like a credential.

The dashboard is not a multi-tenant product. Do not publish it without TLS and a strong password.

## Authority

Writes go through `Network`, `FamilyRegistry` and `BudgetLedger`. The UI cannot raise the allowance, reset leases, or promote prompts. The orchestrator box talks to the **internal director console**: standing instructions and slash-commands (`/help`, `/seed-cef`, `/stop`, `/resume`, `/claim`, `/idea`, `/brief`, `/status`). Free-text messages are stored; they do not start a model while `manual-no-spend` remains in force.

The director still cannot approve its own prompt changes or waive scientific gates. Reviewer packets stay blinded in the worker path; opening a packet in the UI is an audit action, not a way to feed extra context into that role.
