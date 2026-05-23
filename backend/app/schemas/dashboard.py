from pydantic import BaseModel


class DashboardKpis(BaseModel):
    total_quotes: int
    pending_approval: int
    approved_quotes: int
    draft_quotes: int
    quote_amount_total: str
    unread_notifications: int
    export_pending: int


class DashboardOverview(BaseModel):
    generated_at: str
    kpis: DashboardKpis
    recent_quotes: list[dict]
    pipeline: list[dict]
