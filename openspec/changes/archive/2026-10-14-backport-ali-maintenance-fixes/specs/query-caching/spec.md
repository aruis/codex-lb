## MODIFIED Requirements

### Requirement: Projection history reads are bounded per account
The dashboard projections history fetch MUST NOT widen every account's lookback to the widest account window. On PostgreSQL and on capped SQLite reads, the bulk usage-history read MUST bound rows per account by that account's own cutoff. When a per-account row cap is supplied, each account's slice MUST contain every in-cutoff row at or after the supplied uncapped recent floor plus the newest cap-many in-cutoff rows older than that floor. Without a recent floor, the slice MUST contain only the newest cap-many in-cutoff rows. Results MUST be ordered oldest-first by recorded time and row id; on SQLite, nonpositive caps MUST return no tail rows. Uncapped SQLite reads SHALL retain the existing shared-floor snapshot-cache semantics and caller-side cutoff trimming.

The stable projections caller SHALL retain its existing 4320-row cap, configured smoothing floor and response schema. The retained history MUST preserve smoothing values and six-hour recent-burn coverage under the live ingestor's five-second minimum per-account write interval. Capped SQLite reads MUST use existing composite indexes without a temporary sort B-tree.

#### Scenario: One weekly account does not widen the fetch for short-window accounts
- **GIVEN** one account with a 7-day window and several accounts with 5-hour windows
- **WHEN** a capped projections fetch runs on PostgreSQL or SQLite
- **THEN** rows for the 5-hour accounts are bounded by their own cutoff before the cap is applied

#### Scenario: SQLite snapshot cache keeps the shared floor
- **GIVEN** the SQLite backend serves uncapped history through its snapshot cache
- **WHEN** per-account cutoffs are supplied without a row cap
- **THEN** the read retains shared-floor cache semantics and the caller trims each account's slice

#### Scenario: Dense recent samples remain complete
- **WHEN** an account has more recent in-cutoff samples than its row cap
- **THEN** all samples at or after the supplied recent floor remain present, followed in chronological ordering with the newest capped older tail

#### Scenario: Nonpositive tail caps and all-recent histories
- **WHEN** a SQLite cap is zero or negative
- **THEN** no older tail rows are returned and recent-floor rows remain complete
- **WHEN** the supplied recent floor covers the entire cutoff
- **THEN** every in-cutoff row is returned regardless of the tail cap

#### Scenario: Stable dashboard projections match uncapped output
- **GIVEN** 10080 minute-spaced weekly samples and the stable default 30-minute smoothing floor
- **WHEN** the dashboard fetch uses its 4320-row tail cap
- **THEN** 4350 rows are hydrated instead of 10080
- **AND** the stable projection output agrees with the uncapped result within floating-point precision

#### Scenario: SQLite capped probes use existing composite indexes
- **WHEN** capped primary, secondary and floor-exempt compound probes are explained
- **THEN** the query plans use existing usage-window/account indexes and no temporary sort B-tree
