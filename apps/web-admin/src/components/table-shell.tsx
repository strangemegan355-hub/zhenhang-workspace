"use client";

import * as React from "react";
import { TableToolbar } from "@zhenhang/ui";

type Props = {
  title: string;
  children: React.ReactNode;
};

export function TableShell({ title, children }: Props) {
  const [keyword, setKeyword] = React.useState("");
  const [status, setStatus] = React.useState("all");
  const [page, setPage] = React.useState(1);

  return (
    <section className="space-y-3 rounded-lg border bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="text-base font-semibold">{title}</div>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <TableToolbar keyword={keyword} onKeywordChange={setKeyword} onExport={() => alert("TODO export")} />
        <div className="flex items-center gap-2">
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="h-9 rounded-md border px-2 text-sm"
          >
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="done">Done</option>
          </select>
          <button className="h-9 rounded-md border px-3 text-sm" onClick={() => setPage((p) => Math.max(1, p - 1))}>
            Prev
          </button>
          <span className="text-sm">Page {page}</span>
          <button className="h-9 rounded-md border px-3 text-sm" onClick={() => setPage((p) => p + 1)}>
            Next
          </button>
        </div>
      </div>
      {children}
    </section>
  );
}
