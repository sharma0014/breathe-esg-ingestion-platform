import csv
import io
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from dateutil import parser as dateparser


@dataclass
class ParsedRow:
    row_number: int
    raw: dict[str, Any]
    parsed: dict[str, Any]
    error: str | None = None


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    s = str(value).strip()
    if not s:
        return None
    # handle decimal comma (common in EU exports)
    s = s.replace(' ', '')
    if ',' in s and '.' in s:
        # Decide based on which separator appears last.
        # EU style: 1.250,50  -> 1250.50
        # US style: 1,250.50  -> 1250.50
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
    elif s.count(',') == 1 and s.count('.') == 0:
        s = s.replace(',', '.')
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def parse_date(value: Any):
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        dt = dateparser.parse(s, dayfirst=True, yearfirst=False)
        if not dt:
            return None
        return dt.date()
    except Exception:
        return None


def read_csv_bytes(data: bytes) -> list[dict[str, str]]:
    """Best-effort CSV reader for 'realistic messy exports'.

    - Uses csv.Sniffer when possible
    - Supports UTF-8 with BOM
    """

    text = data.decode('utf-8-sig', errors='replace')
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[',', ';', '\t', '|'])
    except Exception:
        dialect = csv.get_dialect('excel')

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    rows: list[dict[str, str]] = []
    for r in reader:
        # normalize keys to stripped strings
        rows.append({(k or '').strip(): (v or '').strip() for k, v in r.items()})
    return rows


def normalize_unit(quantity: Decimal | None, unit: str | None):
    if quantity is None:
        return None, ''
    u = (unit or '').strip().lower()

    # Electricity
    if u in {'kwh', 'kw h', 'kilowatt-hour', 'kilowatt hour'}:
        return quantity, 'kWh'
    if u in {'mwh', 'mw h'}:
        return quantity * Decimal('1000'), 'kWh'

    # Fuel
    if u in {'l', 'lt', 'liter', 'litre', 'liters', 'litres'}:
        return quantity, 'L'
    if u in {'gal', 'gallon', 'gallons', 'us gal', 'us_gal'}:
        return quantity * Decimal('3.78541'), 'L'

    # Distance
    if u in {'km', 'kilometer', 'kilometre'}:
        return quantity, 'km'
    if u in {'mi', 'mile', 'miles'}:
        return quantity * Decimal('1.609344'), 'km'

    return None, ''


def suspicious_reasons_for(record: dict[str, Any]) -> list[str]:
    reasons: list[str] = []

    category = record.get('category')

    if category == 'ELECTRICITY':
        if not record.get('period_start') or not record.get('period_end'):
            reasons.append('missing_billing_period')
        if record.get('normalized_unit') != 'kWh' or record.get('normalized_quantity') is None:
            reasons.append('unrecognized_electricity_unit')
        q = record.get('normalized_quantity')
        if q is not None and q > Decimal('10000000'):
            reasons.append('very_large_consumption')

    if category in {'FUEL'}:
        if not record.get('activity_date'):
            reasons.append('missing_activity_date')
        if record.get('normalized_unit') != 'L' or record.get('normalized_quantity') is None:
            reasons.append('unrecognized_fuel_unit')

    if category == 'PROCUREMENT':
        if record.get('spend_amount') is None:
            reasons.append('missing_spend_amount')
        if not record.get('spend_currency'):
            reasons.append('missing_currency')

    if category in {'TRAVEL_FLIGHT', 'TRAVEL_GROUND'}:
        if record.get('distance_km') is None:
            reasons.append('missing_distance')

    if category == 'TRAVEL_HOTEL':
        if record.get('quantity') is None:
            reasons.append('missing_nights')

    # general
    if record.get('normalized_quantity') is not None and record.get('normalized_quantity') <= 0:
        reasons.append('non_positive_quantity')

    return reasons
