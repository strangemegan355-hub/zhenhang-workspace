import type { MaterialCategoryItem } from "@/components/materials/material-category-tree";

export function getCategoryChildren(
  categories: MaterialCategoryItem[],
  parentId: string | null,
): MaterialCategoryItem[] {
  return categories
    .filter((c) => (c.parent_id ?? null) === parentId)
    .sort((a, b) => a.name.localeCompare(b.name, "zh-CN"));
}

export function getCategoryPath(categories: MaterialCategoryItem[], categoryId: string): string[] {
  const map = new Map(categories.map((c) => [c.id, c]));
  const path: string[] = [];
  let current = map.get(categoryId);
  while (current) {
    path.unshift(current.id);
    current = current.parent_id ? map.get(current.parent_id) : undefined;
  }
  return path;
}

export function categoryHasChildren(categories: MaterialCategoryItem[], categoryId: string): boolean {
  return getCategoryChildren(categories, categoryId).length > 0;
}

export function resolveLeafCategoryId(
  categories: MaterialCategoryItem[],
  path: string[],
): string | undefined {
  const last = path[path.length - 1];
  if (!last) return undefined;
  if (categoryHasChildren(categories, last)) return undefined;
  return last;
}
