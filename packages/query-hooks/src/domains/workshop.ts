import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { queryKeys } from "../keys";

type ApiWrap<T> = { code: string; message: string; data: T };

export function useWorkshopBoardQuery(enabled = true) {
  return useQuery({
    queryKey: queryKeys.workshop.board(),
    enabled,
    refetchInterval: 60_000,
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>>>("/api/v1/workshop/board");
      return data.data;
    },
  });
}
