/**
 * Industrial design tokens — single source for @zhenhang/ui.
 * Light theme placeholders for future extension; default palette is dark industrial.
 */

export type ThemeMode = "dark" | "light";

const darkColors = {
  background: {
    base: "#0F172A",
    elevated: "#111827",
    panel: "#1E293B",
    subtle: "#0B1220",
  },
  border: {
    default: "#334155",
    muted: "#1E293B",
    focus: "#2563EB",
  },
  primary: {
    default: "#2563EB",
    hover: "#1D4ED8",
    muted: "#1E3A8A",
  },
  success: {
    default: "#22C55E",
    muted: "#14532D",
  },
  warning: {
    default: "#F59E0B",
    muted: "#78350F",
  },
  danger: {
    default: "#EF4444",
    muted: "#7F1D1D",
  },
  text: {
    primary: "#F8FAFC",
    secondary: "#CBD5E1",
    muted: "#94A3B8",
    inverse: "#0F172A",
  },
} as const;

const lightColors = {
  background: {
    base: "#F8FAFC",
    elevated: "#FFFFFF",
    panel: "#FFFFFF",
    subtle: "#F1F5F9",
  },
  border: {
    default: "#E2E8F0",
    muted: "#CBD5E1",
    focus: "#2563EB",
  },
  primary: darkColors.primary,
  success: darkColors.success,
  warning: darkColors.warning,
  danger: darkColors.danger,
  text: {
    primary: "#0F172A",
    secondary: "#334155",
    muted: "#64748B",
    inverse: "#F8FAFC",
  },
} as const;

export const spacing = {
  0: "0",
  1: "0.25rem",
  2: "0.5rem",
  3: "0.75rem",
  4: "1rem",
  5: "1.25rem",
  6: "1.5rem",
  8: "2rem",
  10: "2.5rem",
  12: "3rem",
} as const;

export const radius = {
  sm: "0.375rem",
  md: "0.5rem",
  lg: "0.75rem",
  xl: "1rem",
} as const;

export const shadow = {
  sm: "0 1px 2px 0 rgba(0, 0, 0, 0.35)",
  md: "0 4px 6px -1px rgba(0, 0, 0, 0.4)",
  panel: "0 1px 3px 0 rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(51, 65, 85, 0.5)",
} as const;

export const zIndex = {
  base: 0,
  dropdown: 10,
  sticky: 20,
  overlay: 30,
  modal: 40,
  toast: 50,
} as const;

/** Font scale for theme switching (class strings live in typography.ts). */
export const typographyScale = {
  pageTitle: { fontSize: "1.25rem", fontWeight: 600, lineHeight: 1.35 },
  sectionTitle: { fontSize: "0.875rem", fontWeight: 600, lineHeight: 1.4 },
  cardTitle: { fontSize: "0.875rem", fontWeight: 600, lineHeight: 1.4 },
  body: { fontSize: "0.875rem", fontWeight: 400, lineHeight: 1.6 },
  caption: { fontSize: "0.75rem", fontWeight: 400, lineHeight: 1.4 },
  kpi: { fontSize: "1.5rem", fontWeight: 600, lineHeight: 1.2 },
  monoNumber: { fontSize: "0.875rem", fontWeight: 500, lineHeight: 1.4 },
} as const;

export const themes = {
  dark: { colors: darkColors },
  light: { colors: lightColors },
} as const;

/** Active industrial theme (dark). */
export const colors = darkColors;

export const designTokens = {
  colors,
  spacing,
  radius,
  shadow,
  typography: typographyScale,
  zIndex,
  themes,
} as const;

export type DesignTokens = typeof designTokens;
