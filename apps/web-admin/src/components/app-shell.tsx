"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { APP_MENUS } from "@/lib/menu";
import { hasPermission } from "@/lib/access";
import { IndustrialRealtimeProvider } from "@/components/industrial-realtime-provider";
import { NotificationBell } from "@/components/notification-bell";
import { ThemeToggle } from "@/components/theme-toggle";
import { ToastCenter } from "@/components/toast-center";
import { useAuthStore } from "@/store/auth-store";
import { RuntimeDevToolsPanel } from "@zhenhang/runtime-devtools";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const clearSession = useAuthStore((s) => s.clearSession);

  const menus = APP_MENUS.filter((m) => hasPermission(user?.permissions ?? [], m.permission));

  return (
    <IndustrialRealtimeProvider>
    <div className="flex min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <aside className="w-56 border-r bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mb-6 text-sm font-semibold">ERP Admin</div>
        <nav className="space-y-1">
          {menus.map((menu) => (
            <Link
              key={menu.key}
              href={menu.href}
              className={`block rounded-md px-3 py-2 text-sm ${pathname === menu.href ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-black" : "hover:bg-zinc-100 dark:hover:bg-zinc-800"}`}
            >
              {menu.title}
            </Link>
          ))}
        </nav>
      </aside>
      <div className="flex flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b bg-white px-4 dark:border-zinc-800 dark:bg-zinc-900">
          <div className="text-sm text-zinc-500">{user?.username ?? "Guest"}</div>
          <div className="flex items-center gap-2">
            <NotificationBell />
            <ThemeToggle />
            <button
              className="rounded-md border px-3 py-1 text-sm"
              onClick={() => {
                clearSession();
                router.push("/login");
              }}
            >
              Logout
            </button>
          </div>
        </header>
        <main className="flex-1 p-4">{children}</main>
        <ToastCenter />
        <RuntimeDevToolsPanel />
      </div>
    </div>
    </IndustrialRealtimeProvider>
  );
}
