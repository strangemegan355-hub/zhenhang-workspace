"use client";

import { useEffect, useRef } from "react";

export type IndustrialShortcut = {
  id: string;
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  enabled?: boolean;
  preventDefault?: boolean;
  handler: (event: KeyboardEvent) => void;
};

function matchShortcut(e: KeyboardEvent, shortcut: IndustrialShortcut): boolean {
  if (shortcut.enabled === false) return false;
  const key = shortcut.key.toLowerCase();
  const eventKey = e.key.toLowerCase();
  if (eventKey !== key && eventKey !== shortcut.key) return false;
  if (Boolean(shortcut.ctrl) !== e.ctrlKey) return false;
  if (Boolean(shortcut.shift) !== e.shiftKey) return false;
  if (Boolean(shortcut.alt) !== e.altKey) return false;
  return true;
}

export function useIndustrialShortcuts(shortcuts: IndustrialShortcut[]) {
  const shortcutsRef = useRef(shortcuts);

  // Updated in an effect rather than during render: writing a ref while rendering is what the React
  // Compiler flags, and a keydown can only be handled after the commit anyway.
  useEffect(() => {
    shortcutsRef.current = shortcuts;
  }, [shortcuts]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const tag = target?.tagName?.toLowerCase();
      const inField = tag === "input" || tag === "textarea" || tag === "select" || target?.isContentEditable;

      for (const shortcut of shortcutsRef.current) {
        if (!matchShortcut(e, shortcut)) continue;
        if (inField && !shortcut.ctrl && !shortcut.alt) continue;
        if (shortcut.preventDefault !== false) e.preventDefault();
        shortcut.handler(e);
        break;
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);
}

export const INDUSTRIAL_SHORTCUT_HINTS = {
  save: "Ctrl+S",
  export: "Ctrl+Shift+E",
  dock: "Alt+1~4",
  search: "/",
  close: "Esc",
} as const;
