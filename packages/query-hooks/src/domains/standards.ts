import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";
import { queryKeys } from "../keys";
import type { PageData } from "../types";

type ApiWrap<T> = { code: string; message: string; data: T };

export function useUnitsQuery(page = 1, q?: string) {
  return useQuery({
    queryKey: queryKeys.master.units(page, q),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/units", {
        params: { page, page_size: 100, q },
      });
      return data.data;
    },
    staleTime: 60_000,
  });
}

export function useCreateUnitMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { code: string; name: string; remark?: string }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/units", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "units") });
    },
  });
}

export function useUpdateUnitMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: string; body: { code?: string; name?: string; remark?: string } }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(`/api/v1/units/${id}`, body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "units") });
    },
  });
}

export function useDeleteUnitMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(`/api/v1/units/${id}`);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "units") });
    },
  });
}

export function useMaterialCategoriesQuery(page = 1, q?: string) {
  return useQuery({
    queryKey: queryKeys.master.materialCategories(page, q),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/material-categories", {
        params: { page, page_size: 100, q },
      });
      return data.data;
    },
    staleTime: 60_000,
  });
}

export function useCreateMaterialCategoryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { code: string; name: string; parent_id?: string; scope?: string; remark?: string }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        "/api/v1/material-categories",
        body,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "material-categories") });
    },
  });
}

export function useUpdateMaterialCategoryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      body,
    }: {
      id: string;
      body: { code?: string; name?: string; parent_id?: string | null; scope?: string; remark?: string };
    }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(
        `/api/v1/material-categories/${id}`,
        body,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "material-categories") });
    },
  });
}

export function useDeleteMaterialCategoryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(
        `/api/v1/material-categories/${id}`,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "material-categories") });
    },
  });
}
