# Tradeoffs (deliberately not built)

## 1) Async ingestion pipeline (queues, retries, partial reprocessing)

- Why it matters: real enterprise exports can be large, and parsing needs robust retries and observability.
- Why I didn’t build it: the prototype goal is to demonstrate a defendable data model and review flow.
- What I’d do next: Celery/RQ + job state machine + per-row idempotency keys + structured error codes.

## 2) Full emission factor engine

- Why it matters: auditors eventually care about the factor versioning, geography, and methodologies.
- Why I didn’t build it: prompt emphasizes ingestion + normalization as the hard part; factor work would be a separate domain.
- What I’d do next: separate `EmissionFactor` tables with validity periods + method versions, plus computed “emissions rows” derived from normalized activity rows.

## 3) Analyst mapping UI (plants/meters/vendors → facilities/categories)

- Why it matters: onboarding almost always needs interactive mapping and master-data curation.
- Why I didn’t build it: would expand frontend scope substantially.
- What I’d do next: a small “Mappings” screen per source with CSV import/export, row-level diff, and audit logs.
