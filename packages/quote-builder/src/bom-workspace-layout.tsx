"use client";

import type { ReactNode } from "react";
import { ErrorBanner, IndustrialPanel, WorkspaceShell, type WorkspaceShellProps } from "@zhenhang/ui";

export type BomWorkspaceLayoutProps = WorkspaceShellProps & {
  panelLoading?: boolean;
  errorMessage?: string;
  onErrorRetry?: () => void;
};

export function BomWorkspaceLayout({
  panelLoading = false,
  inlineLoading,
  errorMessage,
  onErrorRetry,
  className,
  ...shellProps
}: BomWorkspaceLayoutProps) {
  return (
    <IndustrialPanel loading={panelLoading} inlineLoading={inlineLoading} contentClassName="!p-0">
      {errorMessage ? (
        <div className="p-3 pb-0">
          <ErrorBanner message={errorMessage} onRetry={onErrorRetry} />
        </div>
      ) : null}
      {!panelLoading ? (
        <WorkspaceShell {...shellProps} className={className ?? "rounded-none border-0 shadow-none"} />
      ) : null}
    </IndustrialPanel>
  );
}
