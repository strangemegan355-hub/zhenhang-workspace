from __future__ import annotations

import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.domains.config.repositories import config_repository as repo
from app.models.user import User
from app.schemas.business_settings import BusinessSettingsRead, BusinessSettingsUpdate

CONFIG_KEY = "business.settings"
CONFIG_GROUP = "business"


def default_business_settings() -> dict:
    return {
        "company_name": settings.company_name,
        "company_phone": "",
        "company_address": "",
        "company_email": "",
        "company_remark": "",
        "export_footer": settings.company_export_footer,
        "default_currency": "CNY",
        "default_scrap_rate": 0,
        "default_overhead_rate": 0,
        "default_profit_rate": 20,
        "default_tax_rate": 13,
        "accounting_enabled": False,
        "quote_receivable_enabled": False,
        "procurement_approval_enabled": False,
        "sales_max_discount_rate_pct": 0,
    }


def _merge_settings(raw: dict | None) -> BusinessSettingsRead:
    merged = default_business_settings()
    if raw:
        merged.update({k: v for k, v in raw.items() if v is not None})
    return BusinessSettingsRead.model_validate(merged)


async def get_business_settings(db: AsyncSession) -> BusinessSettingsRead:
    obj = await repo.get_config_by_key(db, CONFIG_KEY)
    if obj is None:
        return _merge_settings(None)
    try:
        stored = json.loads(obj.value)
    except json.JSONDecodeError:
        stored = {}
    if not isinstance(stored, dict):
        stored = {}
    return _merge_settings(stored)


async def get_business_settings_dict(db: AsyncSession) -> dict:
    return (await get_business_settings(db)).model_dump()


async def update_business_settings(
    db: AsyncSession,
    payload: BusinessSettingsUpdate,
    current_user: User,
) -> BusinessSettingsRead:
    current = (await get_business_settings(db)).model_dump()
    updates = payload.model_dump(exclude_unset=True)
    current.update(updates)

    value = json.dumps(current, ensure_ascii=False)
    obj = await repo.get_config_by_key(db, CONFIG_KEY)
    if obj is None:
        await repo.create_config(
            db,
            {
                "key": CONFIG_KEY,
                "value": value,
                "value_type": "json",
                "group": CONFIG_GROUP,
                "description": "业务设置：公司资料与默认报价参数",
                "is_public": False,
                "created_by": current_user.id,
            },
            autocommit=True,
        )
    else:
        await repo.update_config(db, obj, {"value": value, "value_type": "json"}, autocommit=True)

    return BusinessSettingsRead.model_validate(current)
