export type DashboardKpis = {
  total_quotes?: number;
  pending_approval?: number;
  approved_quotes?: number;
  draft_quotes?: number;
  quote_amount_total?: string;
  unread_notifications?: number;
  export_pending?: number;
};

export type PipelineItem = { state: string; count: number };

export type RecentQuote = {
  id?: string;
  quote_no?: string;
  title?: string;
  workflow_state?: string;
  total_amount?: string;
};

export type RiskItem = {
  id: string;
  label: string;
  level: "high" | "medium" | "low";
  count?: number;
  detail?: string;
  href?: string;
};
