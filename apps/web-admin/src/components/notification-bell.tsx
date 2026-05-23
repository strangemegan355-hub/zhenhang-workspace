"use client";

import { useNotificationUnreadCountQuery } from "@zhenhang/query-hooks";

export function NotificationBell() {
  const unreadQuery = useNotificationUnreadCountQuery();
  const count = unreadQuery.data ?? 0;
  return (
    <div className="relative text-sm">
      <span className="inline-flex items-center gap-1.5">
        <span className="h-2 w-2 rounded-full bg-emerald-500" title="实时已连接" />
        Notifications
      </span>
      <span className="ml-2 rounded-full bg-red-500 px-2 py-0.5 text-xs text-white">{count}</span>
    </div>
  );
}
