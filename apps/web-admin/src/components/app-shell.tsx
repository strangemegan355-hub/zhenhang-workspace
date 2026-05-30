"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Clock3,
  LayoutDashboard,
  LogOut,
  Menu,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Bell,
  PanelRightClose,
  PanelRightOpen,
} from "lucide-react";
import { APP_MENUS } from "@/lib/menu";
import { hasPermission } from "@/lib/access";
import { IndustrialRealtimeProvider } from "@/components/industrial-realtime-provider";
import { NotificationBell } from "@/components/notification-bell";
import { ThemeToggle } from "@/components/theme-toggle";
import { useAuthStore } from "@/store/auth-store";
import { RuntimeDevToolsPanel } from "@zhenhang/runtime-devtools";

const iconMap: Record<string, React.ReactNode> = {
  dashboard: <LayoutDashboard size={18} />,
  quotes: <Sparkles size={18} />,
  materials: <ShieldCheck size={18} />,
  machines: <Settings size={18} />,
  customers: <Menu size={18} />,
  suppliers: <Menu size={18} />,
  projects: <PanelRightOpen size={18} />,
  procurement: <PanelRightClose size={18} />,
  "work-orders": <Clock3 size={18} />,
  costing: <Sparkles size={18} />,
  notifications: <Bell size={18} />,
  settings: <Settings size={18} />,
  files: <Menu size={18} />,
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const clearSession = useAuthStore((s) => s.clearSession);
  const [collapsed, setCollapsed] = useState(false);
  const [currentTime, setCurrentTime] = useState("");

  useEffect(() => {
    const update = () => setCurrentTime(new Date().toLocaleTimeString("zh-CN", { hour12: false }));
    update();
    const id = window.setInterval(update, 1000);
    return () => window.clearInterval(id);
  }, []);

  const menus = useMemo(
    () => APP_MENUS.filter((m) => hasPermission(user?.permissions ?? [], m.permission)),
    [user?.permissions],
  );

  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);
  const handleLogout = () => {
    clearSession();
    router.push("/login");
  };

  const activeMenu = APP_MENUS.find((m) => pathname === m.href || pathname.startsWith(`${m.href}/`));

  return (
    <IndustrialRealtimeProvider>
      <div className="flex h-screen min-h-0 flex-col overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)]">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[rgba(255,255,255,0.72)] px-5 backdrop-blur-md dark:bg-[rgba(15,23,42,0.82)]">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setCollapsed((v) => !v)}
              className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--color-border)] bg-white text-[var(--color-text-muted)] shadow-[var(--shadow-card)] transition hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] dark:bg-[var(--color-surface)]"
              aria-label={collapsed ? "展开侧栏" : "折叠侧栏"}
            >
              {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
            </button>
            <div className="hidden flex-col md:flex">
              <div className="text-xs text-[var(--color-text-muted)]">振航工业数字生态系统</div>
              <div className="text-sm font-semibold text-[var(--color-text)]">{activeMenu?.title ?? "工作台"}</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button className="hidden h-10 min-w-[280px] items-center gap-2 rounded-xl border border-[var(--color-border)] bg-white px-3 text-sm text-[var(--color-text-soft)] shadow-[var(--shadow-card)] lg:flex dark:bg-[var(--color-surface)]" type="button">
              <Search size={16} />
              <span>搜索客户、报价、项目、工单</span>
              <kbd className="ml-auto rounded-md border border-[var(--color-border)] bg-[var(--color-surface-soft)] px-1.5 py-0.5 text-[11px] text-[var(--color-text-soft)]">⌘K</kbd>
            </button>
            <ThemeToggle />
            <NotificationBell />
            <div className="flex items-center gap-2 rounded-xl border border-[var(--color-border)] bg-white px-3 py-2 shadow-[var(--shadow-card)] dark:bg-[var(--color-surface)]">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[linear-gradient(135deg,#2563EB,#06B6D4)] text-sm font-semibold text-white">
                {(user?.full_name ?? user?.username ?? "U").charAt(0).toUpperCase()}
              </div>
              <div className="hidden leading-tight sm:block">
                <div className="text-sm font-medium">{user?.full_name ?? user?.username ?? "用户"}</div>
                <div className="text-xs text-[var(--color-text-muted)]">企业账户</div>
              </div>
              <button type="button" onClick={handleLogout} className="rounded-lg p-2 text-[var(--color-text-muted)] transition hover:bg-[var(--color-primary-soft)] hover:text-[var(--color-primary)]" aria-label="退出登录">
                <LogOut size={16} />
              </button>
            </div>
          </div>
        </header>

        <div className="flex min-h-0 flex-1">
          <aside className={`flex shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] transition-all ${collapsed ? "w-[76px]" : "w-[260px]"}`}>
            <div className="flex h-16 items-center gap-3 border-b border-[var(--color-border)] px-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#2563EB,#06B6D4)] text-white shadow-[var(--shadow-card)]">
                <LayoutDashboard size={20} />
              </div>
              {!collapsed && (
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold text-[var(--color-text)]">振航工业 OS</div>
                  <div className="truncate text-xs text-[var(--color-text-muted)]">Enterprise Industrial Technology</div>
                </div>
              )}
            </div>
            <nav className="flex-1 space-y-1 overflow-auto p-3">
              {menus.map((menu) => {
                const href = menu.href === "#" ? "" : menu.href;
                const active = href ? isActive(href) : false;
                const icon = iconMap[menu.key] ?? <Menu size={18} />;
                return (
                  <Link
                    key={menu.key}
                    href={href || "#"}
                    className={`flex items-center gap-3 rounded-xl px-3 py-3 text-sm transition ${active ? "bg-[var(--color-primary-soft)] text-[var(--color-primary)]" : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-soft)] hover:text-[var(--color-text)]"} ${collapsed ? "justify-center" : ""}`}
                    title={collapsed ? menu.title : undefined}
                  >
                    <span className="shrink-0">{icon}</span>
                    {!collapsed && <span className="truncate">{menu.title}</span>}
                  </Link>
                );
              })}
            </nav>
            <div className="border-t border-[var(--color-border)] p-3">
              <button type="button" onClick={() => setCollapsed((v) => !v)} className="flex w-full items-center justify-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-soft)] px-3 py-2.5 text-sm text-[var(--color-text-muted)] transition hover:border-[var(--color-primary)] hover:text-[var(--color-primary)]">
                {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                {!collapsed && <span>收起菜单</span>}
              </button>
            </div>
          </aside>

          <main className="flex min-h-0 flex-1 flex-col overflow-auto bg-[var(--color-bg)]">
            <div className="flex-1 p-6">{children}</div>
            <ShellFooter currentTime={currentTime} />
          </main>
        </div>

        <RuntimeDevToolsPanel />
      </div>
    </IndustrialRealtimeProvider>
  );
}

function ShellFooter({ currentTime }: { currentTime: string }) {
  return (
    <footer className="flex h-9 shrink-0 items-center justify-between border-t border-[var(--color-border)] bg-white px-4 text-xs text-[var(--color-text-muted)] dark:bg-[var(--color-surface)]">
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-[var(--color-success)]" />WS 正常</span>
        <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-[var(--color-success)]" />API 正常</span>
        <span>当前时间 {currentTime || "--:--:--"}</span>
      </div>
      <div>振航工业数字生态系统 · v2.1.0</div>
    </footer>
  );
}
