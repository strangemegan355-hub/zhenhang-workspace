"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useLoginMutation } from "@zhenhang/query-hooks";
import { apiClient } from "@zhenhang/http-client";
import { AlertCircle, Eye, EyeOff, Lock, User } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useAuthStore } from "@/store/auth-store";

const loginSchema = z.object({
  username: z.string().min(1, "请输入用户名"),
  password: z.string().min(6, "密码至少 6 位"),
});

type LoginInput = z.infer<typeof loginSchema>;
type ApiWrap<T> = { code: string; message: string; data: T };

type AxiosLikeError = { response?: { status?: number; data?: { message?: string; detail?: { detail?: string } | string } }; message?: string; code?: string };

function mapProfile(profile: Record<string, unknown>, username: string) {
  const roles = Array.isArray(profile.roles) ? (profile.roles as Array<Record<string, unknown>>) : [];
  const permissions = Array.isArray(profile.permissions) ? (profile.permissions as string[]) : [];
  return { id: String(profile.id ?? ""), username: String(profile.username ?? username), full_name: profile.full_name ? String(profile.full_name) : undefined, roles: roles.map((r) => String(r.code ?? r.name ?? "role")), permissions, data_scope: String(profile.data_scope ?? "self") };
}

function resolveLoginError(err: unknown): string {
  const e = err as AxiosLikeError;
  const status = e.response?.status;
  const body = e.response?.data;
  const nestedDetail = body?.detail && typeof body.detail === "object" ? body.detail.detail : undefined;
  const apiMessage = nestedDetail || body?.message;
  if (!e.response) return "无法连接后端 API，请确认服务已启动且网络正常";
  if (status === 401) return apiMessage || "用户名或密码错误，请检查后重试";
  if (status === 403) return apiMessage || "账号无登录权限";
  if (status && status >= 500) return apiMessage || "服务器错误，请稍后重试或联系管理员";
  return apiMessage || e.message || "登录失败，请稍后重试";
}

export function LoginFormPanel() {
  const router = useRouter();
  const setSession = useAuthStore((s) => s.setSession);
  const loginMutation = useLoginMutation();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const form = useForm<LoginInput>({ resolver: zodResolver(loginSchema), defaultValues: { username: "", password: "" } });

  const onSubmit = async (data: LoginInput) => {
    setErrorMessage(null);
    try {
      const token = await loginMutation.mutateAsync(data);
      useAuthStore.getState().setTokens({ accessToken: token.access_token, refreshToken: token.refresh_token });
      const { data: meWrap } = await apiClient.get<ApiWrap<Record<string, unknown>>>("/api/v1/users/me");
      setSession({ accessToken: token.access_token, refreshToken: token.refresh_token }, mapProfile(meWrap.data, data.username));
      router.push("/dashboard");
    } catch (err) {
      setErrorMessage(resolveLoginError(err));
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-bg)] px-4 py-8">
      <div className="w-full max-w-[380px]">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded bg-[var(--color-accent)] text-sm font-bold text-white">
            振
          </div>
          <h1 className="text-[15px] font-semibold text-[var(--color-text)]">振航 ERP</h1>
          <p className="mt-1 text-[12px] text-[var(--color-text-muted)]">登录您的账户</p>
        </div>

        <div className="rounded-[var(--radius-card)] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-[var(--shadow-panel)]">
          <form className="space-y-3" onSubmit={form.handleSubmit(onSubmit)}>
            <div>
              <label htmlFor="username" className="mb-1 block text-[12px] font-medium text-[var(--color-text)]">
                用户名
              </label>
              <div className="relative">
                <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--color-text-soft)]">
                  <User size={14} />
                </span>
                <input
                  id="username"
                  className="h-8 w-full rounded border border-[var(--color-border)] bg-white pl-8 pr-2 text-[13px] outline-none focus:border-[var(--color-primary)]"
                  placeholder="请输入用户名"
                  autoComplete="username"
                  {...form.register("username")}
                />
              </div>
              {form.formState.errors.username && (
                <p className="mt-1 text-[11px] text-[var(--color-danger)]">{form.formState.errors.username.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="mb-1 block text-[12px] font-medium text-[var(--color-text)]">
                密码
              </label>
              <div className="relative">
                <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--color-text-soft)]">
                  <Lock size={14} />
                </span>
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  className="h-8 w-full rounded border border-[var(--color-border)] bg-white pl-8 pr-8 text-[13px] outline-none focus:border-[var(--color-primary)]"
                  placeholder="请输入密码"
                  autoComplete="current-password"
                  {...form.register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--color-text-soft)] hover:text-[var(--color-text)]"
                >
                  {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
              {form.formState.errors.password && (
                <p className="mt-1 text-[11px] text-[var(--color-danger)]">{form.formState.errors.password.message}</p>
              )}
            </div>

            {errorMessage && (
              <div className="flex items-center gap-2 rounded border border-[var(--color-danger)]/30 bg-[var(--color-accent-soft)] px-3 py-2 text-[12px] text-[var(--color-danger)]" role="alert">
                <AlertCircle size={14} />
                {errorMessage}
              </div>
            )}

            <button type="submit" disabled={loginMutation.isPending} className="btn-primary h-8 w-full">
              {loginMutation.isPending ? "登录中…" : "登录"}
            </button>
          </form>
        </div>

        <p className="mt-4 text-center text-[11px] text-[var(--color-text-soft)]">振航工业 · ERP Desk</p>
      </div>
    </div>
  );
}
