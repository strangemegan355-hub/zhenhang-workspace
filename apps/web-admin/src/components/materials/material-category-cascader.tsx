"use client";

import type { ReactNode } from "react";
import type { MaterialCategoryItem } from "@/components/materials/material-category-tree";
import { fieldInputClass } from "@/lib/form-styles";
import { getCategoryChildren } from "@/lib/material-category-utils";

const LEVEL_LABELS = ["一级分类", "二级分类", "三级分类", "四级分类", "五级分类"];

export function MaterialCategoryCascader({
  categories,
  path,
  onPathChange,
}: {
  categories: MaterialCategoryItem[];
  path: string[];
  onPathChange: (path: string[]) => void;
}) {
  if (categories.length === 0) {
    return <span className="text-[10px] leading-snug text-[var(--color-text-muted)]">请先在材料库维护分类</span>;
  }

  const selects: ReactNode[] = [];
  let parentId: string | null = null;

  for (let level = 0; level < LEVEL_LABELS.length; level += 1) {
    const options = getCategoryChildren(categories, parentId);
    if (options.length === 0) break;

    const selectedId = path[level] ?? "";
    selects.push(
      <select
        key={level}
        className={fieldInputClass}
        value={selectedId}
        onChange={(e) => {
          const nextId = e.target.value;
          onPathChange(nextId ? [...path.slice(0, level), nextId] : path.slice(0, level));
        }}
      >
        <option value="">选择{LEVEL_LABELS[level] ?? `${level + 1}级分类`}</option>
        {options.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </select>,
    );

    if (!selectedId) break;
    parentId = selectedId;
  }

  return <div className="flex min-w-[132px] flex-col gap-1">{selects}</div>;
}
