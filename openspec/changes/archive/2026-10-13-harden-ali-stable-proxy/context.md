# Ali stable reliability patch

## Purpose
An operational patch for the user's explicitly authorized ali deployment. Keep v1.24.0's runtime and schema while correcting verified continuation recovery and starvation defects.

## Evidence
On 2026-10-13 the server was healthy at ~246 MiB RSS and ~1.3% CPU after 16 days. Seven-day non-cancelled model requests had 195 failures out of 3,967 completions. Of 98 stream_incomplete records, 62 carried previous_response_not_found. There were also connection timeouts, invalid input content arrays, and unsupported image web search. Image generation itself succeeded five times.

## Constraints and decisions
Do not publish credentials, restart unrelated services, upgrade the schema, change proxy identity, or silently discard tool/history context. A rejected anchor is recoverable only with an existing verified complete-history body and no delivered output. For example, a complete transcript whose prefix matches the stored conversation may replay once without the invalid anchor; a lone "continue" message may not.

## Operations
Keep backup and rollback commands on ali, with restrictive permissions. Observe post-deployment errors separately from health probes and unit tests. A passing patch test does not establish that all historical connection errors are solved.

The installed final overlay is `codex-lb:1.24.0-ali-hotfix-20261013-2`; the dashboard retains stable version 1.24.0. Two real requests, including complete-history continuation with a server-injected anchor, succeeded after deployment. See verification.md for image identity, backup location, readiness timing and rollback. No beta upgrade is needed for these targeted fixes. A later official upgrade will replace this local overlay, so review whether it contains these fixes before replacing it.
