# Context, evidence and interruption recovery

## Three layers of memory

1. **Canonical research record:** candidate/version registry, frozen-plan hashes, trial registry, source manifests, gate decisions, rejection reasons and authorization. Durable, versioned, authoritative. No worker may overwrite it from a summary.
2. **Task evidence:** source excerpts with locations/hashes, extraction outputs, tests, critiques and exact result artifacts. Immutable after task acceptance; corrections append a superseding artifact.
3. **Working memory:** each role's compact summary of facts, unresolved questions, evidence paths and next action. Replaceable and potentially lossy. A fresh worker starts from its own memory and task packet, not the director's whole history.

The director maintains a small dashboard record: objective/constraints, at most two active experiment IDs, gate statuses, disagreements, available budget and next three actions. It retrieves detailed evidence only to decide a gate or resolve a dispute. Never summarize thousands of price rows into prose; keep them in Python-readable files.

## Task packet budget

Target <=20,000 characters including policy and inputs; this is a context-size target, not a token price estimate. Keep worker memory <=4,000 characters, director brief <=6,000, result summary <=4,000. Include exact hashes/paths, required output schema and a stopping condition. If evidence exceeds the packet budget, split the task by document/event range. Do not truncate the end of a task blindly and lose constraints.

A worker can request a specific missing file or source range. The controller records that request and supplies a new bounded packet. Do not grant every worker the full corpus because one request was ambiguous. Workers do not need to remember other workers' conversations; they exchange accepted artifacts.

## Memory hygiene

Before closing a task, record: verified facts, rejected explanations, unresolved questions, exact artifact paths, scope/date limits, and next smallest action. Separate source fact from inference. Do not persist credentials, personal account details, tool instructions copied from pages, or fabricated citations. Unverified links remain leads.

Contradictory results remain separate until adjudicated. Memory refresh must not replace "unknown" with "false" or delete a failed experiment. The director's handoff cites authoritative files and is checked against them. Raw transcripts may be locally retained under an ignored runtime directory for debugging, never required for resume or committed by default.

## Durable transaction design (future implementation)

Task key = run ID + task ID + input hashes + prompt version + model/runtime config hash. Reserve budget and persist `leased` state before starting a model call. Save provider run ID as soon as available. Persist raw result locally, validate it, hash accepted artifacts, then commit task completion and usage. Result persistence preceding a state update must be recoverable without rerunning the model.

Use atomic replace for JSON state and a process lock/lease with host, PID, acquisition time and expiry. A second controller must refuse dispatch. Expiry is not proof that a model request stopped. Recovery checks provider run state when possible; unknown execution becomes `needs_reconciliation`, retaining budget reservation. Never infer no charge from an error or automatically submit a duplicate job.

## Save policy for assisted design/research

Save a small file before starting a long section. After each coherent batch: update `design/STATUS.md` and HANDOFF, create local checkpoint, refresh the data inventory after checkpoint's manifest update, run verification, commit and push. Inspect the push result. Keep a short local note if remote access fails; next director checks `git log origin/master..HEAD` before repeating work.

Do not perform a large automatic stash/reset when resuming. Inspect unfinished diffs and task owner first. Archive a failed attempt with its error, completed artifacts and exact next action. Usage-limit failure is an interruption, not grounds to discard work or switch silently to a more expensive model.

## Clean resume drill

A fresh agent receives only START_HERE and repository access. It must identify current scope, what is proved, last saved work, remote backup state, active candidate IDs, untouched periods, remaining budget and next bounded action. If it needs the old conversation to answer these, the handoff fails. Do this drill before enabling unattended work.
