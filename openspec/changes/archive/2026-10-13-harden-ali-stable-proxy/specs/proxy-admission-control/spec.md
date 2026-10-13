## ADDED Requirements

### Requirement: Stable deferred cleanup remains responsive under cancellation
The system MUST finish owned cleanup while preserving caller cancellation without starving unrelated requests. Admission settings refresh MUST NOT hold the per-session pending lock, and a registered admission waiter MUST prevent idle eviction until admission or cleanup completes.

#### Scenario: Cancellation while cleanup is pending
- **WHEN** a request is cancelled while its owned cleanup task is still pending
- **THEN** unrelated event-loop work continues and cancellation is surfaced after cleanup finishes

#### Scenario: Settings refresh is delayed during admission
- **WHEN** admission needs a settings refresh and that refresh is delayed
- **THEN** the session pending lock remains available and the admitting session is not retired as idle

#### Scenario: Downstream closes after the SSE source has finished
- **WHEN** downstream closes during an idle heartbeat and the owned source task has already ended or failed
- **THEN** cleanup collects the owned task outcome without an unhandled-task exception log
