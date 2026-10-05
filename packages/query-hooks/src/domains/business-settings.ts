import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";

type ApiWrap<T> = { code: string; message: string; data: T };

export type BusinessSettings = {
  company_name: string;
  company_phone?: string | null;
  company_address?: string | null;
  company_email?: string | null;
  company_remark?: string | null;
  export_footer?: string | null;
  default_currency: string;
  default_scrap_rate: number;
  default_overhead_rate: number;
  default_profit_rate: number;
  default_tax_rate: number;
  accounting_enabled?: boolean;
  quote_receivable_enabled?: boolean;
  procurement_approval_enabled?: boolean;
  sales_max_discount_rate_pct?: number;
};

export function useBusinessSettingsQuery() {
  return useQuery({
    queryKey: qk("business", "settings"),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<BusinessSettings>>("/api/v1/business-settings");
      return data.data;
    },
    staleTime: 30_000,
  });
}

export function useUpdateBusinessSettingsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: Partial<BusinessSettings>) => {
      const { data } = await apiClient.put<ApiWrap<BusinessSettings>>("/api/v1/business-settings", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("business", "settings") });
    },
  });
}
