"use client";

import { useAuditsQuery } from "@zhenhang/query-hooks";
import { IndustrialPage, IndustrialPanel, PageHeader } from "@zhenhang/ui";
import { useState } from "react";
import { fieldInputClass, fieldLabelClass, tableBodyRowClass, tableHeaderRowClass } from "@/lib/form-styles";

export default function AuditsPage() {
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [moduleFilter, setModuleFilter] = useState("");

  // The request lives in the hook domain, as the repository's governance asks, so this page holds
  // only its own filters. It was converted from a hand-written effect to react-query in round 16.
  const auditsQuery = useAuditsQuery(page, q || undefined, moduleFilter || undefined);

  const rows = auditsQuery.data?.items ?? [];
  const total = auditsQuery.data?.total ?? 0;
  const loading = auditsQuery.isPending;

  const moduleOptions = ["auth", "master", "business", "platform", "quote", "procurement", "accounting"];

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader title="审计日志" subtitle="记录所有关键操作，按模块/关键词筛选" />

      <IndustrialPanel title="日志列表">
        <div className="mb-3 flex flex-wrap items-end gap-3">
          <label className="block space-y-1 text-xs">
            <span className={fieldLabelClass}>搜索</span>
            <input
              className={fieldInputClass}
              value={q}
              onChange={(e) => { setQ(e.target.value); setPage(1); }}
              placeholder="用户名、操作详情..."
            />
          </label>
          <label className="block space-y-1 text-xs">
            <span className={fieldLabelClass}>模块</span>
            <select
              className={fieldInputClass}
              value={moduleFilter}
              onChange={(e) => { setModuleFilter(e.target.value); setPage(1); }}
            >
              <option value="">全部</option>
              {moduleOptions.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </label>
        </div>

        <div className="overflow-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className={tableHeaderRowClass}>
                <th className="px-2 py-2 text-left font-normal">时间</th>
                <th className="px-2 py-2 text-left font-normal">模块</th>
                <th className="px-2 py-2 text-left font-normal">操作</th>
                <th className="px-2 py-2 text-left font-normal">资源</th>
                <th className="px-2 py-2 text-left font-normal">用户</th>
                <th className="px-2 py-2 text-left font-normal">详情</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="px-2 py-4 text-center text-[var(--color-text-muted)]">加载中...</td></tr>
              ) : rows.length === 0 ? (
                <tr><td colSpan={6} className="px-2 py-4 text-center text-[var(--color-text-muted)]">无匹配记录</td></tr>
              ) : (
                rows.map((row) => (
                  <tr key={row.id} className={tableBodyRowClass}>
                    <td className="whitespace-nowrap px-2 py-2">{String(row.created_at ?? "").slice(0, 19).replace("T", " ")}</td>
                    <td className="px-2 py-2"><span className="rounded bg-zinc-100 px-1.5 py-0.5 dark:bg-zinc-800">{row.module}</span></td>
                    <td className="px-2 py-2">{row.action}</td>
                    <td className="px-2 py-2 text-[var(--color-text-muted)]">{row.resource_type}#{String(row.resource_id).slice(0, 8)}</td>
                    <td className="px-2 py-2">{row.user_name ?? "—"}</td>
                    <td className="max-w-xs truncate px-2 py-2 text-[var(--color-text-muted)]">{row.detail ?? "—"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-3 flex items-center justify-between text-xs text-[var(--color-text-muted)]">
          <span>共 {total} 条</span>
          <div className="flex gap-2">
            <button type="button" className="rounded border px-2 py-1 disabled:opacity-30" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>上一页</button>
            <button type="button" className="rounded border px-2 py-1 disabled:opacity-30" disabled={page * 20 >= total} onClick={() => setPage((p) => p + 1)}>下一页</button>
          </div>
        </div>
      </IndustrialPanel>
    </IndustrialPage>
  );
}
