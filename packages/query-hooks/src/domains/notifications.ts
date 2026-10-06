import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import {
  getQueryPolicy,
  invalidateByDomain,
  optimisticWithPolicy,
} from "@zhenhang/query-policy-registry";
import { queryKeys } from "../keys";
import type { PageData } from "../types";

type ApiWrap<T> = { code: string; message: string; data: T };

export function useNotificationsQuery(params: {
  page: number;
  keyword?: string;
  unreadOnly?: boolean;
  status?: string;
}) {
  const policy = getQueryPolicy("notifications");
  return useQuery({
    queryKey: queryKeys.notifications.list(params),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/notifications", {
        params: {
          page: params.page,
          q: params.keyword,
          unread_only: params.unreadOnly,
          status: params.status,
        },
      });
      return data.data;
    },
    staleTime: policy.staleTimeMs,
    gcTime: policy.gcTimeMs,
    retry: policy.retry,
    refetchInterval: policy.refetchIntervalMs,
  });
}

export function useNotificationUnreadCountQuery() {
  const policy = getQueryPolicy("notifications");
  return useQuery({
    queryKey: queryKeys.notifications.unreadCount(),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<{ unread: number }>>("/api/v1/notifications/unread-count");
      return data.data.unread;
    },
    staleTime: policy.staleTimeMs,
    refetchInterval: policy.refetchIntervalMs,
  });
}

export function useMarkNotificationReadMutation(params: {
  page: number;
  keyword?: string;
  unreadOnly?: boolean;
}) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.patch<ApiWrap<Record<string, unknown>>>(
        `/api/v1/notifications/${id}/read`,
      );
      return data.data;
    },
    onMutate: async (id: string) => {
      const key = queryKeys.notifications.list(params);
      const rollback = await optimisticWithPolicy<Record<string, unknown>>({
        queryClient,
        key,
        mutationKey: "notifications.markRead",
        updater: (old) => {
          const items = ((old?.items as Record<string, unknown>[] | undefined) ?? []).map((item) =>
            String(item.id) === id
              ? { ...item, status: "read", read_at: new Date().toISOString() }
              : item,
          );
          return { ...(old ?? {}), items };
        },
      });
      return { rollback };
    },
    onError: (_error, _id, ctx) => {
      ctx?.rollback?.();
    },
    onSettled: () => {
      invalidateByDomain(queryClient, "notifications");
    },
  });
}
