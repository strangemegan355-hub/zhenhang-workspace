import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";
import { queryKeys } from "../keys";
import type { PageData } from "../types";

type ApiWrap<T> = { code: string; message: string; data: T };

export type ProjectPayload = {
  project_no?: string;
  name: string;
  customer_id?: string;
  category?: string;
  stage?: string;
  owner_name?: string;
  primary_quote_id?: string;
  target_date?: string;
  remark?: string;
  status?: string;
};

export type ProjectProfitSnapshot = {
  revenue_before_tax?: string | number | null;
  revenue_tax_inclusive?: string | number | null;
  budget_cost?: string | number | null;
  expected_profit?: string | number | null;
  profit_margin_pct?: string | number | null;
  actual_cost_total?: string | number | null;
  cost_variance?: string | number | null;
  realized_profit?: string | number | null;
  realized_margin_pct?: string | number | null;
  link_status: "complete" | "missing_quote" | "missing_cost" | "both_missing";
  health: "good" | "warn" | "bad" | "unknown";
  budget_status: "in_budget" | "over_budget" | "unknown";
};

export type ProjectLinkedQuote = {
  id: string;
  quote_no: string;
  title: string;
  quote_kind: string;
  total_amount: string | number;
  workflow_state: string;
};

export type ProjectLinkedCostEstimate = {
  id: string;
  estimate_no: string;
  product_name: string;
  total_cost: string | number;
  final_total: string | number;
};

export type ProjectSummary = {
  quote_count: number;
  cost_estimate_count: number;
  actual_cost_count?: number;
  linked_quote?: ProjectLinkedQuote | null;
  linked_cost_estimate?: ProjectLinkedCostEstimate | null;
  profit_snapshot?: ProjectProfitSnapshot | null;
};

export type ProjectProfitLedgerItem = {
  id: string;
  project_no: string;
  name: string;
  stage: string;
  owner_name?: string | null;
  profit_snapshot: ProjectProfitSnapshot;
};

export type ProjectProfitLedgerTotals = {
  budget_cost_total?: string | number | null;
  actual_cost_total?: string | number | null;
  variance_total?: string | number | null;
  realized_profit_total?: string | number | null;
  over_budget_count: number;
};

export type ProjectProfitLedgerResponse = {
  total: number;
  page: number;
  page_size: number;
  items: ProjectProfitLedgerItem[];
  totals: ProjectProfitLedgerTotals;
};

export function useProjectsQuery(page = 1, q?: string) {
  return useQuery({
    queryKey: queryKeys.projects.list(page, q),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/projects", {
        params: { page, page_size: 50, q },
      });
      return data.data;
    },
    staleTime: 30_000,
  });
}

export function useProjectSummaryQuery(id?: string) {
  return useQuery({
    queryKey: queryKeys.projects.summary(id ?? ""),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<ProjectSummary>>(`/api/v1/projects/${id}/summary`);
      return data.data;
    },
    enabled: Boolean(id),
  });
}

export function useProjectProfitLedgerQuery(page = 1, q?: string, overBudgetOnly = false) {
  return useQuery({
    queryKey: queryKeys.projects.profitLedger(page, q, overBudgetOnly),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<ProjectProfitLedgerResponse>>("/api/v1/projects/profit-ledger", {
        params: { page, page_size: 50, q, over_budget_only: overBudgetOnly },
      });
      return data.data;
    },
    staleTime: 30_000,
  });
}

export function useCreateProjectMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: ProjectPayload) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/projects", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("projects", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("projects", "profit-ledger") });
    },
  });
}

export function useUpdateProjectMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: string; body: Partial<ProjectPayload> }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(`/api/v1/projects/${id}`, body);
      return data.data;
    },
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({ queryKey: qk("projects", "list") });
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects.summary(vars.id) });
      void queryClient.invalidateQueries({ queryKey: qk("projects", "profit-ledger") });
    },
  });
}

export function useDeleteProjectMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(`/api/v1/projects/${id}`);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("projects", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("projects", "profit-ledger") });
    },
  });
}
