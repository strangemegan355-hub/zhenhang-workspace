"use client";

import Link from "next/link";
import { ArrowUpRight, ClipboardList } from "lucide-react";
import { useApprovalInboxQuery } from "@zhenhang/query-hooks";
import { StatusBadge } from "@zhenhang/ui";
import { hasPermission } from "@/lib/access";
import { useAuthStore } from "@/store/auth-store";
import { DashboardCard } from "./dashboard-card";
import { formatRelativeTime } from "./dashboard-utils";

const TASK_TYPE_LABEL: Record<string, string> = {
  quote_receivable: "应收优惠",
  quote_workflow: "报价",
};

/** UX-006：无审批读权限则不渲染（销售/财务/老板按角色见待办） */
export function ApprovalCenterCard() {
  const perms = useAuthStore((s) => s.user?.permissions ?? []);
  const canRead = hasPermission(perms, "business:approval:read");
  const inboxQuery = useApprovalInboxQuery(canRead);
  if (!canRead) return null;

  const display = (inboxQuery.data?.items ?? []).slice(0, 6);

  return (
    <DashboardCard
      title="审批中心"
      toolbar={
        <Link href="/approvals" className="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:underline">
          进入审批平台
          <ArrowUpRight className="h-3 w-3" />
        </Link>
      }
    >
      {inboxQuery.isLoading ? (
        <p className="py-6 text-center text-sm text-[var(--color-text-muted)]">加载待办…</p>
      ) : display.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <ClipboardList className="mb-2 h-8 w-8 text-[var(--color-border)]" />
          <p className="text-sm text-[var(--color-text-muted)]">暂无待审批任务</p>
        </div>
      ) : (
        <ul className="space-y-2">
          {display.map((item) => (
            <li
              key={`${item.task_type}-${item.id}`}
              className="flex items-center gap-3 rounded border border-[var(--color-border)] bg-[var(--color-surface-soft)] px-3 py-2.5"
            >
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded bg-[var(--color-primary-soft)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--color-primary)]">
                    {TASK_TYPE_LABEL[item.task_type] ?? item.task_type}
                  </span>
                  <span className="truncate text-xs font-medium text-[var(--color-text)]">{item.title}</span>
                </div>
                <p className="mt-0.5 text-[11px] text-[var(--color-text-muted)]">
                  {item.submitter_name ?? "提交人"} · {formatRelativeTime(item.submitted_at)}
                </p>
              </div>
              <StatusBadge status="warning" label="待审批" compact />
            </li>
          ))}
        </ul>
      )}
    </DashboardCard>
  );
}
