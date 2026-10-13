## 1. Stable backports

- [x] 1.1 Adapt force-probe omission and verify dashboard route plus service regressions.
- [x] 1.2 Adapt control-header replacement and verify direct/routed, casing, opaque bodies and bodyless/default behavior.
- [x] 1.3 Backport shared-future exception collection and verify abandoned, late/live and cancelled waiter plus SSE paths.
- [x] 1.4 Adapt capped SQLite history and verify repository, dashboard projection parity and index-plan regressions.

## 2. Release verification

- [x] 2.1 Run affected suites, first-batch regressions, lint/types and strict change/main-spec validation; retain evidence.
- [x] 2.2 Build current-image overlay, verify manifest and isolated production-runtime suites before cutover.
- [x] 2.3 Back up stopped volume/config/current image, deploy only server and verify health, actual probe/dialogue/continuation and cleanup; retain rollback.
- [x] 2.4 Sync verified requirements/context and archive the completed change with evidence and operational commands.
