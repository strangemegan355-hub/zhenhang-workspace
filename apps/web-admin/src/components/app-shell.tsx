"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import {
  Bell,
  Barcode,
  ChevronDown,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  FileText,
  FolderTree,
  LayoutDashboard,
  LogOut,
  Menu,
  Package,
  Search,
  Settings,
  ShoppingCart,
  Truck,
  Users,
  Warehouse,
  Wrench,
} from "lucide-react";
import { APP_MENU_GROUPS, APP_MENUS, ROUTE_GROUP_MAP, type MenuGroup, type MenuItem } from "@/lib/menu";
import { hasPermission } from "@/lib/access";
import { useBusinessSettingsQuery } from "@zhenhang/query-hooks";
import { IndustrialRealtimeProvider } from "@/components/industrial-realtime-provider";
import { NotificationBell } from "@/components/notification-bell";
import { ThemeToggle } from "@/components/theme-toggle";
import { useAuthStore } from "@/store/auth-store";

const iconMap: Record<string, ReactNode> = {
  dashboard: <LayoutDashboard size={16} strokeWidth={1.75} />,
  quotes: <FileText size={16} strokeWidth={1.75} />,
  "quotes-customer": <FileText size={16} strokeWidth={1.75} />,
  projects: <FolderTree size={16} strokeWidth={1.75} />,
  costing: <FileText size={16} strokeWidth={1.75} />,
  "order-profit": <FileText size={16} strokeWidth={1.75} />,
  "product-categories": <Package size={16} strokeWidth={1.75} />,
  products: <Package size={16} strokeWidth={1.75} />,
  "product-cost-templates": <FileText size={16} strokeWidth={1.75} />,
  "product-price-templates": <FileText size={16} strokeWidth={1.75} />,
  customers: <Users size={16} strokeWidth={1.75} />,
  materials: <Warehouse size={16} strokeWidth={1.75} />,
  suppliers: <Truck size={16} strokeWidth={1.75} />,
  standards: <Settings size={16} strokeWidth={1.75} />,
  procurement: <ShoppingCart size={16} strokeWidth={1.75} />,
  "work-orders": <Wrench size={16} strokeWidth={1.75} />,
  fieldwork: <Wrench size={16} strokeWidth={1.75} />,
  workshop: <LayoutDashboard size={16} strokeWidth={1.75} />,
  notifications: <Bell size={16} strokeWidth={1.75} />,
  "business-settings": <Settings size={16} strokeWidth={1.75} />,
  system: <Settings size={16} strokeWidth={1.75} />,
  machines: <Settings size={16} strokeWidth={1.75} />,
  boms: <Package size={16} strokeWidth={1.75} />,
  "acceptance": <FileText size={16} strokeWidth={1.75} />,
  "equipment-units": <Barcode size={16} strokeWidth={1.75} />,
  files: <FileText size={16} strokeWidth={1.75} />,
  accounting: <FileText size={16} strokeWidth={1.75} />,
};

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const clearSession = useAuthStore((s) => s.clearSession);
  const [collapsed, setCollapsed] = useState(false);
  const settingsQuery = useBusinessSettingsQuery();

  const menuGroups = useMemo(() => {
    const flags = settingsQuery.data;
    const settingsReady = !settingsQuery.isLoading && !settingsQuery.isError;
    const filterItems = (items: MenuItem[]) =>
      items.filter((m) => {
        if (!hasPermission(user?.permissions ?? [], m.permission) || m.hidden) return false;
        if (m.featureFlag) {
          if (!settingsReady || !flags?.[m.featureFlag]) return false;
        }
        return true;
      });

    return APP_MENU_GROUPS.map((group) => ({
      ...group,
      items: filterItems(group.items),
    })).filter((group) => group.items.length > 0);
  }, [user?.permissions, settingsQuery.data, settingsQuery.isLoading, settingsQuery.isError]);

  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);
  const activeMenu = APP_MENUS.find((m) => pathname === m.href || pathname.startsWith(`${m.href}/`));
  const routeMeta = ROUTE_GROUP_MAP[pathname] ?? Object.entries(ROUTE_GROUP_MAP).find(([p]) => pathname.startsWith(p))?.[1];

  const handleLogout = () => {
    clearSession();
    router.push("/login");
  };

  return (
    <IndustrialRealtimeProvider>
      <div className="flex h-screen min-h-0 overflow-hidden bg-[var(--color-bg)] text-[var(--color-text)]">
        {/* 左侧栏 — Frappe Workspace Sidebar */}
        <aside
          className="flex shrink-0 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)] transition-[width] duration-200"
          style={{ width: collapsed ? "var(--sidebar-collapsed-width)" : "var(--sidebar-width)" }}
        >
          <div className="flex h-[var(--navbar-height)] items-center gap-2 border-b border-[var(--color-border)] px-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[var(--color-accent)] text-sm font-bold text-white">
              振
            </div>
            {!collapsed ? (
              <div className="min-w-0 flex-1">
                <div className="truncate text-base font-semibold text-[var(--color-text)]">振航 ERP</div>
                <div className="truncate text-sm text-[var(--color-text-soft)]">Desk</div>
              </div>
            ) : null}
          </div>

          <nav className="flex-1 overflow-auto py-2">
            {menuGroups.map((group) => (
              <MenuGroupSection key={group.key} group={group} collapsed={collapsed} isActive={isActive} />
            ))}
          </nav>

          <div className="border-t border-[var(--color-border)] p-2">
            <button
              type="button"
              onClick={() => setCollapsed((v) => !v)}
              className="flex w-full items-center justify-center gap-1 rounded py-1.5 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-soft)]"
              aria-label={collapsed ? "展开侧栏" : "收起侧栏"}
            >
              {collapsed ? <ChevronsRight size={14} /> : <ChevronsLeft size={14} />}
              {!collapsed ? <span>收起</span> : null}
            </button>
          </div>
        </aside>

        {/* 右侧主区域 */}
        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          {/* 顶栏 — Frappe Navbar */}
          <header className="flex h-[var(--navbar-height)] shrink-0 items-center gap-3 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4">
            <nav className="hidden min-w-0 flex-1 items-center gap-1 text-sm text-[var(--color-text-muted)] md:flex">
              {routeMeta ? (
                <>
                  <span className="text-[var(--color-text-soft)]">{routeMeta.group}</span>
                  <ChevronRight size={12} className="text-[var(--color-text-soft)]" />
                </>
              ) : null}
              <span className="truncate font-medium text-[var(--color-text)]">{activeMenu?.title ?? "工作台"}</span>
            </nav>

            <button
              type="button"
              className="hidden h-9 min-w-[200px] flex-1 items-center gap-2 rounded border border-[var(--color-border)] bg-[var(--color-surface-soft)] px-2.5 text-sm text-[var(--color-text-soft)] lg:flex md:max-w-[280px] md:flex-none"
            >
              <Search size={14} />
              <span className="flex-1 text-left">搜索或输入命令</span>
              <kbd className="rounded border border-[var(--color-border)] bg-white px-1.5 text-sm">⌘K</kbd>
            </button>

            <div className="ml-auto flex items-center gap-2">
              <ThemeToggle />
              <NotificationBell />
              <div className="flex items-center gap-1.5 border-l border-[var(--color-border)] pl-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-primary-soft)] text-sm font-semibold text-[var(--color-text)]">
                  {(user?.full_name ?? user?.username ?? "U").charAt(0).toUpperCase()}
                </div>
                <span className="hidden max-w-[80px] truncate text-sm sm:inline">{user?.full_name ?? user?.username}</span>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="rounded p-1 text-[var(--color-text-muted)] hover:bg-[var(--color-surface-soft)]"
                  aria-label="退出登录"
                >
                  <LogOut size={14} />
                </button>
              </div>
            </div>
          </header>

          {/* 内容区 */}
          <main className="min-h-0 flex-1 overflow-auto bg-[var(--color-bg)] p-4">{children}</main>
        </div>
      </div>
    </IndustrialRealtimeProvider>
  );
}

function MenuGroupSection({
  group,
  collapsed,
  isActive,
}: {
  group: MenuGroup;
  collapsed: boolean;
  isActive: (href: string) => boolean;
}) {
  const pathname = usePathname();
  const storageKey = `nav-group-expanded:${group.key}`;
  const hasActiveChild = group.items.some((m) => m.href !== "#" && isActive(m.href));
  const defaultOpen = group.defaultExpanded ?? group.items.length <= 2;

  const [expanded, setExpanded] = useState(() => {
    try {
      const stored = window.localStorage.getItem(storageKey);
      if (stored !== null) return stored === "true";
    } catch {}
    return defaultOpen;
  });

  useEffect(() => {
    // ponytail: auto-expand when navigating into this group; user toggle persists via localStorage
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (hasActiveChild) setExpanded(true);
  }, [hasActiveChild, pathname]);

  const toggleExpanded = () => {
    setExpanded((prev) => {
      const next = !prev;
      window.localStorage.setItem(storageKey, String(next));
      return next;
    });
  };

  if (collapsed) {
    return (
      <div className="mb-1 px-1">
        {group.items.map((menu) => (
          <SidebarMenuLink key={menu.key} menu={menu} collapsed active={menu.href !== "#" && isActive(menu.href)} />
        ))}
      </div>
    );
  }

  return (
    <div className="mb-1 px-2">
      <button
        type="button"
        onClick={toggleExpanded}
        className="flex w-full items-center gap-1 rounded px-2 py-1.5 text-left hover:bg-[var(--color-surface-soft)]"
        aria-expanded={expanded}
      >
        <span className="min-w-0 flex-1 truncate text-sm font-semibold uppercase tracking-wide text-[var(--color-text-soft)]">
          {group.title}
        </span>
        <ChevronDown
          size={12}
          className={`shrink-0 text-[var(--color-text-soft)] transition-transform ${expanded ? "" : "-rotate-90"}`}
        />
      </button>
      {expanded ? (
        <div className="mt-0.5 space-y-px">
          {group.items.map((menu) => (
            <SidebarMenuLink key={menu.key} menu={menu} collapsed={false} active={menu.href !== "#" && isActive(menu.href)} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function SidebarMenuLink({
  menu,
  collapsed,
  active,
}: {
  menu: MenuItem;
  collapsed: boolean;
  active: boolean;
}) {
  const href = menu.href === "#" ? "" : menu.href;
  const icon = iconMap[menu.key] ?? <Menu size={16} strokeWidth={1.75} />;

  return (
    <Link
      href={href || "#"}
      title={collapsed ? menu.title : undefined}
      className={`flex items-center gap-2 rounded text-sm transition ${
        collapsed ? "justify-center px-2 py-2" : "px-2 py-1.5"
      } ${
        active
          ? "bg-[var(--color-primary-soft)] font-medium text-[var(--color-text)]"
          : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-soft)] hover:text-[var(--color-text)]"
      }`}
      style={active && !collapsed ? { boxShadow: "inset 2px 0 0 0 var(--color-primary)" } : undefined}
    >
      <span className="shrink-0 opacity-80">{icon}</span>
      {!collapsed ? <span className="truncate">{menu.title}</span> : null}
    </Link>
  );
}
