import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { queryKeys } from "../keys";

type ApiWrap<T> = { code: string; message: string; data: T };

export type WorkflowAction = {
  action_code: string;
  action_name: string;
  from_state: string;
  to_state: string | null;
};

export function useWorkflowActionsQuery(params: { entityType: string; currentState: string }) {
  return useQuery({
    queryKey: queryKeys.workflow.actions(params.entityType, params.currentState),
    enabled: Boolean(params.entityType && params.currentState),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<WorkflowAction[]>>("/api/v1/workflows/actions", {
        params: { entity_type: params.entityType, current_state: params.currentState },
      });
      return data.data ?? [];
    },
  });
}
