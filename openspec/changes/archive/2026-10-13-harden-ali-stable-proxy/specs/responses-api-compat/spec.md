## ADDED Requirements

### Requirement: Stable verified stale anchor recovery remains account bound
When upstream definitively rejects a previous response before any downstream-visible output, the system SHALL permit at most one anchor-free replay only if the existing complete-history verifier has marked the captured fresh request retry-safe. The replay MUST retain the same owning account, original request deadline and existing reservation/operation lifecycle. Failure of the replay MUST reach the caller. An unverified history, missing owning account, already-visible output, ambiguous transport failure or previously used replay MUST NOT enable anchor-free recovery.

#### Scenario: Verified complete history after rejected anchor
- **WHEN** upstream rejects an anchor and the complete captured history is verified safe before any output or prior replay
- **THEN** a single same-account request contains the complete history without previous_response_id

#### Scenario: Continuation has no verified complete history
- **WHEN** a rejected continuation has no verified complete-history replay body
- **THEN** the service preserves continuation failure without silently dropping the anchor or context

#### Scenario: Output or replay has already occurred
- **WHEN** output has been delivered or an earlier replay has occurred
- **THEN** the service does not issue another anchor-free replay
