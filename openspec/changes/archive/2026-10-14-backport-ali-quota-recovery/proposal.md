## Why

The ali deployment runs a stable 1.24.0 overlay with one Pro account. Upstream code-less usage-limit failures can leave an exhausted account active; confirmed early paid quota resets cannot use the existing Free/monthly-only cooldown exception. Drain-time WebSocket admission currently appears as HTTP 403. These defects can prolong an outage or obscure a recoverable restart.

## What Changes

- Backport upstream #2449 usage-limit classification and refresh behavior, preserving account ownership and settlement order.
- Backport #2405 window-bound, unique reset evidence for paid account recovery, with warm-up evidence kept separate.
- Backport #2255 drain-time WebSocket denial as HTTP 503 with Retry-After.
- Validate against stable dependencies and the ali runtime, preserve consistent backups and rollback, and record source on the existing personal fork branch.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `account-routing`: recognize usage-limit terminal frames and bind cooldown override to unique reset evidence.
- `usage-refresh-policy`: recover paid accounts on verified resets and refresh upon recognized usage-limit failures.
- `graceful-shutdown`: return retryable HTTP denial during WebSocket drain admission.

## Impact

Proxy streaming, WebSocket error handling, background quota reconciliation, and admission middleware. No schema changes, new dependencies, settings, model selection changes, or dashboard changes. Adapt behavior rather than importing unrelated beta architecture. This is a private deployment overlay on the public personal fork, not an upstream release or main merge.
