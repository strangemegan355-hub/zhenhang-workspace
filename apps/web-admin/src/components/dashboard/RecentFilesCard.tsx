"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { ArrowUpRight, Download, Eye, FileImage, FileSpreadsheet, FileText, PenTool } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import { formatRelativeTime } from "./dashboard-utils";

type FileRow = { id: string; file_name: string; file_ext?: string | null; mime_type?: string | null; created_at?: string };

function fileKind(ext?: string | null, mime?: string | null) {
  const e = (ext ?? mime ?? "").toLowerCase();
  if (e.includes("pdf")) return { label: "PDF", icon: FileText, color: "text-[#ef4444] bg-[#fef2f2]" };
  if (e.includes("xls") || e.includes("csv")) return { label: "Excel", icon: FileSpreadsheet, color: "text-[#16a34a] bg-[#f0fdf4]" };
  if (e.includes("dwg") || e.includes("cad") || e.includes("dxf")) return { label: "CAD", icon: PenTool, color: "text-[var(--color-primary)] bg-[var(--color-primary-soft)]" };
  if (e.includes("jpg") || e.includes("png") || e.includes("jpeg") || e.includes("image")) return { label: "图片", icon: FileImage, color: "text-[#7c3aed] bg-[#faf5ff]" };
  return { label: "文件", icon: FileText, color: "text-[#64748b] bg-[#f1f5f9]" };
}

export function RecentFilesCard() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", "recent-files"],
    queryFn: async () => {
      const { data: resp } = await apiClient.get<{ data: { items?: FileRow[] } }>("/api/v1/files", { params: { page: 1, page_size: 5 } });
      return resp.data?.items ?? [];
    },
    staleTime: 60_000,
    retry: 1,
  });
  const items = data ?? [];
  return (
    <DashboardCard title="文件中心" toolbar={<Link href="/files" className="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:underline">全部文件<ArrowUpRight className="h-3 w-3" /></Link>}>
      {isLoading ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">加载中…</p> : items.length === 0 ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">暂无上传文件</p> : (
        <ul className="space-y-2">{items.map((file) => {
          const kind = fileKind(file.file_ext, file.mime_type);
          const Icon = kind.icon;
          return (
            <li key={file.id} className="flex items-center gap-3 rounded border border-[var(--color-border)] px-3 py-2.5">
              <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded \${kind.color}`}><Icon className="h-4 w-4" /></div>
              <div className="min-w-0 flex-1"><p className="truncate text-xs font-medium text-[var(--color-text)]">{file.file_name}</p><p className="text-[11px] text-[var(--color-text-muted)]">{kind.label} · {formatRelativeTime(file.created_at)}</p></div>
              <div className="flex shrink-0 gap-1">
                <Link href={`/files?preview=\${file.id}`} className="rounded p-1.5 text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-primary-soft)] hover:text-[var(--color-primary)]" title="查看"><Eye className="h-4 w-4" /></Link>
                <a href={`\${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/api/v1/files/\${file.id}/download`} className="rounded p-1.5 text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-primary-soft)] hover:text-[var(--color-primary)]" title="下载"><Download className="h-4 w-4" /></a>
              </div>
            </li>
          );
        })}</ul>
      )}
    </DashboardCard>
  );
}
