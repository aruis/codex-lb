## Context

See proposal.md. The live service uses Python 3.14 and one Pro account, with existing HTTP smart bridge routing and a Mihomo HTTP CONNECT proxy. Five unauthenticated connectivity probes received the expected HTTP 401 in 0.9–2.2 seconds; no deterministic proxy outage was reproduced. Credentials and egress identity stay untouched.

## Goals / Non-Goals

Recover verified stale anchors and prevent cancellation/admission lock starvation. Do not introduce beta native egress, new schema, arbitrary history truncation, image-web-search emulation, or unverified failover.

## Decisions

- Adapt merged #1969 and #1972 to stable source. Preserve their regression tests, shared-future semantics and admission-waiter fence.
- Reuse the existing full-history verifier and captured fresh request. Recovery requires a definitive previous-response rejection, no visible output, no response id/event, and zero prior replay. Rebuild only that verified fresh body, preserve operation fencing and reuse the current local recovery lifecycle.
- Keep replay strictly pinned to the initial serving account, including file references. Do not add cross-account fallback or overwrite request history.
- Build an overlay from the installed stable image so Python packages and dashboard assets remain identical. Record patch checksums and use an explicit local image tag.

## Risks / Trade-offs

- Incorrect context proof could lose history → reuse existing verifier and test unverified, visible-output and already-replayed controls.
- Cancellation shielding could hide disconnects → retain upstream cancellation-marker regressions.
- A short smoke test cannot prove a lower production error rate → report validation separately from subsequent traffic observations.
- External connection timeouts and unsupported upstream request shapes remain possible → record them explicitly; do not silently delete client data or change proxy routes.

## Migration Plan

Validate locally and inside an isolated stable-overlay container. Record the original image id and deployment file, create a consistent database backup and retain encryption/config files with restricted permissions. Stop the old container gracefully at cutover, back up the stopped volume, recreate only codex-lb with the overlay, then verify health, account access and logs. Roll back to the original image if verification fails; schema-compatible rollback retains current data. The full stopped-volume snapshot is reserved for data recovery, since restoring it would discard newer requests.

Cold startup of both the original image and the overlay exceeded an initial 45-second deployment readiness window. Automatic rollback worked; subsequent deployment uses a 240-second validation window without changing request timeouts. A real smoke request uncovered an already-finished SSE source task whose exception was not collected on downstream close. Revision 2 collects that owned task outcome; two regression cases first reproduced the issue and then passed.
