## Why

The ali stable overlay still sends an obsolete force-probe parameter, duplicates Codex control media-type headers, leaves failed shared futures uncollected when waiters disappear, and ignores SQLite usage-history caps. The user authorized testing and deploying these four merged upstream fixes while retaining backups and rollback.

## What Changes

- Adapt upstream #2496 to remove the stable probe's max_output_tokens field.
- Adapt #2513 to replace Content-Type case-insensitively and omit all spellings for bodyless control calls.
- Backport #2427 so abandoned shared-future exceptions are collected without changing delivery or cancellation.
- Adapt #2484 to honor per-account SQLite history caps and recent-floor semantics with existing indexes.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `usage-refresh-policy`: force probes omit the unsupported output-token parameter.
- `responses-api-compat`: control calls emit at most one media type.
- `proxy-runtime-observability`: abandoned shared waits do not emit unhandled-task diagnostics.
- `query-caching`: SQLite capped history matches existing PostgreSQL slices.

## Impact

Four backend files plus regression tests. No schema migration, package, dashboard, account identity, proxy routing or quota policy changes. Deploy an overlay on the currently running 20261013-2 image; snapshot the stopped volume and retain that exact image/config for rollback. Existing first-batch reliability patches remain installed.
