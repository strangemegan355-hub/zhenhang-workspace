"use client";

import { useNotificationUnreadCountQuery } from "@zhenhang/query-hooks";
import Link from "next/link";

export function NotificationBell() {
  const unreadQuery = useNotificationUnreadCountQuery();
  const count = unreadQuery.data ?? 0;
  return (
    <Link href="/notifications" className="relative inline-flex items-center text-sm hover:opacity-80">
      <span className="inline-flex items-center gap-1.5">
        <span className="h-2 w-2 rounded-full bg-emerald-500" title="实时通道已启用" />
        通知
      </span>
      {count > 0 ? (
        <span className="ml-2 rounded-full bg-red-500 px-2 py-0.5 text-xs text-white">{count}</span>
      ) : null}
    </Link>
  );
}
