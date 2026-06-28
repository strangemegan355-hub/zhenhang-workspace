import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";

type ApiWrap<T> = { code: string; message: string; data: T };

export type OptionGroup = {
  id: string;
  machine_id: string;
  name: string;
  sort_order?: number;
  items?: OptionItem[];
};

export type OptionItem = {
  id: string;
  group_id: string;
  name: string;
  price_adjustment: number;
  sort_order?: number;
};

export function useOptionGroupsQuery(machineId: string | null, enabled = true) {
  return useQuery({
    queryKey: ["option-groups", machineId],
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<OptionGroup[]>>(
        `/api/v1/machines/${machineId}/option-groups`
      );
      return data.data ?? [];
    },
    enabled: !!machineId && enabled,
  });
}

export function useCreateOptionGroupMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ machineId, name }: { machineId: string; name: string }) => {
      const { data } = await apiClient.post<ApiWrap<OptionGroup>>(
        `/api/v1/machines/${machineId}/option-groups`,
        { name }
      );
      return data.data;
    },
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({ queryKey: ["option-groups", vars.machineId] });
    },
  });
}

export function useDeleteOptionGroupMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (groupId: string) => {
      await apiClient.delete(`/api/v1/option-groups/${groupId}`);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["option-groups"] });
    },
  });
}

export function useCreateOptionItemMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ groupId, name, priceAdjustment }: { groupId: string; name: string; priceAdjustment: number }) => {
      const { data } = await apiClient.post<ApiWrap<OptionItem>>(
        `/api/v1/option-groups/${groupId}/items`,
        { name, price_adjustment: priceAdjustment }
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["option-groups"] });
    },
  });
}

export function useDeleteOptionItemMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (itemId: string) => {
      await apiClient.delete(`/api/v1/option-items/${itemId}`);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["option-groups"] });
    },
  });
}
