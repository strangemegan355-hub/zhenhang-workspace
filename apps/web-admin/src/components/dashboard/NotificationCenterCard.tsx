"use client";

import Link from "next/link";
import { useNotificationsQuery, useNotificationUnreadCountQuery } from "@zhenhang/query-hooks";
import { Bell, ArrowUpRight } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import { formatRelativeTime } from "./dashboard-utils";

export function NotificationCenterCard() {
  const unreadQuery = useNotificationUnreadCountQuery();
  const listQuery = useNotificationsQuery({ page: 1, unreadOnly: false });
  const unreadCount = unreadQuery.data ?? 0;
  const items = ((listQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).slice(0, 5);
  return (
    <DashboardCard title="通知中心" toolbar={<Link href="/notifications" className="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:underline">消息中心{unreadCount > 0 ? ` (${unreadCount})` : ""}<ArrowUpRight className="h-3 w-3" /></Link>}>
      {listQuery.isLoading && !items.length ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">加载中…</p> : items.length === 0 ? (
        <div className="flex flex-col items-center py-8 text-center"><Bell className="mb-2 h-8 w-8 text-[var(--color-border)]" /><p className="text-xs text-[var(--color-text-muted)]">暂无通知</p></div>
      ) : (
        <ul className="space-y-1">{items.map((row) => {
          const id = String(row.id ?? "");
          const isUnread = !row.read_at && String(row.status ?? "") !== "read";
          return (
            <li key={id}>
              <Link href="/notifications" className={`flex items-start justify-between gap-3 rounded px-2 py-2.5 transition-colors hover:bg-[var(--color-surface-soft)] ${isUnread ? "bg-[var(--color-surface-soft)]" : ""}`}>
                <div className="min-w-0 flex-1">
                  <p className={`truncate text-xs text-[var(--color-text)] ${isUnread ? "font-semibold" : "font-medium"}`}>{String(row.title ?? "通知")}</p>
                  <p className="text-[11px] text-[var(--color-text-muted)]">{String(row.channel ?? row.biz_type ?? "system")}</p>
                </div>
                <span className="shrink-0 text-[11px] text-[var(--color-text-muted)]">{formatRelativeTime(String(row.created_at ?? ""))}</span>
              </Link>
            </li>
          );
        })}</ul>
      )}
    </DashboardCard>
  );
}

export function RecentActivityCard() {
  const listQuery = useNotificationsQuery({ page: 1, unreadOnly: false });
  const items = ((listQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).slice(0, 6);
  return (
    <DashboardCard title="最近活动" toolbar={<Link href="/notifications" className="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:underline">查看全部<ArrowUpRight className="h-3 w-3" /></Link>}>
      {items.length === 0 ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">暂无活动记录</p> : (
        <ul className="relative space-y-0 pl-3">
          <div className="absolute bottom-2 left-[7px] top-2 w-px bg-[var(--color-border)]" />
          {items.map((row, idx) => (
            <li key={String(row.id ?? idx)} className="relative pb-3 last:pb-0">
              <span className="absolute -left-3 top-1.5 h-2.5 w-2.5 rounded-full border-2 border-white bg-[var(--color-primary)]" />
              <div className="ml-2 rounded border border-[var(--color-border)] bg-[var(--color-surface-soft)] px-3 py-2">
                <p className="text-xs font-medium text-[var(--color-text)]">{String(row.title ?? "系统活动")}</p>
                <p className="mt-0.5 text-[11px] text-[var(--color-text-muted)]">{formatRelativeTime(String(row.created_at ?? ""))} · {String(row.channel ?? row.biz_type ?? "system")}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </DashboardCard>
  );
}
