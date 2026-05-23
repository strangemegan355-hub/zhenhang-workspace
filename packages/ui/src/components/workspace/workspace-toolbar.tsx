"use client";

import type { CSSProperties, ReactNode } from "react";
import { designTokens } from "../../theme/design-tokens";
import { interactionTokens } from "../../theme/interaction-tokens";
import { workspaceTokens } from "../../theme/workspace-tokens";
import { typography } from "../../theme/typography";
import { cn } from "../../utils/cn";

export type WorkspaceToolbarProps = {
  title?: string;
  subtitle?: ReactNode;
  status?: ReactNode;
  actions?: ReactNode;
  leading?: ReactNode;
  className?: string;
  loading?: boolean;
};

export function WorkspaceToolbar({
  title,
  subtitle,
  status,
  actions,
  leading,
  className,
  loading,
}: WorkspaceToolbarProps) {
  const style: CSSProperties = {
    height: interactionTokens.layout.toolbar,
    minHeight: interactionTokens.layout.toolbar,
    backgroundColor: workspaceTokens.background.toolbar,
    borderBottom: `1px solid ${workspaceTokens.border}`,
  };

  return (
    <header
      className={cn("sticky top-0 z-[20] flex shrink-0 items-center gap-3 px-3", className)}
      style={style}
    >
      {leading}
      <div className="min-w-0 flex-1">
        {title ? <h1 className={`${typography.cardTitle} truncate leading-tight`}>{title}</h1> : null}
        {subtitle ? <div className={`${typography.caption} truncate`}>{subtitle}</div> : null}
      </div>
      {status ? <div className="flex shrink-0 items-center gap-2">{status}</div> : null}
      {actions ? (
        <div
          className="flex shrink-0 flex-wrap items-center gap-1 border-l pl-2"
          style={{ borderColor: workspaceTokens.border, minHeight: interactionTokens.controlHeight.toolbarButton }}
        >
          {actions}
        </div>
      ) : null}
      {loading ? (
        <span className="h-3 w-3 shrink-0 animate-pulse rounded-full" style={{ backgroundColor: designTokens.colors.primary.default }} />
      ) : null}
    </header>
  );
}

export type WorkspaceToolbarButtonProps = {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "default" | "primary" | "danger";
  compact?: boolean;
  active?: boolean;
  loading?: boolean;
  title?: string;
  keyboardHint?: string;
  icon?: ReactNode;
  className?: string;
};

export function WorkspaceToolbarButton({
  children,
  onClick,
  disabled,
  variant = "default",
  compact = true,
  active = false,
  loading = false,
  title,
  keyboardHint,
  icon,
  className,
}: WorkspaceToolbarButtonProps) {
  const h = compact ? interactionTokens.controlHeight.toolbarButton : interactionTokens.controlHeight.input;
  const palette =
    variant === "primary"
      ? { bg: designTokens.colors.primary.default, fg: designTokens.colors.text.primary, border: designTokens.colors.primary.hover }
      : variant === "danger"
        ? { bg: designTokens.colors.danger.muted, fg: designTokens.colors.danger.default, border: designTokens.colors.danger.default }
        : {
            bg: active ? interactionTokens.hover.bg : designTokens.colors.background.panel,
            fg: designTokens.colors.text.secondary,
            border: active ? interactionTokens.hover.borderEmphasis : workspaceTokens.border,
          };

  const hint = keyboardHint ? `${title ?? ""} (${keyboardHint})`.trim() : title;

  return (
    <button
      type="button"
      title={hint || undefined}
      disabled={disabled || loading}
      onClick={onClick}
      className={cn(
        "inline-flex items-center justify-center gap-1.5 rounded text-xs font-medium disabled:cursor-not-allowed disabled:opacity-40",
        compact ? "px-2" : "px-3",
        className,
      )}
      style={{
        height: h,
        minHeight: h,
        backgroundColor: palette.bg,
        color: palette.fg,
        border: `1px solid ${palette.border}`,
        boxShadow: active ? interactionTokens.focusRing : undefined,
        transition: `background-color ${interactionTokens.transition.fast}, border-color ${interactionTokens.transition.fast}`,
      }}
      onMouseEnter={(e) => {
        if (disabled || loading) return;
        e.currentTarget.style.borderColor = interactionTokens.hover.borderEmphasis;
        if (variant === "default") e.currentTarget.style.backgroundColor = interactionTokens.hover.bg;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = palette.border;
        if (variant === "default" && !active) e.currentTarget.style.backgroundColor = palette.bg as string;
      }}
    >
      {loading ? (
        <span className="h-3 w-3 animate-pulse rounded-full" style={{ backgroundColor: palette.fg }} />
      ) : (
        icon
      )}
      {children}
      {keyboardHint && !compact ? (
        <kbd className="ml-1 font-mono text-[10px] opacity-50">{keyboardHint}</kbd>
      ) : null}
    </button>
  );
}
