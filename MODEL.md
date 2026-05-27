# Data Model (Prototype)

This prototype is optimized around the assignment’s core risks: **multi-tenancy**, **source-of-truth tracking**, **unit normalization**, and an **auditable analyst review step**.

## Tenancy

### `Organization`
Represents a tenant (client company). All business data is scoped to an org.

- `slug` is used in API paths (`/api/orgs/{org_slug}/...`) to avoid leaking DB IDs.

### `Membership`
Joins a `User` to an `Organization` with a `role`.

- Enforces multi-tenancy at the application boundary (every org-scoped endpoint verifies active membership).
- Roles are used for future permissions (e.g., lock-for-audit restricted to ADMIN).

### `User`
Custom user model (extends `AbstractUser`) so we can evolve without fighting Django’s default auth.

- Kept **username/password** login for the prototype (SimpleJWT) because it’s the shortest path to a working deployed demo.
- `email` is unique to support realistic enterprise identity later.

## Sources and provenance

### `IngestionSource`
Represents a “connection” inside an org for one source type.

- `source_type`: `SAP | UTILITY | TRAVEL`
- `config` JSON stores source-specific metadata that affects parsing/normalization (example: `plant_code_to_facility`).

This is the first building block for real onboarding: the same org can have multiple SAP extracts or multiple utility portals.

### `IngestionJob`
Represents a single ingestion run (one uploaded export in this prototype).

- Stores `input_file` for evidence / replay.
- Stores counters (`received_rows`, `failed_rows`, `suspicious_rows`, `approved_rows`) for analyst UX.
- `status` captures the high-level state: created → parsed/partial/failed → locked.

**Source-of-truth tracking:** every normalized row points back to the `job`, and optionally to an individual `RawRecord`.

### `RawRecord`
Stores row-level parse outcomes.

- `raw`: raw CSV row as JSON
- `parsed`: best-effort parsed row (even when error)
- `status`: `PARSED | ERROR`
- `error`: parse/classification failure string

This is the “what came in / what failed” backbone of the review dashboard.

## Normalized activity rows

### `NormalizedRecord`
Canonical representation of *one activity line* (fuel line, utility billing line, travel product line, etc.).

Key properties:

- **Scope classification**: stored as a field (`SCOPE_1/2/3`) rather than inferred at query time.
  - Fuel → Scope 1
  - Electricity → Scope 2
  - Procurement → Scope 3
  - Travel → Scope 3

- **Category**: distinguishes sub-types that need different downstream treatment (e.g., flight vs hotel emission factors).

- **Unit normalization**:
  - Stores original `quantity` + `unit`.
  - Stores `normalized_quantity` + `normalized_unit`.

  This allows analysts/auditors to see both “what we got” and “what we normalized to”.

- **Billing periods for utilities**:
  - `period_start` / `period_end` stored explicitly.
  - We *do not* force allocation to calendar months in this prototype (see TRADEOFFS).

- **Provenance**:
  - `job` links to ingestion instance.
  - `raw_record` links to the exact raw row when parsing succeeded.

## Analyst review + audit trail

### Review state
`NormalizedRecord.review_status` is the analyst gate before locking:

- `PENDING` → default
- `APPROVED` → analyst signs off on the row
- `REJECTED` → analyst explicitly rejects a row (kept for traceability)

### Suspicious detection
`NormalizedRecord.suspicious` + `suspicious_reasons[]` capture heuristic “needs attention” signals:

- unrecognized or missing units
- missing billing period
- missing spend or currency
- missing travel distance / nights
- non-positive quantities

This is intentionally explainable and debuggable (string reasons) rather than a black-box score.

### Locking for audit
`IngestionJob` can be locked once **no `PENDING` rows remain**. Locking:

- sets `job.status = LOCKED`
- stamps `locked_at`
- sets `NormalizedRecord.is_locked = True` to prevent edits

### `RecordEditLog`
When an analyst edits a normalized row, we write an append-only log:

- `before`: full serialized record
- `after`: full serialized record
- `edited_by`, `edited_at`, `reason`

This provides an explicit **audit trail of analyst changes**, independent of ingestion.

## Why this shape

- Splitting **RawRecord vs NormalizedRecord** avoids a common trap: overwriting raw evidence with “cleaned” data.
- `IngestionJob` is the natural unit of analyst work and audit locking.
- Keeping source config on `IngestionSource` makes onboarding iterative (mapping tables evolve without code changes).
