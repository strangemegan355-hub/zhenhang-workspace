from uuid import UUID

from pydantic import BaseModel, Field


class OptionItemCreate(BaseModel):
    name: str = Field(max_length=120)
    price_adjustment: float = Field(default=0)
    sort_order: int = Field(default=0)


class OptionItemUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    price_adjustment: float | None = None
    sort_order: int | None = None


class OptionItemRead(BaseModel):
    id: UUID
    option_group_id: UUID
    name: str
    price_adjustment: float
    sort_order: int

    model_config = {"from_attributes": True}


class OptionGroupCreate(BaseModel):
    name: str = Field(max_length=120)
    sort_order: int = Field(default=0)


class OptionGroupUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    sort_order: int | None = None


class OptionGroupRead(BaseModel):
    id: UUID
    machine_id: UUID
    name: str
    sort_order: int
    items: list[OptionItemRead] = []

    model_config = {"from_attributes": True}


class MachineOptionsRead(BaseModel):
    """Flat view for quote option selection panel."""
    groups: list[OptionGroupRead]


class QuoteItemOptionsUpdate(BaseModel):
    option_item_ids: list[UUID] = Field(default_factory=list)
