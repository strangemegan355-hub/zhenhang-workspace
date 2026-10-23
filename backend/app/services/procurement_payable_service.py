from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.notifications.notification_service import create_notification
from app.repositories import accounting_repository as accounting_repo
from app.repositories import procurement_payable_repository as ppr_repo
from app.repositories import procurement_repository as procurement_repo
from app.schemas.accounting import ProcurementPayableRequestRead
from app.schemas.common import PageResponse
from app.services.accounting_service import require_accounting_enabled


async def _require_procurement_payable_enabled(db: AsyncSession) -> None:
    flags = await require_accounting_enabled(db)
    if not flags.procurement_approval_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="采购应付审批未开启，请在业务设置中启用 procurement_approval_enabled",
        )


def _plan_amount(entry) -> Decimal:
    return (Decimal(str(entry.qty)) * Decimal(str(entry.unit_price))).quantize(Decimal("0.01"))


async def _notify_bosses(db: AsyncSession, *, title: str, content: str, biz_id: UUID, created_by: UUID | None) -> None:
    perm_stmt = (
        select(User.id)
        .join(User.roles)
        .join(Role.permissions)
        .where(
            User.is_active.is_(True),
            Permission.code == "business:accounting:approve_procurement_payable",
        )
        .distinct()
    )
    super_stmt = select(User.id).where(User.is_active.is_(True), User.is_superuser.is_(True))
    boss_ids = set((await db.execute(perm_stmt)).scalars().all())
    boss_ids.update((await db.execute(super_stmt)).scalars().all())
    for boss_id in boss_ids:
        await create_notification(
            db,
            title=title,
            content=content,
            biz_type="procurement_payable_request",
            biz_id=biz_id,
            receiver_id=boss_id,
            payload={"procurement_entry_id": str(biz_id)},
            created_by=created_by,
            autocommit=False,
        )


async def create_request_from_entry(
    db: AsyncSession,
    entry_id: UUID,
    current_user: User,
) -> ProcurementPayableRequestRead:
    await _require_procurement_payable_enabled(db)
    entry = await procurement_repo.get_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="采购记录不存在")
    if entry.payable_status == "posted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该采购已生成应付")
    if entry.status == "planned":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先将采购推进至「已下单」再提交应付")

    existing_entry = await accounting_repo.get_entry_by_source(db, "procurement", entry_id)
    if existing_entry is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该采购已有有效应付账目")

    active = await ppr_repo.get_active_request_by_entry(db, entry_id)
    if active is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该采购已有进行中的应付申请")

    amount = _plan_amount(entry)
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="采购计划金额无效")

    obj = await ppr_repo.create_request(
        db,
        {
            "procurement_entry_id": entry_id,
            "requested_by": current_user.id,
            "requested_amount": amount,
            "approval_status": "pending",
            "created_by": current_user.id,
        },
    )
    entry.payable_status = "pending"
    await db.flush()
    await _notify_bosses(
        db,
        title=f"采购应付待审批 · {entry.request_no}",
        content=f"计划金额 {amount} 元，请审批",
        biz_id=entry_id,
        created_by=current_user.id,
    )
    await ppr_repo.commit_session(db)
    loaded = await ppr_repo.get_request(db, obj.id)
    return ProcurementPayableRequestRead.model_validate(loaded or obj)


async def get_request_for_entry(db: AsyncSession, entry_id: UUID) -> ProcurementPayableRequestRead | None:
    _total, rows = await ppr_repo.list_requests(db, page=1, page_size=1, entry_id=entry_id)
    if not rows:
        return None
    return ProcurementPayableRequestRead.model_validate(rows[0])


async def list_requests(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    approval_status: str | None = None,
    entry_id: UUID | None = None,
) -> PageResponse:
    await require_accounting_enabled(db)
    total, items = await ppr_repo.list_requests(
        db, page=page, page_size=page_size, approval_status=approval_status, entry_id=entry_id
    )
    return PageResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ProcurementPayableRequestRead.model_validate(i) for i in items],
    )


async def _create_payable_entry(db: AsyncSession, entry, amount: Decimal, current_user: User):
    occurred_on = entry.need_date or date.today()
    booked_on = date.today()
    material_name = entry.material.name if entry.material else "材料"
    return await accounting_repo.add_entry(
        db,
        {
            "entry_no": await accounting_repo.generate_entry_no(db, "payable"),
            "entry_kind": "payable",
            "status": "confirmed",
            "party_type": "supplier",
            "customer_id": None,
            "supplier_id": entry.supplier_id,
            "project_id": entry.project_id,
            "quote_id": None,
            "amount": amount,
            "settled_amount": Decimal("0"),
            "currency": "CNY",
            "occurred_on": occurred_on,
            "booked_on": booked_on,
            "is_backfill": occurred_on < booked_on,
            "source_type": "procurement",
            "source_id": entry.id,
            "source_no": entry.request_no,
            "approval_status": "approved",
            "title": f"采购应付 · {entry.request_no} · {material_name}",
            "remark": entry.remark,
            "created_by": current_user.id,
        },
    )


async def approve_request(db: AsyncSession, request_id: UUID, current_user: User) -> ProcurementPayableRequestRead:
    await _require_procurement_payable_enabled(db)
    obj = await ppr_repo.get_request(db, request_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="应付申请不存在")
    if obj.approval_status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅待审批申请可通过")
    if obj.payable_entry_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="应付已生成")

    entry = obj.procurement_entry or await procurement_repo.get_entry(db, obj.procurement_entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="采购记录不存在")

    amount = Decimal(str(obj.requested_amount))
    payable = await _create_payable_entry(db, entry, amount, current_user)

    obj.approval_status = "approved"
    obj.approved_by = current_user.id
    obj.approved_at = datetime.now(UTC)
    obj.payable_entry_id = payable.id
    entry.payable_status = "posted"
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    loaded = await ppr_repo.get_request(db, request_id)
    return ProcurementPayableRequestRead.model_validate(loaded or obj)


async def reject_request(
    db: AsyncSession,
    request_id: UUID,
    current_user: User,
    *,
    reason: str | None,
) -> ProcurementPayableRequestRead:
    await _require_procurement_payable_enabled(db)
    obj = await ppr_repo.get_request(db, request_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="应付申请不存在")
    if obj.approval_status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅待审批申请可驳回")
    obj.approval_status = "rejected"
    obj.approved_by = current_user.id
    obj.approved_at = datetime.now(UTC)
    obj.reject_reason = reason.strip() if reason else None
    entry = obj.procurement_entry
    if entry is not None:
        entry.payable_status = "none"
    await ppr_repo.save_request(db, obj)
    loaded = await ppr_repo.get_request(db, request_id)
    return ProcurementPayableRequestRead.model_validate(loaded or obj)
