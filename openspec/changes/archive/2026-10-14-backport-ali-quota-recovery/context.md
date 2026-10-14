# Ali quota recovery backport

Sources: Soju06/codex-lb PRs #2449 (143e07d0), #2405 (3d501ac5), and #2255 (3b75bb2d). Scope is the first three repairs approved in this conversation, on codex/ali-stable-hotfix-20261014. The deployment has one Pro account and SQLite, so a mistakenly blocked or exhausted account can interrupt all traffic.

Example: an account was blocked until Friday, but fresh usage history proves that the exact weekly window reset on Wednesday. It can recover after the minimum cooldown only when the deadline anchor is unique and its real short window is not still exhausted. An unrelated model throttle does not qualify.

A response.failed envelope without code containing an upstream usage-limit sentence is recognized as account exhaustion. An invalid_request_error that quotes the same sentence stays request-scoped. Replays retain existing account ownership, visible-event, reservation, and settlement guards.

Deployment outcomes, checks, source hashes, and rollback location will be recorded after verification. No claim is made that all historical stream failures stem from these defects.

Stable adaptation: the immediate coalesced refresh needs the minimal request-refresh mechanism from upstream #2125 (35ccf8e9), without its metrics additions. The existing stable owned-session refresh path stays intact. Explicit usage-refresh disablement is respected.

The newer short replica-local HTTP-429 burst-cooldown contract in #2449 assumes unrelated beta code absent from stable and is excluded. Explicit rate_limit_exceeded keeps stable behavior.
