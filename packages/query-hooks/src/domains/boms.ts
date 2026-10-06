import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";
import { queryKeys } from "../keys";
import type { PageData } from "../types";

type ApiWrap<T> = { code: string; message: string; data: T };

export function useBomQuery(bomId: string | null) {
  return useQuery({
    queryKey: queryKeys.boms.detail(bomId ?? ""),
    enabled: Boolean(bomId),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>>>(`/api/v1/boms/${bomId}`);
      return data.data;
    },
  });
}

export function useBomItemsQuery(bomId: string | null, page = 1) {
  return useQuery({
    queryKey: queryKeys.boms.items(bomId ?? "", page),
    enabled: Boolean(bomId),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/boms/items", {
        params: { bom_id: bomId, page, page_size: 100 },
      });
      return data.data;
    },
  });
}

export function useCreateBomMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      machine_id: string;
      version: string;
      is_active?: boolean;
      remark?: string;
      status?: string;
    }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/boms", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "boms") });
    },
  });
}

export function useCreateBomItemMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      bom_id: string;
      item_code: string;
      item_name: string;
      unit: string;
      quantity: number;
      unit_cost: number;
      spec?: string;
      remark?: string;
      subsystem?: string;
    }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/boms/items", body);
      return data.data;
    },
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: qk("boms", "items") });
      void queryClient.invalidateQueries({ queryKey: qk("master", "boms") });
      void queryClient.invalidateQueries({ queryKey: queryKeys.boms.detail(variables.bom_id) });
    },
  });
}

export function useImportBomItemsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      bom_id: string;
      items: Array<{
        item_code: string;
        item_name: string;
        unit: string;
        quantity: number;
        unit_cost: number;
      }>;
    }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>[]>>("/api/v1/boms/items/batch", {
        items: body.items.map((item) => ({
          bom_id: body.bom_id,
          ...item,
        })),
      });
      return data.data;
    },
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: qk("boms", "items") });
      void queryClient.invalidateQueries({ queryKey: qk("master", "boms") });
      void queryClient.invalidateQueries({ queryKey: queryKeys.boms.detail(variables.bom_id) });
    },
  });
}
