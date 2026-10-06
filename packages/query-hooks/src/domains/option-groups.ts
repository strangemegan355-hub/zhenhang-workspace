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
  // The backend's `OptionItemRead` declares `option_group_id`; this said `group_id`, which the API never sends.
  // Nothing reads either name today, so the mismatch was latent rather than a runtime bug — but the type was a lie,
  // and it was the only field in the whole hook layer that the response model does not provide.
  option_group_id: string;
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
    mutationFn: async ({
      machineId,
      name,
      sortOrder = 0,
    }: {
      machineId: string;
      name: string;
      sortOrder?: number;
    }) => {
      const { data } = await apiClient.post<ApiWrap<OptionGroup>>(
        `/api/v1/machines/${machineId}/option-groups`,
        { name, sort_order: sortOrder }
      );
      return data.data;
    },
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({ queryKey: ["option-groups", vars.machineId] });
    },
  });
}

export function useUpdateOptionGroupMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ groupId, name, sortOrder = 0 }: { groupId: string; name: string; sortOrder?: number }) => {
      const { data } = await apiClient.put<ApiWrap<OptionGroup>>(`/api/v1/option-groups/${groupId}`, {
        name,
        sort_order: sortOrder,
      });
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["option-groups"] });
    },
  });
}

export function useUpdateOptionItemMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      itemId,
      name,
      priceAdjustment,
      sortOrder = 0,
    }: {
      itemId: string;
      name: string;
      priceAdjustment: number;
      sortOrder?: number;
    }) => {
      const { data } = await apiClient.put<ApiWrap<OptionItem>>(`/api/v1/option-items/${itemId}`, {
        name,
        price_adjustment: priceAdjustment,
        sort_order: sortOrder,
      });
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["option-groups"] });
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
    mutationFn: async ({
      groupId,
      name,
      priceAdjustment,
      sortOrder = 0,
    }: {
      groupId: string;
      name: string;
      priceAdjustment: number;
      sortOrder?: number;
    }) => {
      const { data } = await apiClient.post<ApiWrap<OptionItem>>(
        `/api/v1/option-groups/${groupId}/items`,
        { name, price_adjustment: priceAdjustment, sort_order: sortOrder }
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
