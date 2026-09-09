# Batch 3 research protocol

This batch generates and rejects mechanisms, audits data, and freezes at most two experiments. It does not run a new return test, download bulk history, build a simulator or trading bot, or submit broker orders. The user request takes precedence over stale archive instructions. Alpaca is preferred; old Robinhood preference text is historical.

## Evidence discipline

All price-history periods through September 8, 2026 are treated as development context. Prior reserved windows are consumed. A new event dataset on those dates does not restore an untouched market history. A filing or prospectus can establish a contractual mechanism; it cannot establish profitable price response, participant holdings, or attainable fills. Hypotheses are proposed combinations, without a claim that no one has published or traded them.

Historical data must retain the original accession/document, publication and acceptance times, first observation time if available, effective date, correction chain, source URL and content hash. A date alone cannot support an intraday trade. Restated XBRL values, current constituents, current broker asset flags, revised corporate-action tables and ex-post transaction settlement timestamps must not masquerade as historical knowledge.

The historical event catalog must include terminated, withdrawn, failed, delisted and untradeable cases, with exclusions assigned before looking at forward returns. Keep event counts before and after every filter. Do not silently discard missing outcomes for held positions. Inability to recover a terminal value makes performance incomplete, not zero loss.

## Capital and economic usefulness

Primary modeled capital is $2,500; repeat unchanged rules at $1,000 and $5,000. Whole shares, long only, no borrowed cash, no optional tender instructions or other corporate-action elections. Deterministic exchange-session rules; no discretionary intervention or trading-time AI inference.

Cost accounting includes bid/ask, adverse latency, fees, fixed data/runtime costs and tied-up settled cash. Illustratively, $10/month consumes 4.8% of a $2,500 initial account per year before trading losses; $50/month consumes 24%. These are arithmetic, not provider prices. No paid subscriptions are authorized. New recurring expenditure cannot be justified by gross backtest gains.

## Gates

1. Mechanism/data feasibility: predeclared, bounded document sample selected without price outcomes; public observable timing, deterministic labeling, enough eligible events, and executable instrument support. If a necessary field cannot be recovered, mark the idea data-blocked. Do not replace it with a convenient price/volume proxy.
2. Development: only after the frozen plan and feasibility gate. Preserve all cost scenarios and controls. Failure retires this version. Any revised hypothesis gets a new ID and a new future validation window; never overwrite a failed plan.
3. Untouched validation: prospective period specified in the experiment plan; no performance inspection or adaptive stopping. Data-quality monitoring may see completeness and hashes only. Early risk-stop failure is allowed; early success is not. Too few events means inconclusive.
4. Execution: after statistical gates, 60 consecutive exchange sessions of live-quote observation and local hypothetical orders, extended if fewer than 30 completed hypothetical trades. No broker order submission. Record misses, partial capacity, delayed decisions, source failures and dividends independently; broker paper marks alone are insufficient.
5. Implementation consideration only after all prior gates. No implementation or funding approval is conferred by these files.

## Sources checked September 9 UTC / September 8 Pacific, 2026

- SEC EDGAR APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces . Historical submission records and XBRL interfaces are inputs, not a survivorship-free investment universe.
- SEC publication timing: https://www.sec.gov/about/webmaster-frequently-asked-questions . Acceptance precedes website availability; do not fill at acceptance time.
- Alpaca corporate actions: https://docs.alpaca.markets/us/reference/corporateactions-1 . Default complete-data filtering can omit incomplete events; historical API output alone does not establish first availability.
- Alpaca paper trading: https://docs.alpaca.markets/us/docs/paper-trading . Its stated omissions include market impact, latency slippage and queue position; paper outcomes are not execution proof.

Current tools expose read-only Alpaca data methods, but this batch has not tested their access. No Library tool is exposed. The old Linux Library helper is unavailable; checkpoint.py now saves a hashed local ZIP and a separate local receipt without claiming a cloud update.
