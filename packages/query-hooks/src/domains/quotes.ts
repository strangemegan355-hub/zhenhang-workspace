import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { getQueryPolicy, invalidateByDomain } from "@zhenhang/query-policy-registry";
import { queryKeys } from "../keys";

type ApiWrap<T> = { code: string; message: string; data: T };
type PageData = { items?: Record<string, unknown>[]; total?: number };

export function useQuotesQuery(params: { page: number; keyword?: string }) {
  const policy = getQueryPolicy("quotes");
  return useQuery({
    queryKey: queryKeys.quotes.list(params),
    staleTime: policy.staleTimeMs,
    gcTime: policy.gcTimeMs,
    retry: policy.retry,
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/quotes", {
        params: { page: params.page, q: params.keyword },
      });
      return data.data;
    },
  });
}

export function useQuoteDetailQuery(quoteId: string | null) {
  const policy = getQueryPolicy("quotes");
  return useQuery({
    queryKey: queryKeys.quotes.detail(quoteId ?? ""),
    enabled: Boolean(quoteId),
    staleTime: policy.staleTimeMs,
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>>>(`/api/v1/quotes/${quoteId}`);
      return data.data;
    },
  });
}

export function useQuoteDiffQuery(params: {
  quoteId: string;
  fromVersionNo: number;
  toVersionNo: number;
}) {
  const policy = getQueryPolicy("quotes");
  return useQuery({
    queryKey: queryKeys.quotes.diff(params.quoteId, params.fromVersionNo, params.toVersionNo),
    enabled: Boolean(params.quoteId) && params.fromVersionNo > 0 && params.toVersionNo > 0,
    staleTime: policy.staleTimeMs,
    gcTime: policy.gcTimeMs,
    retry: 0,
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>>>(
        `/api/v1/quotes/${params.quoteId}/versions/diff`,
        { params: { from_version_no: params.fromVersionNo, to_version_no: params.toVersionNo } },
      );
      return data.data;
    },
  });
}

export function useQuoteApprovalsQuery(quoteId: string | null) {
  return useQuery({
    queryKey: queryKeys.quotes.approvals(quoteId ?? ""),
    enabled: Boolean(quoteId),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>[]>>(
        `/api/v1/quotes/${quoteId}/approvals`,
      );
      return data.data ?? [];
    },
  });
}

export function useQuoteTransitionMutation(quoteId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { action_code: string; comment?: string }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        `/api/v1/quotes/${quoteId}/actions/transition`,
        payload,
      );
      return data.data;
    },
    onSettled: () => invalidateByDomain(queryClient, "quotes"),
  });
}

export function useQuoteExportMutation(quoteId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { format: "pdf" | "xlsx"; template_id?: string }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        `/api/v1/quotes/${quoteId}/exports`,
        payload,
      );
      await apiClient.post(
        "/api/v1/quotes/events/process-pending",
        {},
        { params: { event_type: "quote.export.requested" } },
      );
      return data.data;
    },
    onSettled: () => {
      invalidateByDomain(queryClient, "quotes");
      invalidateByDomain(queryClient, "notifications");
    },
  });
}

export function useQuoteExportTaskQuery(taskId: string | null, enabled = true) {
  return useQuery({
    queryKey: queryKeys.quotes.exportTask(taskId ?? ""),
    enabled: Boolean(taskId) && enabled,
    refetchInterval: (q) => {
      const status = (q.state.data as Record<string, unknown> | undefined)?.status;
      return status === "completed" || status === "failed" ? false : 2000;
    },
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>>>(
        `/api/v1/quotes/exports/${taskId}`,
      );
      return data.data;
    },
  });
}

export function useQuoteCopilotQuery(params: {
  quoteId: string;
  fromVersionNo?: number;
  toVersionNo?: number;
}) {
  return useQuery({
    queryKey: queryKeys.quotes.copilot(params.quoteId, params.fromVersionNo, params.toVersionNo),
    enabled: Boolean(params.quoteId),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>>>("/api/v1/ai/copilot/quote-summary", {
        params: {
          quote_id: params.quoteId,
          from_version_no: params.fromVersionNo,
          to_version_no: params.toVersionNo,
        },
      });
      return data.data;
    },
  });
}

export function useCreateQuoteVersionMutation(quoteId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (items: Array<Record<string, unknown>>) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/quotes/versions", {
        quote_id: quoteId,
        items,
      });
      return data.data;
    },
    onSettled: () => invalidateByDomain(queryClient, "quotes"),
  });
}

export function useExportTemplatesQuery() {
  return useQuery({
    queryKey: queryKeys.quotes.exportTemplates(),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Array<Record<string, unknown>>>>("/api/v1/quotes/export-templates");
      return data.data ?? [];
    },
    staleTime: 60_000,
  });
}

export function useCreateQuoteWizardMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/quotes/wizard", payload);
      return data.data;
    },
    onSettled: () => {
      invalidateByDomain(queryClient, "quotes");
      void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.overview() });
    },
  });
}

export function useInvalidateQuoteQueries() {
  const queryClient = useQueryClient();
  return () => invalidateByDomain(queryClient, "quotes");
}
