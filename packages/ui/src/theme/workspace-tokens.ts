import { designTokens } from "./design-tokens";

/** Industrial workspace layout metrics (Siemens/ABB-style dense console). */
export const workspaceTokens = {
  toolbarHeight: 40,
  dockHeaderHeight: 32,
  dockDefaultHeight: 280,
  sidebarWidth: 240,
  sidebarCollapsedWidth: 48,
  panelPadding: 12,
  border: designTokens.colors.border.default,
  background: {
    shell: designTokens.colors.background.base,
    toolbar: designTokens.colors.background.elevated,
    sidebar: designTokens.colors.background.panel,
    main: designTokens.colors.background.base,
    dock: designTokens.colors.background.panel,
    panel: designTokens.colors.background.elevated,
  },
  radius: designTokens.radius.sm,
} as const;
