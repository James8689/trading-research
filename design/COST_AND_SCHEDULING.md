# Cost discipline and scheduling specification

No spending limit has been chosen by James. Keep automatic model calls disabled. Existing configuration call/token/time values are draft engineering bounds, not permission to spend or proof of a dollar cap. No recurring automation is requested or installed as part of this scaffold.

Never make a worker's survival, model access or future subscription conditional on trading P&L. This is an unsafe objective function for research: a short-horizon agent can maximize its chance of survival through excessive tail risk, hidden exposure or selective accounting. Research funding is an exogenous budget; net strategy economics are a separate validation metric.

## Allocate work by information value

For each task record decision it could change, cheapest decisive check, expected source accessibility, maximum effort and stop condition. Prefer checking whether a required field exists before discussing an elaborate simulator. Do not ask multiple workers the same broad question unless a blinded independent judgment is worth its incremental cost.

Initial scheduling policy: at most two candidate families in deep work; three leaf tasks concurrently; one frontier decision after a coherent evidence batch. Work queues may contain more tasks but dispatch only when dependencies, authority and budget are satisfied. Parallelize independent sources; serialize plan changes, shared state and gate decisions.

The director spends frontier calls on disputed facts and research design. Clerical extraction starts with the economy tier after calibration. A standard tier can repair one ambiguous bounded task. One repair attempt maximum for formatting issues; persistent or substantive failure escalates or blocks. Never use recursive self-critique without an attempt cap.

## Budget ledger requirements

Track separately: approved monetary period limit, period start/end, provider billing mode, calls, input/cached/output/reasoning tokens when reported, actual/provider-estimated cost, reserved maximum per-call cost, and unknown charges. Record pricing source/version/date and units; null means unknown, never zero. Subscription limits and API dollars are different ledgers.

Pre-dispatch admission requires sufficient unreserved budget for worst permitted request/tool charges. If a runtime cannot cap a request or expose reliable pricing/usage, it cannot promise a hard monetary limit. Use subscription-only or manual mode when required by user preference; it still consumes usage allowance. Timeouts do not guarantee billing stops. Reconcile before another call after an uncertain failure.

Data purchases and cloud compute are separate from model cost and need explicit budgets. Include human review/rework in model comparisons. Never present fewer tokens as proven cheaper if price or task quality differs.

## Model calibration

Use `evals/research_judgment.json` only as the seed evaluation set. Keep expected labels out of task packets. Evaluate critical-error rate, evidence fidelity, valid-output rate, repair frequency, elapsed time and measured cost per accepted task. Two sound-but-unproven examples guard against a cheap model that rejects everything.

The small fixture set is a screening test, not sufficient statistical certification. Build a separate unseen set with authentic source ambiguity before deploying a tier. Critical leakage/accounting misses require review and restrict the role until fixed. Model/provider/prompt changes trigger a calibration rerun; existing strategy evidence stays unchanged.

## Stop/resume semantics

Every run must have finite cycle/call/time bounds and a budget-period identifier. A stopped run does not reset accounting when resumed. Monthly budget rollover uses the configured period boundary, not process restart. A future scheduler should wake only for ready tasks or meaningful new data; empty polling should not invoke a model.

Do not run historical validation repeatedly while waiting for future sessions. Do not requeue a permanently rejected family automatically. Frontier `continue` means the next explicitly scoped batch, not unlimited permission. Emergency STOP blocks dispatch immediately; in-flight work is reconciled and preserved. Status reports should notify on material outcome/blocker, not every idle poll.
