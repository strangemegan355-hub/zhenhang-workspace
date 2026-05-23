"use client";

import type { CSSProperties, ReactNode } from "react";
import { useState } from "react";
import { designTokens } from "../../theme/design-tokens";
import { interactionTokens } from "../../theme/interaction-tokens";
import { workspaceTokens } from "../../theme/workspace-tokens";
import { typography } from "../../theme/typography";
import { cn } from "../../utils/cn";

export type WorkspaceSidebarProps = {
  title?: string;
  children?: ReactNode;
  footer?: ReactNode;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  width?: number;
  className?: string;
};

export function WorkspaceSidebar({
  title = "导航",
  children,
  footer,
  collapsible = true,
  defaultCollapsed = false,
  width = workspaceTokens.sidebarWidth,
  className,
}: WorkspaceSidebarProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const w = collapsed ? workspaceTokens.sidebarCollapsedWidth : width;

  const style: CSSProperties = {
    width: w,
    minWidth: w,
    backgroundColor: workspaceTokens.background.sidebar,
    borderRight: `1px solid ${workspaceTokens.border}`,
    transition: `width ${interactionTokens.transition.fast} ease-out, min-width ${interactionTokens.transition.fast} ease-out`,
  };

  return (
    <aside className={cn("flex shrink-0 flex-col overflow-hidden", className)} style={style}>
      <div
        className="flex shrink-0 items-center justify-between border-b px-2"
        style={{
          height: interactionTokens.layout.dockHeader,
          borderColor: designTokens.colors.border.muted,
        }}
      >
        {!collapsed ? (
          <span className={typography.sectionTitle} style={{ fontSize: 10 }}>
            {title}
          </span>
        ) : (
          <span className="sr-only">{title}</span>
        )}
        {collapsible ? (
          <button
            type="button"
            aria-label={collapsed ? "展开侧栏" : "收起侧栏"}
            title={collapsed ? `展开 · ${title}` : "收起侧栏"}
            className="rounded px-1.5 py-0.5 text-xs"
            style={{
              color: designTokens.colors.text.muted,
              transition: `background-color ${interactionTokens.transition.fast}`,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = interactionTokens.hover.bg;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "transparent";
            }}
            onClick={() => setCollapsed((c) => !c)}
          >
            {collapsed ? "»" : "«"}
          </button>
        ) : null}
      </div>
      <div
        className="min-h-0 flex-1 overflow-auto"
        style={{ padding: collapsed ? 4 : interactionTokens.layout.panelPadding }}
      >
        {collapsed ? null : children}
      </div>
      {footer && !collapsed ? (
        <div
          className="shrink-0 border-t"
          style={{
            borderColor: designTokens.colors.border.muted,
            padding: interactionTokens.layout.panelPadding,
          }}
        >
          {footer}
        </div>
      ) : null}
    </aside>
  );
}
