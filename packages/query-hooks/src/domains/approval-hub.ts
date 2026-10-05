import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";

type ApiWrap<T> = { code: string; message: string; data: T };

export type ApprovalTask = {
  id: string;
  task_type: string;
  title: string;
  subtitle?: string | null;
  amount?: number | string | null;
  discount_amount?: number | string | null;
  discount_rate_pct?: number | string | null;
  submitter_name?: string | null;
  submitted_at: string;
  status: string;
  source_id?: string | null;
  source_no?: string | null;
  detail_href?: string | null;
  can_approve: boolean;
};

export type ApprovalInbox = {
  total: number;
  items: ApprovalTask[];
};

export function useApprovalInboxQuery(enabled = true) {
  return useQuery({
    queryKey: qk("approvals", "inbox"),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<ApprovalInbox>>("/api/v1/approvals/inbox");
      return data.data;
    },
    enabled,
    staleTime: 10_000,
    refetchInterval: 30_000,
  });
}

export function useApprovalActionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      task_type: string;
      task_id: string;
      action: "approve" | "reject";
      comment?: string;
    }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/approvals/action", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("approvals", "inbox") });
      void queryClient.invalidateQueries({ queryKey: ["accounting"] });
      void queryClient.invalidateQueries({ queryKey: ["quotes"] });
      void queryClient.invalidateQueries({ queryKey: qk("procurement", "list") });
    },
  });
}
