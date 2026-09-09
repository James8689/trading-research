# Batch 3: mechanisms and frozen feasibility plans

No candidate is backtest-ready. No new return series or bulk data were acquired. Prior strategies remain eliminated baselines, and old historical evaluation periods are consumed.

Select two ideas for source feasibility only:

1. **B3-H1-v1: CEF contractual reinvestment route switch.** A plan agent may buy existing shares rather than issue new ones. The frozen version requires a route fixed by original contract, contemporaneous NAV publication, known nonzero participation and a purchase window continuing after entry. If these clauses cannot be established, reject this version rather than loosen it. This has potential repetition but uncertain observable flow.
2. **B3-M2A-v1: capped cash-election unwanted-share allocation.** Holders requesting cash receive some stock when aggregate cash is capped. The hypothesis concerns temporary disposal pressure, not dividend capture. Final cash-election demand, allocation and knowledge times must be observable. Payment plus three sessions is an explicit timing hypothesis, not proven broker delivery.

These are proposed combinations of known mechanisms; unprecedented novelty and alpha are not established. Full eight-part hypotheses and primary-source links are in the agent reports. `frozen_experiment_plans.json` specifies capital, timing, entry/exit, risk, cost/latency stress, controls, future validation and pass/fail gates. Its receipt preserves a SHA-256 freeze. No execution assumptions were derived from candidate returns.

The independent adversary preferred cash-election allocation plus all-cash ETF liquidation, keeping CEF routing in reserve. Root selected CEF routing for its potential repeatability, with the adversary's stricter clause gates. This disagreement is preserved in `agent3_adversarial.md`; it is not consensus validation. Ten pre-freeze specification objections were addressed in `freeze_plans.py` before serialization. Quote fills remain hypothetical and matched controls support predictive, not causal, evidence.

## Preserved alternatives

- H2 preferred-redemption proceeds migrating to a sibling: reserve; optional reinvestment, broker support and spread risk.
- H3 rejected tender inventory: data-blocked; actual broker release unavailable.
- H4 rights oversubscription refunds: rejected for current testing; allocation/refund observability and dilution confounds.
- H5 employee tax-settlement route change: data-blocked; future employee vest schedules and offsetting issuer financing unknown.
- H6 / M2-D partial redemption remnants: rejected for current scope; no robust forced seller or public account allocation data.
- M2-B liquidation cash-state misclassification: reserve; sparse, AP arbitrage and contemporaneous cash valuation/payout costs unresolved.
- M2-C fractional-entitlement sales: data-blocked; actual fractional quantity and disposal timing generally unavailable.
- Constraint-release / residual repurchase capacity: exploratory source leads only; ability to buy is not a forced buyer.

Next action: bounded document probes in the frozen plans, retain every missing/excluded event, then decide whether either idea deserves prices and a simulator. Untouched validation is prospective and conditional on completing gates before its start; never backfill a missed window. All failed ideas and agent disagreements remain in this repo.
