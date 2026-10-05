"use client";

import { IndustrialPanel, typography } from "@zhenhang/ui";
import { useMemo, useState } from "react";
import { searchInputClass } from "@/lib/form-styles";

export type CheckboxOption = { value: string; label: string; hint?: string };

type CheckboxListPanelProps = {
  title: string;
  options: CheckboxOption[];
  selected: string[];
  onChange: (next: string[]) => void;
  onSave: () => void;
  onCancel: () => void;
  submitting?: boolean;
  error?: string | null;
  searchPlaceholder?: string;
  emptyHint?: string;
};

// Sharing this panel keeps the two association editors (a user's roles, a role's permissions)
// consistent, which is exactly the duplication the refactor backlog kept flagging.
export function CheckboxListPanel({
  title,
  options,
  selected,
  onChange,
  onSave,
  onCancel,
  submitting = false,
  error,
  searchPlaceholder = "筛选…",
  emptyHint = "暂无可选项",
}: CheckboxListPanelProps) {
  const [filter, setFilter] = useState("");
  const selectedSet = useMemo(() => new Set(selected), [selected]);

  const visible = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    if (!needle) return options;
    return options.filter(
      (option) =>
        option.value.toLowerCase().includes(needle) || option.label.toLowerCase().includes(needle),
    );
  }, [filter, options]);

  const toggle = (value: string) => {
    const next = new Set(selectedSet);
    if (next.has(value)) next.delete(value);
    else next.add(value);
    onChange([...next].sort());
  };

  return (
    <IndustrialPanel title={title} inlineLoading={submitting}>
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="search"
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            placeholder={searchPlaceholder}
            className={searchInputClass}
          />
          <span className={typography.caption}>已选 {selected.length} 项</span>
          <button type="button" className="btn-primary h-8 px-3 text-xs" disabled={submitting} onClick={onSave}>
            {submitting ? "保存中…" : "保存"}
          </button>
          <button
            type="button"
            className="h-8 rounded-[var(--radius-btn)] border border-[var(--color-border)] px-3 text-xs"
            disabled={submitting}
            onClick={onCancel}
          >
            取消
          </button>
        </div>

        {error ? <p className={`${typography.caption} text-[var(--color-danger)]`}>{error}</p> : null}

        {options.length === 0 ? (
          <p className={typography.caption}>{emptyHint}</p>
        ) : (
          <div className="grid max-h-72 gap-1 overflow-y-auto sm:grid-cols-2 lg:grid-cols-3">
            {visible.map((option) => (
              <label
                key={option.value}
                className="flex items-start gap-2 rounded px-2 py-1.5 text-xs hover:bg-[var(--color-surface-soft)]"
              >
                <input
                  type="checkbox"
                  className="mt-0.5"
                  checked={selectedSet.has(option.value)}
                  onChange={() => toggle(option.value)}
                />
                <span className="min-w-0">
                  <span className="block truncate font-medium text-[var(--color-text)]">{option.label}</span>
                  <span className="block truncate text-[10px] text-[var(--color-text-muted)]">
                    {option.hint ?? option.value}
                  </span>
                </span>
              </label>
            ))}
          </div>
        )}
      </div>
    </IndustrialPanel>
  );
}
