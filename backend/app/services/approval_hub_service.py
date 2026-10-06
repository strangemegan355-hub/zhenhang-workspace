from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import collect_permission_codes
from app.domains.quote.application import quote_application_service as quote_svc
from app.domains.quote.public import queries as quote_repo
from app.models.user import User
from app.repositories import procurement_payable_repository as ppr_repo
from app.repositories import quote_receivable_repository as qrr_repo
from app.schemas.approval_hub import ApprovalInboxResponse, ApprovalTaskRead
from app.services import procurement_payable_service as ppr_svc
from app.services import quote_receivable_service as qrr_svc


def _has_perm(user: User, code: str) -> bool:
    if user.is_superuser:
        return True
    perms = collect_permission_codes(user)
    return code in perms or "*:*:*" in perms


async def list_inbox(db: AsyncSession, current_user: User) -> ApprovalInboxResponse:
    items: list[ApprovalTaskRead] = []

    if _has_perm(current_user, "business:accounting:approve_quote_receivable"):
        _total, pending = await qrr_repo.list_requests(
            db, page=1, page_size=100, approval_status="pending"
        )
        for req in pending:
            quote = req.quote
            requester = req.requester
            items.append(
                ApprovalTaskRead(
                    id=str(req.id),
                    task_type="quote_receivable",
                    title=f"应收优惠 · {quote.quote_no if quote else req.quote_id}",
                    subtitle=quote.title if quote else None,
                    amount=req.requested_amount,
                    discount_amount=req.discount_amount,
                    discount_rate_pct=req.discount_rate_pct,
                    submitter_name=getattr(requester, "full_name", None) or getattr(requester, "username", None),
                    submitted_at=req.created_at,
                    status="pending",
                    source_id=req.quote_id,
                    source_no=quote.quote_no if quote else None,
                    detail_href=f"/quotes/customer",
                    can_approve=True,
                )
            )

    if _has_perm(current_user, "business:accounting:approve_procurement_payable"):
        _total, pending_payables = await ppr_repo.list_requests(
            db, page=1, page_size=100, approval_status="pending"
        )
        for req in pending_payables:
            entry = req.procurement_entry
            requester = req.requester
            items.append(
                ApprovalTaskRead(
                    id=str(req.id),
                    task_type="procurement_payable",
                    title=f"采购应付 · {entry.request_no if entry else req.procurement_entry_id}",
                    subtitle=entry.material.name if entry and entry.material else None,
                    amount=req.requested_amount,
                    submitter_name=getattr(requester, "full_name", None) or getattr(requester, "username", None),
                    submitted_at=req.created_at,
                    status="pending",
                    source_id=req.procurement_entry_id,
                    source_no=entry.request_no if entry else None,
                    detail_href="/procurement",
                    can_approve=True,
                )
            )

    if _has_perm(current_user, "business:quote:approve"):
        _total, quotes = await quote_repo.list_quotes(
            db, page=1, page_size=100, q=None, created_by=None, quote_kind=None
        )
        for quote in quotes:
            if quote.workflow_state != "reviewing":
                continue
            creator = quote.creator
            items.append(
                ApprovalTaskRead(
                    id=str(quote.id),
                    task_type="quote_workflow",
                    title=f"报价审批 · {quote.quote_no}",
                    subtitle=quote.title,
                    amount=quote.total_amount,
                    submitter_name=getattr(creator, "full_name", None) or getattr(creator, "username", None),
                    submitted_at=quote.updated_at,
                    status="reviewing",
                    source_id=quote.id,
                    source_no=quote.quote_no,
                    detail_href=f"/quotes/{quote.id}" if quote.quote_kind != "customer" else "/quotes/customer",
                    can_approve=True,
                )
            )

    items.sort(key=lambda x: x.submitted_at, reverse=True)
    return ApprovalInboxResponse(total=len(items), items=items)


async def execute_action(
    db: AsyncSession,
    *,
    task_type: str,
    task_id: UUID,
    action: str,
    comment: str | None,
    current_user: User,
) -> dict:
    if task_type == "quote_receivable":
        if not _has_perm(current_user, "business:accounting:approve_quote_receivable"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无应收优惠审批权限")
        if action == "approve":
            result = await qrr_svc.approve_request(db, task_id, current_user)
            return {"task_type": task_type, "action": action, "result": result.model_dump()}
        result = await qrr_svc.reject_request(db, task_id, current_user, reason=comment)
        return {"task_type": task_type, "action": action, "result": result.model_dump()}

    if task_type == "procurement_payable":
        if not _has_perm(current_user, "business:accounting:approve_procurement_payable"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无采购应付审批权限")
        if action == "approve":
            result = await ppr_svc.approve_request(db, task_id, current_user)
            return {"task_type": task_type, "action": action, "result": result.model_dump()}
        result = await ppr_svc.reject_request(db, task_id, current_user, reason=comment)
        return {"task_type": task_type, "action": action, "result": result.model_dump()}

    if task_type == "quote_workflow":
        if not _has_perm(current_user, "business:quote:approve"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无报价审批权限")
        code = "approve" if action == "approve" else "reject"
        quote = await quote_svc.transition_quote_state(db, task_id, code, comment, current_user)
        return {"task_type": task_type, "action": action, "result": quote.model_dump() if hasattr(quote, "model_dump") else quote}

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported task_type: {task_type}")
