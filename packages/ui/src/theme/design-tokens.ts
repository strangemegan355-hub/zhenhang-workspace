/**
 * ZhenHang Industrial OS design tokens.
 * Enterprise industrial SaaS with a clean future-tech feel.
 */
export type ThemeMode = "dark" | "light";

const lightColors = {
  background: {
    base: "#F4F5F6",
    elevated: "#FFFFFF",
    panel: "#FFFFFF",
    subtle: "#FAFBFC",
  },
  border: {
    default: "#D1D8DD",
    muted: "#EBEEF0",
    focus: "#171717",
  },
  primary: {
    default: "#171717",
    hover: "#000000",
    muted: "#E8E8E8",
    light: "#F0F0F0",
  },
  success: {
    default: "#10B981",
    muted: "#D1FAE5",
  },
  warning: {
    default: "#F59E0B",
    muted: "#FEF3C7",
  },
  danger: {
    default: "#EF4444",
    muted: "#FEE2E2",
  },
  info: {
    default: "#06B6D4",
    muted: "#CFFAFE",
  },
  text: {
    primary: "#36414C",
    secondary: "#6C7680",
    muted: "#8D99A6",
    inverse: "#FFFFFF",
  },
  sidebar: {
    bg: "#FFFFFF",
    bgGradient: "#FFFFFF",
    hover: "#F4F5F6",
    active: "#F0F0F0",
    text: "#6C7680",
    textActive: "#171717",
    border: "#D1D8DD",
  },
} as const;

const darkColors = {
  background: {
    base: "#0B1220",
    elevated: "#111827",
    panel: "#111827",
    subtle: "#0F172A",
  },
  border: {
    default: "#243041",
    muted: "#1F2937",
    focus: "#60A5FA",
  },
  primary: {
    default: "#60A5FA",
    hover: "#93C5FD",
    muted: "#172554",
    light: "#0F172A",
  },
  success: {
    default: "#34D399",
    muted: "#064E3B",
  },
  warning: {
    default: "#FBBF24",
    muted: "#78350F",
  },
  danger: {
    default: "#F87171",
    muted: "#7F1D1D",
  },
  info: {
    default: "#22D3EE",
    muted: "#083344",
  },
  text: {
    primary: "#F8FAFC",
    secondary: "#CBD5E1",
    muted: "#94A3B8",
    inverse: "#0F172A",
  },
  sidebar: {
    bg: "#0F172A",
    bgGradient: "linear-gradient(180deg, #0F172A 0%, #111827 100%)",
    hover: "rgba(255,255,255,0.06)",
    active: "rgba(96,165,250,0.18)",
    text: "#CBD5E1",
    textActive: "#FFFFFF",
    border: "rgba(255,255,255,0.08)",
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
  16: "4rem",
} as const;

export const radius = {
  none: "0",
  sm: "0.25rem",
  md: "0.375rem",
  lg: "0.375rem",
  xl: "0.5rem",
  "2xl": "0.5rem",
  "3xl": "0.5rem",
  card: "6px",
  full: "9999px",
} as const;

export const shadow = {
  none: "none",
  xs: "none",
  sm: "0 1px 2px rgba(0, 0, 0, 0.04)",
  md: "0 1px 3px rgba(0, 0, 0, 0.06)",
  lg: "0 2px 6px rgba(0, 0, 0, 0.08)",
  panelLight: "0 1px 2px rgba(0, 0, 0, 0.04)",
  panelDark: "0 1px 2px rgba(0, 0, 0, 0.2)",
  card: "0 1px 2px rgba(0, 0, 0, 0.04)",
} as const;

export const zIndex = {
  base: 0,
  dropdown: 10,
  sticky: 20,
  overlay: 30,
  modal: 40,
  toast: 50,
} as const;

export const typographyScale = {
  pageTitle: { fontSize: "1.5rem", fontWeight: 700, lineHeight: 1.25 },
  sectionTitle: { fontSize: "0.875rem", fontWeight: 600, lineHeight: 1.4, letterSpacing: "0.02em" },
  cardTitle: { fontSize: "0.875rem", fontWeight: 600, lineHeight: 1.4 },
  body: { fontSize: "0.875rem", fontWeight: 400, lineHeight: 1.6 },
  caption: { fontSize: "0.75rem", fontWeight: 400, lineHeight: 1.4 },
  kpi: { fontSize: "1.875rem", fontWeight: 700, lineHeight: 1.15, letterSpacing: "-0.01em" },
  monoNumber: { fontSize: "0.875rem", fontWeight: 500, lineHeight: 1.4, fontFamily: "monospace" },
} as const;

export const themes = {
  light: { colors: lightColors },
  dark: { colors: darkColors },
} as const;

export const colors = lightColors;

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
