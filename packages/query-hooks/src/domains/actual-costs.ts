import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";
import { queryKeys } from "../keys";

type ApiWrap<T> = { code: string; message: string; data: T };
type PageData = { items?: Record<string, unknown>[]; total?: number };

export type ProjectActualCostPayload = {
  project_id: string;
  cost_category: string;
  cost_item_code?: string;
  cost_item_name: string;
  amount: number;
  source?: string;
  supplier_id?: string;
  occurred_on: string;
  remark?: string;
};

export type ProjectActualCostRow = {
  id: string;
  project_id: string;
  cost_category: string;
  cost_item_code?: string | null;
  cost_item_name: string;
  amount: string | number;
  source: string;
  supplier_id?: string | null;
  occurred_on: string;
  remark?: string | null;
};

export function useProjectActualCostsQuery(projectId?: string, page = 1) {
  return useQuery({
    queryKey: queryKeys.actualCosts.list(projectId ?? "", page),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/project-actual-costs", {
        params: { page, page_size: 50, project_id: projectId },
      });
      return data.data;
    },
    enabled: Boolean(projectId),
  });
}

export function useCreateProjectActualCostMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: ProjectActualCostPayload) => {
      const { data } = await apiClient.post<ApiWrap<ProjectActualCostRow>>("/api/v1/project-actual-costs", body);
      return data.data;
    },
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({ queryKey: qk("actualCosts", "list") });
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects.summary(vars.project_id) });
      void queryClient.invalidateQueries({ queryKey: qk("projects", "profit-ledger") });
      void queryClient.invalidateQueries({ queryKey: qk("dashboard", "overview") });
    },
  });
}

export function useDeleteProjectActualCostMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, projectId }: { id: string; projectId: string }) => {
      const { data } = await apiClient.delete<ApiWrap<ProjectActualCostRow>>(`/api/v1/project-actual-costs/${id}`);
      return data.data;
    },
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({ queryKey: qk("actualCosts", "list") });
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects.summary(vars.projectId) });
      void queryClient.invalidateQueries({ queryKey: qk("projects", "profit-ledger") });
      void queryClient.invalidateQueries({ queryKey: qk("dashboard", "overview") });
    },
  });
}
