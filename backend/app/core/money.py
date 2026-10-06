"""Decimal money rounding, in one place.

`_money` lived identically in `app/services/costing_service.py` and `app/services/project_profit_snapshot.py` until
round 129 — same signature, same body — and two money rounders that agree today are two that can disagree later.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

TWOPLACES = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
