## 1. Stable backports

- [x] 1.1 Adapt #2405 reset evidence and paid-account recovery; retain warm-up and stale-state guards.
- [x] 1.2 Adapt #2449 shared usage-limit predicate to HTTP and WebSocket classification, health, retry, and refresh paths.
- [x] 1.3 Apply #2255 drain admission denial and public-route regressions.

## 2. Verification

- [x] 2.1 Run upstream regression cases on stable, add stable-path coverage for any adaptations, and verify prior ali overlays remain intact.
- [x] 2.2 Run relevant broad backend, lint/type/architecture, SQLite, and strict OpenSpec checks; record limitations.
- [x] 2.3 Review complete diff, ownership/settlement invariants, and requirement/test mapping.

## 3. Release and preservation

- [x] 3.1 Produce hashed cumulative overlay and validate on ali without using production data or accounts.
- [x] 3.2 Back up image/config and stopped data volume; deploy with automatic rollback and verify health plus a tiny real request.
- [x] 3.3 Sync specs/context and prepare final verified archive/source-preservation records; verify the manifest and release evidence before saving to the existing personal branch.
