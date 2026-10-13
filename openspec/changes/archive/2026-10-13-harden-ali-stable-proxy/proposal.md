## Why

The ali deployment runs v1.24.0 on Python 3.14. Its seven-day request history contains 98 incomplete streams, 62 with a rejected previous-response anchor, and connection timeouts. Stable also predates the reviewed cancellation and admission-lock fixes #1969/#1972. Apply a bounded reliability patch without adopting the beta native transport or dashboard authentication migrations.

## What Changes

- Backport cancellation-safe shared-future waiting and resolve admission settings before the session lock.
- Recover a definitively rejected anchor once on the same account only when the existing verifier proves the complete anchor-free request is safe and no output has been delivered.
- Preserve terminal errors for unverifiable continuation state and ambiguous transport failures.
- Package an overlay of the installed stable image; back up deployment/data, validate independently, and retain a rollback image.
- Inspect the existing proxy path without changing egress identity or authentication.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `proxy-admission-control`: bounded deferred cleanup and settings-free admission critical sections.
- `responses-api-compat`: verified same-account replay after definitive anchor rejection.

## Impact

Python stream/bridge utilities and targeted regressions. No database migration, public endpoint change, token exchange, or frontend change. Deployment uses a clearly identified local stable patch image and the existing data volume.
