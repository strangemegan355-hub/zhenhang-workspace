import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";
import { queryKeys } from "../keys";
import type { PageData } from "../types";

type ApiWrap<T> = { code: string; message: string; data: T };

export type ProcurementEntryPayload = {
  request_no?: string;
  project_id?: string;
  material_id: string;
  supplier_id: string;
  qty: number;
  unit_price: number;
  lead_days?: number;
  need_date?: string;
  remark?: string;
};

export type ProcurementTransferResult = {
  transferred_count: number;
  skipped_count: number;
  items: Array<Record<string, unknown>>;
};

export function useProcurementEntriesQuery(page = 1, q?: string, status?: string) {
  return useQuery({
    queryKey: queryKeys.procurement.list(page, q, status),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/procurement-entries", {
        params: { page, page_size: 50, q, status },
      });
      return data.data;
    },
  });
}

export function useCreateProcurementEntryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: ProcurementEntryPayload) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/procurement-entries", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("procurement", "list") });
    },
  });
}

export function useAdvanceProcurementStatusMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        `/api/v1/procurement-entries/${id}/advance-status`,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("procurement", "list") });
    },
  });
}

export function useDeleteProcurementEntryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(`/api/v1/procurement-entries/${id}`);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("procurement", "list") });
    },
  });
}

export function useTransferProcurementArrivedMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post<ApiWrap<ProcurementTransferResult>>(
        "/api/v1/procurement-entries/transfer-arrived",
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("procurement", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("actualCosts", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("projects", "summary") });
      void queryClient.invalidateQueries({ queryKey: qk("projects", "profit-ledger") });
      void queryClient.invalidateQueries({ queryKey: qk("dashboard", "overview") });
    },
  });
}
