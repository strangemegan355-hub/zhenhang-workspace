import type { BomTreeNode } from "./types";

export type FlatBomRow = {
  node: BomTreeNode;
  depth: number;
  hasChildren: boolean;
};

export function flattenBomTree(
  nodes: BomTreeNode[],
  openIds: Set<string>,
  depth = 0,
): FlatBomRow[] {
  const rows: FlatBomRow[] = [];
  for (const node of nodes) {
    const hasChildren = (node.children?.length ?? 0) > 0;
    rows.push({ node, depth, hasChildren });
    if (hasChildren && openIds.has(node.id)) {
      rows.push(...flattenBomTree(node.children!, openIds, depth + 1));
    }
  }
  return rows;
}

export function reorderArray<T>(items: T[], fromIndex: number, toIndex: number): T[] {
  if (fromIndex === toIndex || fromIndex < 0 || toIndex < 0) return items;
  const next = [...items];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  return next;
}

export function groupBomByPrefix(
  items: Array<{ id: string; item_code: string; item_name: string; quantity: number; unit_cost: number; line_total?: number }>,
): BomTreeNode[] {
  const groups = new Map<string, typeof items>();
  for (const item of items) {
    const prefix = item.item_code.includes("-") ? item.item_code.split("-")[0] : "MISC";
    if (!groups.has(prefix)) groups.set(prefix, []);
    groups.get(prefix)!.push(item);
  }
  return [...groups.entries()].map(([prefix, groupItems]) => {
    const subtotal = groupItems.reduce((s, i) => s + (i.line_total ?? i.quantity * i.unit_cost), 0);
    return {
      id: `grp-${prefix}`,
      code: prefix,
      name: `模块 ${prefix}`,
      quantity: 1,
      unitCost: subtotal,
      lineTotal: subtotal,
      children: groupItems.map((i) => ({
        id: i.id,
        code: i.item_code,
        name: i.item_name,
        quantity: i.quantity,
        unitCost: i.unit_cost,
        lineTotal: i.line_total ?? i.quantity * i.unit_cost,
      })),
    };
  });
}
