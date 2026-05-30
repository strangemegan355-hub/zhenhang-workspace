"use client";

import { useCustomersQuery } from "@zhenhang/query-hooks";
import { IndustrialPage, PageHeader } from "@zhenhang/ui";
import { MasterListPage } from "@/components/master/master-list-page";
import { useMemo, useState } from "react";

type CustomerRow = {
  id: string;
  code: string;
  name: string;
  industry: string;
  level: string;
  status: string;
  phone: string;
};

export default function CustomersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const query = useCustomersQuery(page, search.trim() || undefined);
  const data = (query.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};

  const rows = useMemo(
    () =>
      (data.items ?? []).map((row) => ({
        id: String(row.id ?? ""),
        code: String(row.code ?? ""),
        name: String(row.name ?? ""),
        industry: String(row.industry ?? ""),
        level: String(row.level ?? ""),
        status: String(row.status ?? ""),
        phone: String(row.phone ?? ""),
      })),
    [data.items],
  );

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader
        title="客户管理"
        subtitle="客户主数据统一接入页面标题与页面壳层"
      />
      <MasterListPage<CustomerRow>
        hideInternalHeader
        pageShellMode="embedded"
        title="客户管理"
        persistenceKey="master-customers-v1"
        exportFilename="customers"
        columns={[
          { key: "code", title: "客户编码", canView: true, fixed: "left", width: 140 },
          { key: "name", title: "客户名称", canView: true, width: 200 },
          { key: "industry", title: "行业", canView: true },
          { key: "level", title: "等级", canView: true },
          { key: "status", title: "状态", canView: true },
          { key: "phone", title: "电话", canView: true },
        ]}
        rows={rows}
        total={data.total ?? rows.length}
        page={page}
        onPageChange={setPage}
        search={search}
        onSearchChange={setSearch}
        query={query}
        rowKey={(row) => row.id}
      />
    </IndustrialPage>
  );
}
