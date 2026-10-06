"use client";

import Link from "next/link";
import { useDownloadFileMutation, useFilesQuery, type FileItem } from "@zhenhang/query-hooks";
import { ArrowUpRight, Download, Eye, FileImage, FileSpreadsheet, FileText, PenTool } from "lucide-react";
import { DashboardCard } from "./dashboard-card";
import { formatRelativeTime } from "./dashboard-utils";

function fileKind(ext?: string | null, mime?: string | null) {
  const e = (ext ?? mime ?? "").toLowerCase();
  if (e.includes("pdf")) return { label: "PDF", icon: FileText, color: "text-[#ef4444] bg-[#fef2f2]" };
  if (e.includes("xls") || e.includes("csv")) return { label: "Excel", icon: FileSpreadsheet, color: "text-[#16a34a] bg-[#f0fdf4]" };
  if (e.includes("dwg") || e.includes("cad") || e.includes("dxf")) return { label: "CAD", icon: PenTool, color: "text-[var(--color-primary)] bg-[var(--color-primary-soft)]" };
  if (e.includes("jpg") || e.includes("png") || e.includes("jpeg") || e.includes("image")) return { label: "图片", icon: FileImage, color: "text-[#7c3aed] bg-[#faf5ff]" };
  return { label: "文件", icon: FileText, color: "text-[#64748b] bg-[#f1f5f9]" };
}

export function RecentFilesCard() {
  const filesQuery = useFilesQuery(5);
  const items = filesQuery.data ?? [];
  const isLoading = filesQuery.isLoading;
  const downloadMutation = useDownloadFileMutation();

  // An <a href> cannot carry the Bearer token, so the link could only ever get a 401 from an endpoint
  // that requires platform:file:read. Fetch the bytes with the token instead.
  const handleDownload = async (file: FileItem) => {
    const blob = await downloadMutation.mutateAsync(file.id);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = file.file_name;
    anchor.click();
    URL.revokeObjectURL(url);
  };
  return (
    <DashboardCard title="文件中心" toolbar={<Link href="/files" className="flex items-center gap-1 text-xs text-[var(--color-primary)] hover:underline">全部文件<ArrowUpRight className="h-3 w-3" /></Link>}>
      {isLoading ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">加载中…</p> : items.length === 0 ? <p className="py-6 text-center text-xs text-[var(--color-text-muted)]">暂无上传文件</p> : (
        <ul className="space-y-2">{items.map((file) => {
          const kind = fileKind(file.file_ext, file.mime_type);
          const Icon = kind.icon;
          return (
            <li key={file.id} className="flex items-center gap-3 rounded border border-[var(--color-border)] px-3 py-2.5">
              <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded ${kind.color}`}><Icon className="h-4 w-4" /></div>
              <div className="min-w-0 flex-1"><p className="truncate text-xs font-medium text-[var(--color-text)]">{file.file_name}</p><p className="text-[11px] text-[var(--color-text-muted)]">{kind.label} · {formatRelativeTime(file.created_at)}</p></div>
              <div className="flex shrink-0 gap-1">
                <Link href={`/files?preview=${file.id}`} className="rounded p-1.5 text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-primary-soft)] hover:text-[var(--color-primary)]" title="查看"><Eye className="h-4 w-4" /></Link>
                <button type="button" onClick={() => void handleDownload(file)} className="rounded p-1.5 text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-primary-soft)] hover:text-[var(--color-primary)]" title="下载"><Download className="h-4 w-4" /></button>
              </div>
            </li>
          );
        })}</ul>
      )}
    </DashboardCard>
  );
}
