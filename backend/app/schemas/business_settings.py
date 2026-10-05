from pydantic import BaseModel, Field


class BusinessSettingsBase(BaseModel):
    company_name: str = Field(min_length=1, max_length=120)
    company_phone: str | None = Field(default=None, max_length=32)
    company_address: str | None = Field(default=None, max_length=255)
    company_email: str | None = Field(default=None, max_length=255)
    company_remark: str | None = Field(default=None, max_length=500)
    export_footer: str | None = Field(default=None, max_length=500)
    default_currency: str = Field(default="CNY", max_length=8)
    default_scrap_rate: float = Field(default=0, ge=0, le=100)
    default_overhead_rate: float = Field(default=0, ge=0, le=100)
    default_profit_rate: float = Field(default=20, ge=0, le=100)
    default_tax_rate: float = Field(default=13, ge=0, le=100)
    accounting_enabled: bool = Field(default=False)
    quote_receivable_enabled: bool = Field(default=False)
    procurement_approval_enabled: bool = Field(default=False)
    sales_max_discount_rate_pct: float = Field(default=0, ge=0, le=100)


class BusinessSettingsRead(BusinessSettingsBase):
    pass


class BusinessSettingsUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=120)
    company_phone: str | None = Field(default=None, max_length=32)
    company_address: str | None = Field(default=None, max_length=255)
    company_email: str | None = Field(default=None, max_length=255)
    company_remark: str | None = Field(default=None, max_length=500)
    export_footer: str | None = Field(default=None, max_length=500)
    default_currency: str | None = Field(default=None, max_length=8)
    default_scrap_rate: float | None = Field(default=None, ge=0, le=100)
    default_overhead_rate: float | None = Field(default=None, ge=0, le=100)
    default_profit_rate: float | None = Field(default=None, ge=0, le=100)
    default_tax_rate: float | None = Field(default=None, ge=0, le=100)
    accounting_enabled: bool | None = None
    quote_receivable_enabled: bool | None = None
    procurement_approval_enabled: bool | None = None
    sales_max_discount_rate_pct: float | None = Field(default=None, ge=0, le=100)
