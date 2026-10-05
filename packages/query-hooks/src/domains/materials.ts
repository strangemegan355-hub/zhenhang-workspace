import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";
import { queryKeys } from "../keys";

type ApiWrap<T> = { code: string; message: string; data: T };
type PageData = { items?: Record<string, unknown>[]; total?: number };

export function useMaterialsQuery(page = 1, q?: string, categoryId?: string) {
  return useQuery({
    queryKey: queryKeys.master.materials(page, q, categoryId),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/materials", {
        params: { page, page_size: 100, q, category_id: categoryId || undefined },
      });
      return data.data;
    },
    staleTime: 60_000,
  });
}

export function useCreateMaterialMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      code: string;
      name: string;
      spec?: string;
      unit?: string;
      reference_price?: number;
      category_id?: string;
      category?: string;
      remark?: string;
    }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/materials", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "materials") });
    },
  });
}

export function useDeleteMaterialMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(`/api/v1/materials/${id}`);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "materials") });
    },
  });
}
