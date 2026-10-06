"use client";

import type { CSSProperties, ReactNode } from "react";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import { designTokens } from "../../theme/design-tokens";
import { interactionTokens } from "../../theme/interaction-tokens";
import { workspaceTokens } from "../../theme/workspace-tokens";
import { typography } from "../../theme/typography";
import { EmptyState } from "../loading/empty-state";
import { cn } from "../../utils/cn";

export type WorkspaceDockTab = {
  id: string;
  label: string;
  content: ReactNode;
  badge?: string | number;
};

export type WorkspaceDockProps = {
  tabs: WorkspaceDockTab[];
  defaultTabId?: string;
  activeTabId?: string;
  defaultHeight?: number;
  className?: string;
  onTabChange?: (tabId: string) => void;
  collapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
  emptyMessage?: string;
};

export function WorkspaceDock({
  tabs,
  defaultTabId,
  activeTabId: controlledTabId,
  defaultHeight = workspaceTokens.dockDefaultHeight,
  className,
  onTabChange,
  collapsed: controlledCollapsed,
  onCollapsedChange,
  emptyMessage = "无 Dock 面板",
}: WorkspaceDockProps) {
  const firstId = tabs[0]?.id ?? "";
  const [internalTabId, setInternalTabId] = useState(defaultTabId ?? firstId);
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const requestedTabId = controlledTabId ?? internalTabId;
  // Derived rather than synced: if the requested tab is gone from `tabs`, the first one wins, and the
  // uncontrolled state needs no update because this value already overrides it.
  const activeId = tabs.some((tab) => tab.id === requestedTabId) ? requestedTabId : firstId;
  const collapsed = controlledCollapsed ?? internalCollapsed;
  const tablistId = useId();
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);

  const setCollapsed = useCallback(
    (value: boolean) => {
      if (controlledCollapsed === undefined) setInternalCollapsed(value);
      onCollapsedChange?.(value);
    },
    [controlledCollapsed, onCollapsedChange],
  );

  const setTab = useCallback(
    (id: string) => {
      if (controlledTabId === undefined) setInternalTabId(id);
      onTabChange?.(id);
    },
    [controlledTabId, onTabChange],
  );

  // Only the notification is an effect — a controlled parent has to learn about the fallback, and
  // calling that during render would be a side effect in render.
  useEffect(() => {
    if (activeId !== requestedTabId) onTabChange?.(activeId);
  }, [activeId, requestedTabId, onTabChange]);

  const shellStyle: CSSProperties = {
    backgroundColor: workspaceTokens.background.dock,
    borderTop: `1px solid ${workspaceTokens.border}`,
    height: collapsed ? workspaceTokens.dockHeaderHeight : defaultHeight,
    minHeight: collapsed ? workspaceTokens.dockHeaderHeight : defaultHeight,
    transition: `height ${interactionTokens.transition.fast} ease-out, min-height ${interactionTokens.transition.fast} ease-out`,
  };

  const tabHeight = interactionTokens.controlHeight.dockTab;

  const onTabKeyDown = (e: React.KeyboardEvent, index: number) => {
    const len = tabs.length;
    if (!len) return;
    let next = index;
    if (e.key === "ArrowRight") {
      e.preventDefault();
      next = (index + 1) % len;
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      next = (index - 1 + len) % len;
    } else if (e.key === "Home") {
      e.preventDefault();
      next = 0;
    } else if (e.key === "End") {
      e.preventDefault();
      next = len - 1;
    } else {
      return;
    }
    const tab = tabs[next];
    if (tab) {
      setTab(tab.id);
      tabRefs.current[next]?.focus();
    }
  };

  const active = tabs.find((t) => t.id === activeId) ?? tabs[0];

  return (
    <section className={cn("flex shrink-0 flex-col overflow-hidden", className)} style={shellStyle}>
      <div
        className="flex shrink-0 items-center justify-between border-b px-2"
        style={{
          height: interactionTokens.layout.dockHeader,
          minHeight: interactionTokens.layout.dockHeader,
          borderColor: designTokens.colors.border.muted,
        }}
      >
        <div id={tablistId} role="tablist" aria-label="工作台 Dock" className="flex items-center gap-0.5">
          {tabs.map((tab, i) => {
            const selected = tab.id === activeId;
            return (
              <button
                key={tab.id}
                ref={(el) => {
                  tabRefs.current[i] = el;
                }}
                type="button"
                role="tab"
                id={`dock-tab-${tab.id}`}
                aria-selected={selected}
                aria-controls={`${tablistId}-panel-${tab.id}`}
                tabIndex={selected ? 0 : -1}
                className={cn(
                  "relative rounded-t px-3 text-xs font-medium outline-none",
                  selected ? "text-[#F8FAFC]" : "text-[#94A3B8]",
                )}
                style={{
                  height: tabHeight,
                  backgroundColor: selected ? designTokens.colors.background.elevated : "transparent",
                  borderTop: selected ? `2px solid ${designTokens.colors.primary.default}` : "2px solid transparent",
                  borderBottom: "2px solid transparent",
                  transition: `color ${interactionTokens.transition.fast}, background-color ${interactionTokens.transition.fast}, border-color ${interactionTokens.transition.fast}`,
                }}
                onMouseEnter={(e) => {
                  if (!selected) e.currentTarget.style.color = designTokens.colors.text.secondary;
                }}
                onMouseLeave={(e) => {
                  if (!selected) e.currentTarget.style.color = designTokens.colors.text.muted;
                }}
                onFocus={(e) => {
                  e.currentTarget.style.boxShadow = interactionTokens.focusRing;
                }}
                onBlur={(e) => {
                  e.currentTarget.style.boxShadow = "none";
                }}
                onClick={() => setTab(tab.id)}
                onKeyDown={(e) => onTabKeyDown(e, i)}
              >
                {tab.label}
                {tab.badge != null ? (
                  <span
                    className="ml-1.5 rounded px-1 font-mono text-[10px]"
                    style={{
                      backgroundColor: designTokens.colors.primary.muted,
                      color: designTokens.colors.text.secondary,
                    }}
                  >
                    {tab.badge}
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
        <button
          type="button"
          className={typography.caption}
          style={{ color: designTokens.colors.text.muted, height: tabHeight }}
          onClick={() => setCollapsed(!collapsed)}
          aria-expanded={!collapsed}
        >
          {collapsed ? "展开 ▲" : "收起 ▼"}
        </button>
      </div>
      {!collapsed ? (
        tabs.length === 0 ? (
          <div className="min-h-0 flex-1 p-3">
            <EmptyState message={emptyMessage} />
          </div>
        ) : active ? (
          <div
            id={`${tablistId}-panel-${active.id}`}
            role="tabpanel"
            aria-labelledby={`dock-tab-${active.id}`}
            className="min-h-0 flex-1 overflow-auto"
            style={{ padding: interactionTokens.layout.panelPadding }}
          >
            {active.content}
          </div>
        ) : null
      ) : null}
    </section>
  );
}
