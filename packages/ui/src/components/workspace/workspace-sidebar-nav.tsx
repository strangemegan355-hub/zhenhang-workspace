"use client";

import type { ReactNode } from "react";
import { interactionTokens } from "../../theme/interaction-tokens";
import { designTokens } from "../../theme/design-tokens";
import { typography } from "../../theme/typography";
import { cn } from "../../utils/cn";

export type WorkspaceSidebarNavItem = {
  id: string;
  label: string;
  icon?: ReactNode;
};

export function WorkspaceSidebarNav({
  items,
  activeId,
  onSelect,
  sectionLabel = "模块",
}: {
  items: WorkspaceSidebarNavItem[];
  activeId: string;
  onSelect: (id: string) => void;
  sectionLabel?: string;
}) {
  return (
    <nav className="mb-3" aria-label={sectionLabel}>
      <div
        className={`${typography.caption} mb-1 px-2 uppercase tracking-wide`}
        style={{ color: designTokens.colors.text.muted, fontSize: 10 }}
      >
        {sectionLabel}
      </div>
      <ul className="space-y-0.5" style={{ gap: interactionTokens.layout.sectionGapSm }}>
        {items.map((item) => {
          const active = item.id === activeId;
          return (
            <li key={item.id}>
              <button
                type="button"
                title={item.label}
                className={cn(
                  "flex w-full items-center gap-2 rounded px-2 text-left text-xs transition",
                )}
                style={{
                  height: interactionTokens.controlHeight.toolbarButton,
                  color: active ? designTokens.colors.primary.default : designTokens.colors.text.secondary,
                  backgroundColor: active ? designTokens.colors.background.subtle : "transparent",
                  borderLeft: active ? `2px solid ${designTokens.colors.primary.default}` : "2px solid transparent",
                  transition: `background-color ${interactionTokens.transition.fast}, border-color ${interactionTokens.transition.fast}`,
                }}
                onMouseEnter={(e) => {
                  if (!active) e.currentTarget.style.backgroundColor = interactionTokens.hover.bg;
                }}
                onMouseLeave={(e) => {
                  if (!active) e.currentTarget.style.backgroundColor = "transparent";
                }}
                onClick={() => onSelect(item.id)}
              >
                {item.icon ? <span className="w-4 shrink-0 text-center opacity-80">{item.icon}</span> : null}
                <span className="truncate">{item.label}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
