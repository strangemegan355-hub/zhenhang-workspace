"use client";

import Link from "next/link";
import { useProjectsQuery } from "@zhenhang/query-hooks";
import { ArrowUpRight, FolderKanban } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import { formatRelativeTime } from "./dashboard-utils";

const STAGE_LABELS: Record<string, string> = { lead: "线索", quote: "报价", contract: "合同", production: "生产", delivery: "交付", closed: "结案" };
const STAGE_STYLES: Record<string, string> = { lead: "bg-[#f1f5f9] text-[#64748b]", quote: "bg-[var(--color-primary-soft)] text-[var(--color-primary)]", contract: "bg-[#f0fdf4] text-[#16a34a]", production: "bg-[#fff8e6] text-[#d97706]", delivery: "bg-[#faf5ff] text-[#7c3aed]", closed: "bg-[#f1f5f9] text-[#475569]" };

export function RecentProjectsCard() {
  const { data } = useProjectsQuery(1);
  const items = ((data?.items ?? []) as Record<string, unknown>[]).slice(0, 5);
  return (
    <DashboardCard title="最近项目" toolbar={<Link href="/projects" className="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:underline">全部<ArrowUpRight className="h-3 w-3" /></Link>}>
      {items.length === 0 ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">暂无项目</p> : (
        <ul className="space-y-1">{items.map((item) => {
          const stage = String(item.stage ?? "lead");
          return (
            <li key={String(item.id ?? item.project_no)}>
              <Link href="/projects" className="flex items-center justify-between gap-3 rounded px-2 py-2.5 transition-colors hover:bg-[var(--color-surface-soft)]">
                <div className="flex min-w-0 items-center gap-2.5">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[var(--color-primary-soft)]"><FolderKanban className="h-4 w-4 text-[var(--color-primary)]" /></div>
                  <div className="min-w-0"><p className="truncate text-xs font-medium text-[var(--color-text)]">{String(item.name ?? item.project_no ?? "项目")}</p><p className="text-[11px] text-[var(--color-text-muted)]">{formatRelativeTime(String(item.updated_at ?? item.created_at ?? ""))}</p></div>
                </div>
                <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${STAGE_STYLES[stage] ?? STAGE_STYLES.lead}`}>{STAGE_LABELS[stage] ?? stage}</span>
              </Link>
            </li>
          );
        })}</ul>
      )}
    </DashboardCard>
  );
}
