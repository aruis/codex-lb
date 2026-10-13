## Context

See proposal.md. Installed base is codex-lb:1.24.0-ali-hotfix-20261013-2, healthy with one Pro account and SQLite. The four merged upstream changes must be adapted to stable source without later native transport, user-auth or migration dependencies.

## Goals / Non-Goals

Preserve complete first-batch patches and existing proxy/account/settlement behavior. No new configuration, schema, quota-recovery policy or frontend feature is introduced.

## Decisions

- Remove only the unsupported probe field; retain the single-account request, bounded timeout and immediate usage refresh.
- Reuse existing case-insensitive header replacement if present, otherwise adapt the existing stable equivalent. Verify header spelling/position, direct/routed paths, body bytes, default JSON and bodyless omission.
- Collect the shared future's exception before iterating waiters; retain future results for late waiters and cancellation semantics.
- Adopt indexed per-account SQLite cap queries, preserving complete recent-floor rows, cutoffs, stable ordering/ties and uncapped cache behavior. Do not impose a global 64-row limit or discard recent dense samples.
- Regressions reproduce the defect against the currently installed source before patching; validate dashboard output and repository paths, not only helper behavior.

## Risks / Trade-offs

History slicing could change projections → test capped/uncapped parity, dense writes, cutoffs and index plans. Header changes could mutate opaque realtime bodies → compare exact bytes and header order. Exception collection could suppress delivery → test late/live waiters and cancellation. Online backup can restart under writes → take a stopped-volume snapshot at cutover.

## Migration Plan

Build a four-file overlay from the retained exact current image. Verify image hashes and run isolated tests with no production volume. Save compose/config, image id, schema and a consistent full volume snapshot; recreate only Compose server. Verify readiness (240-second cold-start window), actual probe, authenticated dialogue/continuation, account state and logs. On deployment failure restore the immediately previous image/config, retaining current schema-compatible data. Keep original stable rollback available separately.

## Stable adaptation details

The upstream dashboard test uses newer response-field names and a 64-row caller cap. Stable keeps its existing 4320-row cap and six-hour recent-burn coverage; only SQLite now honors it. The adapted product regression uses 10080 minute-spaced rows, expects 4320 tail plus 30 recent rows, and compares the complete stable projection fields against an uncapped fetch. No newer dashboard schema or cap policy is imported.
