import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";

type ApiWrap<T> = { code: string; message: string; data: T };
type PageData = { items?: Record<string, unknown>[]; total?: number; page?: number; page_size?: number };

export type AftersalesRequest = {
  id: string;
  request_no: string;
  title: string;
  customer_id: string;
  customer_name?: string | null;
  equipment_unit_id?: string | null;
  equipment_serial?: string | null;
  status: string;
  priority: string;
  description?: string | null;
  assigned_to?: string | null;
  assignee_name?: string | null;
  scheduled_date?: string | null;
  completed_date?: string | null;
  resolution?: string | null;
  created_at: string;
  updated_at: string;
};

export type AftersalesCreatePayload = {
  title: string;
  customer_id: string;
  equipment_unit_id?: string;
  priority?: string;
  description?: string;
  assigned_to?: string;
  scheduled_date?: string;
};

export type AftersalesUpdatePayload = {
  title?: string;
  priority?: string;
  status?: string;
  description?: string;
  assigned_to?: string;
  scheduled_date?: string;
  resolution?: string;
};

export function useAftersalesQuery(
  page = 1,
  filters?: { customerId?: string; status?: string; priority?: string; assignedTo?: string },
  enabled = true,
) {
  return useQuery({
    queryKey: ["aftersales", "list", page, filters],
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/aftersales", {
        params: { page, page_size: 20, customer_id: filters?.customerId, status: filters?.status, priority: filters?.priority, assigned_to: filters?.assignedTo },
      });
      return data.data;
    },
    enabled,
    staleTime: 15_000,
  });
}

export function useAftersalesDetailQuery(id: string | null, enabled = true) {
  return useQuery({
    queryKey: ["aftersales", "detail", id],
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<AftersalesRequest>>(`/api/v1/aftersales/${id}`);
      return data.data;
    },
    enabled: !!id && enabled,
  });
}

export function useCreateAftersalesMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: AftersalesCreatePayload) => {
      const { data } = await apiClient.post<ApiWrap<AftersalesRequest>>("/api/v1/aftersales", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["aftersales"] });
    },
  });
}

export function useUpdateAftersalesMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: string; body: AftersalesUpdatePayload }) => {
      const { data } = await apiClient.put<ApiWrap<AftersalesRequest>>(`/api/v1/aftersales/${id}`, body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["aftersales"] });
    },
  });
}

export function useDeleteAftersalesMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/api/v1/aftersales/${id}`);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["aftersales"] });
    },
  });
}
