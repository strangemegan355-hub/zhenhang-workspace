from dataclasses import dataclass, field
from uuid import UUID

from app.schemas.quote import QuoteItemCreate


@dataclass(slots=True)
class CreateQuoteCommand:
    title: str
    customer_id: UUID
    machine_id: UUID
    bom_id: UUID | None = None
    approval_template_id: UUID | None = None
    currency: str = "CNY"
    remark: str | None = None


@dataclass(slots=True)
class CreateQuoteVersionCommand:
    quote_id: UUID
    items: list[QuoteItemCreate] = field(default_factory=list)


@dataclass(slots=True)
class TransitionQuoteCommand:
    quote_id: UUID
    action_code: str
    comment: str | None = None
