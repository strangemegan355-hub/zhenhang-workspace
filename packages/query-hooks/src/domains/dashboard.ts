import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { queryKeys } from "../keys";

type ApiWrap<T> = { code: string; message: string; data: T };

export function useDashboardOverviewQuery() {
  return useQuery({
    queryKey: queryKeys.dashboard.overview(),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>>>("/api/v1/dashboard/overview");
      return data.data;
    },
    refetchInterval: 60_000,
  });
}
