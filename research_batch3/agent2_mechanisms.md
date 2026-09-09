# Agent 2: operational mechanisms and primary-source audit

Read AGENTS, HANDOFF, NEXT_AGENT_DIRECTION, README, original/daily/volume plans and completed update. Historical periods already examined remain development only. This memo proposes mechanisms; it contains no return tests. Checked September 9, 2026 UTC. Novelty means a new, falsifiable combination for this project, not a claim nobody has published it.

## M2-A: cash-election disappointment inventory

**Mechanism hypothesis:** A special distribution caps aggregate cash elections, so some holders who explicitly requested cash receive unwanted new shares. Their delayed disposal, after account allocation, can create temporary inventory supply. Buy the ordinary shares after a fixed allocation window, seeking recovery as that specific supply ends. This is not an ex-dividend capture or price-momentum signal.

**Likely trader/delay:** Cash-preferring income holders, tax-liquidity sellers and accounts with fixed dollar exposures. Election close precedes share-count determination and payment; broker allocation can lag payment. The cap creates unwanted stock, but public documents do not establish actual sales.

**Why persist:** Individual allocations and desired cash amounts are not public. Small, infrequent events and uncertain distribution timing limit institutional capacity. This also weakens identification.

**Cheap expression:** Listed REIT or BDC common shares, purchased in ordinary trading after distribution. Avoid participating in the voluntary election. Cash only, whole shares, no hedge required, but sector exposure must be benchmarked.

**Point-in-time inputs:** Original 8-K exhibits/election notices and every amendment; accepted timestamps; cash cap; total distribution; election deadline; pricing window; pay date; announced final share count and publication timestamp; issuer CIK/CUSIP mapping; actual nominal quotes and dividend/stock entitlements; archived broker availability and allocation evidence. A future final share count cannot populate an earlier signal. Published payment date is only a proxy for arrival in customer accounts.

**Falsifier:** No incremental post-allocation reversal versus cash-only distributions/matched sector exposure; the apparent return is dilution adjustment; effects precede delivery; or no measurable concentration of supply near delivery. Event count too small means inconclusive, not pass.

**Execution killers:** Unexpected equity issuance/repricing, wide spreads, stock-dividend adjustment errors, distress common to cash-conserving issuers, repeated corporate actions, stale quotes and delayed allocation. No stop guarantees protection.

**Primary example, not a chosen winner:** Rayonier's December 2024 filed supplement specifies a 25% cash cap, cash elections subject to proration, January pricing dates and January 30 payment. This establishes operational structure only. [SEC filing](https://www.sec.gov/Archives/edgar/data/52827/000005282724000208/specialdividendsupplemen.htm). Rand's election notice supplies another issuer/type, 20% cash and 80% new stock: [issuer-filed notice](https://ir.randcapital.com/all-sec-filings/content/0001493152-24-050331/ex99-1.htm).

**Verdict:** Most promising for a bounded event/data audit, not yet a return test. Freeze a delivery-proxy rule; never invent actual selling from election proration.

## M2-B: liquidation cash-state misclassification

**Mechanism hypothesis:** An ETF has publicly ceased its economic exposure and holds cash before exchange trading ends, yet some holders sell it as if it still carries its old mandate/risk or urgently avoid an untradeable payout interval. A whole-share buyer may earn a sufficiently large discount to conservatively estimated distributable cash.

**Trader/delay:** Mandate-constrained accounts and operationally constrained investors avoiding delisting. Fund liquidation, final trading and cash credit are separate clocks. Larger APs have creation/redemption access and should eliminate most discounts; the hypothesis needs a residual below their economical creation-unit size, not an assumption they disappear.

**Cheap expression:** US-listed ETFs that explicitly announce an all-cash state, with independently verifiable assets/liabilities. Automatic liquidation rather than voluntary redemption; Alpaca eligibility must be checked. Exclude illiquid asset liquidations and expected cash transitions not yet evidenced.

**Point-in-time inputs:** Original 497 supplement and amendment accession/acceptance times; all-cash effective date; observed publication timestamps of NAV and holdings; liabilities/reserves; distribution notices; AP redemption availability/cutoff; delisting schedule; executable quotes; actual payout/cash-availability date; any interim distributions. Final liquidation proceeds are an outcome, never entry valuation.

**Falsifier:** No discount beyond quoted spreads and conservative liability/payout-delay reserve; cash-state confirmation only exists after trading stops; discounts cannot be filled at ask; no repetition across sponsors. Low opportunity count may make it an occasional cash-management trade rather than project solution.

**Execution killers:** Redemption arbitrage already closes gap; liquidation expenses; undisclosed derivative residuals; stale NAV; cancellation; cash trapped; corporate-action processing fees; position becoming untradeable before exit. Require a payout-based exit and cash-delay stress, not synthetic sale at final NAV.

**Primary evidence:** Tradr states its closing funds expected an all-cash transition February 14, 2025, before February 21 final trading and approximately February 28 liquidation. The current page is NOT proof that this text was available historically; need contemporaneous 497. [Sponsor notice](https://www.tradretfs.com/). iShares' closure page separates final NAV and liquidation distribution; these retrospective values cannot be signal inputs. [Closure records](https://www.ishares.com/us/products/272346/?cid=synd).

**Verdict:** Worth a small source-availability audit; likely sparse and efficiently arbitraged. Strongest accounting falsifier: no contemporaneous cash-NAV record means no historical backtest.

## M2-C: fractional-entitlement sale exhaustion

**Mechanism hypothesis:** Distribution agents aggregate fractional spin-off entitlements and must sell them rather than retain investment exposure. A documented short sale window could leave transient supply in a thin new listing; a long purchase after that window could capture inventory normalization.

**Constraints:** Execution timing is often entirely the agent's discretion, beneficial-holder fractional quantities are private, and the pressure may be trivial. Larger traders already know spin-off flows. Common spin-off selling is not original enough; only the specifically measured fractional batch is the proposed mechanism.

**Point-in-time data:** Final Form 10 information statement and amendments, ratio, when-issued/regular-way schedule, agent-sale schedule or contemporaneous completion disclosure, actual aggregated fractional quantity and publication time, issuer identifiers and executable when-issued/regular-way quotes. Record-holder counts do not reconstruct beneficial fractional entitlements.

**Falsifier/execution:** Quantity unavailable, sale timing undisclosed, effect absent once ordinary spin-off flows controlled, wide new-listing spreads, corporate-action symbol errors and inability to trade when-issued shares. Treat missing quantity as a data rejection, not replace with a favorable price pattern.

**Primary evidence:** Solstice's preliminary filing explicitly gives the agent discretion and contemplates when-issued sales; it contains unfilled terms and cannot stand in for final terms. [SEC preliminary document](https://www.sec.gov/Archives/edgar/data/2064953/000162828025043179/exhibit991-10x12ba1.htm). Versant's information statement also delegates timing and aggregation. [SEC document](https://www.sec.gov/Archives/edgar/data/2067876/000119312525306792/d894612dex991.htm).

**Verdict:** Preserve, data-blocked. Do not select for return testing.

## M2-D: partial-call lottery inventory

Mandatory partial preferred/bond redemptions create account-level inventory uncertainty and cash-delivery delays. A tempting proposed edge is a discount compensating holders for operational inconvenience. DTC, however, conducts an impartial participant-level lottery; that does not give a small retail account a favorable expected allocation. Account-level results are not publicly observable point-in-time. DTC also permits cancellation/revision. [DTC redemption mechanics](https://www.dtcc.com/asset-services/corporate-actions-processing/redemptions). Preferred eligibility, spread, credit risk and broker allocation policy further dominate. **Reject as currently specified:** no identified directional expected-return advantage beyond redemption/credit carry, and no accessible account-level historical lottery data.

## Cross-cutting data/implementation findings

- SEC APIs provide submissions and XBRL JSON updated as filings disseminate. Use original accession documents, not latest restated company facts. Store publication/acceptance and first-observed timestamps separately; access timestamp now cannot establish historical visibility. [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces). SEC describes acceptance time in the complete submission header as EST; verify DST/UTC conversion against filing-index display and avoid interpreting a bare timestamp without provenance. [SEC FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions).
- Alpaca's corporate-action endpoint explicitly gives no guarantee of creation timing and may deliver events with delay; retrospective endpoint records are not a point-in-time announcement feed. Freeze forward snapshots if used. [Alpaca corporate actions](https://docs.alpaca.markets/us/reference/corporateactions-1).
- Alpaca's voluntary-action documentation describes email instructions and a $100 per-client action fee. It also describes shares moving to placeholders until DTC allocation. This is a major small-account obstacle and does not establish deterministic election automation. Confirm the actual account's applicable schedule before any future eligibility decision; do not assume this broker-partner page proves James's exact fee. Avoid voluntary tender/rights strategies for now. At modeled capital, $100 equals 4% of the entire account. [Alpaca voluntary actions](https://docs.alpaca.markets/us/docs/voluntary-corporate-actions).
- Odd-lot tender priority exists in actual offer documents but is widely known, offer-specific and potentially ruined by fees. It is not a novel selected hypothesis. [Example SEC offer](https://www.sec.gov/Archives/edgar/data/1309108/000114036125006098/ny20044175x1_exa1a.htm).

No market prices, return series or large datasets were downloaded. No broker endpoints or orders were called. Recommend at most M2-A and M2-B for source feasibility work, subject to synthesis with other agents.
