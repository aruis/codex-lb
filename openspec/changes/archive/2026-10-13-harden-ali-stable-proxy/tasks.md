## 1. Stable implementation

- [x] 1.1 Adapt #1969 cancellation/shared-future fixes and verify upstream cancellation regressions.
- [x] 1.2 Adapt #1972 admission snapshot/waiter fences and verify idle lease and settings-stall regressions.
- [x] 1.3 Add verified same-account stale-anchor recovery and verify successful, unverified, visible, previously replayed, and replay-failure cases.

## 2. Validation and deployment

- [x] 2.1 Run affected unit/integration tests, lint/type checks and strict OpenSpec validation; retain results.
- [x] 2.2 Build a stable-image overlay and verify the same regressions against the production Python runtime.
- [x] 2.3 Back up deployment, data and original image; deploy and verify health/account state/logs, with a tested rollback command.
- [x] 2.4 Sync verified requirements/context and archive the change; document remaining upstream/network limitations.
