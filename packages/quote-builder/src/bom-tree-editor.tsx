"use client";

import { useVirtualizer } from "@tanstack/react-virtual";
import * as React from "react";
import {
  EmptyState,
  StatusBadge,
  SystemPill,
  WorkspaceToolbarButton,
  designTokens,
  interactionTokens,
  typography,
} from "@zhenhang/ui";
import { flattenBomTree, groupBomByPrefix, reorderArray } from "./tree-utils";
import type { BomTreeNode } from "./types";

export function flatBomToTree(
  items: Array<{ id: string; item_code: string; item_name: string; quantity: number; unit_cost: number; line_total?: number }>,
  industrial = true,
): BomTreeNode[] {
  if (industrial && items.length > 3) return groupBomByPrefix(items);
  return items.map((i) => ({
    id: i.id,
    code: i.item_code,
    name: i.item_name,
    quantity: i.quantity,
    unitCost: i.unit_cost,
    lineTotal: i.line_total ?? i.quantity * i.unit_cost,
  }));
}

export function BomTreeEditor({
  nodes,
  rootLabel = "设备 BOM",
  selectedId,
  onSelect,
  onImportToQuote,
  onNodesReorder,
  totalCost,
  readOnly,
  embedded,
  loading = false,
}: {
  nodes: BomTreeNode[];
  rootLabel?: string;
  selectedId?: string;
  onSelect?: (id: string) => void;
  onImportToQuote?: () => void;
  onNodesReorder?: (nodes: BomTreeNode[]) => void;
  totalCost?: number;
  readOnly?: boolean;
  embedded?: boolean;
  loading?: boolean;
}) {
  const [localNodes, setLocalNodes] = React.useState(nodes);
  const [search, setSearch] = React.useState("");
  const [openIds, setOpenIds] = React.useState<Set<string>>(() => new Set(["root", ...nodes.map((n) => n.id)]));
  const [dragIndex, setDragIndex] = React.useState<number | null>(null);
  const parentRef = React.useRef<HTMLDivElement>(null);
  const rowH = interactionTokens.controlHeight.tableRow;

  React.useEffect(() => {
    setLocalNodes(nodes);
    setOpenIds(new Set(["root", ...nodes.map((n) => n.id)]));
  }, [nodes]);

  const root: BomTreeNode = React.useMemo(
    () => ({
      id: "root",
      code: "ROOT",
      name: rootLabel,
      quantity: 1,
      unitCost: totalCost ?? localNodes.reduce((s, n) => s + n.lineTotal, 0),
      lineTotal: totalCost ?? localNodes.reduce((s, n) => s + n.lineTotal, 0),
      children: localNodes,
    }),
    [rootLabel, localNodes, totalCost],
  );

  const flatRows = React.useMemo(() => {
    const rows = flattenBomTree([root], openIds);
    if (!search.trim()) return rows;
    const q = search.toLowerCase();
    return rows.filter(
      (r) => r.node.code.toLowerCase().includes(q) || r.node.name.toLowerCase().includes(q),
    );
  }, [root, openIds, search]);

  const virtualizer = useVirtualizer({
    count: flatRows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => rowH,
    overscan: 8,
  });

  const toggleOpen = (id: string) => {
    setOpenIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleDrop = (toIndex: number) => {
    if (dragIndex === null || dragIndex === toIndex || readOnly) return;
    const reordered = reorderArray(localNodes, dragIndex, toIndex);
    setLocalNodes(reordered);
    onNodesReorder?.(reordered);
    setDragIndex(null);
  };

  const shellClass = embedded
    ? "flex min-h-[280px] flex-1 flex-col overflow-hidden border-0 bg-transparent shadow-none"
    : "flex h-[380px] flex-col overflow-hidden rounded border shadow-sm";

  const border = designTokens.colors.border.default;
  const bgPanel = designTokens.colors.background.panel;
  const bgSubtle = designTokens.colors.background.subtle;

  if (loading) {
    return (
      <div className={shellClass} style={{ borderColor: border, backgroundColor: bgPanel }}>
        <div className="space-y-2 p-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="animate-pulse rounded"
              style={{ height: rowH, backgroundColor: designTokens.colors.border.muted }}
            />
          ))}
        </div>
      </div>
    );
  }

  const onlyRoot = localNodes.length === 0;

  return (
    <div className={shellClass} style={embedded ? undefined : { borderColor: border, backgroundColor: bgPanel }}>
      <div
        className="flex shrink-0 items-center gap-2 border-b px-2 py-1.5"
        style={{ borderColor: border, backgroundColor: bgSubtle, minHeight: interactionTokens.layout.toolbar }}
      >
        <span className={typography.cardTitle}>BOM 结构树</span>
        <SystemPill status={onlyRoot ? "idle" : "info"} mono>
          {Math.max(flatRows.length - 1, 0)} 节点
        </SystemPill>
        {onImportToQuote ? <StatusBadge status="success" label="可导入" compact /> : null}
        <div className="ml-auto flex items-center gap-1">
          <input
            type="search"
            placeholder="筛选物料…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="rounded border px-2 text-xs"
            style={{
              height: interactionTokens.controlHeight.input,
              width: 112,
              borderColor: border,
              backgroundColor: designTokens.colors.background.base,
              color: designTokens.colors.text.primary,
            }}
          />
          {onImportToQuote ? (
            <WorkspaceToolbarButton compact variant="primary" onClick={onImportToQuote}>
              导入报价
            </WorkspaceToolbarButton>
          ) : null}
        </div>
      </div>

      {onlyRoot ? (
        <EmptyState message="暂无 BOM 物料" hint="绑定 BOM 后可展开结构树并导入报价行" />
      ) : (
        <>
          <div
            className="grid shrink-0 grid-cols-[1fr_72px_72px_80px] gap-0 border-b px-2 py-1 text-[10px] font-semibold uppercase tracking-wide"
            style={{
              borderColor: border,
              backgroundColor: designTokens.colors.background.elevated,
              color: designTokens.colors.text.muted,
              height: rowH,
              alignItems: "center",
            }}
          >
            <span>编码 / 名称</span>
            <span className="text-right">数量</span>
            <span className="text-right">单价</span>
            <span className="text-right">小计</span>
          </div>
          <div ref={parentRef} className="min-h-0 flex-1 overflow-auto">
            <div style={{ height: `${virtualizer.getTotalSize()}px`, position: "relative" }}>
              {virtualizer.getVirtualItems().map((vi) => {
                const row = flatRows[vi.index];
                const { node, depth, hasChildren } = row;
                const selected = selectedId === node.id;
                const isRoot = node.id === "root";
                const nodeIdx = !isRoot && depth === 1 ? localNodes.findIndex((n) => n.id === node.id) : -1;
                const draggable = !readOnly && nodeIdx >= 0;

                return (
                  <div
                    key={`${node.id}-${vi.index}`}
                    style={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      width: "100%",
                      height: `${vi.size}px`,
                      transform: `translateY(${vi.start}px)`,
                      backgroundColor: selected ? designTokens.colors.background.subtle : undefined,
                      borderBottom: `1px solid ${designTokens.colors.border.muted}`,
                      transition: `background-color ${interactionTokens.transition.fast}`,
                    }}
                    draggable={draggable}
                    onDragStart={() => draggable && setDragIndex(nodeIdx)}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={() => draggable && nodeIdx >= 0 && handleDrop(nodeIdx)}
                    onClick={() => !isRoot && onSelect?.(node.id)}
                    className={`grid grid-cols-[1fr_72px_72px_80px] items-center px-2 text-sm ${
                      dragIndex === nodeIdx ? "opacity-50" : ""
                    } ${!isRoot ? "cursor-pointer hover:bg-[#1a2332]" : ""}`}
                  >
                    <div className="flex min-w-0 items-center gap-1" style={{ paddingLeft: depth * 14 }}>
                      {hasChildren ? (
                        <button
                          type="button"
                          className="flex h-5 w-5 shrink-0 items-center justify-center rounded border text-[10px]"
                          style={{ borderColor: border, color: designTokens.colors.text.muted }}
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleOpen(node.id);
                          }}
                        >
                          {openIds.has(node.id) ? "▾" : "▸"}
                        </button>
                      ) : (
                        <span className="w-5 shrink-0" />
                      )}
                      {draggable ? (
                        <span className="cursor-grab" style={{ color: designTokens.colors.text.muted }}>
                          ⠿
                        </span>
                      ) : null}
                      <div className="min-w-0 truncate">
                        <span
                          className={`${typography.monoNumber} text-[11px]`}
                          style={{ color: designTokens.colors.text.muted }}
                        >
                          {isRoot ? "" : node.code}
                        </span>
                        <span className="ml-1 truncate" style={{ color: designTokens.colors.text.secondary }}>
                          {node.name}
                        </span>
                      </div>
                    </div>
                    <span className={`${typography.monoNumber} text-right text-xs`}>{isRoot ? "" : node.quantity}</span>
                    <span className={`${typography.monoNumber} text-right text-xs`}>
                      {isRoot ? "" : node.unitCost.toFixed(2)}
                    </span>
                    <span className={`${typography.monoNumber} text-right text-xs font-semibold`}>
                      {node.lineTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
          <div
            className="shrink-0 border-t px-3 py-2 text-right text-sm font-semibold tabular-nums"
            style={{ borderColor: border, backgroundColor: bgSubtle, color: designTokens.colors.text.primary }}
          >
            BOM 合计 ¥{(root.lineTotal ?? 0).toLocaleString()}
          </div>
        </>
      )}
    </div>
  );
}
