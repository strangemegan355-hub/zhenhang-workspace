import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";
import type { PageData } from "../types";

type ApiWrap<T> = { code: string; message: string; data: T };

export function useEquipmentUnitsQuery(
  page = 1,
  pageSize = 20,
  q?: string,
  buildStatus?: string,
  machineId?: string,
  customerId?: string,
) {
  return useQuery({
    queryKey: qk("master", "equipment-units", { page, pageSize, q, buildStatus, machineId, customerId }),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/equipment-units", {
        params: {
          page,
          page_size: pageSize,
          ...(q ? { q } : {}),
          ...(buildStatus ? { build_status: buildStatus } : {}),
          ...(machineId ? { machine_id: machineId } : {}),
          ...(customerId ? { customer_id: customerId } : {}),
        },
      });
      return data.data;
    },
    staleTime: 30_000,
  });
}

export function useEquipmentUnitDetailQuery(id: string) {
  return useQuery({
    queryKey: qk("master", "equipment-unit-detail", id),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>>>(`/api/v1/equipment-units/${id}`);
      return data.data;
    },
    enabled: Boolean(id),
    staleTime: 30_000,
  });
}

export function useCreateEquipmentUnitMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/equipment-units", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "equipment-units") });
    },
  });
}

export function useUpdateEquipmentUnitMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, body }: { id: string; body: Record<string, unknown> }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(`/api/v1/equipment-units/${id}`, body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "equipment-units") });
    },
  });
}

export function useAdvanceEquipmentStatusMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, newStatus }: { id: string; newStatus: string }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        `/api/v1/equipment-units/${id}/advance-status`,
        undefined,
        { params: { new_status: newStatus } },
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "equipment-units") });
    },
  });
}
