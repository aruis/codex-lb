# Ali maintenance verification

## Completeness, correctness and coherence

Four backend files implement upstream #2496, #2513, #2427 and #2484 on the installed 1.24.0 overlay. Existing account ownership, reservation settlement, request deadlines and first-batch cleanup/recovery are untouched. No schema, dependencies, settings or dashboard response fields change.

The pre-fix tests reproduce 22 functional failures across force-probe route (1), control headers (16), abandoned shared wait (1) and capped SQLite repository (4). An additional adapted dashboard product regression reproduces the unbounded 10080-row fetch versus the expected 4350 rows. Initial upstream dashboard test names/defaults were incompatible with stable and were adapted rather than importing newer dashboard behavior.

The final suites cover service and admin probe routes, 48 direct/routed native/SDK media-type variants plus bodyless/default bodies, live/late/cancelled/abandoned waiters and SSE cleanup, account cutoffs, zero/negative caps, uncapped recent bursts, all-recent histories, oldest-first ordering and existing index plans. Stable dashboard capped/uncapped payload parity is checked with 10080 samples. First-batch continuation, cancellation and idle-admission regressions are included.

## Validation evidence

- Local Python 3.14.8: 1109 passed, 9 PostgreSQL-only skipped, 95.71 seconds.
- Production Python 3.14.7 isolated image: 1108 passed, 9 PostgreSQL-only skipped, 1 deselected, 246.67 seconds. The deselected check scans Git-tracked source and passed locally; the production-derived image intentionally has no Git. Runtime tests had no production volume or network. Six Hypothesis cache-location warnings use an in-memory test cache.
- Ruff lint/format, ty for the four changed backend files and git whitespace checks pass.
- Change strict validation and all four affected main specs strict validation pass. Normal main-spec validation: 57 passed, zero failed. Historical whole-tree placeholder-Purpose warnings are outside this change.
- Before-image source hashes for all four files matched the installed image. The final image verifies their patch hashes plus all seven inherited first-batch patch hashes.
- In the dense product test the stable cap/floor hydrates 4350 instead of 10080 rows (56.8% fewer); this is fixture-specific and not a claim of the same production speedup.

## Deployment and rollback

- Deployed image: `codex-lb:1.24.0-ali-hotfix-20261014-1`, image id `sha256:21f2ac230d32da720bc46acc9172235818bb4360ebb5971cb5cf835ea440d7de`. The dashboard version remains 1.24.0 because this is a local stable overlay.
- Previous exact image: `sha256:6b470fe442d484ef98a6c73b938a58c6ea6f2fe0f279d9f0b6f0e379c7031c67`, retained as `codex-lb:ali-before-maintenance-20261014` and in a 99,891,200-byte image archive. Loading the archive succeeded and restored the expected image id.
- Backup directory: `/opt/codex-lb/backups/20261014-maintenance/`, mode 0700. Saved Compose/config, deployment metadata, image-before.tar and data-volume.tar are mode 0600. Full volume snapshot size 729,169,920 bytes; it contains store.db and encryption.key. Stopped SQLite quick_check returned `ok`.
- Only Compose service `server` was recreated. Cutover including graceful stop, consistent volume backup, database validation and cold startup: 173.0 seconds. Readiness budget was 240 seconds after recreate.
- Schema remains `20260816_000000_add_model_source_embeddings`; no migrations ran.
- Actual Force Probe: HTTP 200, 4.24 seconds; before/after account status active and usage refresh fetch succeeded. The standalone diagnostic explicitly initializes/closes its own HTTP client; it does not reuse the web process's client singleton.
- Actual dashboard: 4349 capped rows versus 11358 uncapped rows, with full stable payload parity at a fixed diagnostic clock. This is 61.7% fewer hydrated rows for the current dataset, not a measured latency claim. The cap/clock overrides exist only in the temporary diagnostic process and are restored before exit; server settings are unchanged.
- Two authenticated gpt-6-luna requests completed with HTTP 200 and OK in 2.57 and 1.35 seconds. The second carries full dialogue history; server logs confirm a session-anchor injection. The expiring temporary key was removed and the final database count is zero.
- Final health and ready endpoints: HTTP 200. Docker healthy, restart count zero, OOM false. One active Pro account. Sample CPU 1.44%, memory 268 MiB / 1 GiB. Startup and smoke logs have zero ERROR/Traceback and no continuity-persistence failure.
- Rollback script syntax and saved Compose configuration validate; the saved image archive was actually loaded successfully. Live rollback was not invoked because deployment and smoke checks passed.

Return to the immediately previous 20261013-2 patch, retaining its earlier fixes:

```sh
ssh ali '/opt/codex-lb/patches/20261014-maintenance/rollback.sh'
```

The script can reload the saved image if its retained tag is missing, restores the previous Compose file and recreates only server without pulling. Allow up to 240 seconds for cold startup, then verify /health/ready. Schema-compatible rollback preserves current data. Restore data-volume.tar only for actual data recovery, as doing so discards later writes. The original unpatched 1.24.0 rollback remains available separately under the 20261013-reliability directory.

Source overlay, final manifest, Dockerfiles, test logs, operational scripts and deployment-result.json are retained at `/opt/codex-lb/patches/20261014-maintenance/`. The local managed stable worktree retains the cumulative code/tests and both archived changes. No commit or public PR was created during the deployment itself.

## Limitations

This batch does not implement unsupported image web search, rewrite invalid user content arrays, add quota-reset recovery, alter external proxy identity or prove a lower long-term request failure rate. General external network failures can still occur.

## Source preservation

The two deployed batches are preserved on the personal fork branch
[aruis/codex-lb](https://github.com/aruis/codex-lb/tree/codex/ali-stable-hotfix-20261014),
based on v1.24.0. It contains source, regression tests, OpenSpec changes,
manifests and deployment/rollback scripts. Database snapshots, encryption
keys, image archives and deployment credentials remain in the protected
server backups. Exact runtime restoration uses the saved image archive; a
new build from the source branch may use a newer base runtime image.

Archived operational scripts were normalized for repository lint/format
checks before publication. Their formatting retained the parsed program
structure (apart from import order). The dashboard diagnostic now uses
scoped standard-library patch contexts to restore its clock/cap overrides,
which also satisfies full-repository typing. The 11 deployed source-file
checksums remain unchanged.

## Source-publication checks

Before pushing the preservation branch, full-repository Ruff lint/format and
ty checks passed, as did proxy architecture checks, frontend lint/type/build
and 1148 frontend tests. The broader backend gate passed 6404 unit tests
(71 skipped), 2023 core integration tests (32 skipped), 259 HTTP/WebSocket
bridge tests, and 27 e2e tests (1 skipped). SQLite migration upgrade/drift
checks and source/wheel packaging were also run separately.

Full make ci stopped at its PostgreSQL stage because the local test service
at 127.0.0.1:5432 was unavailable. The downstream PostgreSQL migration,
Docker and Kubernetes/Helm stages did not run in that attempt. This record
distinguishes the validated deployed snapshot from a completed full CI gate.
