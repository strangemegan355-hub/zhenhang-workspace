from pydantic import BaseModel


class DashboardKpis(BaseModel):
    total_quotes: int
    pending_approval: int
    approved_quotes: int
    draft_quotes: int
    quote_amount_total: str
    unread_notifications: int
    export_pending: int


class DashboardProfitKpis(BaseModel):
    active_projects: int
    over_budget_count: int
    total_realized_profit: str | None = None
    total_variance: str | None = None


class OverBudgetProjectItem(BaseModel):
    project_id: str
    project_no: str
    name: str
    cost_variance: str
    actual_cost_total: str | None = None
    budget_cost: str | None = None


class DashboardOverview(BaseModel):
    generated_at: str
    kpis: DashboardKpis
    profit_kpis: DashboardProfitKpis | None = None
    over_budget_top3: list[OverBudgetProjectItem] = []
    recent_quotes: list[dict]
    pipeline: list[dict]
