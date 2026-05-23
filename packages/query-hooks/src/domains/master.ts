import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { queryKeys } from "../keys";

type ApiWrap<T> = { code: string; message: string; data: T };
type PageData = { items?: Record<string, unknown>[]; total?: number };

export function useCustomersQuery(page = 1, q?: string) {
  return useQuery({
    queryKey: queryKeys.master.customers(page, q),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/customers", {
        params: { page, page_size: 50, q },
      });
      return data.data;
    },
    staleTime: 60_000,
  });
}

export function useMachinesQuery(page = 1, q?: string) {
  return useQuery({
    queryKey: queryKeys.master.machines(page, q),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/machines", {
        params: { page, page_size: 50, q },
      });
      return data.data;
    },
    staleTime: 60_000,
  });
}

export function useBomsListQuery(page = 1, q?: string) {
  return useQuery({
    queryKey: queryKeys.master.boms(page, q),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/boms", {
        params: { page, page_size: 50, q },
      });
      return data.data;
    },
    staleTime: 60_000,
  });
}

export function useApprovalTemplatesQuery(page = 1) {
  return useQuery({
    queryKey: queryKeys.master.approvalTemplates(page),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/quotes/approval-templates", {
        params: { page, page_size: 50 },
      });
      return data.data;
    },
    staleTime: 60_000,
  });
}
