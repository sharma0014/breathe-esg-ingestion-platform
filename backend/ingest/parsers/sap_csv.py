from decimal import Decimal
from typing import Any

from .utils import ParsedRow, _to_decimal, normalize_unit, parse_date, read_csv_bytes, suspicious_reasons_for


SAP_DATE_KEYS = ['Posting Date', 'Document Date', 'Belegdatum', 'Buchungsdatum']
SAP_PLANT_KEYS = ['Plant', 'Werk', 'Werks']
SAP_QTY_KEYS = ['Quantity', 'Menge']
SAP_UNIT_KEYS = ['Unit', 'ME', 'BME', 'Base Unit of Measure']
SAP_MAT_KEYS = ['Material Description', 'Materialkurztext', 'Short Text', 'Kurztext']
SAP_VENDOR_KEYS = ['Vendor Name', 'Vendor', 'Lieferant', 'Supplier']
SAP_AMOUNT_KEYS = ['Amount', 'Amount in doc. curr.', 'Betrag in Belegwährung', 'Net value', 'Net Value']
SAP_CCY_KEYS = ['Currency', 'Währung', 'Curr.']
SAP_DOC_KEYS = ['Material Doc.', 'Material Document', 'Materialbeleg', 'Document Number', 'Belegnummer']


def _first_value(row: dict[str, str], keys: list[str]) -> str:
    for k in keys:
        if k in row and row[k] != '':
            return row[k]
    return ''


def parse_sap_export(data: bytes, *, source_config: dict[str, Any] | None = None):
    """Parses a *flat file* CSV export from SAP GUI list/download.

    This prototype supports a pragmatic subset:
    - Fuel issues / movements with qty+unit (normalized to liters)
    - Procurement invoice/PO history lines with spend+currency

    It tolerates:
    - German headers
    - decimal comma
    - ';' delimiter (common in DE locales)
    """

    cfg = source_config or {}
    plant_map: dict[str, str] = cfg.get('plant_code_to_facility', {})

    rows = read_csv_bytes(data)
    parsed_rows: list[ParsedRow] = []

    for idx, r in enumerate(rows, start=2):
        raw = dict(r)
        parsed: dict[str, Any] = {}

        date_str = _first_value(r, SAP_DATE_KEYS)
        plant = _first_value(r, SAP_PLANT_KEYS)
        qty_str = _first_value(r, SAP_QTY_KEYS)
        unit_str = _first_value(r, SAP_UNIT_KEYS)
        mat_desc = _first_value(r, SAP_MAT_KEYS)
        vendor = _first_value(r, SAP_VENDOR_KEYS)
        amount_str = _first_value(r, SAP_AMOUNT_KEYS)
        ccy = _first_value(r, SAP_CCY_KEYS)
        doc = _first_value(r, SAP_DOC_KEYS)

        parsed['plant_code'] = plant
        parsed['doc'] = doc
        parsed['date'] = date_str
        parsed['material_or_text'] = mat_desc
        parsed['vendor'] = vendor
        parsed['qty'] = qty_str
        parsed['unit'] = unit_str
        parsed['amount'] = amount_str
        parsed['currency'] = ccy

        activity_date = parse_date(date_str)
        qty = _to_decimal(qty_str)
        amount = _to_decimal(amount_str)

        if qty is not None and unit_str:
            normalized_qty, normalized_unit = normalize_unit(qty, unit_str)
            rec = {
                'category': 'FUEL',
                'scope': 'SCOPE_1',
                'source_row_ref': doc or f"row-{idx}",
                'activity_date': activity_date,
                'description': mat_desc or 'SAP fuel line',
                'quantity': qty,
                'unit': unit_str,
                'normalized_quantity': normalized_qty,
                'normalized_unit': normalized_unit,
                'supplier': vendor,
            }
        elif amount is not None and ccy:
            rec = {
                'category': 'PROCUREMENT',
                'scope': 'SCOPE_3',
                'source_row_ref': doc or f"row-{idx}",
                'activity_date': activity_date,
                'description': mat_desc or 'SAP procurement line',
                'supplier': vendor,
                'spend_amount': amount,
                'spend_currency': ccy,
            }
        else:
            parsed_rows.append(
                ParsedRow(
                    row_number=idx,
                    raw=raw,
                    parsed=parsed,
                    error='Could not classify row as fuel (qty+unit) or procurement (amount+currency).',
                )
            )
            continue

        if plant:
            facility_name = plant_map.get(plant)
            if facility_name:
                rec['facility_name'] = facility_name

        reasons = suspicious_reasons_for(rec)
        rec['suspicious'] = len(reasons) > 0
        rec['suspicious_reasons'] = reasons

        parsed_rows.append(ParsedRow(row_number=idx, raw=raw, parsed={**parsed, **rec}, error=None))

    return parsed_rows
