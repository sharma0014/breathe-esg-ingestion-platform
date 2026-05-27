# Sources + Real-world shapes (what I researched, what I modeled)

The assignment explicitly asks for realistic shapes and for me to be able to defend why my sample data looks like it does.

## 1) SAP (fuel + procurement)

### What I researched

- SAP commonly exposes data through a few families of integration patterns:
  - **Flat file exports** from SAP GUI reports / list downloads (still extremely common in early onboarding)
  - **IDocs** for structured message exchange
  - **BAPIs/RFCs** for function-level integration
  - **OData** services (SAP Gateway) for modern API access

### What I chose for the prototype

**Choice:** Flat-file CSV upload.

Why:

- It’s a realistic “first week of onboarding” artifact.
- It naturally includes the messy problems the prompt calls out: German headers, dates in local formats, units, and plant codes.
- It avoids needing SAP credentials or middleware for a deployable demo.

### What the sample looks like and why

File: `sample_data/sap_export_fuel_and_procurement.csv`

- Uses `;` delimiter (common when the locale uses comma decimals)
- Uses EU numeric formatting (`12.990,00`) and decimal comma (`320,00`)
- Includes a **plant code** (`1000`, `2000`) that requires mapping to a facility
- Mixes two line shapes:
  - fuel-like lines with `Menge` (qty) + `ME` (unit)
  - procurement-like lines with `Betrag in Belegwährung` + `Währung`

### What would break in real deployments

- Real SAP extracts vary massively by transaction/report and customization; headers and semantics differ.
- A production system needs strong source versioning, per-client templates, and robust column mapping.
- Procurement often needs PO/invoice/GR reconciliation and sometimes item-level quantities, not just spend.

## 2) Utility electricity

### What I researched

- Facilities teams typically get electricity usage as:
  - portal **CSV export** (common)
  - **PDF bill** downloads
  - less commonly, a utility **API**

- Utility data is naturally organized by **billing period** (start/end), which may not align to calendar months.

### What I chose for the prototype

**Choice:** Portal CSV upload.

Why:

- Easy to acquire for most customers
- Still captures the key modeling problem: billing periods and units

### What the sample looks like and why

File: `sample_data/utility_electricity_portal_export.csv`

- Includes a `Meter ID` and `Service Address`
- Includes `Billing Period Start` and `Billing Period End`
- Includes consumption in both `kWh` and `MWh` (normalized to `kWh`)
- Includes one intentionally broken row with missing usage to demonstrate failed-row handling

### What would break in real deployments

- Some utilities provide multiple usage components (peak/off-peak), demand charges, reactive energy, etc.
- Meter IDs often require mapping to internal facility hierarchies.
- Unit conventions differ (kWh vs kVAh, etc.).

## 3) Corporate travel

### What I researched

- Travel platforms commonly provide:
  - report exports as CSV
  - APIs (e.g., SAP Concur developer portal provides many APIs; using them requires OAuth/app setup)

In practice, onboarding often starts with CSV exports even if an API integration is planned.

### What I chose for the prototype

**Choice:** Travel export CSV upload.

Why:

- Realistic first step without needing credentials
- Lets the prototype show category-specific gaps and suspicious flags

### What the sample looks like and why

File: `sample_data/travel_platform_export.csv`

- Contains `Type` (FLIGHT/HOTEL/CAR/etc.) to drive category classification
- Includes rows where **distance is missing** (common if only airport codes are available)
- Includes an `UNKNOWN` type row to demonstrate row-level failure reporting
- Hotel rows omit `Nights` on purpose to show “suspicious” detection; in a real export this might be present, but missing/blank fields happen

### What would break in real deployments

- Distance computation from airport codes needs an airport reference dataset and cabin class / routing rules.
- Real platforms have complex objects (ticket exchanges, refunds, multi-leg flights) that need a richer model.

