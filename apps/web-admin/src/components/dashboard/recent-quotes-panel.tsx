"use client";

import { IndustrialPanel, typography } from "@zhenhang/ui";
import Link from "next/link";
import type { RecentQuote } from "./types";

const STATE_LABELS: Record<string, string> = {
  draft: "草稿",
  reviewing: "审批中",
  approved: "已批准",
};

function formatMoney(value: string | number | undefined) {
  const n = Number(value ?? 0);
  return new Intl.NumberFormat("zh-CN", { style: "currency", currency: "CNY", maximumFractionDigits: 0 }).format(n);
}

export function RecentQuotesPanel({ recent }: { recent: RecentQuote[] }) {
  return (
    <IndustrialPanel
      title="最近报价"
      toolbar={
        <Link href="/quotes" className="text-xs text-blue-500 hover:underline">
          全部
        </Link>
      }
      empty={recent.length === 0}
      emptyMessage="暂无报价，请创建首单。"
    >
      <ul className="divide-y divide-[#334155]">
        {recent.map((q) => (
          <li key={String(q.id)} className="flex items-center justify-between py-2 text-sm">
            <div>
              <div className={typography.cardTitle}>{String(q.quote_no)}</div>
              <div className={typography.caption}>{String(q.title ?? "")}</div>
            </div>
            <div className="text-right">
              <div className={typography.caption}>
                {STATE_LABELS[String(q.workflow_state)] ?? q.workflow_state}
              </div>
              <div className={typography.monoNumber}>{formatMoney(q.total_amount)}</div>
            </div>
          </li>
        ))}
      </ul>
    </IndustrialPanel>
  );
}
