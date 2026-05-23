"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useLoginMutation } from "@zhenhang/query-hooks";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useAuthStore } from "@/store/auth-store";

const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(6, "Password must be at least 6 chars"),
});

type LoginInput = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const setSession = useAuthStore((s) => s.setSession);
  const loginMutation = useLoginMutation();
  const form = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "admin", password: "" },
  });

  const onSubmit = async (data: LoginInput) => {
    const token = await loginMutation.mutateAsync(data);
    setSession(
      {
        accessToken: token.access_token,
        refreshToken: token.refresh_token,
      },
      {
        id: "",
        username: data.username,
        roles: [],
        permissions: [],
        data_scope: "self",
      },
    );
    router.push("/dashboard");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
      <form
        className="w-full max-w-sm space-y-4 rounded-lg border bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900"
        onSubmit={form.handleSubmit(onSubmit)}
      >
        <h1 className="text-lg font-semibold">Sign in</h1>
        <div>
          <input className="h-10 w-full rounded-md border px-3" placeholder="Username" {...form.register("username")} />
          <p className="mt-1 text-xs text-red-500">{form.formState.errors.username?.message}</p>
        </div>
        <div>
          <input
            className="h-10 w-full rounded-md border px-3"
            placeholder="Password"
            type="password"
            {...form.register("password")}
          />
          <p className="mt-1 text-xs text-red-500">{form.formState.errors.password?.message}</p>
        </div>
        <button className="h-10 w-full rounded-md bg-zinc-900 text-sm text-white dark:bg-zinc-100 dark:text-black">
          {loginMutation.isPending ? "Signing in..." : "Login"}
        </button>
      </form>
    </div>
  );
}
