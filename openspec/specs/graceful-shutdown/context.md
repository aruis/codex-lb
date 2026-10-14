# Graceful shutdown context

## Ali stable quota and drain backport (2026-10-14)

The 1.24.0 ali overlay adapts upstream #2449, #2405 and #2255, with the minimal coalesced-refresh dependency from #2125. See the capability's [requirements](spec.md) and the [verified ali backport](../../changes/archive/2026-10-14-backport-ali-quota-recovery/verification.md) for source and validation details. Existing same-owner recovery, quota-credit semantics and operator configuration remain the stable defaults.

For example, a code-less upstream usage-limit terminal frame marks the serving account rate limited and schedules a tracked refresh. A paid account can recover before its old predicted deadline only after unique post-block evidence proves the same quota window reset. An invalid-request envelope quoting a usage-limit sentence cannot qualify. Restart-time WebSocket admission returns a retryable 503 response with Retry-After rather than an opaque pre-handshake access rejection.
