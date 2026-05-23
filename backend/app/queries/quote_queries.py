from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class ListQuotesQuery:
    page: int = 1
    page_size: int = 20
    q: str | None = None


@dataclass(slots=True)
class CompareQuoteVersionsQuery:
    quote_id: UUID
    from_version_no: int
    to_version_no: int
