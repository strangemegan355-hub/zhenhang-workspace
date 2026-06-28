"use client";

import { IndustrialPanel, typography } from "@zhenhang/ui";
import Link from "next/link";

const MOCK_FEED = [
  { id: "1", title: "审批状态更新", time: "刚刚", channel: "workflow" },
  { id: "2", title: "导出完成", time: "2 分钟前", channel: "quote" },
  { id: "3", title: "新通知", time: "8 分钟前", channel: "notification" },
];

export function RealtimeNotificationsPanel({ unreadCount = 0 }: { unreadCount?: number }) {
  const items =
    unreadCount > 0
      ? [
          ...MOCK_FEED.slice(0, 2),
          { id: "unread", title: `${unreadCount} 条未读通知`, time: "待处理", channel: "notification" },
        ]
      : MOCK_FEED;

  return (
    <IndustrialPanel
      title="实时通知"
      toolbar={
        <Link href="/notifications" className="text-xs text-blue-500 hover:underline">
          消息中心
        </Link>
      }
    >
      <ul className="space-y-2">
        {items.map((item) => (
          <li
            key={item.id}
            className="flex items-center justify-between gap-2 border-b border-[var(--color-border-soft)] py-2 last:border-0"
          >
            <div>
              <p className={typography.cardTitle}>{item.title}</p>
              <p className={typography.caption}>{item.channel}</p>
            </div>
            <span className={typography.caption}>{item.time}</span>
          </li>
        ))}
      </ul>
    </IndustrialPanel>
  );
}
