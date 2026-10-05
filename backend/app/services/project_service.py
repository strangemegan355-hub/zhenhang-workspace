from decimal import Decimal
from typing import TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import scope_predicate
from app.models.project import Project
from app.models.user import User
from app.repositories import project_actual_cost_repository as actual_cost_repo
from app.repositories import project_repository as repo
from app.schemas.common import PageResponse
from app.schemas.project import (
    ProjectLinkedCostEstimate,
    ProjectLinkedQuote,
    ProjectProfitLedgerItem,
    ProjectProfitLedgerResponse,
    ProjectProfitLedgerTotals,
    ProjectProfitSnapshot,
    ProjectRead,
    ProjectSummaryRead,
)
from app.services.project_profit_snapshot import build_project_profit_snapshot

T = TypeVar("T", bound=BaseModel)


def _page(total: int, page: int, page_size: int, items: list, schema: type[T]) -> PageResponse:
    return PageResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[schema.model_validate(i) for i in items],
    )


async def _build_project_profit_context(db: AsyncSession, project) -> dict:
    linked_quote = await repo.find_linked_quote(db, project)
    linked_cost = await repo.find_linked_cost_estimate(db, project.id)
    quote_count = await repo.count_quotes_for_project(db, project.id)
    cost_count = await repo.count_cost_estimates_for_project(db, project.id)
    actual_count, actual_sum = await actual_cost_repo.sum_amount_by_project(db, project.id)

    current_version = None
    if linked_quote:
        current_version = await repo.find_current_quote_version(db, linked_quote.id)

    profit_data = build_project_profit_snapshot(
        quote_kind=linked_quote.quote_kind if linked_quote else None,
        quote_total_amount=Decimal(str(linked_quote.total_amount)) if linked_quote else None,
        version_total_amount=Decimal(str(current_version.total_amount)) if current_version else None,
        analysis_snapshot=current_version.analysis_snapshot if current_version else None,
        budget_cost=Decimal(str(linked_cost.total_cost)) if linked_cost else None,
        actual_cost_total=Decimal(str(actual_sum)) if actual_count > 0 else None,
    )
    return {
        "linked_quote": linked_quote,
        "linked_cost": linked_cost,
        "profit_snapshot": ProjectProfitSnapshot.model_validate(profit_data),
        "quote_count": quote_count,
        "cost_count": cost_count,
        "actual_count": actual_count,
    }


async def create_project(db: AsyncSession, payload: dict, current_user: User) -> ProjectRead:
    if not payload.get("project_no"):
        payload["project_no"] = await repo.generate_project_no(db)
    payload["created_by"] = current_user.id
    obj = await repo.create_project(db, payload)
    return ProjectRead.model_validate(obj)


async def list_projects(
    db: AsyncSession, page: int, page_size: int, q: str | None, current_user: User
) -> PageResponse:
    total, items = await repo.list_projects(
        db, page, page_size, q, predicate=scope_predicate(Project, current_user)
    )
    return _page(total, page, page_size, items, ProjectRead)


async def get_project_or_404(
    db: AsyncSession, object_id: UUID, current_user: User
) -> ProjectRead:
    obj = await repo.get_project(db, object_id, predicate=scope_predicate(Project, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectRead.model_validate(obj)


async def get_project_summary(
    db: AsyncSession, object_id: UUID, current_user: User
) -> ProjectSummaryRead:
    obj = await repo.get_project(db, object_id, predicate=scope_predicate(Project, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    ctx = await _build_project_profit_context(db, obj)
    summary = ProjectSummaryRead.model_validate(obj)
    return summary.model_copy(
        update={
            "linked_quote": ProjectLinkedQuote.model_validate(ctx["linked_quote"]) if ctx["linked_quote"] else None,
            "linked_cost_estimate": ProjectLinkedCostEstimate.model_validate(ctx["linked_cost"]) if ctx["linked_cost"] else None,
            "quote_count": ctx["quote_count"],
            "cost_estimate_count": ctx["cost_count"],
            "actual_cost_count": ctx["actual_count"],
            "profit_snapshot": ctx["profit_snapshot"],
        }
    )


def _sum_optional(values: list[Decimal | None]) -> Decimal | None:
    present = [v for v in values if v is not None]
    if not present:
        return None
    return sum(present, Decimal("0"))


def _ledger_totals(items: list[ProjectProfitLedgerItem]) -> ProjectProfitLedgerTotals:
    snapshots = [item.profit_snapshot for item in items]
    over_budget_count = sum(1 for s in snapshots if s.budget_status == "over_budget")
    return ProjectProfitLedgerTotals(
        budget_cost_total=_sum_optional([s.budget_cost for s in snapshots]),
        actual_cost_total=_sum_optional([s.actual_cost_total for s in snapshots]),
        variance_total=_sum_optional([s.cost_variance for s in snapshots]),
        realized_profit_total=_sum_optional([s.realized_profit for s in snapshots]),
        over_budget_count=over_budget_count,
    )


async def aggregate_profit_kpis(db: AsyncSession, *, limit: int = 500) -> dict:
    _, projects = await repo.list_projects(db, 1, limit, None)
    over_budget: list[dict] = []
    realized_profits: list[Decimal] = []
    variances: list[Decimal] = []

    for project in projects:
        ctx = await _build_project_profit_context(db, project)
        snap = ctx["profit_snapshot"]
        if snap.realized_profit is not None:
            realized_profits.append(snap.realized_profit)
        if snap.cost_variance is not None:
            variances.append(snap.cost_variance)
        if snap.budget_status == "over_budget" and snap.cost_variance is not None:
            over_budget.append(
                {
                    "project_id": str(project.id),
                    "project_no": project.project_no,
                    "name": project.name,
                    "cost_variance": str(snap.cost_variance),
                    "actual_cost_total": str(snap.actual_cost_total) if snap.actual_cost_total is not None else None,
                    "budget_cost": str(snap.budget_cost) if snap.budget_cost is not None else None,
                }
            )

    over_budget.sort(key=lambda row: Decimal(row["cost_variance"]), reverse=True)
    total_realized = _sum_optional(realized_profits)
    total_variance = _sum_optional(variances)
    return {
        "active_projects": len(projects),
        "over_budget_count": len(over_budget),
        "total_realized_profit": str(total_realized) if total_realized is not None else None,
        "total_variance": str(total_variance) if total_variance is not None else None,
        "over_budget_top3": over_budget[:3],
    }


async def list_profit_ledger(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    current_user: User,
    *,
    over_budget_only: bool = False,
) -> ProjectProfitLedgerResponse:
    predicate = scope_predicate(Project, current_user)
    if over_budget_only:
        _, projects = await repo.list_projects(db, 1, 500, q, predicate=predicate)
        ledger_items: list[ProjectProfitLedgerItem] = []
        for project in projects:
            ctx = await _build_project_profit_context(db, project)
            if ctx["profit_snapshot"].budget_status != "over_budget":
                continue
            ledger_items.append(
                ProjectProfitLedgerItem(
                    id=project.id,
                    project_no=project.project_no,
                    name=project.name,
                    stage=project.stage,
                    owner_name=project.owner_name,
                    profit_snapshot=ctx["profit_snapshot"],
                )
            )
        total = len(ledger_items)
        start = (page - 1) * page_size
        page_items = ledger_items[start : start + page_size]
    else:
        total, projects = await repo.list_projects(db, page, page_size, q, predicate=predicate)
        page_items = []
        for project in projects:
            ctx = await _build_project_profit_context(db, project)
            page_items.append(
                ProjectProfitLedgerItem(
                    id=project.id,
                    project_no=project.project_no,
                    name=project.name,
                    stage=project.stage,
                    owner_name=project.owner_name,
                    profit_snapshot=ctx["profit_snapshot"],
                )
            )

    return ProjectProfitLedgerResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=page_items,
        totals=_ledger_totals(page_items),
    )


async def update_project(
    db: AsyncSession, object_id: UUID, payload: dict, current_user: User
) -> ProjectRead:
    obj = await repo.get_project(db, object_id, predicate=scope_predicate(Project, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    updated = await repo.update_project(db, obj, payload)
    return ProjectRead.model_validate(updated)


async def delete_project(db: AsyncSession, object_id: UUID, current_user: User) -> ProjectRead:
    obj = await repo.get_project(db, object_id, predicate=scope_predicate(Project, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    deleted = await repo.soft_delete_project(db, obj)
    return ProjectRead.model_validate(deleted)
