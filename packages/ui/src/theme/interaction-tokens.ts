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
    tableRow: 36,
  },

  layout: {
    toolbar: 44,
    panelPadding: 16,
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
      border: `${designTokens.colors.success.default}33`,
    },
    warning: {
      fg: designTokens.colors.warning.default,
      bg: designTokens.colors.warning.muted,
      border: `${designTokens.colors.warning.default}33`,
    },
    danger: {
      fg: designTokens.colors.danger.default,
      bg: designTokens.colors.danger.muted,
      border: `${designTokens.colors.danger.default}33`,
    },
    info: {
      fg: designTokens.colors.primary.default,
      bg: designTokens.colors.primary.light,
      border: `${designTokens.colors.primary.default}22`,
    },
    idle: {
      fg: designTokens.colors.text.muted,
      bg: designTokens.colors.background.subtle,
      border: designTokens.colors.border.default,
    },
    processing: {
      fg: designTokens.colors.warning.default,
      bg: designTokens.colors.warning.muted,
      border: `${designTokens.colors.warning.default}44`,
    },
  },

  focusRing: `0 0 0 2px ${designTokens.colors.background.base}, 0 0 0 3px ${designTokens.colors.primary.muted}`,

  hover: {
    border: designTokens.colors.border.default,
    borderEmphasis: "#1677ff",
    bg: designTokens.colors.primary.light,
    bgSubtle: "#f0f6ff",
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