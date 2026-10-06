import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";

type ApiWrap<T> = { code: string; message: string; data: T };

export type AcceptanceTemplate = {
  id: string;
  machine_id: string | null;
  name: string;
  template_type: string;
  items: unknown[] | null;
  created_at: string;
};

export type AcceptanceRecord = {
  id: string;
  equipment_unit_id: string;
  template_id: string | null;
  record_no: string;
  inspector_name: string | null;
  test_date: string | null;
  overall_result: string | null;
  status: string;
  remarks: string | null;
  items: unknown[] | null;
  punch_items: unknown[] | null;
  created_at: string;
};

const TEMPLATES = qk("acceptance", "templates");
const RECORDS = qk("acceptance", "records");
const RECORD_DETAIL = qk("acceptance", "record-detail");

/** The templates of one machine. */
export function useAcceptanceTemplatesQuery(machineId?: string) {
  return useQuery({
    queryKey: [...TEMPLATES, machineId ?? ""],
    enabled: Boolean(machineId),
    queryFn: async (): Promise<AcceptanceTemplate[]> => {
      const { data } = await apiClient.get<ApiWrap<AcceptanceTemplate[]>>(
        `/api/v1/machines/${machineId}/acceptance-templates`,
      );
      return data.data ?? [];
    },
    staleTime: 20_000,
  });
}

/** The acceptance records of one equipment unit. */
export function useAcceptanceRecordsQuery(unitId?: string) {
  return useQuery({
    queryKey: [...RECORDS, unitId ?? ""],
    enabled: Boolean(unitId),
    queryFn: async (): Promise<AcceptanceRecord[]> => {
      const { data } = await apiClient.get<ApiWrap<AcceptanceRecord[]>>(
        `/api/v1/equipment-units/${unitId}/acceptance-records`,
      );
      return data.data ?? [];
    },
    staleTime: 20_000,
  });
}

/** One record, including its punch items, for the detail panel. */
export function useAcceptanceRecordQuery(recordId?: string) {
  return useQuery({
    queryKey: [...RECORD_DETAIL, recordId ?? ""],
    enabled: Boolean(recordId),
    queryFn: async (): Promise<AcceptanceRecord> => {
      const { data } = await apiClient.get<ApiWrap<AcceptanceRecord>>(
        `/api/v1/acceptance-records/${recordId}`,
      );
      return data.data;
    },
  });
}

/** Imperative reads for prefilling the edit forms, which are not rendering queries. */
export async function fetchAcceptanceTemplate(templateId: string): Promise<AcceptanceTemplate> {
  const { data } = await apiClient.get<ApiWrap<AcceptanceTemplate>>(
    `/api/v1/acceptance-templates/${templateId}`,
  );
  return data.data;
}

export async function fetchAcceptanceRecord(recordId: string): Promise<AcceptanceRecord> {
  const { data } = await apiClient.get<ApiWrap<AcceptanceRecord>>(
    `/api/v1/acceptance-records/${recordId}`,
  );
  return data.data;
}

function invalidateTemplates(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({ queryKey: TEMPLATES });
}

function invalidateRecords(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({ queryKey: RECORDS });
  void queryClient.invalidateQueries({ queryKey: RECORD_DETAIL });
}

export function useCreateAcceptanceTemplateMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      machineId,
      payload,
    }: {
      machineId: string;
      payload: Record<string, unknown>;
    }) => {
      const { data } = await apiClient.post<ApiWrap<AcceptanceTemplate>>(
        `/api/v1/machines/${machineId}/acceptance-templates`,
        payload,
      );
      return data.data;
    },
    onSuccess: () => invalidateTemplates(queryClient),
  });
}

export function useUpdateAcceptanceTemplateMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      templateId,
      payload,
    }: {
      templateId: string;
      payload: Record<string, unknown>;
    }) => {
      const { data } = await apiClient.put<ApiWrap<AcceptanceTemplate>>(
        `/api/v1/acceptance-templates/${templateId}`,
        payload,
      );
      return data.data;
    },
    onSuccess: () => invalidateTemplates(queryClient),
  });
}

export function useDeleteAcceptanceTemplateMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (templateId: string) => {
      await apiClient.delete(`/api/v1/acceptance-templates/${templateId}`);
    },
    onSuccess: () => invalidateTemplates(queryClient),
  });
}

export function useCreateAcceptanceRecordMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      unitId,
      payload,
    }: {
      unitId: string;
      payload: Record<string, unknown>;
    }) => {
      const { data } = await apiClient.post<ApiWrap<AcceptanceRecord>>(
        `/api/v1/equipment-units/${unitId}/acceptance-records`,
        payload,
      );
      return data.data;
    },
    onSuccess: () => invalidateRecords(queryClient),
  });
}

export function useUpdateAcceptanceRecordMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      recordId,
      payload,
    }: {
      recordId: string;
      payload: Record<string, unknown>;
    }) => {
      const { data } = await apiClient.put<ApiWrap<AcceptanceRecord>>(
        `/api/v1/acceptance-records/${recordId}`,
        payload,
      );
      return data.data;
    },
    onSuccess: () => invalidateRecords(queryClient),
  });
}

export function useDeleteAcceptanceRecordMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (recordId: string) => {
      await apiClient.delete(`/api/v1/acceptance-records/${recordId}`);
    },
    onSuccess: () => invalidateRecords(queryClient),
  });
}

export function useCreatePunchItemMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      recordId,
      payload,
    }: {
      recordId: string;
      payload: Record<string, unknown>;
    }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>(
        `/api/v1/acceptance-records/${recordId}/punch-items`,
        payload,
      );
      return data.data;
    },
    onSuccess: () => invalidateRecords(queryClient),
  });
}

export function useUpdatePunchItemMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      itemId,
      payload,
    }: {
      itemId: string;
      payload: Record<string, unknown>;
    }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(
        `/api/v1/punch-items/${itemId}`,
        payload,
      );
      return data.data;
    },
    onSuccess: () => invalidateRecords(queryClient),
  });
}

export function useDeletePunchItemMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (itemId: string) => {
      await apiClient.delete(`/api/v1/punch-items/${itemId}`);
    },
    onSuccess: () => invalidateRecords(queryClient),
  });
}
