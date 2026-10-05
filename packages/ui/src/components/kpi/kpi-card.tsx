"use client";

import type { CSSProperties, ReactNode } from "react";
import { designTokens } from "../../theme/design-tokens";
import { typography } from "../../theme/typography";
import { ShimmerBlock } from "../loading/shimmer";
import { cn } from "../../utils/cn";

export type KpiCardStatus = "success" | "warning" | "danger" | "normal";
export type TrendDirection = "up" | "down" | "flat";

export type KpiCardProps = {
  title: string;
  value: string | number;
  trend?: string;
  trendDirection?: TrendDirection;
  trendPercent?: number | string;
  status?: KpiCardStatus;
  icon?: ReactNode;
  loading?: boolean;
  compact?: boolean;
  showStatusIndicator?: boolean;
  className?: string;
  onClick?: () => void;
};

const statusAccent: Record<KpiCardStatus, string> = {
  normal: designTokens.colors.primary.default,
  success: designTokens.colors.success.default,
  warning: designTokens.colors.warning.default,
  danger: designTokens.colors.danger.default,
};

const trendArrow: Record<TrendDirection, string> = {
  up: "↑",
  down: "↓",
  flat: "→",
};

function trendColor(direction: TrendDirection, status: KpiCardStatus): string {
  if (direction === "flat") return designTokens.colors.text.muted;
  if (direction === "up") return status === "danger" ? designTokens.colors.danger.default : designTokens.colors.success.default;
  return status === "success" ? designTokens.colors.warning.default : designTokens.colors.danger.default;
}

export function KpiCard({
  title,
  value,
  trend,
  trendDirection = "flat",
  trendPercent,
  status = "normal",
  icon,
  loading = false,
  compact = false,
  showStatusIndicator = true,
  className,
  onClick,
}: KpiCardProps) {
  const { colors, radius, shadow, spacing } = designTokens;
  const accent = statusAccent[status];

  const style: CSSProperties = {
    backgroundColor: colors.background.elevated,
    border: `1px solid ${colors.border.default}`,
    borderRadius: radius.lg,
    boxShadow: shadow.sm,
    borderLeftWidth: "3px",
    borderLeftColor: accent,
    padding: compact ? spacing[3] : spacing[4],
  };

  const Wrapper = onClick ? "button" : "div";
  const hasTrend = Boolean(trend || trendPercent != null);

  return (
    <Wrapper
      type={onClick ? "button" : undefined}
      onClick={onClick}
      className={cn(
        "group block w-full text-left transition-all duration-150",
        "hover:border-[#c8d8f0] hover:bg-[#f0f6ff] hover:shadow-sm",
        onClick && "cursor-pointer",
        className,
      )}
      style={style}
    >
      <div className="flex items-start justify-between gap-2">
        <span className={typography.caption}>{title}</span>
        <div className="flex items-center gap-2">
          {showStatusIndicator && !loading ? (
            <span
              className="h-2 w-2 shrink-0 rounded-full"
              style={{ backgroundColor: accent, boxShadow: `0 0 6px ${accent}55` }}
              title={status}
            />
          ) : null}
          {icon ? <span className="text-[#6b7fa3]">{icon}</span> : null}
        </div>
      </div>

      {loading ? (
        <div className={compact ? "mt-2 space-y-2" : "mt-3 space-y-2"}>
          <ShimmerBlock className={compact ? "h-6 w-2/3" : "h-8 w-2/3"} />
          <ShimmerBlock className="h-3 w-1/3" />
        </div>
      ) : (
        <>
          <div
            className={cn(
              compact ? "mt-1.5 text-xl" : typography.kpi,
              typography.monoNumber,
              compact ? "font-semibold tabular-nums" : "mt-2",
            )}
          >
            {value}
          </div>
          {hasTrend ? (
            <p
              className={cn(typography.caption, compact ? "mt-1" : "mt-1.5", "flex items-center gap-1")}
              style={{ color: trendColor(trendDirection, status) }}
            >
              <span className="font-mono text-[11px]">{trendArrow[trendDirection]}</span>
              {trendPercent != null ? (
                <span className="font-mono tabular-nums">
                  {typeof trendPercent === "number" ? `${trendPercent > 0 ? "+" : ""}${trendPercent}%` : trendPercent}
                </span>
              ) : null}
              {trend ? <span>{trend}</span> : null}
            </p>
          ) : null}
        </>
      )}
    </Wrapper>
  );
}
