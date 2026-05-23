"use client";

import type { CSSProperties, ReactNode } from "react";
import { interactionTokens } from "../../theme/interaction-tokens";
import { workspaceTokens } from "../../theme/workspace-tokens";
import { InlineLoadingBar } from "../loading/inline-loading-bar";
import { ProcessingOverlay } from "../loading/processing-overlay";
import { cn } from "../../utils/cn";

export type WorkspaceShellProps = {
  toolbar?: ReactNode;
  sidebar?: ReactNode;
  main?: ReactNode;
  dock?: ReactNode;
  loading?: boolean;
  loadingLabel?: string;
  inlineLoading?: boolean;
  className?: string;
  minHeight?: number | string;
};

export function WorkspaceShell({
  toolbar,
  sidebar,
  main,
  dock,
  loading = false,
  loadingLabel = "处理中…",
  inlineLoading = false,
  className,
  minHeight = 640,
}: WorkspaceShellProps) {
  const shellStyle: CSSProperties = {
    backgroundColor: workspaceTokens.background.shell,
    border: `1px solid ${workspaceTokens.border}`,
    borderRadius: workspaceTokens.radius,
    minHeight,
  };

  return (
    <div className={cn("relative flex flex-col overflow-hidden", className)} style={shellStyle}>
      <InlineLoadingBar active={inlineLoading} />
      {toolbar}
      <div className="flex min-h-0 flex-1">
        {sidebar}
        {main}
      </div>
      {dock}
      <ProcessingOverlay active={loading} label={loadingLabel} />
    </div>
  );
}
