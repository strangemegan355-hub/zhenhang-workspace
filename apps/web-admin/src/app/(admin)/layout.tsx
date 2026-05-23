"use client";

import { useCurrentUserQuery } from "@zhenhang/query-hooks";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AppShell } from "@/components/app-shell";
import { useAuthStore } from "@/store/auth-store";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  const setUser = useAuthStore((s) => s.setUser);
  const clearSession = useAuthStore((s) => s.clearSession);
  const router = useRouter();
  const currentUserQuery = useCurrentUserQuery(Boolean(token?.accessToken));

  useEffect(() => {
    if (!token) router.replace("/login");
  }, [router, token]);

  useEffect(() => {
    if (currentUserQuery.data) {
      const profile = currentUserQuery.data as Record<string, unknown>;
      const roles = Array.isArray(profile.roles) ? (profile.roles as Array<Record<string, unknown>>) : [];
      setUser({
        id: String(profile.id ?? ""),
        username: String(profile.username ?? ""),
        full_name: profile.full_name ? String(profile.full_name) : undefined,
        roles: roles.map((r) => String(r.code ?? r.name ?? "role")),
        permissions: ["*:*:*", "dashboard:view", "platform:notification:read", "quote:read"],
        data_scope: String(profile.data_scope ?? "self"),
      });
    }
  }, [currentUserQuery.data, setUser]);

  useEffect(() => {
    if (currentUserQuery.isError) {
      clearSession();
      router.replace("/login");
    }
  }, [clearSession, currentUserQuery.isError, router]);

  return <AppShell>{children}</AppShell>;
}
