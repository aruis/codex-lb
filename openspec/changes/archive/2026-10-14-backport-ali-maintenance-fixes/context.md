# Ali maintenance batch

The user authorized this batch on 2026-10-14 after reviewing four recommended merged fixes. Sources: upstream #2496, #2513, #2427 and #2484. This extends the 2026-10-13 overlay and does not replace its reliability changes.

For example, a dense 3-hour history must remain complete even when it has more than 64 samples; only older tail rows are capped. A healthy account's Force Probe must not receive a false HTTP 400 because of an obsolete output-token parameter. Backups contain credentials and are retained with restrictive permissions; validation outputs contain no plaintext keys or account identities.

## Rollout result

The final four-file overlay is installed as codex-lb:1.24.0-ali-hotfix-20261014-1. The 11-file cumulative manifest verifies both maintenance files and inherited reliability patches. Live probe, capped/uncapped dashboard parity and dialogue continuation pass. See verification.md for backups, exact image identities and the rollback command to 20261013-2.
