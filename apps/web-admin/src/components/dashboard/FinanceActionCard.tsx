"use client";

import Link from "next/link";
import { Wallet } from "lucide-react";
import { hasPermission } from "@/lib/access";
import { useAuthStore } from "@/store/auth-store";
import { DashboardCard } from "./dashboard-card";

const ACTIONS = [
  {
    href: "/accounting/ledger",
    title: "待收款",
    desc: "客户账目明细 · 登记收款与核销",
  },
  {
    href: "/accounting/supplier-ledger",
    title: "待付款",
    desc: "供应商台账 · 应付与付款",
  },
  {
    href: "/accounting",
    title: "收支台账",
    desc: "全部记账、补录与导出",
  },
] as const;

/** 工作台财务行动入口（UX-003 / UX-006）：无记账读权限则不渲染 */
export function FinanceActionCard() {
  const perms = useAuthStore((s) => s.user?.permissions ?? []);
  if (!hasPermission(perms, "business:accounting:read")) return null;

  return (
    <DashboardCard
      title="财务待办"
      toolbar={
        <span className="inline-flex items-center gap-1 text-[11px] text-[var(--color-text-muted)]">
          <Wallet className="h-3 w-3" />
          收付款
        </span>
      }
    >
      <ul className="space-y-2">
        {ACTIONS.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className="flex items-center justify-between gap-3 rounded border border-[var(--color-border)] px-3 py-2.5 transition-colors hover:bg-[var(--color-surface-soft)]"
            >
              <div className="min-w-0">
                <p className="text-xs font-medium text-[var(--color-text)]">{item.title}</p>
                <p className="mt-0.5 text-[11px] text-[var(--color-text-muted)]">{item.desc}</p>
              </div>
              <span className="shrink-0 text-xs text-[var(--color-primary)]">打开</span>
            </Link>
          </li>
        ))}
      </ul>
    </DashboardCard>
  );
}
