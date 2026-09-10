# Operator dashboard

Single-operator web console for the research network. It does not dispatch models or brokers. Python 3.11+ and the standard library are enough.

## Run locally

```sh
export DASHBOARD_PASSWORD='choose-a-long-password'
python go.py --mode dashboard
```

On Windows PowerShell: `$env:DASHBOARD_PASSWORD='...'; py -3 go.py --mode dashboard`. You can also put `DASHBOARD_PASSWORD` in a gitignored `.env` at the repo root.

Equivalent: `python -m dashboard`. The process listens on `0.0.0.0:8787` by default (`DASHBOARD_HOST`, `DASHBOARD_PORT`). If `DASHBOARD_PASSWORD` is unset on a fresh `research_state/`, a password is generated and printed once.

## Local model keys

Keys live in a gitignored `.env` at the repository root. Process environment variables override the file.

Two ways to fill it:

1. **From the console.** Spend → *Provider keys · .env*. Pick a vendor, paste the key, optionally set a default model and base URL, and save. Role routing (`provider:model`) is edited in the same card. The value is written straight into `.env` and applied to the running process, so a paste takes effect without a restart.
2. **By hand.** Copy `.env.example` to `.env` and edit it, then restart.

The console can only write these variables:

| Writable from the UI | Not writable |
|---|---|
| `OPENAI_/ANTHROPIC_/XAI_` `API_KEY`, `BASE_URL`, `MODEL` | `DASHBOARD_PASSWORD` |
| `ROLE_DIRECTOR_PLAN`, `ROLE_RESEARCHER`, `ROLE_DATA_AUDITOR`, `ROLE_REVIEWER`, `ROLE_DIRECTOR_DECISION`, `ROLE_IMPROVEMENT_PROPOSAL` | `RESEARCH_BUDGET_PERIOD`, `RESEARCH_BUDGET_LIMIT_USD`, `RESEARCH_MAX_CALL_USD`, `RESEARCH_USD_PER_MTOK_*` |

The server rejects any other variable name, refuses values containing quotes, newlines, or non-printable characters, and allows plain `http` base URLs only on loopback. `POST /api/env` requires the session cookie and the CSRF header. The audit log records which variable changed and whether it was set or cleared, never the value.

**A key is not an allowance.** Budget variables stay out of the UI because the dashboard must not raise its own spend, so edit `RESEARCH_BUDGET_PERIOD` and `RESEARCH_BUDGET_LIMIT_USD` in `.env` yourself and restart. They replace the placeholder $0 ledger only and cannot raise an existing period.

Once a key and a period both exist, **Dispatch next model call** (Mission or Spend) or Orchestrator `/dispatch [role]` sends **one** leased packet. There is no background loop.

The UI shows provider, model id, and key last-four. `GET /api/env` never returns a secret. Brokers remain disabled.

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
