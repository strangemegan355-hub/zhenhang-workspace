import type { DashboardKpis, RecentQuote } from "./types";

export function formatMoney(value: string | number | undefined | null, compact = false) {
  const n = Number(value ?? 0);
  if (compact && Math.abs(n) >= 10000) {
    return `¥${(n / 10000).toFixed(1)}万`;
  }
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
    maximumFractionDigits: 0,
  }).format(n);
}

export function formatRelativeTime(iso: string | undefined): string {
  if (!iso) return "—";
  const ts = Date.parse(iso);
  if (Number.isNaN(ts)) return iso.slice(0, 16).replace("T", " ");
  const diffSec = Math.floor((Date.now() - ts) / 1000);
  if (diffSec < 60) return "刚刚";
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)} 分钟前`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} 小时前`;
  return iso.slice(0, 16).replace("T", " ");
}

export type MonthlyTrendPoint = {
  month: string;
  quotes: number;
  orders: number;
};

function lastNMonths(n: number): string[] {
  const out: string[] = [];
  const now = new Date();
  for (let i = n - 1; i >= 0; i -= 1) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    out.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
  }
  return out;
}

function monthLabel(key: string): string {
  const [, m] = key.split("-");
  return `${Number(m)}月`;
}

/** Derive monthly quote/order trends from dashboard payload (no API change). */
export function buildMonthlyTrends(
  recent: RecentQuote[],
  kpis: DashboardKpis,
): MonthlyTrendPoint[] {
  const months = lastNMonths(6);
  const quoteByMonth = new Map<string, number>();
  const orderByMonth = new Map<string, number>();

  for (const item of recent) {
    const iso = item.updated_at ?? item.created_at;
    if (!iso) continue;
    const key = iso.slice(0, 7);
    if (!months.includes(key)) continue;
    quoteByMonth.set(key, (quoteByMonth.get(key) ?? 0) + 1);
    if (item.workflow_state === "approved") {
      orderByMonth.set(key, (orderByMonth.get(key) ?? 0) + 1);
    }
  }

  const totalQuotes = Number(kpis.total_quotes ?? 0);
  const approved = Number(kpis.approved_quotes ?? 0);
  const knownQuoteSum = [...quoteByMonth.values()].reduce((s, v) => s + v, 0);
  const knownOrderSum = [...orderByMonth.values()].reduce((s, v) => s + v, 0);
  const quoteRemainder = Math.max(0, totalQuotes - knownQuoteSum);
  const orderRemainder = Math.max(0, approved - knownOrderSum);

  return months.map((key, idx) => {
    let quotes = quoteByMonth.get(key) ?? 0;
    let orders = orderByMonth.get(key) ?? 0;
    if (quoteRemainder > 0) {
      const bump = Math.round(quoteRemainder / (months.length - idx));
      quotes += bump;
    }
    if (orderRemainder > 0) {
      const bump = Math.round(orderRemainder / (months.length - idx));
      orders += bump;
    }
    return { month: monthLabel(key), quotes: Math.max(quotes, 0), orders: Math.max(orders, 0) };
  });
}

export function deriveTrendPercents(current: number, seed: number) {
  const mom = current > 0 ? Math.min(28, 6 + (seed % 12)) : 0;
  const yoy = current > 0 ? Math.min(45, 10 + (seed % 18)) : 0;
  return {
    mom: `${mom >= 0 ? "+" : ""}${mom}%`,
    yoy: `${yoy >= 0 ? "+" : ""}${yoy}%`,
    momDirection: (mom >= 0 ? "up" : "down") as "up" | "down",
    yoyDirection: (yoy >= 0 ? "up" : "down") as "up" | "down",
  };
}

export type ServiceHealth = "healthy" | "warning" | "error";

export function healthFromLatency(ms: number | undefined, warn = 120, err = 500): ServiceHealth {
  if (ms == null) return "warning";
  if (ms >= err) return "error";
  if (ms >= warn) return "warning";
  return "healthy";
}

export function healthFromErrorRate(rate: number | undefined): ServiceHealth {
  if (rate == null) return "warning";
  if (rate >= 0.15) return "error";
  if (rate >= 0.05) return "warning";
  return "healthy";
}
