from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.domains.quote.application import quote_application_service as app_svc
from app.domains.quote.application import quote_option_service as opt_svc
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.option_group import QuoteItemOptionsUpdate
from app.schemas.quote import (
    ApprovalNodeRead,
    ApprovalTemplateDetailRead,
    ApprovalTemplateRead,
    ApprovalTemplateWithNodesCreate,
    QuoteActionPayload,
    QuoteApprovalRead,
    QuoteCreate,
    QuoteDetailRead,
    QuoteExportRequest,
    QuoteExportTaskRead,
    QuoteItemRead,
    QuoteRead,
    QuoteVersionCreate,
    QuoteVersionRead,
    QuoteWizardCreate,
    CustomerQuoteCreate,
    CustomerQuoteUpdate,
)
from app.schemas.quote import ApprovalTemplateRead
from app.schemas.quote import QuoteRead

router = APIRouter()


@router.post("", response_model=QuoteRead, status_code=status.HTTP_201_CREATED)
async def create_quote(
    payload: QuoteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:create"))],
) -> QuoteRead:
    return await app_svc.create_quote(db, payload.model_dump(), current)


@router.get("", response_model=PageResponse[QuoteRead])
async def list_quotes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
    quote_kind: str | None = Query(default=None, max_length=32),
) -> PageResponse:
    return await app_svc.list_quotes(db, page=page, page_size=page_size, q=q, current_user=current, quote_kind=quote_kind)


@router.post("/wizard", response_model=QuoteDetailRead, status_code=status.HTTP_201_CREATED)
async def create_quote_wizard(
    payload: QuoteWizardCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:create"))],
) -> QuoteDetailRead:
    data = await app_svc.create_quote_wizard(
        db,
        {
            **payload.model_dump(exclude={"initial_items"}),
            "initial_items": [i.model_dump() for i in payload.initial_items],
        },
        current,
    )
    return QuoteDetailRead.model_validate(data)


@router.post("/customer", response_model=QuoteDetailRead, status_code=status.HTTP_201_CREATED)
async def create_customer_quote(
    payload: CustomerQuoteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:create"))],
) -> QuoteDetailRead:
    data = await app_svc.create_customer_quote(db, payload.model_dump(), current)
    return QuoteDetailRead.model_validate(data)


@router.put("/{quote_id}/customer", response_model=QuoteDetailRead)
async def update_customer_quote(
    quote_id: UUID,
    payload: CustomerQuoteUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:update"))],
) -> QuoteDetailRead:
    data = await app_svc.update_customer_quote(db, quote_id, payload.model_dump(exclude_unset=True), current)
    return QuoteDetailRead.model_validate(data)


@router.delete("/{quote_id}/customer", response_model=QuoteRead)
async def delete_customer_quote(
    quote_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:update"))],
) -> QuoteRead:
    return await app_svc.delete_customer_quote(db, quote_id, current)


@router.post("/versions", response_model=QuoteVersionRead, status_code=status.HTTP_201_CREATED)
async def create_quote_version(
    payload: QuoteVersionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:update"))],
) -> QuoteVersionRead:
    return await app_svc.create_quote_version(db, payload.quote_id, [i.model_dump() for i in payload.items], current)


@router.post("/{quote_id}/actions/transition", response_model=QuoteRead)
async def transition_quote(
    quote_id: UUID,
    payload: QuoteActionPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:approve"))],
) -> QuoteRead:
    return await app_svc.transition_quote_state(db, quote_id, payload.action_code, payload.comment, current)


@router.post("/approval-templates", response_model=ApprovalTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_approval_template(
    payload: ApprovalTemplateWithNodesCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:approve"))],
) -> ApprovalTemplateRead:
    return await app_svc.create_approval_template(db, payload.model_dump(), current)


@router.get("/approval-templates", response_model=PageResponse[ApprovalTemplateRead])
async def list_approval_templates(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:quote:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await app_svc.list_approval_templates(db, page=page, page_size=page_size, q=q)


@router.get("/export-templates")
async def list_export_templates(
    _: Annotated[User, Depends(require_permissions("business:quote:read"))],
) -> list[dict]:
    return await app_svc.list_export_templates()


@router.get("/{quote_id}", response_model=QuoteDetailRead)
async def get_quote(
    quote_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:read"))],
) -> QuoteDetailRead:
    data = await app_svc.get_quote_detail(db, quote_id, current)
    return QuoteDetailRead.model_validate(data)


@router.get("/{quote_id}/versions", response_model=list[QuoteVersionRead])
async def list_quote_versions(
    quote_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:read"))],
) -> list[QuoteVersionRead]:
    return await app_svc.list_quote_versions(db, quote_id, current)


@router.get("/{quote_id}/approvals", response_model=list[QuoteApprovalRead])
async def list_quote_approvals(
    quote_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:read"))],
) -> list[QuoteApprovalRead]:
    return await app_svc.list_quote_approvals(db, quote_id, current)


@router.get("/approval-templates/{template_id}", response_model=ApprovalTemplateDetailRead)
async def get_approval_template(
    template_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:quote:read"))],
) -> ApprovalTemplateDetailRead:
    data = await app_svc.get_approval_template_detail(db, template_id)
    return ApprovalTemplateDetailRead(
        **ApprovalTemplateRead.model_validate(data["template"]).model_dump(),
        nodes=[ApprovalNodeRead.model_validate(n) for n in data["nodes"]],
    )


@router.get("/{quote_id}/copilot-summary")
async def quote_copilot_summary(
    quote_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:read"))],
    from_version_no: int | None = Query(default=None, ge=1),
    to_version_no: int | None = Query(default=None, ge=1),
) -> dict:
    # Passed through, not discarded: the service applies the caller's data scope, so a quote outside it
    # answers 404 instead of exposing its cost and profit analysis.
    return await app_svc.summarize_quote_for_copilot(
        db, quote_id, current, from_version_no=from_version_no, to_version_no=to_version_no
    )


@router.get("/{quote_id}/versions/diff")
async def diff_quote_versions(
    quote_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:read"))],
    from_version_no: int = Query(ge=1),
    to_version_no: int = Query(ge=1),
) -> dict:
    # No signature change for compare_quote_versions: it is an internal helper whose third caller is the
    # copilot passing it as compare_fn, so a new parameter would ripple into the analysis function. The
    # already-scoped detail lookup answers 404 for an out-of-scope quote, which is the same guarantee.
    await app_svc.get_quote_detail(db, quote_id, current)
    return await app_svc.compare_quote_versions(db, quote_id, from_version_no, to_version_no)


@router.post("/{quote_id}/exports", response_model=QuoteExportTaskRead, status_code=status.HTTP_202_ACCEPTED)
async def request_quote_export(
    quote_id: UUID,
    payload: QuoteExportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:export"))],
) -> QuoteExportTaskRead:
    return await app_svc.create_export_task(
        db, quote_id, payload.format, current, template_id=payload.template_id
    )


@router.get("/exports/{task_id}", response_model=QuoteExportTaskRead)
async def get_quote_export_task(
    task_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:read"))],
) -> QuoteExportTaskRead:
    # get_export_task keeps its signature: the background handler in
    # app/domains/events/event_handlers/quote_export_handlers.py calls it with no user. The scope check happens
    # here, on the task's quote, before anything is returned.
    task = await app_svc.get_export_task(db, task_id)
    await app_svc.get_quote_detail(db, task.quote_id, current)
    return task


@router.post("/events/replay-dead-letter")
async def replay_dead_letter_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("platform:event:replay"))],
    event_type: str | None = Query(default=None, max_length=128),
) -> dict:
    return await app_svc.replay_dead_letter_events(db, event_type)


@router.post("/events/process-pending")
async def process_pending_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("platform:event:process"))],
    event_type: str | None = Query(default=None, max_length=128),
) -> dict:
    return await app_svc.process_pending_events(db, event_type)


@router.put("/{quote_id}/items/{item_id}/options", response_model=QuoteItemRead)
async def update_quote_item_options(
    quote_id: UUID,
    item_id: UUID,
    payload: QuoteItemOptionsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:update"))],
) -> dict:
    try:
        return await opt_svc.update_quote_item_options(
            db, quote_id, item_id, payload.option_item_ids, current
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
