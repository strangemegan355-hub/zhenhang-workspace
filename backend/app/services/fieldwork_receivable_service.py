from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import accounting_repository as accounting_repo
from app.repositories import fieldwork_repository as fieldwork_repo
from app.schemas.accounting import AccountingEntryRead
from app.services.accounting_service import require_accounting_enabled


async def post_receivable_from_repair(
    db: AsyncSession,
    record_id: UUID,
    current_user: User,
) -> AccountingEntryRead:
    await require_accounting_enabled(db)
    record = await fieldwork_repo.get_record(db, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="现场作业记录不存在")
    if record.record_type != "repair":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅外出维修记录可生成应收")
    if not record.customer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="维修记录缺少客户")
    if record.receivable_entry_id is not None:
        existing = await accounting_repo.get_entry(db, record.receivable_entry_id)
        if existing is not None and existing.status != "void":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该维修记录已生成应收")

    dup = await accounting_repo.get_entry_by_source(db, "fieldwork_repair", record_id)
    if dup is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该维修记录已有有效应收账目")

    amount = Decimal(str(record.repair_amount or 0))
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先填写维修费用（repair_amount）")

    await accounting_repo.register_ledger_account(db, record.customer_id, current_user.id)

    occurred_on = record.occurred_on or date.today()
    booked_on = date.today()
    is_backfill = occurred_on < booked_on

    entry = await accounting_repo.add_entry(
        db,
        {
            "entry_no": await accounting_repo.generate_entry_no(db, "receivable"),
            "entry_kind": "receivable",
            "status": "confirmed",
            "party_type": "customer",
            "customer_id": record.customer_id,
            "supplier_id": None,
            "project_id": record.project_id,
            "quote_id": None,
            "amount": amount,
            "settled_amount": Decimal("0"),
            "currency": "CNY",
            "occurred_on": occurred_on,
            "booked_on": booked_on,
            "is_backfill": is_backfill,
            "source_type": "fieldwork_repair",
            "source_id": record.id,
            "source_no": record.record_no,
            "approval_status": "none",
            "title": f"外出维修应收 · {record.record_no}",
            "remark": record.remark or record.detail,
            "created_by": current_user.id,
        },
    )

    record.receivable_entry_id = entry.id
    await db.flush()
    await db.commit()
    await db.refresh(entry)

    loaded = await accounting_repo.get_entry(db, entry.id)
    return AccountingEntryRead.model_validate(loaded or entry)
