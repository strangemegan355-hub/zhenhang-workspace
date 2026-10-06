"use client";

import { DataGrid } from "@zhenhang/data-grid";
import type { GridColumn } from "@zhenhang/data-grid";
import {
  EmptyState,
  ErrorBanner,
  IndustrialPage,
  IndustrialPanel,
  PageHeader,
  TableSkeleton,
  WorkspaceToolbarButton,
  typography,
  useIndustrialShortcuts,
} from "@zhenhang/ui";
import { useRouter } from "next/navigation";
import { useCallback, useRef, useState } from "react";
import { searchInputClass } from "@/lib/form-styles";

type QueryLike = {
  isLoading: boolean;
  isError: boolean;
  isFetching: boolean;
  refetch: () => void;
};

type MasterListPageProps<T extends Record<string, unknown>> = {
  title: string;
  searchPlaceholder?: string;
  persistenceKey: string;
  exportFilename: string;
  columns: Array<GridColumn<T>>;
  rows: T[];
  total: number;
  page: number;
  onPageChange: (page: number) => void;
  search: string;
  onSearchChange: (value: string) => void;
  query: QueryLike;
  pageSize?: number;
  rowKey: (row: T) => string;
  onRowClick?: (row: T) => void;
  rowActions?: (row: T) => React.ReactNode;
  onBatchDelete?: (selected: T[]) => void | Promise<void>;
  toolbarExtra?: React.ReactNode;
  emptyHint?: string;
  embedded?: boolean;
  /** Fill main workspace height (default true for list pages) */
  fill?: boolean;
  hideInternalHeader?: boolean;
  externalHeader?: React.ReactNode;
  pageShellMode?: "auto" | "embedded" | "page";
};

export function MasterListPage<T extends Record<string, unknown>>({
  title,
  searchPlaceholder = "搜索… (/ 聚焦)",
  persistenceKey,
  exportFilename,
  columns,
  rows,
  total,
  page,
  onPageChange,
  search,
  onSearchChange,
  query,
  pageSize = 50,
  rowKey,
  onRowClick,
  rowActions,
  onBatchDelete,
  toolbarExtra,
  emptyHint,
  embedded = false,
  fill = true,
  hideInternalHeader = false,
  externalHeader,
  pageShellMode = "auto",
}: MasterListPageProps<T>) {
  const searchRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const [selectedRows, setSelectedRows] = useState<T[]>([]);

  const handleSelectionChange = useCallback((rows: T[]) => {
    setSelectedRows(rows);
  }, []);

  const handleBatchDelete = useCallback(() => {
    if (!onBatchDelete || selectedRows.length === 0) return;
    void onBatchDelete(selectedRows);
  }, [onBatchDelete, selectedRows]);

  useIndustrialShortcuts([
    { id: "focus-search", key: "/", preventDefault: true, handler: () => searchRef.current?.focus() },
    { id: "refresh", key: "s", ctrl: true, handler: () => query.refetch() },
    {
      id: "clear",
      key: "Escape",
      handler: () => {
        onSearchChange("");
        searchRef.current?.blur();
      },
    },
    { id: "nav-customers", key: "1", alt: true, handler: () => router.push("/customers") },
    { id: "nav-machines", key: "2", alt: true, handler: () => router.push("/machines") },
    { id: "nav-boms", key: "3", alt: true, handler: () => router.push("/boms") },
    { id: "nav-workshop", key: "4", alt: true, handler: () => router.push("/workshop") },
  ]);

  const exportCsv = () => {
    if (rows.length === 0) return;
    const keys = columns.map((c) => c.key);
    const header = `${keys.join(",")}\n`;
    const body = rows.map((row) => keys.map((k) => String(row[k] ?? "")).join(",")).join("\n");
    const blob = new Blob([header + body], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${exportFilename}-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const panel = (
    <IndustrialPanel
      fill={fill}
      title={hideInternalHeader ? undefined : title}
      inlineLoading={query.isFetching && !query.isLoading}
      className={fill ? "min-h-0" : undefined}
      toolbar={
        <div className="flex flex-wrap items-center gap-2">
          <input
            ref={searchRef}
            type="search"
            placeholder={searchPlaceholder}
            value={search}
            className={searchInputClass}
            onChange={(e) => onSearchChange(e.target.value)}
          />
          <WorkspaceToolbarButton keyboardHint="Ctrl+S" title="刷新" onClick={() => query.refetch()}>
            刷新
          </WorkspaceToolbarButton>
          {onBatchDelete ? (
            <WorkspaceToolbarButton
              variant="danger"
              disabled={selectedRows.length === 0}
              onClick={handleBatchDelete}
            >
              删除选中{selectedRows.length > 0 ? ` (${selectedRows.length})` : ""}
            </WorkspaceToolbarButton>
          ) : null}
          {toolbarExtra}
          <span className={typography.caption}>Alt+1~4 切换主数据/车间</span>
        </div>
      }
    >
      {query.isLoading ? (
        <div className="flex min-h-0 flex-1 flex-col">
          <TableSkeleton rows={10} cols={columns.length} />
        </div>
      ) : query.isError ? (
        <div className="flex min-h-0 flex-1 flex-col">
          <ErrorBanner message={`无法加载${title}。`} onRetry={() => query.refetch()} />
        </div>
      ) : rows.length === 0 ? (
        <div className="flex min-h-0 flex-1 flex-col">
          <EmptyState
            message={`暂无${title.replace(/管理$/, "")}数据`}
            hint={emptyHint ?? "请确认后端 API 已启动并完成 seed"}
          />
        </div>
      ) : (
        <DataGrid
          columns={columns}
          rows={rows}
          rowKey={rowKey}
          page={page}
          total={total}
          pageSize={pageSize}
          onPageChange={onPageChange}
          persistenceKey={persistenceKey}
          onRowClick={onRowClick}
          rowActions={rowActions}
          onBatchAction={onBatchDelete ? (rows) => void onBatchDelete(rows) : undefined}
          hideBatchToolbar={Boolean(onBatchDelete)}
          onSelectionChange={onBatchDelete ? handleSelectionChange : undefined}
          onExport={exportCsv}
          emptyMessage={`暂无${title.replace(/管理$/, "")}记录`}
        />
      )}
    </IndustrialPanel>
  );

  const body = (
    <>
      {!hideInternalHeader && !externalHeader ? <PageHeader title={title} /> : null}
      {externalHeader}
      {panel}
    </>
  );

  const usePageShell = pageShellMode === "page" || (pageShellMode === "auto" && !embedded);
  if (usePageShell) {
    return (
      <IndustrialPage gap="md" fill={fill}>
        {body}
      </IndustrialPage>
    );
  }

  if (embedded) {
    return fill ? <div className="flex min-h-0 flex-1 flex-col">{body}</div> : body;
  }
  return <>{body}</>;
}
