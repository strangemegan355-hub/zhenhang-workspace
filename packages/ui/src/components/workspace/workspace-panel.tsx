"use client";

import type { CSSProperties, ReactNode } from "react";
import { designTokens } from "../../theme/design-tokens";
import { interactionTokens } from "../../theme/interaction-tokens";
import { workspaceTokens } from "../../theme/workspace-tokens";
import { typography } from "../../theme/typography";
import { cn } from "../../utils/cn";

export type WorkspacePanelProps = {
  title?: string;
  toolbar?: ReactNode;
  footer?: ReactNode;
  children?: ReactNode;
  className?: string;
  bodyClassName?: string;
  noPadding?: boolean;
};

export function WorkspacePanel({
  title,
  toolbar,
  footer,
  children,
  className,
  bodyClassName,
  noPadding = false,
}: WorkspacePanelProps) {
  const shellStyle: CSSProperties = {
    backgroundColor: workspaceTokens.background.panel,
    border: `1px solid ${workspaceTokens.border}`,
    borderRadius: workspaceTokens.radius,
  };

  return (
    <section className={cn("flex min-h-0 flex-col overflow-hidden", className)} style={shellStyle}>
      {title || toolbar ? (
        <header
          className="flex shrink-0 items-center justify-between gap-2 border-b"
          style={{
            borderColor: designTokens.colors.border.muted,
            padding: `8px ${interactionTokens.layout.panelPadding}px`,
            minHeight: 32,
          }}
        >
          {title ? <h3 className={typography.cardTitle}>{title}</h3> : <span />}
          {toolbar ? <div className="flex items-center gap-1">{toolbar}</div> : null}
        </header>
      ) : null}
      <div
        className={cn("min-h-0 flex-1 overflow-auto", bodyClassName)}
        style={{ padding: noPadding ? 0 : interactionTokens.layout.panelPadding }}
      >
        {children}
      </div>
      {footer ? (
        <footer
          className="shrink-0 border-t text-xs"
          style={{
            borderColor: designTokens.colors.border.muted,
            padding: `6px ${interactionTokens.layout.panelPadding}px`,
            color: designTokens.colors.text.muted,
          }}
        >
          {footer}
        </footer>
      ) : null}
    </section>
  );
}
