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
