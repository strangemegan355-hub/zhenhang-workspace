"use client";

import Link from "next/link";
import { useWorkOrdersQuery } from "@zhenhang/query-hooks";
import { StatusBadge, type InteractionStatus } from "@zhenhang/ui";
import { ArrowUpRight, Wrench } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import { formatRelativeTime } from "./dashboard-utils";

const STATUS_LABELS: Record<string, string> = { todo: "待开工", doing: "进行中", done: "已完成", exception: "异常" };
const STATUS_MAP: Record<string, InteractionStatus> = { todo: "idle", doing: "processing", done: "success", exception: "danger" };

export function RecentWorkOrdersCard() {
  const { data } = useWorkOrdersQuery(1);
  const items = ((data?.items ?? []) as Record<string, unknown>[]).slice(0, 5);
  return (
    <DashboardCard title="最近工单" toolbar={<Link href="/work-orders" className="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:underline">全部<ArrowUpRight className="h-3 w-3" /></Link>}>
      {items.length === 0 ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">暂无工单</p> : (
        <ul className="space-y-1">{items.map((item) => {
          const status = String(item.status ?? "todo");
          return (
            <li key={String(item.id ?? item.work_order_no)}>
              <Link href="/work-orders" className="flex items-center justify-between gap-3 rounded px-2 py-2.5 transition-colors hover:bg-[var(--color-surface-soft)]">
                <div className="flex min-w-0 items-center gap-2.5">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[var(--color-primary-soft)]"><Wrench className="h-4 w-4 text-[var(--color-primary)]" /></div>
                  <div className="min-w-0"><p className="truncate text-xs font-medium text-[var(--color-text)]">{String(item.work_order_no ?? item.task_desc ?? "工单")}</p><p className="text-[11px] text-[var(--color-text-muted)]">{formatRelativeTime(String(item.updated_at ?? item.created_at ?? ""))}</p></div>
                </div>
                <StatusBadge status={STATUS_MAP[status] ?? "idle"} label={STATUS_LABELS[status] ?? status} compact />
              </Link>
            </li>
          );
        })}</ul>
      )}
    </DashboardCard>
  );
}
