import { designTokens } from "./design-tokens";

const { colors } = designTokens;

/** Tailwind-friendly class strings referencing token colors. */
export const typography = {
  pageTitle: `text-2xl font-semibold tracking-tight text-[${colors.text.primary}]`,
  sectionTitle: `text-base font-semibold uppercase tracking-wide text-[${colors.text.secondary}]`,
  cardTitle: `text-base font-semibold text-[${colors.text.primary}]`,
  body: `text-base leading-relaxed text-[${colors.text.secondary}]`,
  caption: `text-sm text-[${colors.text.muted}]`,
  kpi: `text-3xl font-semibold tabular-nums text-[${colors.text.primary}]`,
  monoNumber: `font-mono text-base tabular-nums text-[${colors.text.primary}]`,
} as const;

export type TypographyVariant = keyof typeof typography;

export const fontFamily = {
  sans: 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  mono: 'ui-monospace, "Cascadia Code", "SF Mono", Consolas, monospace',
} as const;
