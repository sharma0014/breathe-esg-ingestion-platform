# Decisions

This document records the key ambiguities in the prompt and what I chose for the prototype.

## Global product decisions

### Multi-tenancy boundary
**Choice:** All API routes that touch client data are nested under `/api/orgs/{org_slug}/...`.

- Why: explicit tenancy is hard to accidentally bypass; it also mirrors how an analyst would think (“I’m working in ACME”).
- Alternative: org inferred from token claims or a header. That’s convenient but easier to misuse.

### Review gate + audit lock
**Choice:** Records must be `APPROVED` or `REJECTED` (no longer `PENDING`) before a job can be locked.

- Why: matches “approve rows before they’re locked for audit” and forces a deliberate analyst action.
- Tradeoff: rejected rows are still present (for traceability). A real system might require remediation workflows.

### Emissions calculation
**Choice:** This prototype focuses on ingestion + normalization + review, not carbon factor calculation.

- Why: prompt explicitly says the hard part is messy data ingestion, not computing carbon.
- What’s left: normalized fields are designed to plug into an emission-factor engine later.

## Source 1: SAP (fuel + procurement)

### Ingestion mechanism
**Choice:** File upload of a flat CSV export (SAP GUI list → spreadsheet export).

- Why it’s realistic: many enterprises still move data around as “CSV from SAP” for ad-hoc reporting and onboarding.
- Why not IDoc/OData/BAPI in this prototype: those require integration/auth, middleware, and a much larger surface area.

### Subset of SAP reality handled
**Handled:**
- Fuel-like lines: rows with `Quantity` + `Unit` (or German equivalents) → normalized to liters
- Procurement-like lines: rows with `Amount` + `Currency` → stored as spend
- German headers are supported for a pragmatic subset (`Belegdatum`, `Menge`, `ME`, `Währung`, etc.)
- EU numeric formats supported (e.g., `12.990,00`)

**Ignored (explicitly):**
- Line-item taxes, GR/IR reconciliation, returns/credit memos, split accounting, and SAP master-data joins
- Deep plant code validation (we only support a simple mapping table)

### Plant codes
**Choice:** Source config can contain `plant_code_to_facility` mapping.

- Why: in real onboarding, plant codes are meaningless without a lookup.
- Prototype scope: a management command seeds a small mapping; a real UI would let analysts maintain it.

## Source 2: Utility electricity

### Ingestion mechanism
**Choice:** File upload of a portal CSV export.

- Why: utilities vary widely; CSV exports are a common “least common denominator” across providers.
- Why not PDFs: realistic but would require OCR/PDF parsing that would dominate the 4-day prototype.

### Billing periods
**Choice:** Keep the utility billing period as `period_start` → `period_end`.

- Why: real bills don’t align to calendar months; forcing alignment without an explicit policy is risky.
- Analysts can review periods directly.

### Subset handled
- kWh and MWh normalization to kWh
- date formats `YYYY-MM-DD` and `DD/MM/YYYY` (day-first parsing)

Ignored:
- tariffs, TOU (time-of-use) buckets, demand charges as first-class fields

## Source 3: Corporate travel

### Ingestion mechanism
**Choice:** File upload of a CSV export from a travel platform.

- Why: most travel platforms can export report CSVs, and customers frequently start onboarding with exports.
- Alternative: API pull (Concur/Navan APIs). I researched Concur’s API docs; it’s viable but requires OAuth/app setup that’s hard to demo without credentials.

### Distances
**Choice:** Flag missing distance as `suspicious`.

- Why: travel exports sometimes provide only airport codes; distance is a common gap.
- Not built: airport-code → distance calculation (would require a maintained airport reference dataset).

### Subset handled
- Product classification: FLIGHT/HOTEL/GROUND-ish categories
- Missing/unknown types become row-level failures (visible to analysts)

## What I would ask the PM

- What’s the intended “unit of audit”: per-job, per-period, or per-reporting-cycle lock?
- Should rejected rows be excluded from downstream outputs automatically or require remediation?
- Do we need a mapping UI (plants/meters/suppliers → facilities/categories), and who owns it (client vs analyst)?
- Should we support incremental loads (idempotency keys) or is each upload a one-off snapshot?
