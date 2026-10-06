import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";
import { queryKeys } from "../keys";
import type { PageData } from "../types";

type ApiWrap<T> = { code: string; message: string; data: T };

export type WorkOrderPayload = {
  work_order_no?: string;
  project_id: string;
  machine_id?: string;
  task_desc: string;
  process_node?: string;
  team?: string;
  owner_name?: string;
  plan_start?: string;
  plan_end?: string;
  drawing_version?: string;
  exception_type?: string;
  remark?: string;
};

export type WorkOrderSummary = {
  total: number;
  todo: number;
  doing: number;
  done: number;
  exception_count: number;
  completed_today: number;
};

export function useWorkOrdersQuery(page = 1, q?: string, status?: string, projectId?: string) {
  return useQuery({
    queryKey: queryKeys.workOrders.list(page, q, status, projectId),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/work-orders", {
        params: { page, page_size: 50, q, status, project_id: projectId },
      });
      return data.data;
    },
  });
}

export function useWorkOrderSummaryQuery() {
  return useQuery({
    queryKey: queryKeys.workOrders.summary(),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<WorkOrderSummary>>("/api/v1/work-orders/summary");
      return data.data;
    },
    staleTime: 30_000,
  });
}

export function useCreateWorkOrderMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: WorkOrderPayload) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/work-orders", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("workOrders", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("workOrders", "summary") });
      void queryClient.invalidateQueries({ queryKey: qk("workshop", "board") });
    },
  });
}

export function useAdvanceWorkOrderMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        `/api/v1/work-orders/${id}/advance-status`,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("workOrders", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("workOrders", "summary") });
      void queryClient.invalidateQueries({ queryKey: qk("workshop", "board") });
      void queryClient.invalidateQueries({ queryKey: qk("projects", "list") });
    },
  });
}

export function useClaimWorkOrderMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, claimed_by }: { id: string; claimed_by: string }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(`/api/v1/work-orders/${id}/claim`, {
        claimed_by,
      });
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("workOrders", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("workOrders", "summary") });
      void queryClient.invalidateQueries({ queryKey: qk("workshop", "board") });
    },
  });
}

export function useDeleteWorkOrderMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(`/api/v1/work-orders/${id}`);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("workOrders", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("workOrders", "summary") });
      void queryClient.invalidateQueries({ queryKey: qk("workshop", "board") });
    },
  });
}

export function useGenerateWorkOrderChainMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { project_id: string; start_date?: string; step_days?: number; drawing_version?: string }) => {
      const { data } = await apiClient.post<ApiWrap<{ created_count: number; items: Record<string, unknown>[] }>>(
        "/api/v1/work-orders/generate-standard-chain",
        body,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("workOrders", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("workOrders", "summary") });
      void queryClient.invalidateQueries({ queryKey: qk("workshop", "board") });
      void queryClient.invalidateQueries({ queryKey: qk("projects", "list") });
    },
  });
}


export function usePostWorkOrderExpenseMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      workOrderId,
      amount,
      title,
    }: {
      workOrderId: string;
      amount: number;
      title: string;
    }) => {
      const { data } = await apiClient.post<{ data: Record<string, unknown> }>(
        `/api/v1/work-orders/${workOrderId}/post-expense`,
        { amount, title },
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("workOrders", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("workOrders", "summary") });
      void queryClient.invalidateQueries({ queryKey: qk("workshop", "board") });
    },
  });
}
