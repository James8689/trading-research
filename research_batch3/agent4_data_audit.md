# Agent 4: point-in-time feasibility audit

Decision: existing prices support diagnostics, not the proposed event mechanisms. No evidence of alpha is claimed. No broker request, download, simulator, or order was made. Archive instructions were read as project context; current user constraints govern.

## Actual local evidence

Read AGENTS, HANDOFF, NEXT_AGENT_DIRECTION, README and the frozen extension/daily/volume plans and saved data audits. Yahoo AAPL file has chart/result with meta, timestamp, events and indicators; these are historical bars and corporate-action records, not an announcement archive. The six-semiconductor January 2020 Alpaca file has request, counts, columns and bars. The manifest preserves request and hash. No quote-named files were found. The historical handoff reports one successful quote probe but this is not a verified saved quote dataset. Current tools expose 26 Alpaca data functions, including quotes, corporate actions and assets; successful access and subscription coverage have NOT been tested in this session.

The 37 surviving stocks are unsuitable as an event universe. Need delisted issuers, renamed securities, mergers, effective listing intervals and CIK-to-security mapping. SEC registrants alone are not a tradable universe; funds, debt, multiple classes and private registrants require filtering. A current Alpaca asset list cannot reconstruct historical eligibility.

Already examined periods include 2011–2025 and prices through September 4, 2026. Calling 2022–2025 or 2024–2025 untouched again is invalid. Treat all available history as development/diagnostic evidence. Reserve prospective observations from October 1, 2026 only if rules and parser gates are frozen before then; if delayed, move the start forward before collection. Do not backfill an alleged prospective holdout after inspecting outcomes.

## Mechanism feasibility

1. **SEC acceptance-time constraint release.** Historical filing documents and accession identities can support an as-known event log. Extract explicit operative language, covenant definition, remaining buyback authority, lender waiver effective date, cash restriction release, and conditions still outstanding. Accounting quarter-end or a restated XBRL fact is not the knowledge time. Acceptance is a conservative observation time only when no earlier public release is substituted. Record original acceptance header and index timestamp, timezone conversion and document hash; reject unresolved timing conflicts. Public disclosure of capacity is not evidence the issuer is obliged to trade. Quarterly buyback aggregates cannot identify daily execution. Feasibility: conditional, with a small manually checked document set before prices.

2. **Tender completion residual demand.** Public tender terms and amendments can establish expiration, final acceptance/proration, payment terms and remaining authorization. Distinguish issuer equity repurchases from debt and third-party offers. Tendered-but-returned shares can create selling, while completion may release a repurchase restriction; the sign is ambiguous. Payment can occur after final results. Never infer settlement from the scheduled expiration or assume unspent authorization forces market buying. Feasibility: conditional; a viable event requires explicit open-market restart intent/capacity or another measurable participant constraint, not generic completion.

3. **Distribution reinvestment routing.** Fund-specific dated DRIP documents can say when agent purchases begin and whether shares are issued or bought in the market. Public distribution dates alone cannot reveal opt-in capital, broker inventory, execution day or internal netting. Premium/discount can switch routing within a window, making an end-of-window NAV classification lookahead. Distinguish fund-sponsored plan from broker reinvestment. Historical plan versions and NAV availability timestamps are essential. Feasibility: weak until a dated mechanical routing rule is verified; share issuance can extinguish the hypothesized buying entirely.

4. **Other constraint-release events.** Explicit debt covenant waivers, cash repatriation restrictions ending, court escrow releases or restored exchange eligibility are searchable disclosures. The operative date can precede filing and be conditional; unrestricted cash may repay debt rather than buy equity. ETF/index reinclusion requires historical provider eligibility and implementation notices, not present constituents. Feasibility: document-specific and likely too sparse for frequent opportunities. No universal earnings-blackout calendar should be invented.

## Small probes before any return test

- Freeze a document-only sample of 10 consecutive qualifying historical equity tender completions from a fixed SEC filing-date interval, including cancellations and zero remaining capacity. Cap at 30 documents, not a price-selected sample. Extract terms, timestamp and payment evidence; tally missing fields. No prices yet.
- Inspect five consecutive covenant/waiver or restricted-cash-release disclosures from the same declared search protocol. Require two independent readers to agree on binding clause, release conditions and possible trader. Reject capacity-only stories without a testable buyer prediction.
- Inspect three fund DRIP prospectuses and their dated amendments; transcribe purchase versus issuance rules, date windows and NAV timing. Fail routing feasibility if the plan version or contemporaneous inputs cannot be recovered.
- Only after document gate, request at most two symbols and two one-minute quote windows, one historical and one current read-only probe. Save feed, timestamps, sizes, conditions, request, count and errors. A connected tool name is not access verification. Do not repeat bulk retries after a tiny failure.

Suggested document gate: >=90% complete critical fields and 100% reconciled knowledge timestamps among retained events; excluded/missing events retained in ledger. This gate establishes data feasibility, not economic efficacy. Missing-event selection bias remains a reason to stop.

## Fields and execution required for any later test

Event ID; CIK; accession; security class; ticker validity interval; form/amendment lineage; original document hash; accepted_at; earliest_release_at if independently evidenced; observed_at; effective_at; extraction version; required conditions; event-specific cash/share amounts; universe eligibility known_at. Preserve amendment history instead of overwriting. Use original filing-linked facts rather than present companyfacts values without accession filtering.

Quote audit requires SIP NBBO bid/ask, sizes, quote conditions, exchange/session calendar and halt status around both decision and execution; bids/asks do not guarantee a fill. Payable-date dividends belong in cash settlement; ex-date receivables must not fund orders. Simulate whole shares, settled cash, corporate actions and delisting recovery. For $2,500, spreads in CEFs/small caps, $0.01 ticks, low event count, adverse selection and gaps can dominate. Separate minimum spread-crossing cost from extra latency slippage; reject any hypothesis requiring invisible queue priority, short borrow or subsecond execution.

## Primary-source grounding (checked September 9 UTC, September 8 PT, 2026)

- [SEC data APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces): public submission history and filing-linked XBRL are available; extracting as-known events is additional work.
- [SEC developer resources](https://www.sec.gov/about/developer-resources): public archival submissions include filing headers. Respect fair-access policy and avoid mass collection at this stage.
- [Actual equity tender terms](https://www.sec.gov/Archives/edgar/data/1101215/000119312519197208/d777726dex99a1a.htm): guaranteed delivery and conditional tenders can delay final proration/payment. This is evidence of a delay, not of positive returns.
- [SEC tender guidance](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/tender-offer-rules-schedules): payment/return obligations do not create a precise universally identical settlement date.
- [SEC Rule 10b-18 FAQ](https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions/division-trading-markets-answers-frequently-asked-questions-concerning-rule-10b-18-safe-harbor): safe-harbor conditions are not a requirement that firms buy, nor a blanket ban outside safe harbor.
- [Blackstone fund annual report with DRIP terms](https://www.blackstone.com/wp-content/uploads/sites/2/2020/06/blackstone_funds_a19_final-1.pdf): historical example of a multi-day market-purchase window and possible switch to issuance. Not proof of current terms for another fund.
- [Alpaca corporate-action support](https://alpaca.markets/support/what-are-corporate-action-announcements-and-how-can-i-access-them): availability after declaration does not establish original announcement-time delivery for a backtest. Store observed ingestion times going forward.

All mechanism-to-return statements above are hypotheses/inferences. Sources establish operations, not alpha.
