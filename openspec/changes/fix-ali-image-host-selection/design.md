## Context
See proposal.md. The production snapshot advertises gpt-5.6-luna for Pro and explicitly suppresses gpt-5.5.

## Goals / Non-Goals
Restore image generation and editing with the existing account and image API. Do not change client configuration, public model names, retries, quotas or schema.

## Decisions
Backport upstream #2320 selector verbatim: Luna then 5.5, requiring registry plan visibility and no suppression, defaulting to Luna if neither qualifies. Share it with default probes to avoid another hardcoded stale host. Preserve explicit probe models. The existing routing pipeline continues to enforce account entitlement and key scope; selection is not proof of entitlement.

## Risks / Trade-offs
A stale catalog can still advertise an inaccessible host; preserve existing errors and do not add cross-account retries. Test partial, authoritative, cold and suppressed catalogs. Validate actual generation before declaring success.

## Migration Plan
Build on the exact installed image. Run isolated SQLite regression tests without production mounts. Save the old image and configuration, gracefully stop and archive the data volume, then recreate with the new image. Automatically restore the previous configuration/image if readiness fails. Rollback retains current data; the stopped-volume backup is disaster recovery only.
