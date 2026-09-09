# Result packet template — not evidence

- task identity and input/prompt/model hashes:
- status: completed / blocked / failed / needs_reconciliation
- recommendation: advance_for_review / reject / inconclusive / request_input
- compact finding:
- verified facts, each with source path/hash/location and known-at time:
- inference and alternative explanation:
- unverified claims / missing fields:
- outputs and hashes:
- checks performed and actual results:
- falsifier outcome:
- usage/cost and unknown-charge fields:
- next smallest action:
- refreshed own memory (facts, rejected paths, unresolved questions, source index):

Recommendation is advisory. This expanded design contract supersedes the draft runner's simpler result shape for a later implementation; do not claim the current runner supports it.
