"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/accounting/ledger", label: "客户应收", hint: "待收款 / 欠款" },
  { href: "/accounting", label: "收支台账", hint: "全部记账明细" },
  { href: "/accounting/supplier-ledger", label: "供应商应付", hint: "待付款 / 欠款" },
] as const;

function isActive(pathname: string, href: string) {
  if (href === "/accounting") {
    return pathname === "/accounting" || pathname === "/accounting/";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

/** 财务三页统一子导航（UX-003） */
export function FinanceSubNav() {
  const pathname = usePathname() ?? "";

  return (
    <nav
      aria-label="财务中心视图"
      className="flex flex-wrap gap-1 rounded-[var(--radius-card)] border border-[var(--color-border)] bg-[var(--color-surface)] p-1"
    >
      {TABS.map((tab) => {
        const active = isActive(pathname, tab.href);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={
              active
                ? "rounded-[var(--radius-btn)] bg-[var(--color-primary-soft)] px-3 py-1.5 text-sm font-medium text-[var(--color-primary)]"
                : "rounded-[var(--radius-btn)] px-3 py-1.5 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-soft)] hover:text-[var(--color-text)]"
            }
            title={tab.hint}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
