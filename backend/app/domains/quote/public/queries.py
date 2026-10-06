"""Reads the quote domain publishes for callers outside it.

`app/services/*` used to import `app.domains.quote.repositories` directly, which made the repository
part of their contract: any refactor inside the domain would have broken them, and the layer gate could
not distinguish an intended use from an accident. These re-exports are the contract instead — the
repository and the policies stay private, and renaming something inside them is a change to this file
alone.
"""

from app.domains.quote.policies.data_scope_policy import owner_scope_user_id
from app.domains.quote.repositories.quote_repository import (
    get_bom,
    get_current_quote_version,
    get_quote,
    get_quote_item,
    get_quote_version_by_no,
    list_bom_items,
    list_quote_items_by_version,
    list_quotes,
    max_quote_version_no,
)

__all__ = [
    "get_bom",
    "get_current_quote_version",
    "get_quote",
    "get_quote_item",
    "get_quote_version_by_no",
    "list_bom_items",
    "list_quote_items_by_version",
    "list_quotes",
    "max_quote_version_no",
    "owner_scope_user_id",
]
