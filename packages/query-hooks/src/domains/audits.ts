import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";

type ApiWrap<T> = { code: string; message: string; data: T };

export type AuditRow = {
  id: string;
  module: string;
  action: string;
  resource_type: string;
  resource_id: string;
  detail: string;
  user_name: string;
  created_at: string;
};

const AUDITS = qk("platform", "audits");

export type AuditPage = { items: AuditRow[]; total: number };

/**
 * Audit log page. Reading it needs `platform:audit:read`, which no trial role may hold, so this is
 * only ever reachable by the bootstrap superuser.
 */
export function useAuditsQuery(page = 1, keyword?: string, moduleFilter?: string) {
  return useQuery({
    queryKey: [...AUDITS, page, keyword ?? "", moduleFilter ?? ""],
    queryFn: async (): Promise<AuditPage> => {
      const { data } = await apiClient.get<ApiWrap<{ items?: AuditRow[]; total?: number }>>(
        "/api/v1/audits",
        {
          params: {
            page,
            page_size: 20,
            q: keyword || undefined,
            module: moduleFilter || undefined,
          },
        },
      );
      return { items: data.data?.items ?? [], total: data.data?.total ?? 0 };
    },
    staleTime: 15_000,
  });
}
