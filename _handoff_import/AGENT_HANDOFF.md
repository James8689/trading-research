# Handoff for the next agent (trading-research)

James wants this work on **https://github.com/James8689/trading-research**, default branch **master**.

A previous cloud agent was started from **James8689/blog**, so `cursor[bot]` could not push here. Do **not** put this code in the blog repo. You are in the right repo. Commit/push on branch `cursor/research-dashboard-1f7e` (or a new `cursor/...` branch) and open a PR into **master**.

## What was built

Password-protected operator dashboard for the existing research network.

```sh
export DASHBOARD_PASSWORD='choose-a-long-password'
python go.py --mode dashboard
```

- Listens on `0.0.0.0:8787` (`DASHBOARD_HOST` / `DASHBOARD_PORT`).
- Stdlib only. No pip. No model dispatch. No broker.
- Persistence is gitignored `research_state/*.sqlite3` (network, improvement, budget, families, ui).
- Writes go through `Network` / `FamilyRegistry` / `BudgetLedger`, never raw SQL.
- Orchestrator chat persists standing instructions. Slash commands: `/help` `/brief` `/status` `/seed-cef` `/stop` `/resume` `/idea` `/claim`.
- Minimal family registry: `research_loop/families.py`. `seed-cef` registers B3-H1-v1.
- Spend page shows the fail-closed ledger (currently `$0`, admission blocked) plus API-key **aliases only** (never secrets).

Docs: `docs/DASHBOARD.md`, latest `HANDOFF.md` entry dated September 10.

## How to apply this zip

From a clean `trading-research` checkout on `master` at `54577e2` (or current origin/master if it is still that commit):

```sh
cd trading-research
unzip dashboard-handoff.zip
# files overlay the repo; AGENT_HANDOFF.md can stay or be deleted after reading
python go.py --mode check
```

If you prefer git history instead of overlay, this zip also contains:

```sh
git fetch dashboard-changes.bundle HEAD:cursor/research-dashboard-1f7e
git checkout cursor/research-dashboard-1f7e
```

or:

```sh
git checkout -b cursor/research-dashboard-1f7e origin/master
git am dashboard-changes.patch
```

Then:

```sh
git push -u origin HEAD
```

Create the PR against **master**, not main.

## Verify

```sh
python go.py --mode check   # 61 tests + 153 archive hashes when this was written
export DASHBOARD_PASSWORD=test
python go.py --mode dashboard
```

Browser: login → Mission (spend blocked, CEF seed) → Roles → Spend → Families → Orchestrator (send a note and `/help`) → Audit.

## Do not

- Do not run `research_loop/runner.py` provider path.
- Do not live-trade or enable paid model spend without James choosing an allowance.
- Do not unfreeze B3 plans or retune rejected backtests.
- Do not treat this UI as autonomous agents. Roles are queued tasks; the director is a persisted console, not a running model.

## Next product work James already asked for

After this lands: keep the dashboard, then the scientific slice is still **one real B3-H1-v1 document-feasibility cycle** (ingest original filings; a reject/block counts as success). Cloud hosting of the UI is `DASHBOARD_PASSWORD` + persistent `research_state/` volume; TLS in front; single operator.

## Commits already made (if you import the bundle/patch)

- `74f5597` Add password-protected operator dashboard with durable director console
- `82d616d` Put the director composer above the transcript so it stays visible
