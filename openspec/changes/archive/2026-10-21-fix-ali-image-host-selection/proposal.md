## Why

Ali's current catalog suppresses gpt-5.5 while advertising gpt-5.6-luna for Pro. Images currently hardcode the suppressed host and fail with HTTP 503 no_plan_support_for_model before contacting upstream.

## What Changes

- Backport upstream #2320's zero-configuration ordered host selector for image generation, editing and default account probes.
- Preserve public image models, explicit probe models, authentication and reservation settlement.
- Validate the deployed artifact, back up the previous image and stopped data volume, and retain a rollback script.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `images-api-compat`: choose a visible unsuppressed internal host.
- `usage-refresh-policy`: default probes share the same host selection.

## Impact

Shared model selector, image routes, account probes and regression tests. No schema migration, settings or dependency changes. Deploy as an overlay on the existing Ali stable image.
