"use client";

import type { MaterialCategoryItem } from "@/components/materials/material-category-tree";
import { fieldInputClass } from "@/lib/form-styles";
import { getCategoryChildren } from "@/lib/material-category-utils";

const LEVEL_LABELS = ["一级分类", "二级分类", "三级分类", "四级分类", "五级分类"];

type CascadeLevel = {
  level: number;
  options: MaterialCategoryItem[];
  selectedId: string;
};

/**
 * Work out which selects to render and what each one offers.
 *
 * This lives outside the component because the compiler rejects a value that JSX consumed and the
 * surrounding code then mutates: the loop used to advance `level` after the JSX built from it was
 * already in `selects`.
 */
function buildCascadeLevels(categories: MaterialCategoryItem[], path: string[]): CascadeLevel[] {
  const levels: CascadeLevel[] = [];
  let parentId: string | null = null;

  for (const [level] of LEVEL_LABELS.entries()) {
    const options = getCategoryChildren(categories, parentId);
    if (options.length === 0) break;

    const selectedId = path[level] ?? "";
    levels.push({ level, options, selectedId });

    if (!selectedId) break;
    parentId = selectedId;
  }

  return levels;
}

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

  const levels = buildCascadeLevels(categories, path);

  return (
    <div className="flex min-w-[132px] flex-col gap-1">
      {levels.map(({ level, options, selectedId }) => (
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
        </select>
      ))}
    </div>
  );
}
