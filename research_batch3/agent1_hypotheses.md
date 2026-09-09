# Agent 1 — first-principles hypothesis generation

Research only, September 2026. Read AGENTS.md, HANDOFF.md, NEXT_AGENT_DIRECTION.md, README.md, all six existing experiment plans, and the completed second-batch Markdown result summary. Previous price/volume, trend, opening/closing and overnight variants remain rejected. Nothing below has been backtested. These are proposed combinations of established institutional mechanics, not claims of unprecedented discovery or returns. Historical periods already examined are development material; only future observations after a recorded freeze can be called untouched.

All candidates assume $2,500, whole shares, settled cash, no borrowing or shorts, low-cost deterministic operation and no live orders. Event scarcity is a material concern, not something to cure by adding weaker signals. A portfolio that earns only occasional small special-situation gains may fail James's objective even if its mechanism is real.

## H1 — CEF reinvestment route switch near distribution payment

**Mechanism.** Some closed-end fund reinvestment plans acquire shares in the market when the fund trades below NAV, but issue shares under specified conditions when it trades above NAV. The proposed edge is a discontinuity in actual market buying around that contractual route switch, conditional on an already declared cash distribution. This is a hypothesis about who buys existing shares, not dividend capture or generic discount mean reversion.

**Likely trader.** The transfer agent, investing cash for enrolled holders under its plan, potentially becomes an insensitive buyer. Actual enrollment and broker participation must be established; a distribution alone does not establish the size of buying. Brokers may run their own synthetic reinvestment rather than use the issuer plan, contaminating both the proposed flow and plan-route controls.

**Delay.** Payment dates and the plan's allowed execution window separate an accounting event from purchases. A documented BlackRock plan permits open-market purchases over a window rather than guaranteeing a single payment-day auction. The precise route can depend on contemporaneous market price and NAV, so yesterday's discount is not proof of today's purchases.

**Why not eliminated.** Small dollar flow, uncertain enrollment, fund-specific clauses and limited ability to hedge NAV exposures may make the opportunity unattractive at institutional size. This is conjecture: sophisticated CEF funds could already absorb it.

**Cheap expression.** Long eligible exchange-listed CEF common shares through ordinary stock orders, sell after a frozen window. Require broker tradability; do not enroll in a plan or assume special DRIP pricing. Credit, municipal and equity CEFs offer different risk backgrounds but should not be pooled without controls.

**Exact PIT data.** Original plan and amendments with EDGAR acceptance timestamps; contemporaneously announced distribution amount, ex-date and payment date; timestamped NAV publication, nominal share price/NBBO, splits and distributions, delisted/merged fund identity, lagged shares outstanding, historical plan enrollment if disclosed. Never use final NAV before its publication or infer all holders reinvest. Archive plan execution reports if available.

**Falsification.** No positive incremental net return against matched no-market-purchase plans/payment-placebo dates; the signal is equally strong above and below the contractual route switch; only ex-date adjustment explains it; effect disappears after NAV-factor matching; no measurable plan demand or insufficient independent fund clusters. Evaluate actual route-switch errors as failures.

**Execution failure.** Thin CEF books, stale NAV, underlying bond moves, route changes mid-window, underlying distribution dilution, crossed/odd-lot quotes, payment-date revisions, commissions and cash lockup. A bid-to-ask round trip can exceed expected flow impact.

**Priority: advance to feasibility audit.** Most repeatable mechanism here, but enrollment and actual execution timing may block a causal test.

Primary evidence: [BlackRock automatic reinvestment plan](https://www.sec.gov/Archives/edgar/data/1259708/000134100414000207/exe.htm). This supports the route and execution-window mechanics only; it does not establish alpha.

## H2 — redemption proceeds migrate into a contractual sibling

**Mechanism.** When a preferred-share series is fully redeemed, investors wishing to preserve issuer and income exposure may redeploy into the nearest surviving same-issuer series after cash actually arrives. Buy the surviving series before the documented cash-release date, exit shortly afterward. Unlike redemption arbitrage, the proposed traded instrument is never assumed redeemable at par.

**Likely trader.** Income mandates and retail income holders of the redeemed series; reinvestment is unusually plausible, not compulsory. Exclude an assumed migration where no close contractual substitute exists.

**Delay.** Public redemption notice precedes cash settlement. Cash-only accounts and operational cash-application workflows can delay reinvestment until proceeds are credited. DTC payment date is not automatically the broker credit time.

**Why not eliminated.** Same-issuer preferred books may be small and illiquid; hedging issuer credit and rate duration is imperfect; expected proceeds are large relative to a sibling's liquidity but small in institutional dollars. Conversely, specialist preferred investors may already anticipate the flow.

**Cheap expression.** Whole shares of exchange-listed preferred/depositary shares priced within the account's position cap, contingent on Alpaca support. Prefer full unconditional redemption notices; partial lotteries destroy certainty about cash recipients and amounts.

**Exact PIT data.** Timestamped redemption notice and amendments, redeemed share count and price, stated payment date, original and current prospectus terms for every then-listed sibling (coupon, fixed/floating reset, ranking, cumulative status, call rights), outstanding float, announced sibling calls, quote histories and actual broker cash-credit observations in future shadow research. Freeze a deterministic contractual similarity rule before returns are inspected.

**Falsification.** No migration into the predetermined sibling; matched unrelated preferreds move identically; returns occur entirely at announcement rather than cash availability; cash dates shifted by holidays do not shift the proposed effect; issuer-specific news or rate duration explains the outcome. A small handful of issuers is insufficient even with many securities.

**Execution failure.** Large spreads, low quote sizes, call caps, credit deterioration, future coupon-reset surprises, accrued-dividend mistakes, symbols missing from broker support, and selection bias from today's surviving preferreds. Position stops cannot guarantee protection from credit gaps.

**Priority: second feasibility candidate.** Strong public event timestamps, but scarcity, spreads and unknown migration fractions may fail immediately.

Primary examples: [KeyCorp full redemption notice](https://www.sec.gov/Archives/edgar/data/91576/000162828026057141/key-20260814.htm), [Via partial redemption notice](https://www.sec.gov/Archives/edgar/data/1606268/000160626826000008/a992viarenewablesnoticeofp.htm). These verify distinct full/partial mechanics, not migration behavior.

## H3 — rejected tender inventory becomes tradeable again

**Mechanism.** Oversubscribed CEF tenders leave unsuccessful shares with investors whose only reason to hold was tender participation. Their residual inventory may be sold once the unaccepted shares are released. Supply could temporarily depress the fund beyond changes in NAV; buy only after a predeclared public release milestone, then hold a short fixed interval. This is specifically an inventory-release hypothesis, not buying the headline tender discount.

**Likely trader.** Tender arbitrageurs and exiting holders whose allocation was prorated. They are motivated sellers, but a broker may never have restricted exchange sale of unaccepted shares; this premise requires proof.

**Delay.** Expiration, final proration and return/availability of unaccepted shares are different events. Do not use final proration counts to trade before their publication.

**Why not eliminated.** CEF liquidity and short availability limit neutral hedges; uncertain residual inventory and broker release times make pre-positioning risky. Specialists may already trade this unwind, so novelty and persistence are weak.

**Cheap expression.** Long listed CEF after release; no tender submission and no short leg required.

**Exact PIT data.** All original tender terms, amendments, final allocation notices and acceptance timestamps; shares tendered and accepted as first publicly known; contemporaneous NAV; broker/repository evidence of release timing, distributions and NBBO. A legal requirement for prompt return does not reveal the actual timestamp.

**Falsification.** No evidence of operationally locked shares; price pressure occurs before release; no association with publicly known rejected inventory after controlling for NAV and tender-price anchoring; matched non-oversubscribed tenders behave similarly.

**Execution failure.** Broker timing unavailable historically, stale marks, shrinking fund assets increasing expense ratios, permanent discount changes, reverse causality and low independent event counts.

**Priority: hold / likely PIT-blocked.** Preserve rather than converting it into a generic post-tender reversal.

Primary evidence: [CEF tender purchase and proration terms](https://www.sec.gov/Archives/edgar/data/813623/000199937125020802/ex99-a1i.htm), [SEC tender interpretation](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/tender-offer-rules-schedules). The extra operational lock premise is unverified.

## H4 — rights-subscription cash refunds release funding pressure

**Mechanism.** Fully funded oversubscription requests tie up more investor cash than ultimately needed. Participants may sell the issuer's ordinary shares to fund the request, then regain cash after allocation. A common-share price response around a documented refund could differ from the economically necessary dilution at issuance. The proposed trade buys common shares after the final allocation/refund announcement, not cheap rights.

**Likely trader.** Cash-constrained existing shareholders exercising oversubscription rights. Their pre-funding is contractual; selling the same issuer and reinvesting refunds are hypotheses.

**Delay.** Subscription expiry precedes allocation and excess-cash refund. A final notice can reveal excess cash only after the fact. Advance deployment cannot assume a refund amount learned later.

**Why not eliminated.** Small offerings, complicated rights terms, uncertain refund size and dates, and diluted common-equity risk. These frictions may instead make the trade uneconomic for everyone.

**Cheap expression.** Ordinary shares only, avoiding rights exercise fees and unsupported instruments. No subscription action is proposed.

**Exact PIT data.** Filed rights terms, cash pre-funding requirement, subscription and oversubscription limits, timestamped final allocation/refund announcement, refund agent timeline, shares issued and cash raised, exact dilution, NBBO and then-listed issuer identity. Broker-level refunds are likely not public historically.

**Falsification.** Net moves explained by issuance/dilution, no ascertainable funding pressure, refunds too small or dispersed, effect appears equally in offerings without prefunded oversubscriptions. No repeatable public refund timestamp means a tradable historical claim fails.

**Execution failure.** Distressed issuers, wide spreads, extension/cancellation, unknown allotment, corporate-action adjustments and broker refunds well after assumed dates.

**Priority: reject for present testing unless a public timestamped refund dataset is established.**

Primary evidence: [Prefunding oversubscription terms](https://www.sec.gov/Archives/edgar/data/1071264/000119312513175515/d524171dex991.htm), [Refund terms](https://www.sec.gov/Archives/edgar/data/1308858/000091957417006563/d7452405a_424b-2.htm). Neither establishes the price effect.

## H5 — employee tax-settlement route changes remove recurring forced sales

**Mechanism.** An issuer switching employee awards from broker sell-to-cover to issuer net-share withholding changes market supply even if compensation economics and vesting counts stay similar. If investors extrapolate habitual vest-day selling after a publicly announced switch, the first scheduled post-switch vesting may clear with less supply. Long the issuer over that explicitly scheduled vest window, measuring incremental return against its pre-switch vest days and matched unchanged issuers.

**Likely trader.** Under sell-to-cover, the designated broker sells shares to meet employee taxes. Under net settlement, the issuer withholds shares and funds taxes with cash. These are different mechanisms, not synonyms for corporate open-market repurchases.

**Delay.** Disclosure may precede future recurring vest events. The market may not map an accounting-policy sentence to a future supply schedule. Many disclosures are retrospective; those cannot generate advance signals.

**Why not eliminated.** Unstructured policy footnotes and employee schedules are costly to interpret; events are sparse. Large firms could nevertheless trade a known schedule cheaply; this persistence claim is weaker than H1.

**Cheap expression.** Liquid U.S. common shares, avoiding shorting the old regime. Deterministic extraction after a reviewed development dictionary, no real-time AI inference.

**Exact PIT data.** Original filing acceptance times and text; effective date and scope of policy change; publicly disclosed future non-executive vest dates and award counts known before vesting; external sale versus withholding labels; employer cash/financing disclosures. Form 4 insider transactions are not a census of employee sales.

**Falsification.** Only retrospective disclosures available, non-executive schedule unknowable, issuer funds withholding via an offsetting ATM sale, effects explained by earnings/blackouts, or no difference between externally sold and withheld shares. Cash financing can reverse the proposed sign.

**Execution failure.** Earnings-event overlap, undocumented schedules, discretionary employee sales, mistaken classification of tax withholding as exchange volume, issuer cash strain and lookahead from quarterly totals.

**Priority: creative but data-blocked; do not substitute executive Form 4 as the missing employee universe.**

Primary evidence: [Disclosed change from sell-to-cover to net settlement](https://www.sec.gov/Archives/edgar/data/1474432/000162828025021855/a10kfy2025.pdf), [Issuer ATM funds tax withholding](https://www.sec.gov/Archives/edgar/data/1451809/000145180925000078/sitimecorporationfy24proof.pdf). These support the mechanism and a direct counterexample.

## H6 — partial redemption lottery creates predictable residual-lot cleanup

**Mechanism.** A partial preferred redemption can leave holders with awkward residual positions. Accounts that target fixed position counts or minimum dollar sizes might liquidate remnants after allocations become visible. Buy the surviving series after the actual allocation/release date if the mechanism yields a temporary concession, using issuer siblings only as controls. This differs from collecting a pro-rata redemption payout or assuming every holder receives an equal fraction.

**Likely trader.** Small accounts and mandates eliminating uneconomic residual holdings; no contractual sale obligation is known.

**Delay.** DTC-level lottery, broker allocation and customer statements can be asynchronous. Public notice does not identify customer-level remnant sizes.

**Why not eliminated.** Fragmented holder behavior, small absolute flow and preferred liquidity. These same conditions may mean the effect is too weak and diffuse to measure.

**Cheap expression.** Long surviving preferred whole shares, contingent on broker support. Do not exploit or manipulate redemption allocation.

**Exact PIT data.** Partial redemption notice/terms/timestamp, fraction redeemed, DTC and broker lottery methodology and execution date, publicly observable residual float, dividend accrual, broker-level size distribution or a clearly labeled prospective proxy, NBBO.

**Falsification.** Pro-rata or lottery process does not generate predicted remnants; no observable customer allocations; holders reinvest proceeds rather than sell; issuer/rates fully explain returns. Aggregate redeemed fraction cannot stand in for actual customer distribution.

**Execution failure.** Redemption confusion, lottery variance at a $2,500 scale, spreads, accrued-dividend accounting and permanent liquidity deterioration after float shrinks.

**Priority: reject for current scope.** Essential microdata unavailable and no strong forced seller. Preserve as a failed feasibility hypothesis rather than searching for a favorable event window.

Primary evidence: [Via partial redemption by lot](https://www.sec.gov/Archives/edgar/data/1606268/000160626826000008/a992viarenewablesnoticeofp.htm). Customer residual-sale behavior is explicitly unverified.

## Selection recommendation

Advance at most H1 and H2 to small, source-only feasibility audits. Do not download histories or build a simulator merely because these are the least weak ideas. H1 must establish actual plan rules, historical NAV publication times and credible reinvestment demand; H2 must establish broker support, a PIT sibling map and enough independent issuers with affordable quotes. If those prerequisites fail, select zero. Neither candidate yet satisfies event frequency, net alpha, untouched validation, concentration, a 25% drawdown ceiling or 30–60-session shadow testing.
