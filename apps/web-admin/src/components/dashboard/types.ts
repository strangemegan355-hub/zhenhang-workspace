export type DashboardKpis = {
  total_quotes?: number;
  pending_approval?: number;
  approved_quotes?: number;
  draft_quotes?: number;
  quote_amount_total?: string;
  unread_notifications?: number;
  export_pending?: number;
};

export type DashboardProfitKpis = {
  active_projects?: number;
  over_budget_count?: number;
  total_variance?: string | number;
  total_realized_profit?: string | number;
};

export type PipelineItem = { state: string; count: number };

export type RecentQuote = {
  id?: string;
  quote_no?: string;
  title?: string;
  workflow_state?: string;
  total_amount?: string;
  updated_at?: string;
  created_at?: string;
};

export type RiskItem = {
  id: string;
  label: string;
  level: "high" | "medium" | "low";
  count?: number;
  detail?: string;
  href?: string;
};

export type WorkflowNode = {
  key: string;
  label: string;
  approver: string;
  time?: string;
  state: "done" | "active" | "pending";
};

export type ApprovalItem = {
  id: string;
  type: "quote" | "procurement" | "project";
  title: string;
  submitter: string;
  submittedAt: string;
  status: string;
  href: string;
};

export type OverBudgetProjectItem = {
  project_id?: string;
  id?: string;
  project_no?: string;
  name?: string;
  variance?: string | number;
  budget_cost?: string | number;
  actual_cost_total?: string | number;
  cost_variance?: string | number;
};
