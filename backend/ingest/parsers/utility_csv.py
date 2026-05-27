from typing import Any

from .utils import ParsedRow, _to_decimal, normalize_unit, parse_date, read_csv_bytes, suspicious_reasons_for


UTILITY_START_KEYS = ['Billing Period Start', 'Start Date', 'From', 'Period Start']
UTILITY_END_KEYS = ['Billing Period End', 'End Date', 'To', 'Period End']
UTILITY_METER_KEYS = ['Meter ID', 'Meter', 'Meter Number', 'Service Point']
UTILITY_ADDR_KEYS = ['Service Address', 'Address', 'Site']
UTILITY_USAGE_KEYS = ['Usage', 'Consumption', 'kWh', 'Energy']
UTILITY_UNIT_KEYS = ['Usage Unit', 'Unit', 'UOM']
UTILITY_COST_KEYS = ['Cost', 'Amount', 'Total Cost']
UTILITY_CCY_KEYS = ['Currency', 'CCY']


def _first_value(row: dict[str, str], keys: list[str]) -> str:
    for k in keys:
        if k in row and row[k] != '':
            return row[k]
    return ''


def parse_utility_export(data: bytes, *, source_config: dict[str, Any] | None = None):
    """Parses a portal CSV export for electricity usage.

    Assumptions (documented in SOURCES.md):
    - Facilities team exports a CSV with a billing period (start/end)
    - Usage is an energy quantity with a unit (kWh/MWh)
    - Billing periods may not align with calendar months (we keep the period as-is)
    """

    rows = read_csv_bytes(data)
    parsed_rows: list[ParsedRow] = []

    for idx, r in enumerate(rows, start=2):
        raw = dict(r)
        start_str = _first_value(r, UTILITY_START_KEYS)
        end_str = _first_value(r, UTILITY_END_KEYS)
        meter = _first_value(r, UTILITY_METER_KEYS)
        addr = _first_value(r, UTILITY_ADDR_KEYS)

        usage_str = _first_value(r, UTILITY_USAGE_KEYS)
        unit_str = _first_value(r, UTILITY_UNIT_KEYS)
        if 'kWh' in r and not unit_str:
            unit_str = 'kWh'

        cost_str = _first_value(r, UTILITY_COST_KEYS)
        ccy = _first_value(r, UTILITY_CCY_KEYS)

        period_start = parse_date(start_str)
        period_end = parse_date(end_str)
        usage = _to_decimal(usage_str)
        normalized_qty, normalized_unit = normalize_unit(usage, unit_str)

        rec = {
            'category': 'ELECTRICITY',
            'scope': 'SCOPE_2',
            'source_row_ref': meter or f"row-{idx}",
            'period_start': period_start,
            'period_end': period_end,
            'description': addr or f"Meter {meter}" if meter else 'Utility electricity line',
            'quantity': usage,
            'unit': unit_str,
            'normalized_quantity': normalized_qty,
            'normalized_unit': normalized_unit,
        }

        cost = _to_decimal(cost_str)
        if cost is not None:
            rec['spend_amount'] = cost
            rec['spend_currency'] = ccy

        reasons = suspicious_reasons_for(rec)
        rec['suspicious'] = len(reasons) > 0
        rec['suspicious_reasons'] = reasons

        # Treat rows with completely missing usage as parse errors
        if usage is None:
            parsed_rows.append(
                ParsedRow(
                    row_number=idx,
                    raw=raw,
                    parsed=rec,
                    error='Missing usage/consumption value',
                )
            )
            continue

        parsed_rows.append(ParsedRow(row_number=idx, raw=raw, parsed=rec, error=None))

    return parsed_rows
