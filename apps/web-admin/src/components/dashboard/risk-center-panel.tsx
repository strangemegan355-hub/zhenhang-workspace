"use client";

import { IndustrialPanel, StatusBadge, typography, riskLevelToStatus } from "@zhenhang/ui";
import Link from "next/link";
import type { DashboardKpis, RiskItem } from "./types";

function buildRisksFromKpis(kpis: DashboardKpis): RiskItem[] {
  const items: RiskItem[] = [];
  const pending = Number(kpis.pending_approval ?? 0);
  const exportPending = Number(kpis.export_pending ?? 0);
  const unread = Number(kpis.unread_notifications ?? 0);

  if (pending > 0) {
    items.push({
      id: "approval-timeout",
      label: "超时审批",
      level: pending >= 5 ? "high" : "medium",
      count: pending,
      detail: `${pending} 单待处理`,
      href: "/quotes",
    });
  }
  if (exportPending > 0) {
    items.push({
      id: "export-fail",
      label: "导出排队 / 失败风险",
      level: exportPending >= 3 ? "high" : "medium",
      count: exportPending,
      detail: `${exportPending} 个任务排队`,
      href: "/quotes",
    });
  }
  if (unread > 0) {
    items.push({
      id: "notifications",
      label: "待处理通知",
      level: "low",
      count: unread,
      href: "/notifications",
    });
  }

  return items;
}

const FALLBACK_RISKS: RiskItem[] = [
  { id: "low-margin", label: "低毛利报价", level: "medium", count: 2, detail: "毛利率 < 15%", href: "/quotes" },
  { id: "approval-timeout", label: "超时审批", level: "high", count: 1, detail: "> 48h 未处理", href: "/quotes" },
  { id: "export-fail", label: "导出失败", level: "medium", count: 0, detail: "近 24h 无失败", href: "/quotes" },
  { id: "bom-missing", label: "BOM 缺失", level: "low", count: 1, detail: "关联 BOM 未绑定", href: "/quotes" },
  { id: "customer-risk", label: "高风险客户", level: "high", count: 1, detail: "信用预警客户", href: "/quotes" },
];

const LEVEL_LABEL = { high: "高", medium: "中", low: "低" } as const;

export function RiskCenterPanel({ kpis }: { kpis?: DashboardKpis }) {
  const derived = kpis ? buildRisksFromKpis(kpis) : [];
  const display = derived.length > 0 ? derived : FALLBACK_RISKS;

  return (
    <IndustrialPanel title="风险中心">
      <ul className="space-y-2">
        {display.map((risk) => {
          const row = (
            <li
              key={risk.id}
              className="flex items-center justify-between gap-2 rounded px-2 py-2 transition hover:bg-[#1a2332]"
              style={{ minHeight: 32 }}
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <StatusBadge
                    status={riskLevelToStatus(risk.level)}
                    label={LEVEL_LABEL[risk.level]}
                    compact
                  />
                  <span className={typography.cardTitle}>{risk.label}</span>
                </div>
                {risk.detail ? <p className={`${typography.caption} mt-0.5`}>{risk.detail}</p> : null}
              </div>
              {risk.count != null ? (
                <span className={typography.monoNumber}>{risk.count}</span>
              ) : null}
            </li>
          );
          return risk.href ? (
            <Link key={risk.id} href={risk.href} className="block">
              {row}
            </Link>
          ) : (
            row
          );
        })}
      </ul>
    </IndustrialPanel>
  );
}
