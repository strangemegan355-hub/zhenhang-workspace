from decimal import Decimal

from app.services.project_profit_snapshot import build_project_profit_snapshot


def test_complete_customer_quote_and_cost() -> None:
    snapshot = build_project_profit_snapshot(
        quote_kind="customer",
        quote_total_amount=Decimal("113000"),
        version_total_amount=Decimal("100000"),
        analysis_snapshot={"before_tax": "100000", "final_total": "113000"},
        budget_cost=Decimal("72000"),
    )
    assert snapshot["revenue_before_tax"] == Decimal("100000.00")
    assert snapshot["revenue_tax_inclusive"] == Decimal("113000.00")
    assert snapshot["budget_cost"] == Decimal("72000.00")
    assert snapshot["expected_profit"] == Decimal("28000.00")
    assert snapshot["profit_margin_pct"] == Decimal("28.00")
    assert snapshot["link_status"] == "complete"
    assert snapshot["health"] == "good"


def test_missing_cost_estimate() -> None:
    snapshot = build_project_profit_snapshot(
        quote_kind="customer",
        quote_total_amount=Decimal("113000"),
        version_total_amount=Decimal("100000"),
        analysis_snapshot={"before_tax": "100000", "final_total": "113000"},
        budget_cost=None,
    )
    assert snapshot["expected_profit"] is None
    assert snapshot["link_status"] == "missing_cost"
    assert snapshot["health"] == "unknown"


def test_missing_quote() -> None:
    snapshot = build_project_profit_snapshot(budget_cost=Decimal("50000"))
    assert snapshot["link_status"] == "missing_quote"
    assert snapshot["expected_profit"] is None


def test_low_margin_health() -> None:
    snapshot = build_project_profit_snapshot(
        quote_kind="customer",
        quote_total_amount=Decimal("108000"),
        version_total_amount=Decimal("100000"),
        analysis_snapshot={"before_tax": "100000", "final_total": "108000"},
        budget_cost=Decimal("93000"),
    )
    assert snapshot["expected_profit"] == Decimal("7000.00")
    assert snapshot["profit_margin_pct"] == Decimal("7.00")
    assert snapshot["health"] == "bad"


def test_industrial_quote_uses_version_subtotal() -> None:
    snapshot = build_project_profit_snapshot(
        quote_kind="industrial",
        quote_total_amount=Decimal("250000"),
        version_total_amount=Decimal("250000"),
        budget_cost=Decimal("210000"),
    )
    assert snapshot["revenue_before_tax"] == Decimal("250000.00")
    assert snapshot["expected_profit"] == Decimal("40000.00")
    assert snapshot["profit_margin_pct"] == Decimal("16.00")
    assert snapshot["health"] == "good"


def test_actual_cost_variance_and_realized_profit() -> None:
    snapshot = build_project_profit_snapshot(
        quote_kind="customer",
        quote_total_amount=Decimal("113000"),
        version_total_amount=Decimal("100000"),
        analysis_snapshot={"before_tax": "100000", "final_total": "113000"},
        budget_cost=Decimal("72000"),
        actual_cost_total=Decimal("78000"),
    )
    assert snapshot["actual_cost_total"] == Decimal("78000.00")
    assert snapshot["cost_variance"] == Decimal("6000.00")
    assert snapshot["realized_profit"] == Decimal("22000.00")
    assert snapshot["realized_margin_pct"] == Decimal("22.00")
    assert snapshot["budget_status"] == "over_budget"


def test_in_budget_when_actual_below_budget() -> None:
    snapshot = build_project_profit_snapshot(
        quote_kind="customer",
        version_total_amount=Decimal("100000"),
        budget_cost=Decimal("80000"),
        actual_cost_total=Decimal("75000"),
    )
    assert snapshot["cost_variance"] == Decimal("-5000.00")
    assert snapshot["budget_status"] == "in_budget"
