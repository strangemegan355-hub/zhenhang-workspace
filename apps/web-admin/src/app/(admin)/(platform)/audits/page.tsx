"use client";

import { useAuditsQuery } from "@zhenhang/query-hooks";
import { PageHeader } from "@zhenhang/ui";
import { useMemo, useState } from "react";
import { MasterListPage } from "@/components/master/master-list-page";
import { fieldInputClass, fieldLabelClass } from "@/lib/form-styles";

const MODULE_OPTIONS = ["auth", "master", "business", "platform", "quote", "procurement", "accounting"];

type AuditDisplayRow = {
  id: string;
  at: string;
  module: string;
  action: string;
  resource: string;
  user: string;
  detail: string;
};

export default function AuditsPage() {
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState("");
  const [moduleFilter, setModuleFilter] = useState("");

  // The request lives in the hook domain, as the repository's governance asks, so this page holds
  // only its own filters.
  const auditsQuery = useAuditsQuery(page, keyword || undefined, moduleFilter || undefined);

  // Rows carry display-ready values: GridColumn has no per-cell renderer, so the formatting the old
  // table did inline happens here, as it does on the other list pages.
  const rows: AuditDisplayRow[] = useMemo(
    () =>
      (auditsQuery.data?.items ?? []).map((row) => ({
        id: row.id,
        at: String(row.created_at ?? "").slice(0, 19).replace("T", " "),
        module: String(row.module ?? ""),
        action: String(row.action ?? ""),
        resource: `${String(row.resource_type ?? "")}#${String(row.resource_id ?? "").slice(0, 8)}`,
        user: String(row.user_name ?? "—"),
        detail: String(row.detail ?? "—"),
      })),
    [auditsQuery.data],
  );

  return (
    <MasterListPage<AuditDisplayRow>
      title="日志列表"
      externalHeader={<PageHeader title="审计日志" subtitle="记录所有关键操作，按模块/关键词筛选" />}
      searchPlaceholder="用户名、操作详情..."
      persistenceKey="audits-v1"
      exportFilename="audits"
      pageSize={20}
      columns={[
        { key: "at", title: "时间", canView: true, fixed: "left", width: 150 },
        { key: "module", title: "模块", canView: true, width: 110 },
        { key: "action", title: "操作", canView: true, width: 140 },
        { key: "resource", title: "资源", canView: true, width: 170 },
        { key: "user", title: "用户", canView: true, width: 110 },
        { key: "detail", title: "详情", canView: true },
      ]}
      rows={rows}
      total={auditsQuery.data?.total ?? 0}
      page={page}
      onPageChange={setPage}
      search={keyword}
      onSearchChange={(value) => {
        setKeyword(value);
        setPage(1);
      }}
      query={{
        isLoading: auditsQuery.isLoading,
        isError: auditsQuery.isError,
        isFetching: auditsQuery.isFetching,
        refetch: () => {
          void auditsQuery.refetch();
        },
      }}
      rowKey={(row) => row.id}
      emptyHint="无匹配记录"
      toolbarExtra={
        <label className="block space-y-1 text-xs">
          <span className={fieldLabelClass}>模块</span>
          <select
            className={fieldInputClass}
            value={moduleFilter}
            onChange={(event) => {
              setModuleFilter(event.target.value);
              setPage(1);
            }}
          >
            <option value="">全部</option>
            {MODULE_OPTIONS.map((module) => (
              <option key={module} value={module}>
                {module}
              </option>
            ))}
          </select>
        </label>
      }
    />
  );
}
