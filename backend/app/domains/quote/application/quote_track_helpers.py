"""Product vs machine dual-track helpers for quotes (K-005 / UX-001).

Preferred path: standard sellable **Product** (+ optional price/cost templates).
``machine_id`` / ``bom_id`` remain for legacy and advanced BOM quotes; fields are never deleted.

When ``product_id`` is set, missing ``machine_id`` / ``bom_id`` are filled from the product's
linked machine and default BOM when present. Machine-only quotes stay valid for historical data.
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

QuoteTrack = Literal["product", "product_with_machine_link", "machine_legacy", "none"]

PREFERRED_QUOTE_TRACK: QuoteTrack = "product"


def classify_quote_track(
    product_id: UUID | None,
    machine_id: UUID | None,
) -> QuoteTrack:
    if product_id and machine_id:
        return "product_with_machine_link"
    if product_id:
        return "product"
    if machine_id:
        return "machine_legacy"
    return "none"


async def apply_product_machine_defaults(db: AsyncSession, quote_payload: dict[str, Any]) -> dict[str, Any]:
    """Mutate and return ``quote_payload`` with product-derived machine/BOM defaults.

    Does not overwrite an explicitly supplied ``machine_id`` or ``bom_id``.
    Does not remove either field when only machine is supplied (legacy path).
    """
    product_id = quote_payload.get("product_id")
    if not product_id:
        return quote_payload

    from app.services.product_service import get_product_or_none

    product = await get_product_or_none(db, product_id)
    if product is None:
        return quote_payload

    if product.machine_id and not quote_payload.get("machine_id"):
        quote_payload["machine_id"] = product.machine_id
    if product.default_bom_id and not quote_payload.get("bom_id"):
        quote_payload["bom_id"] = product.default_bom_id
    return quote_payload


def strip_client_quote_totals(payload: dict[str, Any]) -> dict[str, Any]:
    """Server owns header totals; drop any client-supplied amount fields before create."""
    for key in ("total_amount", "total_cost", "profit_amount", "profit_rate"):
        payload.pop(key, None)
    return payload
