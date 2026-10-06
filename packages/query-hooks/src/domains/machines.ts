import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";
import { queryKeys } from "../keys";
import type { PageData } from "../types";

type ApiWrap<T> = { code: string; message: string; data: T };

export function useMachinesQuery(page = 1, q?: string, pageSize = 50) {
  return useQuery({
    queryKey: queryKeys.master.machines(page, q, pageSize),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/machines", {
        params: { page, page_size: pageSize, q },
      });
      return data.data;
    },
    staleTime: 60_000,
  });
}

export function useCreateMachineMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      category_id?: string;
      code: string;
      name: string;
      model_no?: string;
      status?: string;
      description?: string;
    }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/machines", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "machines") });
    },
  });
}

export function useUpdateMachineMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      body,
    }: {
      id: string;
      body: {
        category_id?: string | null;
        code?: string;
        name?: string;
        model_no?: string;
        status?: string;
        description?: string;
      };
    }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(`/api/v1/machines/${id}`, body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "machines") });
    },
  });
}

export function useDeleteMachineMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(`/api/v1/machines/${id}`);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "machines") });
    },
  });
}

export function useMachineCategoriesQuery(page = 1, q?: string) {
  return useQuery({
    queryKey: queryKeys.master.machineCategories(page, q),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/machines/categories", {
        params: { page, page_size: 100, q },
      });
      return data.data;
    },
    staleTime: 60_000,
  });
}

export function useCreateMachineCategoryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { code: string; name: string; description?: string }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        "/api/v1/machines/categories",
        body,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "machine-categories") });
    },
  });
}

export function useUpdateMachineCategoryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      body,
    }: {
      id: string;
      body: { code?: string; name?: string; description?: string };
    }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(
        `/api/v1/machines/categories/${id}`,
        body,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "machine-categories") });
    },
  });
}

export function useDeleteMachineCategoryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(
        `/api/v1/machines/categories/${id}`,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "machine-categories") });
    },
  });
}

export function useMachineParametersQuery(page = 1, machineId?: string, q?: string) {
  return useQuery({
    queryKey: queryKeys.master.machineParameters(page, machineId, q),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/machines/parameters", {
        params: { page, page_size: 100, q, machine_id: machineId || undefined },
      });
      return data.data;
    },
    enabled: Boolean(machineId),
    staleTime: 30_000,
  });
}

export function useCreateMachineParameterMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      machine_id: string;
      param_key: string;
      param_name: string;
      value?: string;
      unit?: string;
      sort_order?: number;
      remarks?: string;
    }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        "/api/v1/machines/parameters",
        body,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "machine-parameters") });
    },
  });
}

export function useUpdateMachineParameterMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      body,
    }: {
      id: string;
      body: {
        param_key?: string;
        param_name?: string;
        value?: string;
        unit?: string;
        sort_order?: number;
        remarks?: string;
      };
    }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(
        `/api/v1/machines/parameters/${id}`,
        body,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "machine-parameters") });
    },
  });
}

export function useDeleteMachineParameterMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(
        `/api/v1/machines/parameters/${id}`,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "machine-parameters") });
    },
  });
}

export function useMachineImagesQuery(page = 1, machineId?: string, q?: string) {
  return useQuery({
    queryKey: queryKeys.master.machineImages(page, machineId, q),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/machines/images", {
        params: { page, page_size: 100, q, machine_id: machineId || undefined },
      });
      return data.data;
    },
    enabled: Boolean(machineId),
    staleTime: 30_000,
  });
}

export function useCreateMachineImageMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      machine_id: string;
      file_url: string;
      file_name?: string;
      sort_order?: number;
    }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        "/api/v1/machines/images",
        body,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "machine-images") });
    },
  });
}

export function useUpdateMachineImageMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      body,
    }: {
      id: string;
      body: { file_url?: string; file_name?: string; sort_order?: number };
    }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(
        `/api/v1/machines/images/${id}`,
        body,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "machine-images") });
    },
  });
}

export function useDeleteMachineImageMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(
        `/api/v1/machines/images/${id}`,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "machine-images") });
    },
  });
}

export function useMachinePricingProfileQuery(machineId?: string) {
  return useQuery({
    queryKey: qk("master", "machine-pricing", machineId),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>>>(
        `/api/v1/machines/${machineId}/pricing-profile`,
      );
      return data.data;
    },
    enabled: Boolean(machineId),
    staleTime: 60_000,
  });
}
