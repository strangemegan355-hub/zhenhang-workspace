from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ProductCategoryBase(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    parent_id: UUID | None = None
    status: str = Field(default="active", max_length=32)
    remark: str | None = None


class ProductCategoryCreate(ProductCategoryBase):
    pass


class ProductCategoryUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    parent_id: UUID | None = None
    status: str | None = Field(default=None, max_length=32)
    remark: str | None = None


class ProductCategoryRead(ProductCategoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


# --- Product ---


class ProductBase(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    category_id: UUID | None = None
    spec: str | None = Field(default=None, max_length=200)
    power: str | None = Field(default=None, max_length=64)
    unit: str = Field(default="EA", max_length=32)
    status: str = Field(default="active", max_length=32)
    reference_cost: Decimal = Field(default=Decimal("0"), ge=0)
    reference_price: Decimal = Field(default=Decimal("0"), ge=0)
    machine_id: UUID | None = None
    default_bom_id: UUID | None = None
    default_cost_template_id: UUID | None = None
    default_price_template_id: UUID | None = None
    remark: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    category_id: UUID | None = None
    spec: str | None = Field(default=None, max_length=200)
    power: str | None = Field(default=None, max_length=64)
    unit: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, max_length=32)
    reference_cost: Decimal | None = Field(default=None, ge=0)
    reference_price: Decimal | None = Field(default=None, ge=0)
    machine_id: UUID | None = None
    default_bom_id: UUID | None = None
    default_cost_template_id: UUID | None = None
    default_price_template_id: UUID | None = None
    remark: str | None = None


class ProductRead(ProductBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool

    model_config = {"from_attributes": True}


# --- Cost Template ---


class ProductCostTemplateLineBase(BaseModel):
    line_type: str = Field(default="material", max_length=32)
    item_code: str = Field(min_length=1, max_length=64)
    item_name: str = Field(min_length=1, max_length=200)
    unit: str = Field(default="EA", max_length=32)
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    sort_order: int = 0


class ProductCostTemplateLineRead(ProductCostTemplateLineBase):
    id: UUID
    template_id: UUID

    model_config = {"from_attributes": True}


class ProductCostTemplateBase(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    product_id: UUID | None = None
    scrap_rate: Decimal = Field(default=Decimal("0"), ge=0)
    overhead_rate: Decimal = Field(default=Decimal("0"), ge=0)
    status: str = Field(default="active", max_length=32)
    remark: str | None = None


class ProductCostTemplateCreate(ProductCostTemplateBase):
    lines: list[ProductCostTemplateLineBase] = Field(default_factory=list)


class ProductCostTemplateUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    product_id: UUID | None = None
    scrap_rate: Decimal | None = Field(default=None, ge=0)
    overhead_rate: Decimal | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, max_length=32)
    remark: str | None = None
    lines: list[ProductCostTemplateLineBase] | None = None


class ProductCostTemplateRead(ProductCostTemplateBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool
    lines: list[ProductCostTemplateLineRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# --- Price Template ---


class ProductPriceTemplateLineBase(BaseModel):
    item_code: str = Field(min_length=1, max_length=64)
    item_name: str = Field(min_length=1, max_length=200)
    unit: str = Field(default="EA", max_length=32)
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    unit_price: Decimal = Field(default=Decimal("0"), ge=0)
    sort_order: int = 0


class ProductPriceTemplateLineRead(ProductPriceTemplateLineBase):
    id: UUID
    template_id: UUID

    model_config = {"from_attributes": True}


class ProductPriceTemplateBase(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    product_id: UUID | None = None
    cost_template_id: UUID | None = None
    margin_rate: Decimal = Field(default=Decimal("0.2"), ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0)
    discount_rate: Decimal = Field(default=Decimal("0"), ge=0)
    status: str = Field(default="active", max_length=32)
    remark: str | None = None


class ProductPriceTemplateCreate(ProductPriceTemplateBase):
    lines: list[ProductPriceTemplateLineBase] = Field(default_factory=list)


class ProductPriceTemplateUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    product_id: UUID | None = None
    cost_template_id: UUID | None = None
    margin_rate: Decimal | None = Field(default=None, ge=0)
    tax_rate: Decimal | None = Field(default=None, ge=0)
    discount_rate: Decimal | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, max_length=32)
    remark: str | None = None
    lines: list[ProductPriceTemplateLineBase] | None = None


class ProductPriceTemplateRead(ProductPriceTemplateBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None
    is_deleted: bool
    lines: list[ProductPriceTemplateLineRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# --- Quote payload ---


class ProductQuoteLinePayload(BaseModel):
    item_code: str
    item_name: str
    unit: str
    quantity: Decimal
    unit_cost: Decimal
    unit_price: Decimal
    source_type: str = "product"


class ProductQuotePayload(BaseModel):
    product_id: UUID
    product_code: str
    product_name: str
    spec: str | None = None
    cost_template_id: UUID | None = None
    price_template_id: UUID | None = None
    margin_rate: Decimal
    machine_id: UUID | None = None
    default_bom_id: UUID | None = None
    lines: list[ProductQuoteLinePayload] = Field(default_factory=list)
