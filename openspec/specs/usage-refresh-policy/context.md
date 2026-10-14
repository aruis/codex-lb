# Usage Refresh Policy Context

## Purpose

This context explains how codex-lb derives an account's usage and status, and
how to diagnose disagreements between codex-lb and Codex Desktop or the Codex
CLI quota pill.

codex-lb treats `/wham/usage` as the source of truth for account usage. Other
OpenAI account surfaces can display reset state earlier than `/wham/usage`,
especially during team reset windows, so the dashboard can temporarily show an
account as `rate_limited` even when Codex Desktop says the quota has reset.

## Upstream Usage Source

codex-lb refreshes account usage by calling:

```http
GET https://chatgpt.com/backend-api/wham/usage
```

The call is made per account on the configured refresh tick, which defaults to
60 seconds. The client lives in
[`app/core/clients/usage.py`](../../../app/core/clients/usage.py), and the
scheduler lives in
[`app/core/usage/refresh_scheduler.py`](../../../app/core/usage/refresh_scheduler.py).

## Status Derivation

The fetched usage is fed through
[`apply_usage_quota`](../../../app/core/usage/quota.py), which derives account
status from `primary_window.used_percent`:

- `secondary_used >= 100`, regardless of `primary_used`: `QUOTA_EXCEEDED`
- `used_percent >= 100` on the primary rate-limit window: `RATE_LIMITED`
- `used_percent < 100`: `ACTIVE`

There is no manual reset step inside codex-lb. Recovery is driven by the next
refresh tick that observes a sub-100 value from `/wham/usage`.

## Why Codex Settings Can Disagree

Codex Desktop's Settings -> Account view and `/wham/usage` are fed by different
OpenAI-side data sources:

- `/wham/usage` exposes the rate limiter's internal counter. It updates lazily,
  typically on the next chargeable request through that account, or when its
  internal window crosses `reset_at`.
- Settings -> Account is fed by a separate account/quota view that often picks
  up team-side reset events earlier.

During a reset window it is normal for Settings -> Account to show the reset
state while `/wham/usage` still returns `used_percent: 100` for a short period
afterwards. codex-lb mirrors `/wham/usage` during that window, so the account
stays `RATE_LIMITED` or `QUOTA_EXCEEDED` until upstream catches up.

## Limit Warm-Up Exhaustion Threshold

Reset-confirmed limit warm-up compares the usage sample from before a refresh
with the sample written after that refresh. The pre-refresh sample must be at
or above the configured exhausted threshold, the post-refresh sample must be
below `100`, and `reset_at` must move forward.

The exhausted threshold defaults to `99.0` because some upstream usage payloads
plateau at 99 percent for windows that are practically exhausted. This avoids
missing reset-confirmed warm-ups for those accounts while keeping the reset
confirmation requirement intact. Operators who want the historical strict
behavior can set the threshold to `100.0`.

## Operational Notes

- Wait first. The next request through that account usually wakes the upstream
  rate limiter; codex-lb auto-recovers on the next refresh tick after the
  upstream payload changes.
- The dashboard Force Probe action fires one minimal `responses.create` against
  the selected account and immediately refreshes its usage. An accepted 2xx
  probe also contributes to that replica's probing-health recovery streak;
  non-2xx results do not restore routing health. Settlement reloads and
  normalizes weekly/monthly and zero-primary-capacity usage like ordinary
  routing and is discarded when newer replica-local runtime activity arrives
  during that snapshot load.
- Do not manually flip the codex-lb account state to `ACTIVE` while
  `/wham/usage` still reports the account as fully used. That only masks the
  upstream state and can route traffic back to an account that the upstream
  limiter will reject.

## Verification Example

To confirm that the disagreement is upstream rather than codex-lb's mirror,
call `/wham/usage` directly with the same account token codex-lb is using:

```bash
ACCESS_TOKEN=...
ACCOUNT_ID=...   # chatgpt-account-id UUID, not codex-lb's id

curl -s https://chatgpt.com/backend-api/wham/usage \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "chatgpt-account-id: ${ACCOUNT_ID}" \
  -H "Accept: application/json" | jq '.rate_limit'
```

If `primary_window.used_percent` is still `100` here while Settings -> Account
shows the account as reset, codex-lb has nothing fresher to mirror. The account
is inside the upstream propagation window, and the practical fix is to wait or
use the Force Probe action. Check its `probe_status_code`: a non-2xx response
does not count as evidence that the account is healthy.

## Related Work

- [#676 - initial bug report on `/wham/usage` vs. Settings UI divergence](https://github.com/Soju06/codex-lb/issues/676)
- [#677 - dashboard per-account force-probe action](https://github.com/Soju06/codex-lb/issues/677)

## Ali stable Force Probe compatibility

The 2026-10-14 maintenance overlay adapts upstream #2496 to the stable probe body. It omits the obsolete output-token field so a usable account is not reported as HTTP 400 solely because upstream rejects that parameter. The probe still sends one tiny account-bound request and refreshes usage; it does not enable a new quota-reset or account-recovery policy.

For example, Force Probe on the selected Pro account sends a single-dot instruction without max_output_tokens. A successful status can inform existing probe settlement, while an unrelated auth or network failure retains its original status. Validation and rollback are recorded in `openspec/changes/archive/2026-10-14-backport-ali-maintenance-fixes/verification.md`; see spec.md for the endpoint contract.

## Ali stable quota and drain backport (2026-10-14)

The 1.24.0 ali overlay adapts upstream #2449, #2405 and #2255, with the minimal coalesced-refresh dependency from #2125. See the capability's [requirements](spec.md) and the [verified ali backport](../../changes/archive/2026-10-14-backport-ali-quota-recovery/verification.md) for source and validation details. Existing same-owner recovery, quota-credit semantics and operator configuration remain the stable defaults.

For example, a code-less upstream usage-limit terminal frame marks the serving account rate limited and schedules a tracked refresh. A paid account can recover before its old predicted deadline only after unique post-block evidence proves the same quota window reset. An invalid-request envelope quoting a usage-limit sentence cannot qualify. Restart-time WebSocket admission returns a retryable 503 response with Retry-After rather than an opaque pre-handshake access rejection.
