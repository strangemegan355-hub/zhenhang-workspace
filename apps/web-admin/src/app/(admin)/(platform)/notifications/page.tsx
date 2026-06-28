"use client";

import { DataGrid } from "@zhenhang/data-grid";
import {
  useMarkNotificationReadMutation,
  useNotificationsQuery,
} from "@zhenhang/query-hooks";
import {
  EmptyState,
  ErrorBanner,
  IndustrialPage,
  IndustrialPanel,
  TableSkeleton,
  typography,
  useIndustrialShortcuts,
} from "@zhenhang/ui";
import { useMemo, useRef, useState } from "react";
import { fieldInputClass } from "@/lib/form-styles";

export default function NotificationsPage() {
  const [page, setPage] = useState(1);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [search, setSearch] = useState("");
  const searchRef = useRef<HTMLInputElement>(null);
  const query = useNotificationsQuery({ page, unreadOnly });
  const markRead = useMarkNotificationReadMutation({ page, unreadOnly });
  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};
  const rows = useMemo(() => {
    const items = (data.items ?? []).map((row) => ({
      id: String(row.id ?? ""),
      title: String(row.title ?? ""),
      channel: String(row.channel ?? ""),
      status: row.read_at ? "read" : String(row.status ?? "sent"),
      bizType: String(row.biz_type ?? ""),
    }));
    if (!search.trim()) return items;
    const q = search.toLowerCase();
    return items.filter((r) => r.title.toLowerCase().includes(q) || r.channel.toLowerCase().includes(q));
  }, [data.items, search]);

  useIndustrialShortcuts([
    {
      id: "focus-search",
      key: "/",
      preventDefault: true,
      handler: () => searchRef.current?.focus(),
    },
  ]);

  const exportCsv = () => {
    const header = "id,title,channel,status,biz_type\n";
    const body = rows.map((r) => `${r.id},${r.title},${r.channel},${r.status},${r.bizType}`).join("\n");
    const blob = new Blob([header + body], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `notifications-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <IndustrialPage gap="md" fill>
      <IndustrialPanel
        fill
        title="通知中心"
        inlineLoading={query.isFetching && !query.isLoading}
        toolbar={
          <div className="flex items-center gap-3">
              <input
                ref={searchRef}
                type="search"
                placeholder="筛选标题… (/ 聚焦)"
                value={search}
                className={fieldInputClass}
                onChange={(e) => setSearch(e.target.value)}
              />
            <label className={`flex h-8 items-center gap-2 ${typography.body}`}>
              <input type="checkbox" checked={unreadOnly} onChange={(e) => setUnreadOnly(e.target.checked)} />
              仅未读
            </label>
          </div>
        }
        loading={false}
      >
        {query.isLoading ? (
          <div className="flex min-h-0 flex-1 flex-col">
            <TableSkeleton rows={8} cols={4} />
          </div>
        ) : query.isError ? (
          <div className="flex min-h-0 flex-1 flex-col">
            <ErrorBanner message="无法加载通知列表。" onRetry={() => query.refetch()} />
          </div>
        ) : rows.length === 0 ? (
          <div className="flex min-h-0 flex-1 flex-col">
            <EmptyState
              message="暂无通知"
              hint={
                unreadOnly
                  ? "当前没有未读通知，可取消「仅未读」查看全部；审批或导出完成后会在此显示"
                  : "审批通过、驳回或 PDF 导出完成后，系统将推送通知至此"
              }
            />
          </div>
        ) : (
          <DataGrid
            columns={[
              { key: "title", title: "标题", canView: true, fixed: "left", width: 320 },
              { key: "channel", title: "渠道", canView: true },
              { key: "status", title: "状态", canView: true },
              { key: "bizType", title: "业务类型", canView: true },
            ]}
            rows={rows}
            rowKey={(row) => String(row.id)}
            page={page}
            total={data.total ?? rows.length}
            onPageChange={setPage}
            persistenceKey="notification-grid-v2"
            onRowClick={(row) => {
              if (row.id) markRead.mutate(String(row.id));
            }}
            onBatchAction={(selected) => {
              selected.forEach((row) => {
                if (row.id) markRead.mutate(String(row.id));
              });
            }}
            onExport={exportCsv}
          />
        )}
      </IndustrialPanel>
    </IndustrialPage>
  );
}
