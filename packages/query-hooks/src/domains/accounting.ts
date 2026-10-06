import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";
import { queryKeys } from "../keys";

type ApiWrap<T> = { code: string; message: string; data: T };
type PageData = { items?: Record<string, unknown>[]; total?: number; page?: number; page_size?: number };

export type AccountingFeatureFlags = {
  accounting_enabled: boolean;
  quote_receivable_enabled: boolean;
  procurement_approval_enabled: boolean;
};

export type AccountingModuleStatus = {
  module: string;
  schema_version: string;
  flags: AccountingFeatureFlags;
  entry_count: number;
};

export type AccountingEntryPayload = {
  entry_kind: string;
  customer_id?: string;
  supplier_id?: string;
  project_id?: string;
  amount: number;
  occurred_on: string;
  due_date?: string;
  title: string;
  remark?: string;
  is_backfill?: boolean;
};

export type AccountingEntry = {
  id: string;
  entry_no: string;
  entry_kind: string;
  status: string;
  customer_id?: string | null;
  supplier_id?: string | null;
  amount: number | string;
  occurred_on: string;
  due_date?: string | null;
  booked_on: string;
  is_backfill: boolean;
  title: string;
  remark?: string | null;
};

export type QuoteReceivableRequest = {
  id: string;
  quote_id: string;
  requested_amount: number | string;
  standard_amount: number | string;
  discount_amount: number | string;
  discount_rate_pct: number | string;
  needs_boss_approval: boolean;
  approval_status: string;
  receivable_entry_id?: string | null;
  reject_reason?: string | null;
};

export function useQuoteReceivableRequestQuery(quoteId: string | null, enabled = true) {
  return useQuery({
    queryKey: queryKeys.accounting.quoteReceivableByQuote(quoteId ?? ""),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<QuoteReceivableRequest | null>>(
        `/api/v1/accounting/quote-receivable-requests/by-quote/${quoteId}`,
      );
      return data.data;
    },
    enabled: enabled && Boolean(quoteId),
    staleTime: 10_000,
  });
}

export function useQuoteReceivableRequestsQuery(page = 1, approvalStatus?: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.accounting.quoteReceivableRequests(page, approvalStatus),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/accounting/quote-receivable-requests", {
        params: { page, page_size: 20, approval_status: approvalStatus || undefined },
      });
      return data.data;
    },
    enabled,
    staleTime: 10_000,
  });
}

export function useCreateQuoteReceivableRequestMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (quoteId: string) => {
      const { data } = await apiClient.post<ApiWrap<QuoteReceivableRequest>>(
        `/api/v1/accounting/quote-receivable-requests/from-quote/${quoteId}`,
      );
      return data.data;
    },
    onSuccess: (_data, quoteId) => {
      void queryClient.invalidateQueries({ queryKey: qk("accounting", "quote-receivable-by-quote", quoteId) });
      void queryClient.invalidateQueries({ queryKey: qk("accounting", "quote-receivable-requests") });
    },
  });
}

export function useApproveQuoteReceivableMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (requestId: string) => {
      const { data } = await apiClient.post<ApiWrap<QuoteReceivableRequest>>(
        `/api/v1/accounting/quote-receivable-requests/${requestId}/approve`,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("accounting", "quote-receivable-requests") });
      void queryClient.invalidateQueries({ queryKey: qk("accounting", "quote-receivable-by-quote") });
    },
  });
}

export function useRejectQuoteReceivableMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ requestId, reason }: { requestId: string; reason?: string }) => {
      const { data } = await apiClient.post<ApiWrap<QuoteReceivableRequest>>(
        `/api/v1/accounting/quote-receivable-requests/${requestId}/reject`,
        { reason },
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("accounting", "quote-receivable-requests") });
      void queryClient.invalidateQueries({ queryKey: qk("accounting", "quote-receivable-by-quote") });
    },
  });
}

export function useConfirmQuoteReceivableMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (requestId: string) => {
      const { data } = await apiClient.post<ApiWrap<AccountingEntry>>(
        `/api/v1/accounting/quote-receivable-requests/${requestId}/confirm`,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("accounting", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("accounting", "quote-receivable-requests") });
      void queryClient.invalidateQueries({ queryKey: qk("accounting", "quote-receivable-by-quote") });
      void queryClient.invalidateQueries({ queryKey: qk("accounting", "status") });
      void queryClient.invalidateQueries({ queryKey: qk("quotes", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("quotes", "detail") });
    },
  });
}

export function useAccountingStatusQuery() {
  return useQuery({
    queryKey: queryKeys.accounting.status(),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<AccountingModuleStatus>>("/api/v1/accounting/status");
      return data.data;
    },
    staleTime: 15_000,
  });
}

export function useAccountingEntriesQuery(
  page = 1,
  filters?: { customerId?: string; supplierId?: string; entryKind?: string; includeVoid?: boolean; dateFrom?: string; dateTo?: string },
  enabled = true,
) {
  return useQuery({
    queryKey: queryKeys.accounting.list(page, filters?.customerId, filters?.supplierId, filters?.entryKind, filters?.includeVoid),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/accounting/entries", {
        params: {
          page,
          page_size: 20,
          customer_id: filters?.customerId || undefined,
          supplier_id: filters?.supplierId || undefined,
          entry_kind: filters?.entryKind || undefined,
          include_void: filters?.includeVoid || undefined,
          date_from: filters?.dateFrom || undefined,
          date_to: filters?.dateTo || undefined,
        },
      });
      return data.data;
    },
    enabled,
    staleTime: 15_000,
  });
}

export function useCreateAccountingEntryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: AccountingEntryPayload) => {
      const { data } = await apiClient.post<ApiWrap<AccountingEntry>>("/api/v1/accounting/entries", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["accounting"] });
    },
  });
}

export function useCreateBackfillEntryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: AccountingEntryPayload) => {
      const { data } = await apiClient.post<ApiWrap<AccountingEntry>>("/api/v1/accounting/entries/backfill", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["accounting"] });
      void queryClient.invalidateQueries({ queryKey: ["quotes"] });
    },
  });
}

export function useConfirmAccountingEntryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<ApiWrap<AccountingEntry>>(`/api/v1/accounting/entries/${id}/confirm`);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["accounting"] });
    },
  });
}

export function useVoidAccountingEntryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<ApiWrap<AccountingEntry>>(`/api/v1/accounting/entries/${id}/void`);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["accounting"] });
      void queryClient.invalidateQueries({ queryKey: ["quotes"] });
    },
  });
}

export type CustomerLedgerSummary = {
  customer_id: string;
  customer_name: string;
  customer_code?: string | null;
  receivable_total: number | string;
  received_total: number | string;
  outstanding_total: number | string;
  open_bill_count: number;
  last_occurred_on?: string | null;
  is_registered?: boolean;
};

export type LedgerEntry = {
  id: string;
  entry_no: string;
  entry_kind: string;
  status: string;
  amount: number | string;
  settled_amount: number | string;
  open_amount: number | string;
  payment_status?: string | null;
  source_type: string;
  source_label: string;
  source_no?: string | null;
  quote_id?: string | null;
  occurred_on: string;
  title: string;
  remark?: string | null;
  is_backfill: boolean;
  allocations?: { receivable_entry_id: string; receivable_entry_no?: string | null; amount: string }[];
};

export type CustomerLedgerDetail = {
  customer_id: string;
  customer_name?: string;
  customer_code?: string | null;
  receivable_total: number | string;
  received_total: number | string;
  outstanding_total: number | string;
  open_bill_count: number;
  receivables: LedgerEntry[];
  receipts: LedgerEntry[];
  timeline: LedgerEntry[];
  open_receivables: LedgerEntry[];
};

export type LedgerReceivablePayload = {
  amount: number;
  occurred_on: string;
  title: string;
  remark?: string;
  is_backfill?: boolean;
};

export type ReceiptAllocationPayload = {
  receivable_entry_id: string;
  amount: number;
};

export type ReceiptCreatePayload = {
  customer_id: string;
  amount: number;
  occurred_on: string;
  title: string;
  remark?: string;
  allocations: ReceiptAllocationPayload[];
};

export function useLedgerCustomersQuery(
  page = 1,
  filters?: { outstandingOnly?: boolean; q?: string },
  enabled = true,
) {
  return useQuery({
    queryKey: queryKeys.accounting.ledgerCustomers(page, filters?.outstandingOnly, filters?.q),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/accounting/ledger/customers", {
        params: {
          page,
          page_size: 20,
          outstanding_only: filters?.outstandingOnly || undefined,
          q: filters?.q || undefined,
        },
      });
      return data.data;
    },
    enabled,
    staleTime: 15_000,
  });
}

export function useCustomerLedgerDetailQuery(customerId: string | null, enabled = true) {
  return useQuery({
    queryKey: queryKeys.accounting.ledgerDetail(customerId ?? ""),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<CustomerLedgerDetail>>(
        `/api/v1/accounting/ledger/customers/${customerId}`,
      );
      return data.data;
    },
    enabled: enabled && Boolean(customerId),
    staleTime: 10_000,
  });
}

export function useCreateLedgerReceiptMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: ReceiptCreatePayload) => {
      const { data } = await apiClient.post<ApiWrap<AccountingEntry>>("/api/v1/accounting/ledger/receipts", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["accounting"] });
    },
  });
}

export function useRegisterLedgerCustomerMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (customerId: string) => {
      const { data } = await apiClient.post<ApiWrap<CustomerLedgerSummary>>("/api/v1/accounting/ledger/customers", {
        customer_id: customerId,
      });
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["accounting"] });
    },
  });
}

export function useCreateLedgerReceivableMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ customerId, body }: { customerId: string; body: LedgerReceivablePayload }) => {
      const { data } = await apiClient.post<ApiWrap<AccountingEntry>>(
        `/api/v1/accounting/ledger/customers/${customerId}/receivables`,
        body,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["accounting"] });
    },
  });
}

export function useCreateProcurementPayableRequestMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (entryId: string) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        `/api/v1/accounting/procurement-payable-requests/from-entry/${entryId}`,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["accounting"] });
      void queryClient.invalidateQueries({ queryKey: qk("procurement", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("approvals", "inbox") });
    },
  });
}

// ── Supplier ledger ──

export function useSupplierLedgerQuery(
  page = 1,
  filters?: { outstandingOnly?: boolean; q?: string },
  enabled = true,
) {
  return useQuery({
    queryKey: ["accounting", "supplier-ledger", page, filters?.outstandingOnly, filters?.q],
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/accounting/ledger/suppliers", {
        params: { page, page_size: 20, outstanding_only: filters?.outstandingOnly, q: filters?.q || undefined },
      });
      return data.data;
    },
    enabled,
    staleTime: 15_000,
  });
}

export function useSupplierLedgerDetailQuery(supplierId: string | null, enabled = true) {
  return useQuery({
    queryKey: ["accounting", "supplier-ledger-detail", supplierId],
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>>>(
        `/api/v1/accounting/ledger/suppliers/${supplierId}`,
      );
      return data.data;
    },
    enabled: !!supplierId && enabled,
  });
}

export function useRegisterSupplierLedgerMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (supplierId: string) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        "/api/v1/accounting/ledger/suppliers",
        { supplier_id: supplierId },
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["accounting"] });
    },
  });
}

export type SupplierPayablePayload = {
  amount: number;
  occurred_on: string;
  due_date?: string;
  title: string;
  remark?: string;
  is_backfill?: boolean;
};

export function useCreateSupplierPayableMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ supplierId, body }: { supplierId: string; body: SupplierPayablePayload }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        `/api/v1/accounting/ledger/suppliers/${supplierId}/payables`,
        body,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["accounting"] });
    },
  });
}

export type PaymentAllocation = {
  payable_entry_id: string;
  amount: number;
};

export type PaymentPayload = {
  supplier_id: string;
  amount: number;
  occurred_on: string;
  title: string;
  remark?: string;
  allocations: PaymentAllocation[];
};

export function useCreateSupplierPaymentMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: PaymentPayload) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        "/api/v1/accounting/ledger/payments",
        body,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["accounting"] });
    },
  });
}


export function useAccountingEntryQuery(entryId?: string) {
  return useQuery({
    queryKey: [...qk("accounting", "detail"), entryId ?? ""],
    enabled: Boolean(entryId),
    queryFn: async () => {
      const { data } = await apiClient.get<{ data: Record<string, unknown> }>(
        `/api/v1/accounting/entries/${entryId}`,
      );
      return data.data;
    },
  });
}

export function useUpdateAccountingEntryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      entryId,
      payload,
    }: {
      entryId: string;
      payload: Record<string, unknown>;
    }) => {
      const { data } = await apiClient.put<{ data: Record<string, unknown> }>(
        `/api/v1/accounting/entries/${entryId}`,
        payload,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("accounting", "list") });
      void queryClient.invalidateQueries({ queryKey: qk("accounting", "detail") });
    },
  });
}

export type AccountingExportFilters = {
  customerId?: string;
  supplierId?: string;
  entryKind?: string;
  dateFrom?: string;
  dateTo?: string;
};

export function useExportAccountingEntriesMutation() {
  return useMutation({
    mutationFn: async (filters: AccountingExportFilters) => {
      const { data } = await apiClient.get<Blob>("/api/v1/accounting/entries/export", {
        params: {
          customer_id: filters.customerId || undefined,
          supplier_id: filters.supplierId || undefined,
          entry_kind: filters.entryKind || undefined,
          date_from: filters.dateFrom || undefined,
          date_to: filters.dateTo || undefined,
        },
        responseType: "blob",
      });
      return data;
    },
  });
}
