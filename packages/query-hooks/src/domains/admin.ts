import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";
import type { PageData } from "../types";

type ApiWrap<T> = { code: string; message: string; data: T };

const USERS = qk("platform", "users");
const ROLES = qk("platform", "roles");
const PERMISSIONS = qk("platform", "permissions");
const DEPARTMENTS = qk("platform", "departments");
const TENANTS = qk("platform", "tenants");

// The admin plane: accounts, roles, the permission catalogue, departments and tenants. Every
// mutation invalidates its own list, so a page never shows a stale roster after a write.

export function useUsersQuery(page = 1, q?: string) {
  return useQuery({
    queryKey: [...USERS, page, q],
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/users", {
        params: { page, page_size: 50, q },
      });
      return data.data;
    },
    staleTime: 30_000,
  });
}

export function useCreateUserMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      username: string;
      password: string;
      email?: string;
      full_name?: string;
      phone?: string;
      department_id?: string;
      role_codes?: string[];
    }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/users", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: USERS });
    },
  });
}

export function useUpdateUserMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      ...body
    }: {
      id: string;
      email?: string;
      full_name?: string;
      phone?: string;
      department_id?: string;
      is_active?: boolean;
    }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(`/api/v1/users/${id}`, body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: USERS });
    },
  });
}

export function useSetUserRolesMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, roleCodes }: { id: string; roleCodes: string[] }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(`/api/v1/users/${id}/roles`, {
        role_codes: roleCodes,
      });
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: USERS });
    },
  });
}

export function useRolesQuery(page = 1, q?: string) {
  return useQuery({
    queryKey: [...ROLES, page, q],
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/roles", {
        params: { page, page_size: 50, q },
      });
      return data.data;
    },
    staleTime: 30_000,
  });
}

export function useCreateRoleMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { code: string; name: string; description?: string; data_scope?: string }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/roles", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ROLES });
    },
  });
}

export function useUpdateRoleMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      ...body
    }: {
      id: string;
      name?: string;
      description?: string;
      data_scope?: string;
    }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(`/api/v1/roles/${id}`, body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ROLES });
    },
  });
}

export function useSetRolePermissionsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, permissionCodes }: { id: string; permissionCodes: string[] }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(
        `/api/v1/roles/${id}/permissions`,
        { permission_codes: permissionCodes },
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ROLES });
    },
  });
}

export function usePermissionsQuery(page = 1, q?: string) {
  return useQuery({
    queryKey: [...PERMISSIONS, page, q],
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/permissions", {
        params: { page, page_size: 200, q },
      });
      return data.data;
    },
    staleTime: 5 * 60_000,
  });
}

// Departments come back as a flat tree (a bare list), not a page: the organisation is small and a
// paginated tree would hand the client a partial parent chain it cannot render.
export function useDepartmentsQuery() {
  return useQuery({
    queryKey: DEPARTMENTS,
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>[]>>("/api/v1/departments");
      return Array.isArray(data.data) ? data.data : [];
    },
    staleTime: 60_000,
  });
}

export function useCreateDepartmentMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      code: string;
      name: string;
      parent_id?: string;
      sort_order?: number;
      description?: string;
    }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/departments", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: DEPARTMENTS });
    },
  });
}

export function useUpdateDepartmentMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      ...body
    }: {
      id: string;
      name?: string;
      parent_id?: string;
      sort_order?: number;
      description?: string;
    }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(
        `/api/v1/departments/${id}`,
        body,
      );
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: DEPARTMENTS });
    },
  });
}

export function useTenantsQuery(page = 1, q?: string) {
  return useQuery({
    queryKey: [...TENANTS, page, q],
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/tenants", {
        params: { page, page_size: 50, q },
      });
      return data.data;
    },
    staleTime: 60_000,
  });
}

export function useCreateTenantMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { code: string; name: string }) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/tenants", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: TENANTS });
    },
  });
}

export function useUpdateTenantMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...body }: { id: string; name?: string; is_active?: boolean }) => {
      const { data } = await apiClient.put<ApiWrap<Record<string, unknown>>>(`/api/v1/tenants/${id}`, body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: TENANTS });
    },
  });
}
