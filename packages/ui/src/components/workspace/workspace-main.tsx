"use client";

import type { CSSProperties, ReactNode } from "react";
import { workspaceTokens } from "../../theme/workspace-tokens";
import { cn } from "../../utils/cn";

export type WorkspaceMainProps = {
  children?: ReactNode;
  className?: string;
};

export function WorkspaceMain({ children, className }: WorkspaceMainProps) {
  const style: CSSProperties = {
    backgroundColor: workspaceTokens.background.main,
  };

  return (
    <main className={cn("relative min-h-0 min-w-0 flex-1 overflow-auto", className)} style={style}>
      <div className="flex h-full min-h-0 flex-col gap-3 p-3">{children}</div>
    </main>
  );
}
