"use client";

import { useMemo, useState } from "react";
import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { TrendingUp } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import { buildMonthlyTrends } from "./dashboard-utils";
import type { DashboardKpis, RecentQuote } from "./types";

export function SalesOverviewPanel({ recent, kpis }: { recent: RecentQuote[]; kpis: DashboardKpis }) {
  const [activeTab, setActiveTab] = useState<"all" | "quotes" | "orders">("all");
  const data = useMemo(() => buildMonthlyTrends(recent, kpis), [recent, kpis]);
  const totalQuotes = data.reduce((s, d) => s + d.quotes, 0);
  const totalOrders = data.reduce((s, d) => s + d.orders, 0);

  return (
    <DashboardCard
      title="销售控制中心"
      fill
      toolbar={
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 rounded-full bg-[var(--color-primary-soft)] px-2.5 py-1 text-[11px] font-medium text-[var(--color-text)]">
            <TrendingUp className="h-3 w-3" />
            近 6 月
          </span>
          <div className="flex rounded border border-[var(--color-border)] p-0.5 text-[11px]">
            {([["all", "全部"], ["quotes", "报价"], ["orders", "订单"]] as const).map(([key, label]) => (
              <button key={key} type="button" onClick={() => setActiveTab(key)} className={`rounded px-2.5 py-1 ${activeTab === key ? "bg-[var(--color-primary)] text-white" : "text-[var(--color-text-muted)] hover:text-[var(--color-text)]"}`}>{label}</button>
            ))}
          </div>
        </div>
      }
      contentClassName="flex flex-col"
    >
      <div className="mb-4 flex flex-wrap gap-4 text-sm">
        <div><span className="text-[var(--color-text-muted)]">报价累计 </span><span className="font-semibold tabular-nums text-[var(--color-text)]">{totalQuotes}</span></div>
        <div><span className="text-[var(--color-text-muted)]">订单累计 </span><span className="font-semibold tabular-nums text-[var(--color-text)]">{totalOrders}</span></div>
      </div>
      <div className="min-h-[400px] flex-1">
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={data} margin={{ top: 8, right: 12, left: -8, bottom: 0 }}>
            <defs>
              <linearGradient id="quoteGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#171717" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#171717" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="orderGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6c7680" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#6c7680" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#d1d8dd" vertical={false} />
            <XAxis dataKey="month" tick={{ fill: "#6c7680", fontSize: 12 }} axisLine={{ stroke: "#d1d8dd" }} tickLine={false} />
            <YAxis tick={{ fill: "#6c7680", fontSize: 12 }} axisLine={false} tickLine={false} allowDecimals={false} />
            <Tooltip contentStyle={{ borderRadius: 6, border: "1px solid #d1d8dd", boxShadow: "0 1px 2px rgba(0,0,0,0.04)" }} />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
            {(activeTab === "all" || activeTab === "quotes") && (
              <Area type="monotone" dataKey="quotes" name="月度报价" stroke="#171717" strokeWidth={2} fill="url(#quoteGradient)" dot={{ r: 3, fill: "#171717", strokeWidth: 0 }} activeDot={{ r: 5 }} />
            )}
            {(activeTab === "all" || activeTab === "orders") && (
              <Area type="monotone" dataKey="orders" name="月度订单" stroke="#6c7680" strokeWidth={2} fill="url(#orderGradient)" dot={{ r: 3, fill: "#6c7680", strokeWidth: 0 }} activeDot={{ r: 5 }} />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </DashboardCard>
  );
}
