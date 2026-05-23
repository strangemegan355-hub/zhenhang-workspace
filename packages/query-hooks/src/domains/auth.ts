import { useMutation, useQuery } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { getQueryPolicy } from "@zhenhang/query-policy-registry";
import { queryKeys } from "../keys";

type ApiWrap<T> = { code: string; message: string; data: T };
type LoginResp = { access_token: string; refresh_token: string; token_type: string };

export function useLoginMutation() {
  return useMutation({
    mutationFn: async (payload: { username: string; password: string }) => {
      const { data } = await apiClient.post<ApiWrap<LoginResp>>("/api/v1/auth/login", payload);
      return data.data;
    },
  });
}

export function useCurrentUserQuery(enabled: boolean) {
  const policy = getQueryPolicy("auth");
  return useQuery({
    queryKey: queryKeys.auth.currentUser(),
    enabled,
    staleTime: policy.staleTimeMs,
    gcTime: policy.gcTimeMs,
    retry: policy.retry,
    refetchOnWindowFocus: policy.refetchOnWindowFocus,
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>>>("/api/v1/users/me");
      return data.data;
    },
  });
}
