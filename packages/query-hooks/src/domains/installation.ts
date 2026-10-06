import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";

type ApiWrap<T> = { code: string; message: string; data: T };

export type InstallationPlan = {
  id: string;
  equipment_unit_id: string;
  status: string;
  planned_start_date: string | null;
  planned_end_date: string | null;
  actual_start_date: string | null;
  actual_end_date: string | null;
  customer_accepted: boolean | null;
  customer_accepted_date: string | null;
  customer_representative: string | null;
  remarks: string | null;
  install_items: unknown[] | null;
  commissioning_items: unknown[] | null;
  created_at: string;
};


const PLANS = qk("installation", "plans");

/** The plans of one equipment unit. */
export function useInstallationPlansQuery(unitId?: string) {
  return useQuery({
    queryKey: [...PLANS, unitId ?? ""],
    enabled: Boolean(unitId),
    queryFn: async (): Promise<InstallationPlan[]> => {
      const { data } = await apiClient.get<ApiWrap<InstallationPlan[]>>(
        `/api/v1/equipment-units/${unitId}/installation-plans`,
      );
      return data.data ?? [];
    },
    staleTime: 20_000,
  });
}

/** One plan, for the detail panel. */
export function useInstallationPlanQuery(planId?: string) {
  return useQuery({
    queryKey: [...PLANS, "detail", planId ?? ""],
    enabled: Boolean(planId),
    queryFn: async (): Promise<InstallationPlan> => {
      const { data } = await apiClient.get<ApiWrap<InstallationPlan>>(
        `/api/v1/installation-plans/${planId}`,
      );
      return data.data;
    },
  });
}

/**
 * Read one plan imperatively, for prefilling the edit form.
 *
 * A read is not a mutation, so this is a plain function rather than a fake `useMutation`; the point
 * is that the endpoint stays in this module and the page never touches `apiClient`.
 */
export async function fetchInstallationPlan(planId: string): Promise<InstallationPlan> {
  const { data } = await apiClient.get<ApiWrap<InstallationPlan>>(
    `/api/v1/installation-plans/${planId}`,
  );
  return data.data;
}

function invalidate(queryClient: ReturnType<typeof useQueryClient>, unitId?: string) {
  void queryClient.invalidateQueries({ queryKey: PLANS });
  if (unitId) {
    void queryClient.invalidateQueries({ queryKey: [...PLANS, unitId] });
  }
}

export function useCreateInstallationPlanMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      unitId,
      payload,
    }: {
      unitId: string;
      payload: Record<string, unknown>;
    }) => {
      const { data } = await apiClient.post<ApiWrap<InstallationPlan>>(
        `/api/v1/equipment-units/${unitId}/installation-plans`,
        payload,
      );
      return data.data;
    },
    onSuccess: (_data, variables) => invalidate(queryClient, variables.unitId),
  });
}

export function useUpdateInstallationPlanMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      planId,
      payload,
    }: {
      planId: string;
      payload: Record<string, unknown>;
    }) => {
      const { data } = await apiClient.put<ApiWrap<InstallationPlan>>(
        `/api/v1/installation-plans/${planId}`,
        payload,
      );
      return data.data;
    },
    onSuccess: () => invalidate(queryClient),
  });
}

export function useDeleteInstallationPlanMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (planId: string) => {
      await apiClient.delete(`/api/v1/installation-plans/${planId}`);
    },
    onSuccess: () => invalidate(queryClient),
  });
}
