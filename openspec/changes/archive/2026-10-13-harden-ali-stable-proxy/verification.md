# Verification evidence

## Completeness and correctness

- Cancellation/shared-future and admission-waiter fences are adapted from merged upstream #1969 and #1972, without their unrelated later changes.
- Same-owner recovery requires the existing verified fresh-body flag, a definitive anchor rejection, zero replay count, no response id/events, and no visible/model output. It parses the captured complete body, retains the account and deadline, fences registered operation spool reset before closing the old session, and reuses the existing reservation/operation lifecycle.
- Nine new service-path cases cover verified and rewritten rejections, incomplete history, visible output, accepted responses, prior replay, repeated failure, operation identity and failed owner fence.
- The new cases against unmodified v1.24.0 reproduce five failures; four conservative controls pass. The patched version passes all nine.

## Validation

- Final local Python 3.14.8 affected unit/integration suites: **908 passed** (91.14 seconds). Earlier revision: 906 passed (207.31 seconds).
- Final production Python 3.14.7 isolated image: **136 passed** (29.58 seconds), without mounting production data or networking. Earlier revision: 134 passed (32.54 seconds).
- Changed production files: Ruff lint/format and ty checks passed; git diff whitespace check passed.
- Strict change validation passed. Normal main-spec validation: **57 passed**.
- Strict whole-tree validation reports 22 pre-existing placeholder-Purpose warnings in the stable tag; affected capabilities pass. This patch does not rewrite unrelated specifications.
- Corrected two upstream regression-test timestamps to use the current monotonic clock, so tests do not rely on host uptime. Corrected an existing bridge test's missing database fixture. These corrections change test setup only.
- Final downstream-close cases reproduce two uncollected owned-source task exceptions before the SSE cleanup adjustment; both pass after the adjustment. The source may end normally or fail while the wrapper is paused on a heartbeat.

## Runtime identity

All seven original production file SHA-256 values matched the v1.24.0 Git tag before patching. The overlay uses the retained exact installed base image; packages, dashboard, endpoints and migration files are unchanged. The image manifest records original and patched hashes.

## Deployment and live validation

- Deployed image: `codex-lb:1.24.0-ali-hotfix-20261013-2`.
- Deployed image id: `sha256:6b470fe442d484ef98a6c73b938a58c6ea6f2fe0f279d9f0b6f0e379c7031c67`.
- All seven production source hashes match the revision-2 manifest. The dashboard version remains 1.24.0 because this is a local stable overlay.
- Original stable image retained as `codex-lb:ali-baseline-20261013` (image id `sha256:ba5598aaa70f7acf74a958139037604621ec2582a7fb5fe1e870f08bece807d6`).
- Consistent stopped-volume backup and original deployment/config: `/opt/codex-lb/backups/20261013-reliability-final/`. The 728,616,960-byte tar includes the SQLite store and encryption key; backup directory mode 0700 and files 0600. SQLite quick_check returned `ok`.
- Schema revision remains `20260816_000000_add_model_source_embeddings`; no migration was run. Only Compose service `server` was recreated.
- Initial 45-second readiness window caused an automatic rollback; the original image also needed about 74 seconds to start. The rollback restored a healthy original service. Subsequent readiness validation used 240 seconds; final revision-2 cutover completed in 93.8 seconds.
- Final `/health` and `/health/ready`: HTTP 200. Docker healthy, restart count 0, OOM false. One active Pro account remains available. Final sample: 235.7 MiB / 1 GiB, CPU 1.23%.
- Final two authenticated `gpt-6-luna` requests returned HTTP 200 and completed with `OK` in 4.47 and 2.36 seconds. The second request carried complete dialogue history; logs confirm one `session_anchor_injected`, and both request records are successful.
- Temporary five-minute test key was created and removed through the API-key service; the final database check found zero remaining test keys. Credentials were never printed.
- Final container startup and smoke logs: zero ERROR/Traceback and zero `bridge_continuity_persistence_failed`. This observation covers startup and smoke validation, not a long-term error-rate claim.

## Rollback and reproduction

Restore the exact original deployment without downloading another image:

```sh
ssh ali '/opt/codex-lb/patches/20261013-reliability/rollback.sh'
```

Schema-compatible rollback preserves current data. Restore the stopped-volume snapshot only for actual data recovery, because restoring it loses newer writes. Allow up to 240 seconds for cold startup and recheck readiness.

The seven source files, Dockerfile, manifest, isolated-test images/logs, deployment result and rollback script are retained at `/opt/codex-lb/patches/20261013-reliability/`. Local code and tests remain in the attached stable worktree. Deployment scripts and the final manifest are retained beside this record.

## Remaining limitations

External proxy connection timeouts were not deterministically reproduced: five unauthenticated upstream connectivity probes returned expected HTTP 401 in 0.9–2.2 seconds. Unsupported image web search and invalid input content arrays require separate compatibility evidence and are not silently rewritten. Production error-rate improvement requires new traffic observations and is not inferred from health checks.
