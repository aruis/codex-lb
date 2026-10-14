## Context

Stable 1.24.0 uses code tables for streaming failure recognition and a Free/monthly-only reset-confirmed exception. The existing ali overlays preserve request ownership, cancellation cleanup, probe compatibility, and SQLite dashboard bounds. Those changes must remain intact.

## Goals / Non-Goals

Implement #2449, #2405, and #2255 on this stable branch without importing unrelated beta refactors. Preserve explicit error-code precedence, cooldown authority, paused/deactivated states, settlement ordering, and file/session account ownership. Image-host selection and credit semantics are out of scope.

## Decisions

1. Apply the upstream semantic patches with minimal stable-specific adaptations. Missing codes normalize to upstream_error; message recognition only supplements that classification, never invalid_request_error or an explicit unrelated code. HTTP and WebSocket health, replay eligibility, and usage refresh use one predicate. Existing replay ownership rules remain in charge.
2. Resolve post-block reset evidence in primary, secondary, and monthly slots. Require a unique matching deadline baseline and adjacent temporal-reset transition, latest available quota, and elapsed minimum cooldown. Normalize legacy NULL primary slots. Preserve live exhausted short-window blocking and do not infer absent capacity from unknown plans. Separate warm-up evidence from recovery evidence.
3. Reuse the existing ASGI HTTP-denial utility and local overload envelope for drain-time WebSocket admission. Preserve handler exclusion and in-flight balancing.
4. Deploy an immutable overlay on the current ali image after both local and runtime regression tests. Save previous image, compose/env, and a stopped-volume snapshot. Recreate only server and automatically restore the previous image/config if readiness fails within 240 seconds. No schema migration is introduced.

## Risks / Trade-offs

Message recognition must not interpret request-quoted text as account exhaustion. Reset scans can include long histories; correctness requires the original matching baseline rather than a truncation that drops it. Stable upstream-file drift requires manual review of every rejected patch hunk. Full PostgreSQL infrastructure checks depend on an available test database; ali uses SQLite and requires SQLite/runtime checks regardless.

## Migration Plan

No database migration, setting change, or public model change. Verify exact base image and source manifest before deployment. Preserve all earlier patch hashes and include this batch in the existing personal fork branch and local Git bundle.

## Open Questions

None for the authorized first three fixes.
