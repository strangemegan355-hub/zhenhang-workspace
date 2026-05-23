import { designTokens } from "./design-tokens";

export type InteractionDensity = "compact" | "normal";
export type InteractionStatus = "success" | "warning" | "danger" | "info" | "idle" | "processing";

export const interactionTokens = {
  density: {
    compact: "compact",
    normal: "normal",
  } as const,

  controlHeight: {
    toolbarButton: 32,
    input: 32,
    dockTab: 28,
    tableRow: 32,
  },

  layout: {
    toolbar: 40,
    panelPadding: 12,
    dockHeader: 32,
    sectionGapSm: 8,
    sectionGapMd: 12,
    sectionGapLg: 16,
  },

  transition: {
    fast: "120ms",
    normal: "180ms",
  },

  status: {
    success: {
      fg: designTokens.colors.success.default,
      bg: designTokens.colors.success.muted,
      border: `${designTokens.colors.success.default}44`,
    },
    warning: {
      fg: designTokens.colors.warning.default,
      bg: designTokens.colors.warning.muted,
      border: `${designTokens.colors.warning.default}44`,
    },
    danger: {
      fg: designTokens.colors.danger.default,
      bg: designTokens.colors.danger.muted,
      border: `${designTokens.colors.danger.default}44`,
    },
    info: {
      fg: designTokens.colors.primary.default,
      bg: designTokens.colors.primary.muted,
      border: `${designTokens.colors.primary.default}44`,
    },
    idle: {
      fg: designTokens.colors.text.muted,
      bg: designTokens.colors.background.panel,
      border: designTokens.colors.border.default,
    },
    processing: {
      fg: designTokens.colors.warning.default,
      bg: designTokens.colors.warning.muted,
      border: `${designTokens.colors.warning.default}55`,
    },
  },

  focusRing: `0 0 0 2px ${designTokens.colors.background.base}, 0 0 0 3px ${designTokens.colors.primary.default}66`,

  hover: {
    border: designTokens.colors.border.default,
    borderEmphasis: "#475569",
    bg: "#1a2332",
  },
} as const;

export function statusPalette(status: InteractionStatus) {
  return interactionTokens.status[status];
}

/** Map legacy ok/warn/error levels to interaction status */
export function legacyLevelToStatus(level: "ok" | "warn" | "error" | "idle"): InteractionStatus {
  if (level === "ok") return "success";
  if (level === "warn") return "warning";
  if (level === "error") return "danger";
  return "idle";
}

/** Workflow / quote states → status badge variant */
export function workflowStateToStatus(state: string): InteractionStatus {
  const map: Record<string, InteractionStatus> = {
    draft: "idle",
    reviewing: "processing",
    approved: "success",
    rejected: "danger",
    running: "processing",
    idle: "idle",
    alarm: "danger",
  };
  return map[state] ?? "info";
}

export function riskLevelToStatus(level: "high" | "medium" | "low"): InteractionStatus {
  if (level === "high") return "danger";
  if (level === "medium") return "warning";
  return "idle";
}

export function exportStatusToInteraction(status: string): InteractionStatus {
  const s = status.toLowerCase();
  if (s === "completed" || s === "success") return "success";
  if (s === "failed" || s === "error") return "danger";
  if (s === "pending" || s === "processing" || s === "running") return "processing";
  return "idle";
}
