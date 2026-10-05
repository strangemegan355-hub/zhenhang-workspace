import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";
import { queryKeys } from "../keys";

type ApiWrap<T> = { code: string; message: string; data: T };
type PageData = { items?: Record<string, unknown>[]; total?: number };

export type CostLineMaterial = {
  material_id?: string;
  category_id?: string;
  category_path?: string[];
  name: string;
  spec?: string;
  qty: number;
  unit: string;
  unit_price: number;
  sort_order?: number;
};

export type CostLineMachine = {
  machine_id?: string;
  name: string;
  spec?: string;
  power_kw?: string;
  unit_price: number;
  qty: number;
  sort_order?: number;
};

export type CostLineProcess = {
  process_name: string;
  equipment?: string;
  hours: number;
  rate: number;
  sort_order?: number;
};

export type CostEstimatePayload = {
  product_name: string;
  product_spec?: string;
  power_kw?: string;
  customer_id?: string;
  project_id?: string;
  drawing_no?: string;
  qty: number;
  delivery_note?: string;
  remark?: string;
  outsource_cost: number;
  logistics_cost: number;
  scrap_rate?: number;
  overhead_rate?: number;
  profit_rate?: number;
  tax_rate?: number;
  material_lines: CostLineMaterial[];
  machine_lines: CostLineMachine[];
  process_lines: CostLineProcess[];
};

export type CostEstimateSummary = {
  material_cost: number;
  machine_cost: number;
  labor_cost: number;
  other_cost: number;
  base_cost: number;
  scrap_cost: number;
  overhead_cost: number;
  total_cost: number;
  profit_amount: number;
  before_tax: number;
  tax_amount: number;
  final_total: number;
  unit_final: number;
};

export function useCostEstimatesQuery(page = 1, q?: string) {
  return useQuery({
    queryKey: queryKeys.costing.list(page, q),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/cost-estimates", {
        params: { page, page_size: 50, q },
      });
      return data.data;
    },
    staleTime: 30_000,
  });
}

export function useCostEstimateQuery(id?: string) {
  return useQuery({
    queryKey: queryKeys.costing.detail(id ?? ""),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>>>(`/api/v1/cost-estimates/${id}`);
      return data.data;
    },
    enabled: Boolean(id),
  });
}

export function usePreviewCostEstimateMutation() {
  return useMutation({
    mutationFn: async (body: CostEstimatePayload) => {
      const { data } = await apiClient.post<ApiWrap<CostEstimateSummary>>("/api/v1/cost-estimates/preview", body);
      return data.data;
    },
  });
}

export function useCreateCostEstimateMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: CostEstimatePayload) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/cost-estimates", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("costing", "list") });
    },
  });
}

export function useUpdateCostEstimateMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: string; body: Partial<CostEstimatePayload> & { status?: string } }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(`/api/v1/cost-estimates/${id}`, body);
      return data.data;
    },
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({ queryKey: qk("costing", "list") });
      void queryClient.invalidateQueries({ queryKey: queryKeys.costing.detail(vars.id) });
    },
  });
}

export function useDeleteCostEstimateMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(`/api/v1/cost-estimates/${id}`);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("costing", "list") });
    },
  });
}
