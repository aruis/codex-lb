# Evidence and scope

Backports the host selector from upstream PR #2320, head
`ec528054b6c9bfd3b10360bd04027c43d0dadd25`. The existing private deployment
is based on `f687af8942d4ca952ec850a60150ba361cedf54c` and image
`sha256:2d70f828cf63e132b142009ace3be9465d430ea34ed9985e566c7c28057fb69d`.

On 2026-10-21 at 16:20 CST, Codex's images/generations alias returned HTTP
503 `no_plan_support_for_model` for internal gpt-5.5. The production snapshot
advertises gpt-5.6-luna for Pro and suppresses gpt-5.5. There is no need to
change downstream Codex config, public image models or authentication.

The production overlay replaces only the shared selector, proxy API and
account service. Both replaced existing files match the branch base SHA-256
before patching. No database migrations or new settings.

## Verification before deployment

- Isolated Docker validation with no network and no production mounts:
  231 image/probe/schema/translation/host-matrix tests passed in 157.38s.
- Ruff check and formatting check passed for all eight changed Python files.
- Strict change validation and both affected main specs passed.
- Full strict spec validation: 36 pass, 21 fail. The unchanged HEAD's specs
  reproduce exactly the same 21 failures under the current OpenSpec CLI;
  unrelated historical spec issues were not changed.
- Before/after regression: replacing only the API file with the deployed old
  version causes all four canonical/Codex generation cases to fail (both cold
  and current catalogs); the patched suite passes all four.
- Runtime image builds on the exact installed image and imports successfully;
  cold selection resolves to gpt-5.6-luna.

## Release plan

Private release artifacts: `/opt/codex-lb/patches/20261021-image-host`.
Stopped-volume, image and configuration backup:
`/opt/codex-lb/backups/20261021-image-host`.
Rollback: `/opt/codex-lb/patches/20261021-image-host/rollback.sh`.
Rollback restores the old image/config and preserves current data; restore the
stopped-volume archive only for disaster recovery while the service is stopped.
Real image generation and ordinary Responses must pass after cutover.

## Deployment result

Deployed `codex-lb:1.24.0-ali-hotfix-20261021-1`, image ID
`sha256:58552e4d34436fd2b690f86902a10cd414b20a3765e6a18ebe7c1b63265177b0`.
Runtime source commit: `070696c8` (later documentation commits do not change
runtime code). Ready check passed; total cutover including graceful stop,
backup and cold startup was 357.9 seconds. Startup was slow while the host
showed swap-in activity and 37-46% I/O wait; no OOM or container restart.
This operational constraint is independent of the host-selector change.

The previous image archive is 100,275,200 bytes; the stopped-volume archive
is 1,007,656,960 bytes, including database and encryption key. SQLite quick_check
returned ok, revision remains 20260816_000000_add_model_source_embeddings.
Backup directory is mode 0700, archives 0600, rollback script 0700.

## Post-deployment checks

Real authenticated request to `/backend-api/codex/images/generations` using
`gpt-image-2` succeeded in 24.74s, HTTP 200, PNG 1,185,856 bytes and
1254x1254 pixels (the upstream returned those dimensions for a 1024x1024
request). Output SHA-256:
`5ee558abf865038a8d8c3170a843c603036f8e7c22b1ce9fdff48d25d2470853`.
Usage reported 23 input and 515 output tokens, total 538. Logs confirm
internal gpt-5.6-luna selection and images_route_complete status=200.
The returned dimensions are recorded as an existing upstream behavior, not
corrected or promised by this host-compatibility patch.

Ordinary gpt-6.1-sol Responses returned HTTP 200 and response.completed.
The expiring temporary test key was deleted in finally. Docker reports
healthy, zero restarts and OOMKilled=false. Rollback script passes sh -n.
Private release evidence and a Git bundle were also retained locally under
`~/.codex/backups/codex-lb/20261021-image-host/`.
