"use client";

import { IndustrialPanel, typography } from "@zhenhang/ui";
import { designTokens } from "@zhenhang/ui";
import Link from "next/link";

const ACTIONS = [
  { href: "/quotes/new", label: "新建报价", desc: "向导创建" },
  { href: "/quotes", label: "报价中心", desc: "列表与工作台" },
  { href: "/notifications", label: "通知中心", desc: "消息与已读" },
  { href: "/workshop", label: "车间看板", desc: "产线状态" },
];

export function QuickActionsPanel() {
  return (
    <IndustrialPanel title="快捷入口">
      <div className="grid gap-2 sm:grid-cols-2">
        {ACTIONS.map((action) => (
          <Link
            key={action.href}
            href={action.href}
            className="rounded-lg border px-3 py-3 transition hover:border-[#475569]"
            style={{
              borderColor: designTokens.colors.border.default,
              backgroundColor: designTokens.colors.background.subtle,
            }}
          >
            <p className={typography.cardTitle}>{action.label}</p>
            <p className={typography.caption}>{action.desc}</p>
          </Link>
        ))}
      </div>
    </IndustrialPanel>
  );
}
