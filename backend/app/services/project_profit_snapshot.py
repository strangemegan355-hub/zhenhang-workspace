"""Pure project profit KPI calculation — no DB access."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Literal, TypedDict

_TWOPLACES = Decimal("0.01")

LinkStatus = Literal["complete", "missing_quote", "missing_cost", "both_missing"]
HealthStatus = Literal["good", "warn", "bad", "unknown"]
BudgetStatus = Literal["in_budget", "over_budget", "unknown"]


class ProjectProfitSnapshotData(TypedDict):
    revenue_before_tax: Decimal | None
    revenue_tax_inclusive: Decimal | None
    budget_cost: Decimal | None
    expected_profit: Decimal | None
    profit_margin_pct: Decimal | None
    actual_cost_total: Decimal | None
    cost_variance: Decimal | None
    realized_profit: Decimal | None
    realized_margin_pct: Decimal | None
    link_status: LinkStatus
    health: HealthStatus
    budget_status: BudgetStatus


def _money(value: Decimal) -> Decimal:
    return value.quantize(_TWOPLACES, rounding=ROUND_HALF_UP)


def _to_decimal(value: object | None) -> Decimal | None:
    if value is None:
        return None
    return _money(Decimal(str(value)))


def _revenue_from_quote(
    *,
    quote_kind: str | None,
    quote_total_amount: Decimal | None,
    version_total_amount: Decimal | None,
    analysis_snapshot: dict | None,
) -> tuple[Decimal | None, Decimal | None]:
    if quote_kind is None and quote_total_amount is None and version_total_amount is None:
        return None, None

    snapshot = analysis_snapshot or {}
    before_tax = _to_decimal(snapshot.get("before_tax"))
    tax_inclusive = _to_decimal(snapshot.get("final_total"))

    if quote_kind == "customer":
        before_tax = before_tax or version_total_amount or quote_total_amount
        tax_inclusive = tax_inclusive or quote_total_amount
        return before_tax, tax_inclusive

    amount = version_total_amount or quote_total_amount
    return amount, amount


def _link_status(has_quote: bool, has_cost: bool) -> LinkStatus:
    if has_quote and has_cost:
        return "complete"
    if has_quote:
        return "missing_cost"
    if has_cost:
        return "missing_quote"
    return "both_missing"


def _health(margin_pct: Decimal | None) -> HealthStatus:
    if margin_pct is None:
        return "unknown"
    if margin_pct < Decimal("8"):
        return "bad"
    if margin_pct < Decimal("15"):
        return "warn"
    return "good"


def _budget_status(variance: Decimal | None) -> BudgetStatus:
    if variance is None:
        return "unknown"
    if variance > 0:
        return "over_budget"
    return "in_budget"


def build_project_profit_snapshot(
    *,
    quote_kind: str | None = None,
    quote_total_amount: Decimal | None = None,
    version_total_amount: Decimal | None = None,
    analysis_snapshot: dict | None = None,
    budget_cost: Decimal | None = None,
    actual_cost_total: Decimal | None = None,
) -> ProjectProfitSnapshotData:
    revenue_before_tax, revenue_tax_inclusive = _revenue_from_quote(
        quote_kind=quote_kind,
        quote_total_amount=quote_total_amount,
        version_total_amount=version_total_amount,
        analysis_snapshot=analysis_snapshot,
    )

    has_quote = revenue_before_tax is not None
    has_cost = budget_cost is not None
    link_status = _link_status(has_quote, has_cost)

    expected_profit: Decimal | None = None
    profit_margin_pct: Decimal | None = None
    if revenue_before_tax is not None and budget_cost is not None:
        expected_profit = _money(revenue_before_tax - budget_cost)
        if revenue_before_tax > 0:
            profit_margin_pct = _money(expected_profit / revenue_before_tax * Decimal("100"))

    actual_total = _to_decimal(actual_cost_total) if actual_cost_total is not None else None
    if actual_total is not None and actual_total == 0:
        actual_total = None

    cost_variance: Decimal | None = None
    if actual_total is not None and budget_cost is not None:
        cost_variance = _money(actual_total - budget_cost)

    realized_profit: Decimal | None = None
    realized_margin_pct: Decimal | None = None
    if revenue_before_tax is not None and actual_total is not None:
        realized_profit = _money(revenue_before_tax - actual_total)
        if revenue_before_tax > 0:
            realized_margin_pct = _money(realized_profit / revenue_before_tax * Decimal("100"))

    return {
        "revenue_before_tax": revenue_before_tax,
        "revenue_tax_inclusive": revenue_tax_inclusive,
        "budget_cost": budget_cost,
        "expected_profit": expected_profit,
        "profit_margin_pct": profit_margin_pct,
        "actual_cost_total": actual_total,
        "cost_variance": cost_variance,
        "realized_profit": realized_profit,
        "realized_margin_pct": realized_margin_pct,
        "link_status": link_status,
        "health": _health(profit_margin_pct),
        "budget_status": _budget_status(cost_variance),
    }
