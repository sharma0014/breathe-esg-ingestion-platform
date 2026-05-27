from decimal import Decimal
from typing import Any

from .utils import ParsedRow, _to_decimal, normalize_unit, parse_date, read_csv_bytes, suspicious_reasons_for


TYPE_KEYS = ['Type', 'Product', 'Category']
TRAVELER_KEYS = ['Traveler', 'Employee', 'Traveler Name']
BOOK_DATE_KEYS = ['Booking Date', 'Booked Date', 'Transaction Date']
START_DATE_KEYS = ['Start Date', 'Trip Start', 'Departure Date', 'Check-in Date']
ORIGIN_KEYS = ['Origin', 'From', 'From Airport']
DEST_KEYS = ['Destination', 'To', 'To Airport']
DIST_KEYS = ['Distance', 'Distance (mi)', 'Distance (km)']
DIST_UNIT_KEYS = ['Distance Unit', 'Distance UOM']
NIGHTS_KEYS = ['Nights', 'Room Nights']
AMOUNT_KEYS = ['Amount', 'Total', 'Transaction Amount']
CCY_KEYS = ['Currency', 'CCY']


def _first_value(row: dict[str, str], keys: list[str]) -> str:
    for k in keys:
        if k in row and row[k] != '':
            return row[k]
    return ''


def parse_travel_export(data: bytes, *, source_config: dict[str, Any] | None = None):
    """Parses a corporate travel platform CSV export.

    This is intentionally platform-agnostic but modeled after typical Concur/Navan-style exports:
    - A row describes one travel product: flight/hotel/ground
    - Origin/destination may be airport codes; distance may be absent
    """

    rows = read_csv_bytes(data)
    parsed_rows: list[ParsedRow] = []

    for idx, r in enumerate(rows, start=2):
        raw = dict(r)

        t = _first_value(r, TYPE_KEYS).strip().upper()
        traveler = _first_value(r, TRAVELER_KEYS)

        booking_date = parse_date(_first_value(r, BOOK_DATE_KEYS))
        start_date = parse_date(_first_value(r, START_DATE_KEYS))
        origin = _first_value(r, ORIGIN_KEYS).strip().upper()
        dest = _first_value(r, DEST_KEYS).strip().upper()

        dist_str = _first_value(r, DIST_KEYS)
        dist_unit = _first_value(r, DIST_UNIT_KEYS)
        if 'Distance (mi)' in r and r.get('Distance (mi)') and not dist_unit:
            dist_unit = 'mi'
        if 'Distance (km)' in r and r.get('Distance (km)') and not dist_unit:
            dist_unit = 'km'

        dist = _to_decimal(dist_str)
        if dist is not None:
            dist_km, _ = normalize_unit(dist, dist_unit or 'km')
        else:
            dist_km = None

        nights = _to_decimal(_first_value(r, NIGHTS_KEYS))
        amount = _to_decimal(_first_value(r, AMOUNT_KEYS))
        ccy = _first_value(r, CCY_KEYS)

        if t in {'FLIGHT', 'AIR', 'AIRFARE'}:
            category = 'TRAVEL_FLIGHT'
            scope = 'SCOPE_3'
        elif t in {'HOTEL', 'LODGING'}:
            category = 'TRAVEL_HOTEL'
            scope = 'SCOPE_3'
        elif t in {'CAR', 'GROUND', 'RAIL', 'TAXI'}:
            category = 'TRAVEL_GROUND'
            scope = 'SCOPE_3'
        else:
            parsed_rows.append(
                ParsedRow(
                    row_number=idx,
                    raw=raw,
                    parsed={'type': t, 'traveler': traveler},
                    error='Unknown travel product type; expected FLIGHT/HOTEL/CAR/RAIL/etc.',
                )
            )
            continue

        rec: dict[str, Any] = {
            'category': category,
            'scope': scope,
            'source_row_ref': f"row-{idx}",
            'activity_date': start_date or booking_date,
            'description': f"{t.title()} for {traveler}".strip(),
            'traveler': traveler,
            'origin': origin,
            'destination': dest,
            'distance_km': dist_km,
        }

        if category == 'TRAVEL_HOTEL':
            # nights as quantity
            q = nights
            rec['quantity'] = q
            rec['unit'] = 'nights'
            rec['normalized_quantity'] = q
            rec['normalized_unit'] = 'nights'

        if amount is not None:
            rec['spend_amount'] = amount
            rec['spend_currency'] = ccy

        reasons = suspicious_reasons_for(rec)
        rec['suspicious'] = len(reasons) > 0
        rec['suspicious_reasons'] = reasons

        parsed_rows.append(ParsedRow(row_number=idx, raw=raw, parsed=rec, error=None))

    return parsed_rows
