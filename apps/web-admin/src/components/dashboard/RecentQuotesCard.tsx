"use client";

import Link from "next/link";
import { StatusBadge, workflowStateToStatus } from "@zhenhang/ui";
import { ArrowUpRight, FileText } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import { formatRelativeTime } from "./dashboard-utils";
import type { RecentQuote } from "./types";

const STATE_LABELS: Record<string, string> = { draft: "草稿", reviewing: "审核中", approved: "已批准", rejected: "已驳回" };

export function RecentQuotesCard({ recent = [] }: { recent?: RecentQuote[] }) {
  const items = recent.slice(0, 5);
  return (
    <DashboardCard title="最近报价" toolbar={<Link href="/quotes" className="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:underline">全部<ArrowUpRight className="h-3 w-3" /></Link>}>
      {items.length === 0 ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">暂无报价记录</p> : (
        <ul className="space-y-1">{items.map((item) => {
          const state = item.workflow_state ?? "draft";
          return (
            <li key={item.id ?? item.quote_no}>
              <Link href={`/quotes/\${item.id ?? ""}`} className="flex items-center justify-between gap-3 rounded px-2 py-2.5 transition-colors hover:bg-[var(--color-surface-soft)]">
                <div className="flex min-w-0 items-center gap-2.5">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[var(--color-primary-soft)]"><FileText className="h-4 w-4 text-[var(--color-primary)]" /></div>
                  <div className="min-w-0">
                    <p className="truncate text-xs font-medium text-[var(--color-text)]">{item.quote_no ?? item.title ?? "报价"}</p>
                    <p className="text-[11px] text-[var(--color-text-muted)]">{formatRelativeTime(item.updated_at ?? item.created_at)}</p>
                  </div>
                </div>
                <StatusBadge status={workflowStateToStatus(state)} label={STATE_LABELS[state] ?? state} compact />
              </Link>
            </li>
          );
        })}</ul>
      )}
    </DashboardCard>
  );
}
