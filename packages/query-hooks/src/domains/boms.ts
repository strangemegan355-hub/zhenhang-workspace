import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { queryKeys } from "../keys";

type ApiWrap<T> = { code: string; message: string; data: T };
type PageData = { items?: Record<string, unknown>[]; total?: number };

export function useBomQuery(bomId: string | null) {
  return useQuery({
    queryKey: queryKeys.boms.detail(bomId ?? ""),
    enabled: Boolean(bomId),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>>>(`/api/v1/boms/${bomId}`);
      return data.data;
    },
  });
}

export function useBomItemsQuery(bomId: string | null, page = 1) {
  return useQuery({
    queryKey: queryKeys.boms.items(bomId ?? "", page),
    enabled: Boolean(bomId),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/boms/items", {
        params: { bom_id: bomId, page, page_size: 200 },
      });
      return data.data;
    },
  });
}
