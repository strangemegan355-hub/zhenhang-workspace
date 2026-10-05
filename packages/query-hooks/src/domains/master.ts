import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";
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

export function useCreateCustomerMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      code: string;
      name: string;
      short_name?: string;
      industry?: string;
      level?: string;
      status?: string;
      phone?: string;
      email?: string;
      address?: string;
      remarks?: string;
    }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/customers", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "customers") });
    },
  });
}

export function useDeleteCustomerMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(`/api/v1/customers/${id}`);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "customers") });
    },
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
