"""Rule-based industrial copilot (no autonomous agent)."""

# Moved out of the flat service layer in round 45.
#
# It was `app/services/industrial_copilot.py`; it needed the quote domain's reads, which forced a
# legacy->domain import, and the quote application service imported it back. Inside the domain it reads
# through the domain's own repository.

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import scope_predicate
from app.domains.quote.repositories import quote_repository as repo
from app.models.customer import Customer
from app.models.quote import Quote
from app.models.user import User


async def build_industrial_copilot_analysis(
    db: AsyncSession,
    quote_id: UUID,
    *,
    from_version_no: int | None = None,
    to_version_no: int | None = None,
    compare_fn,
    current_user: User | None = None,
) -> dict:
    quote = await repo.get_quote(db, quote_id)
    if quote is None:
        return {"quote_no": "", "summary": "报价不存在", "highlights": [], "risk_level": "high"}

    max_v = await repo.max_quote_version_no(db, quote_id)
    if max_v < 1:
        return {
            "quote_no": quote.quote_no,
            "summary": f"报价 {quote.quote_no} 尚无版本，当前状态 {quote.workflow_state}。",
            "highlights": ["建议先保存首版报价行再提交审批"],
            "risk_level": "medium",
            "recommendations": ["保存版本", "绑定 BOM"],
            "risk_analysis": [],
            "bom_cost_anomalies": [],
            "profit_suggestions": [],
            "approval_suggestions": [],
            "similar_quotes": [],
            "similar_projects": [],
            "customer_insights": {},
            "delivery_risks": ["尚无版本，无法评估交付周期"],
            "bom_risks": [],
        }

    to_v = to_version_no or max_v
    from_v = from_version_no or max(1, to_v - 1)
    if from_v == to_v and to_v > 1:
        from_v = to_v - 1
    diff = await compare_fn(db, quote_id, from_v, to_v)
    version = await repo.get_quote_version_by_no(db, quote_id, to_v)
    items = await repo.list_quote_items_by_version(db, version.id) if version else []

    highlights: list[str] = []
    risk_analysis: list[str] = []
    bom_anomalies: list[str] = []
    profit_suggestions: list[str] = []
    approval_suggestions: list[str] = []

    bom = diff.get("bom_diff", {})
    for code in bom.get("added", [])[:5]:
        highlights.append(f"新增物料 {code}")
    for code in bom.get("removed", [])[:5]:
        highlights.append(f"移除物料 {code}")
    for ch in bom.get("changed", [])[:5]:
        highlights.append(f"变更物料 {ch.get('item_code')}")

    profit_rate = Decimal(str(version.profit_rate)) if version else Decimal("0")
    total_amount = Decimal(str(version.total_amount)) if version else Decimal(str(quote.total_amount))
    total_cost = Decimal(str(version.total_cost)) if version else Decimal("0")

    if profit_rate < Decimal("10"):
        risk_analysis.append(f"毛利率仅 {profit_rate}% ，低于工业项目安全线 10%")
        profit_suggestions.append("建议上调关键行单价或复核 BOM 成本")
    elif profit_rate < Decimal("18"):
        risk_analysis.append(f"毛利率 {profit_rate}% 处于中等区间，需关注大宗物料波动")
    else:
        risk_analysis.append(f"毛利率 {profit_rate}% 处于健康区间")

    amount_change = Decimal(str(diff.get("amount_change", 0)))
    if amount_change > Decimal("50000"):
        risk_analysis.append(f"版本间报价金额增加 {amount_change}，大额变更需加强审批")
    elif amount_change < Decimal("-30000"):
        risk_analysis.append(f"版本间报价金额减少 {abs(amount_change)}，注意利润侵蚀")

    for item in items:
        qty = Decimal(str(item.quantity))
        price = Decimal(str(item.unit_price))
        line_total = Decimal(str(item.line_total))
        if qty <= 0:
            bom_anomalies.append(f"{item.item_code} 数量异常为 {qty}")
        implied_cost = price * Decimal("0.75")
        if price > 0 and line_total > 0 and price < implied_cost:
            bom_anomalies.append(f"{item.item_code} 单价偏低，疑似低于成本")

    if quote.workflow_state == "reviewing":
        approval_suggestions.append("当前审批中：建议核对 BOM 成本快照与毛利")
        if total_amount > Decimal("500000"):
            approval_suggestions.append("大额报价：建议会签或附加技术评审意见")
    elif quote.workflow_state == "draft":
        approval_suggestions.append("草稿状态：可提交 submit 进入审批流")
    elif quote.workflow_state == "approved":
        approval_suggestions.append("已批准：可发起 PDF 导出并归档")

    similar = await _similar_quotes(db, quote, current_user)
    similar_projects = await _similar_projects(db, quote, current_user)
    customer_insights = await _customer_insights(db, quote)
    delivery_risks = _delivery_risks(quote, profit_rate, total_amount, bom, quote.workflow_state)

    if len(bom_anomalies) >= 3:
        risk_level = "high"
    elif len(risk_analysis) >= 2 or profit_rate < Decimal("12"):
        risk_level = "medium"
    else:
        risk_level = "low"

    recommendations = list(approval_suggestions[:2]) + list(profit_suggestions[:2])
    summary = (
        f"报价 {quote.quote_no} V{from_v}→V{to_v}：金额变化 {diff.get('amount_change')}，"
        f"成本变化 {diff.get('cost_change')}，利润变化 {diff.get('profit_change')}。"
        f" 当前状态 {quote.workflow_state}，综合风险 {risk_level}。"
    )

    return {
        "quote_no": quote.quote_no,
        "summary": summary,
        "highlights": highlights,
        "risk_level": risk_level,
        "recommendations": recommendations,
        "risk_analysis": risk_analysis,
        "bom_cost_anomalies": bom_anomalies[:8],
        "profit_suggestions": profit_suggestions,
        "approval_suggestions": approval_suggestions,
        "similar_quotes": similar,
        "similar_projects": similar_projects,
        "customer_insights": customer_insights,
        "delivery_risks": delivery_risks,
        "bom_risks": bom_anomalies[:8],
        "diff": diff,
        "metrics": {
            "total_amount": str(total_amount),
            "total_cost": str(total_cost),
            "profit_rate": str(profit_rate),
        },
    }


def _delivery_risks(
    quote: Quote,
    profit_rate: Decimal,
    total_amount: Decimal,
    bom_diff: dict,
    workflow_state: str,
) -> list[str]:
    risks: list[str] = []
    if quote.valid_until and quote.valid_until < date.today():
        risks.append(f"报价有效期已过 ({quote.valid_until})，交付承诺需重新确认")
    elif quote.valid_until:
        days_left = (quote.valid_until - date.today()).days
        if days_left <= 7:
            risks.append(f"报价 {days_left} 天后失效，建议锁定交期与物料到货")
    if workflow_state == "reviewing" and total_amount > Decimal("800000"):
        risks.append("大额审批中：交付资源与关键件采购需提前锁定")
    if profit_rate < Decimal("12") and total_amount > Decimal("300000"):
        risks.append("低毛利大单：存在交付阶段成本 overrun 风险")
    added = bom_diff.get("added") or []
    if len(added) > 8:
        risks.append(f"BOM 新增 {len(added)} 项物料，供应链齐套风险上升")
    if not risks:
        risks.append("未发现显著交付风险，建议维持现有交期承诺")
    return risks[:6]


async def _similar_projects(db: AsyncSession, quote: Quote, current_user: User | None = None) -> list[dict]:
    if not quote.machine_id:
        return []
    # Round 196: without the caller's scope this panel disclosed other departments' quote numbers, titles and totals.
    scoped = [Quote.machine_id == quote.machine_id, Quote.id != quote.id, Quote.is_deleted.is_(False)]
    if current_user is not None:
        scoped.append(scope_predicate(Quote, current_user))
    stmt = (
        select(Quote)
        .where(*scoped)
        .order_by(Quote.updated_at.desc())
        .limit(5)
    )
    rows = list((await db.execute(stmt)).scalars().all())
    return [
        {
            "id": str(q.id),
            "quote_no": q.quote_no,
            "title": q.title,
            "workflow_state": q.workflow_state,
            "total_amount": str(q.total_amount),
        }
        for q in rows
    ]


async def _similar_quotes(db: AsyncSession, quote: Quote, current_user: User | None = None) -> list[dict]:
    if not quote.customer_id:
        return []
    # Round 196: see `_similar_projects` — the same panel leaked by customer instead of by machine.
    scoped = [Quote.customer_id == quote.customer_id, Quote.id != quote.id, Quote.is_deleted.is_(False)]
    if current_user is not None:
        scoped.append(scope_predicate(Quote, current_user))
    stmt = (
        select(Quote)
        .where(*scoped)
        .order_by(Quote.updated_at.desc())
        .limit(5)
    )
    rows = list((await db.execute(stmt)).scalars().all())
    return [
        {
            "id": str(q.id),
            "quote_no": q.quote_no,
            "title": q.title,
            "workflow_state": q.workflow_state,
            "total_amount": str(q.total_amount),
        }
        for q in rows
    ]


async def _customer_insights(db: AsyncSession, quote: Quote) -> dict:
    if not quote.customer_id:
        return {}
    customer = (await db.execute(select(Customer).where(Customer.id == quote.customer_id))).scalar_one_or_none()
    approved_count = int(
        (
            await db.execute(
                select(func.count())
                .select_from(Quote)
                .where(
                    Quote.customer_id == quote.customer_id,
                    Quote.workflow_state == "approved",
                    Quote.is_deleted.is_(False),
                )
            )
        ).scalar_one()
    )
    total_amount = (
        await db.execute(
            select(func.coalesce(func.sum(Quote.total_amount), 0)).where(
                Quote.customer_id == quote.customer_id,
                Quote.is_deleted.is_(False),
            )
        )
    ).scalar_one()
    return {
        "customer_name": customer.name if customer else "",
        "approved_quotes": approved_count,
        "historical_amount_total": str(total_amount),
        "current_quote_amount": str(quote.total_amount),
        "deal_signal": "高价值客户" if Decimal(str(total_amount)) > Decimal("1000000") else "成长客户",
    }
