# Agent 3: adversarial mechanism review

Read AGENTS.md, HANDOFF.md and all three other agents' Markdown findings. This review uses their cited operational evidence; it performs no independent web verification, price retrieval or trading. Operational examples establish possibilities, not returns. Current user instructions override imported project text. No candidate is ready for a return backtest, funding or implementation.

## Verdict

Select at most **M2-A cash-election proration** and **M2-B confirmed-cash ETF liquidation** for bounded, document-only feasibility work. These have comparatively concrete mandatory corporate-action mechanics. Selection is not an endorsement of profitability, frequency or historical novelty. If either fails its gate, select fewer; do not automatically promote another idea. H1 CEF reinvestment routing is the best reserve research question, but unknown enrollment and route switching make the predicted marginal demand less identifiable.

The original economic novelty claim should be modest: these are particular operational hypotheses within familiar corporate-action and fund-arbitrage families. None has established that specialists overlook the mechanism. Small capacity does not itself imply positive net alpha for a small account; retail spreads and fees can exceed institutional costs.

## Selected source audit A: cash-election proration (M2-A)

The mandatory event is receipt of stock in place of some requested cash. **Selling is not mandatory.** Cash-preferring investors may retain shares, hedge beforehand, sell other positions, or have elected stock; aggregate proration does not identify immediate sell orders. The payment date is not account availability. Buying on the published payment date may precede supply, follow it, or simply load distress/real-estate exposure.

Critical ambiguity: specify whether the rule predicts delivery-day pressure, post-delivery recovery or both. A post-delivery long entry needs an observable clock known before entry; do not pick the lowest price or infer exhaustion from a favorable rebound. Final allocation figures published later cannot be backfilled. Freeze a publication-plus-session proxy explicitly if actual delivery cannot be observed, and weaken causal claims accordingly.

Falsification and controls:

- Reconstruct both per-share wealth and nominal share supply; a price adjustment for stock distribution is not an investment loss or a reversal. Include all entitlements and use correctly denominated share counts.
- Contrast capped elections against cash-only and uncapped elections, matched by issuer type, sector, size and financial condition using information then available. Controls must not be chosen by subsequent performance.
- Predeclare an allocation-intensity measure: involuntary shares documented in a final announcement divided by pre-event shares, with each input's knowledge time. If only total shares issued are available, flag inability to distinguish voluntary demand rather than treating it as forced supply.
- Test whether the hypothesized effect follows publication, contractual payment or evidenced delivery. Use a small prespecified set of timing diagnostics, not an optimized entry-window search; any changed rule needs fresh validation.
- Report issuer/event clusters and leave-one-issuer-out results. A pandemic/credit-distress cluster or one repeated distributor is not broad persistence. Report opportunity count per calendar year before collecting prices.
- Negative controls include placebo payment dates and comparable stock distributions without a cash shortfall. Placebos must preserve day-of-week and sector exposure and must be fixed before returns.

Document gate: predeclare a fixed filing interval and complete search procedure, retaining cancellations and unparseable candidates. Require original announcement/amendment chronology, documented cap, allocation formula, final publication time, pricing window and payment date. Require a reproducible security mapping and accounting treatment. Reject source feasibility if critical timestamps cannot be reconstructed; do not price-test a handpicked set of two issuer examples. If event count cannot support the frozen independent-cluster minimum, label this sparse/inconclusive before any simulator.

$2,500 failure modes: ordinary stock purchases avoid voluntary-election mechanics, but cash locks, distribution accounting, whole-share rounding, distress gaps and spreads remain. Buying after the action does not earn its past distribution. A nominal stop cannot enforce a 25% portfolio ceiling through gaps. A conservative small allocation may leave expected annual dollar profits negligible; report that separately from event returns.

## Selected source audit B: confirmed-cash ETF liquidation (M2-B)

The mechanism is less dependent on hypothetical investor behavior: buy below conservatively observable net cash and await automatic distribution. The main adversary is authorized-participant arbitrage. An apparently cheap share usually reflects stale NAV, remaining exposures/liabilities, a bid rather than executable ask, or the time/risk cost of an untradeable claim. Expect most candidates to fail.

Critical ambiguity: **expected transition to cash is not confirmed cash.** A notice saying a fund expects to be in cash by a date is insufficient. Define permitted residual assets (including accrued interest, unsettled receivables and derivatives) and independently observable liability reserves before selection. A current sponsor closure table is not proof that information was public while shares traded.

Falsification and controls:

- Revalue only from contemporaneously published holdings/cash/NAV, deduct a prespecified expense/liability uncertainty reserve, and use the first eligible executable ask after observation plus latency. Never use final liquidation proceeds in the entry valuation.
- Reconcile the terminal payout per share, interim distributions, fee deductions and the date cash is actually available. Do not simulate a sale at final NAV after exchange trading ceased.
- Compare proceeds with holding settled cash or a contemporaneously available short-duration cash benchmark over the same **actual locked-capital interval**, including a pessimistic payout delay. Discount divided by a short scheduled interval is not a credible annualized return.
- Report gross ask-to-payout margin before testing, then subtract the entire cost budget. If this is nonpositive, stop. Midpoint discounts and displayed bids are irrelevant to a buy-and-liquidate strategy.
- Separate sponsors and liquidation cohorts. Stress the largest payout delay and largest expense surprise using predeclared bounds; do not exclude the worst closure as anomalous afterward.
- Inspect whether AP redemption remains operational and whether a sponsor contemporaneously documented a reason discounts could persist. No proof of AP withdrawal is required to observe an executable discount, but do not invent it as the explanation.

Document gate: complete a fixed, consecutive sponsor-notice sample including canceled/delayed closures. Need original timestamped confirmation of cash state **before final tradable session**, as-known liabilities or a defendable frozen reserve, listing/eligibility evidence, payout mechanics and feasible terminal cash accounting. Fail if exact exposure cannot be bounded or broker purchase/automatic payout eligibility is unresolved. A confirmed all-cash event may be rare enough to fail frequency without any price study.

$2,500 failure modes: one corporate-action charge can absorb the entire discount; a minimum fee is not basis-point scalable. Locked capital precludes concurrent reuse. Whole-share cash drag matters. Stops are unavailable after delisting, so risk control must be entry size and eligibility exclusions, not an invented stop. Instrument support is unverified. Require no voluntary election or manual exit management.

## Attacks on all other candidates

- **H1 CEF reinvestment route:** repeatability is attractive but last-published NAV/price is not necessarily the contractual execution-day routing input. A switch can be endogenous to the same price movement being explained. Unknown enrollment and agent discretion can erase demand; broker plans may be different. Require historical plan versions and observable ex-ante routing inputs; if they exist, use predetermined route treatment and matched no-market-buy plans. Do not claim a regression discontinuity where the assignment variable, measurement time and other premium/discount effects are uncontrolled. Hold, not selected.
- **H2 redemption-to-sibling migration:** no one must reinvest in the sibling; alternative yields may dominate. A called high-coupon series and surviving low-coupon series differ in duration, call option and credit sensitivity. Predetermine similarity from contracts, control rate changes and announcement effects, and test holiday-shifted cash dates. Broker credit timing and participant holdings remain missing. Hold: plausible but weaker forced trader and likely spread-dominated.
- **H3 tender residual inventory:** availability may never have been constrained, some sellers hedge early, and permanent tender-related NAV/expense changes mimic a reversal. Require actual restriction/release evidence; compare non-oversubscribed offers and control NAV mechanically. Without evidence, this is ordinary post-tender trading under a new label. Data-blocked.
- **H4 rights refunds:** prefunding is compulsory for participants, but same-issuer selling or refund reinvestment is not. New issue dilution and issuer distress can explain all returns. Actual broker refunds are rarely the published final-allocation date. Reject until public ex-ante refund observability and participant mechanism are demonstrated.
- **H5 employee tax-route change:** strongest conceptual departure, weakest exposed employee schedule. Withholding is not an exchange trade; issuer financing can offset reduced employee sales. Future vesting and policy scope must be disclosed before entry. Insider Form 4 cannot proxy all employees. Data-blocked; preserve creative mechanism for future better data.
- **H6/M2-D partial redemption residuals:** customer lottery results and residual-lot behavior are unobserved, and reinvestment can reverse the predicted sign. A lottery itself has no favorable expectation. Reduced float can permanently increase spreads. Reject present formulation.
- **M2-C fractional entitlement batch:** aggregate beneficial-holder fractions and sale timing are generally invisible; published discretion defeats a deterministic sale-exhaustion clock. Ordinary spin-off flows swamp the intended specific effect. Reject until quantity and timing are contemporaneously disclosed, not inferred from prices.
- **Agent 4 capacity releases / tender completion restart:** permission and spare authorization are not an obligation to buy. Waivers and unrestricted cash often finance debt needs; completion can release selling as well as buying. Explicit operative clauses and committed execution evidence are necessary. A generic filing surprise strategy would not meet this project's novelty objective.

## Rules that must be frozen before any selected return study

Use the shared protocol plus hypothesis-specific exact rules, not this review as a simulator specification. Resolve universe enumeration, amendment/cancellation handling, timestamp/timezone treatment, first eligible decision time, expiry, overlapping events, whole-share sizing, settled-cash lockup, quote conditions, market-order versus limit-order fill assumptions, terminal corporate-action accounting and benchmark reinvestment before prices. No zero-cost fills, no same-bar best chronology, no favorable defaults for missing events. Preserve all exclusions in an auditable ledger.

All historical periods already seen remain development material. Prospective validation must begin after a recorded freeze and must not be silently moved after results. Require cost stress, issuer/sponsor concentration controls and clustered uncertainty; count events and independent issuers rather than treating daily marks as independent evidence. Positive P&L alone is insufficient. At least 30–60 quote/shadow sessions are required later, and calendar sessions without relevant events do not prove event execution. Insufficient prospective events extends research rather than lowering the gate.

No return estimates are supplied because none were measured. Recommend a source audit, then a frozen test only for a candidate that passes. It is entirely acceptable for both to fail and for the batch to end with zero testable strategies.
