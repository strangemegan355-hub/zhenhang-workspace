import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";
import { queryKeys } from "../keys";

type ApiWrap<T> = { code: string; message: string; data: T };
type PageData = { items?: Record<string, unknown>[]; total?: number };

export type FieldworkRecordPayload = {
  record_type: "repair" | "shortage" | "loading";
  customer_id?: string;
  project_id?: string;
  machine_id?: string;
  material_id?: string;
  occurred_on?: string;
  reporter_name?: string;
  headline: string;
  detail?: string;
  qty?: number;
  hours?: number;
  repair_amount?: number;
  urgency?: string;
  extra?: Record<string, unknown>;
  remark?: string;
  service_request_id?: string;
};

export type FieldworkRecordUpdatePayload = {
  detail?: string;
  urgency?: string;
  remark?: string;
  repair_amount?: number;
};

export type FieldworkSummary = {
  total: number;
  repair: number;
  shortage: number;
  loading: number;
  open_shortages: number;
};

export function useFieldworkRecordsQuery(page = 1, q?: string, recordType?: string, status?: string) {
  return useQuery({
    queryKey: queryKeys.fieldwork.list(page, q, recordType, status),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/fieldwork-records", {
        params: { page, page_size: 50, q, record_type: recordType, status },
      });
      return data.data;
    },
  });
}

export function useFieldworkSummaryQuery() {
  return useQuery({
    queryKey: queryKeys.fieldwork.summary(),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<FieldworkSummary>>("/api/v1/fieldwork-records/summary");
      return data.data;
    },
    staleTime: 30_000,
  });
}

export function useCreateFieldworkRecordMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: FieldworkRecordPayload) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/fieldwork-records", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("fieldwork", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("fieldwork", "summary") });
    },
  });
}

export function useAdvanceFieldworkStatusMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        `/api/v1/fieldwork-records/${id}/advance-status`,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("fieldwork", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("fieldwork", "summary") });
    },
  });
}

export function useDeleteFieldworkRecordMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(`/api/v1/fieldwork-records/${id}`);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("fieldwork", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("fieldwork", "summary") });
    },
  });
}

export function useUpdateFieldworkRecordMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: string; body: FieldworkRecordUpdatePayload }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(`/api/v1/fieldwork-records/${id}`, body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("fieldwork", "list") });
    },
  });
}

export function usePostFieldworkReceivableMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        `/api/v1/fieldwork-records/${id}/post-receivable`,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("fieldwork", "list") });
      void queryClient.invalidateQueries({ queryKey: ["accounting"] });
    },
  });
}
