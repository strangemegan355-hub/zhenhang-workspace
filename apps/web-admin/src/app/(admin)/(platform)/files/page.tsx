"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { EmptyState, ErrorBanner, IndustrialPanel, IndustrialPage, typography } from "@zhenhang/ui";
import {
  Download,
  FileArchive,
  FileSpreadsheet,
  FileText,
  Image as ImageIcon,
  Search,
  Upload,
} from "lucide-react";
import { useRef, useState } from "react";
import { fieldInputClass, inlineBtnClass } from "@/lib/form-styles";
import { useAuthStore } from "@/store/auth-store";

type FileItem = {
  id: string;
  file_name: string;
  file_ext: string | null;
  mime_type: string | null;
  size_bytes: number;
  category: string;
  created_at: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const CATEGORIES = ["全部", "技术文档", "产品资料", "报价文件", "BOM", "合同文件", "图纸", "质检", "现场资料"];

const FILE_TYPE_ICONS: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  pdf: FileText,
  docx: FileText,
  doc: FileText,
  xlsx: FileSpreadsheet,
  xls: FileSpreadsheet,
  jpg: ImageIcon,
  jpeg: ImageIcon,
  png: ImageIcon,
  zip: FileArchive,
  rar: FileArchive,
};

const FILE_TYPE_COLORS: Record<string, string> = {
  pdf: "text-[var(--color-danger)] bg-[var(--color-accent-soft)]",
  docx: "text-[var(--color-primary)] bg-[var(--color-primary-soft)]",
  doc: "text-[var(--color-primary)] bg-[var(--color-primary-soft)]",
  xlsx: "text-[var(--color-success)] bg-[var(--color-surface-soft)]",
  xls: "text-[var(--color-success)] bg-[var(--color-surface-soft)]",
  jpg: "text-[var(--color-primary)] bg-[var(--color-primary-soft)]",
  jpeg: "text-[var(--color-primary)] bg-[var(--color-primary-soft)]",
  png: "text-[var(--color-primary)] bg-[var(--color-primary-soft)]",
  zip: "text-[var(--color-warning)] bg-[var(--color-surface-soft)]",
  rar: "text-[var(--color-warning)] bg-[var(--color-surface-soft)]",
};

function extensionOf(name: string): string {
  const parts = name.split(".");
  return parts.length > 1 ? (parts.pop() as string).toLowerCase() : "";
}

function formatSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value >= 10 || unit === 0 ? Math.round(value) : value.toFixed(1)} ${units[unit]}`;
}

function formatDate(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "—" : parsed.toLocaleDateString();
}

export default function FilesPage() {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.token?.accessToken);
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("全部");
  const [actionError, setActionError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // The list is small (page_size 100) and filtering in the browser keeps typing responsive
  // without firing a request per keystroke.
  const filesQuery = useQuery({
    queryKey: ["files"],
    enabled: Boolean(token),
    queryFn: async (): Promise<FileItem[]> => {
      const resp = await fetch(`${API_BASE}/api/v1/files?page=1&page_size=100`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const body = await resp.json();
      // UnifiedResponseMiddleware wraps every JSON body as {code, message, data}.
      const page = body?.data ?? body;
      return (page?.items ?? []) as FileItem[];
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("category", activeCategory === "全部" ? "general" : activeCategory);
      form.append("upload", file);
      const resp = await fetch(`${API_BASE}/api/v1/files/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return resp.json();
    },
    onSuccess: () => {
      setActionError(null);
      void queryClient.invalidateQueries({ queryKey: ["files"] });
    },
    onError: (error: unknown) =>
      setActionError(`上传失败：${error instanceof Error ? error.message : "未知错误"}`),
  });

  async function downloadFile(file: FileItem) {
    if (!token) return;
    try {
      const resp = await fetch(`${API_BASE}/api/v1/files/${file.id}/download`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = file.file_name;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setActionError(null);
    } catch (error: unknown) {
      setActionError(`下载失败：${error instanceof Error ? error.message : "未知错误"}`);
    }
  }

  const files = filesQuery.data ?? [];
  const filteredFiles = files.filter((file) => {
    const matchCategory = activeCategory === "全部" || file.category === activeCategory;
    const matchSearch = !search || file.file_name.toLowerCase().includes(search.toLowerCase());
    return matchCategory && matchSearch;
  });

  return (
    <IndustrialPage gap="md">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className={typography.pageTitle}>文件中心</h1>
          <p className={typography.caption}>管理所有项目文档与资料 · 数据来自 /api/v1/files</p>
        </div>
        <button
          type="button"
          className="btn-primary h-8 gap-2 px-3 text-xs"
          disabled={uploadMutation.isPending || !token}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload size={14} />
          {uploadMutation.isPending ? "上传中…" : "上传文件"}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={(event) => {
            const picked = event.target.files?.[0];
            if (picked) uploadMutation.mutate(picked);
            event.target.value = "";
          }}
        />
      </div>

      {actionError ? <ErrorBanner message={actionError} /> : null}

      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setActiveCategory(cat)}
            className={`rounded-[var(--radius-btn)] border px-3 py-1.5 text-xs font-medium transition-colors ${
              activeCategory === cat
                ? "border-[var(--color-primary)] bg-[var(--color-primary-soft)] text-[var(--color-primary)]"
                : "border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:bg-[var(--color-surface-soft)]"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      <IndustrialPanel title={`文件列表 (${filteredFiles.length})`} inlineLoading={filesQuery.isFetching}>
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <div className="relative min-w-[200px] flex-1">
            <Search size={15} className="absolute top-1/2 left-3 -translate-y-1/2 text-[var(--color-text-soft)]" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索文件名..."
              className={`${fieldInputClass} h-9 pl-9`}
            />
          </div>
        </div>

        {filesQuery.isError ? (
          <ErrorBanner message="文件列表加载失败，请检查后端连接后重试" onRetry={() => filesQuery.refetch()} />
        ) : files.length === 0 ? (
          <EmptyState message="暂无文件" hint="点击右上角「上传文件」上传第一个文件" />
        ) : (
          <div className="grid gap-3 sm:grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
            {filteredFiles.map((file) => {
              const ext = extensionOf(file.file_name);
              const Icon = FILE_TYPE_ICONS[ext] ?? FileText;
              const colorClass = FILE_TYPE_COLORS[ext] ?? "text-[var(--color-text-muted)] bg-[var(--color-surface-soft)]";

              return (
                <div
                  key={file.id}
                  className="group relative rounded-[var(--radius-card)] border border-[var(--color-border)] bg-[var(--color-surface)] p-4 transition-colors hover:bg-[var(--color-surface-soft)]"
                >
                  <div className="flex items-start gap-3">
                    <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${colorClass}`}>
                      <Icon size={20} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-[var(--color-text)]">{file.file_name}</p>
                      <p className="mt-0.5 text-[11px] text-[var(--color-text-muted)]">
                        {formatSize(file.size_bytes)} · {file.category}
                      </p>
                      <div className="mt-2 flex items-center gap-3 text-[11px] text-[var(--color-text-muted)]">
                        <span>{formatDate(file.created_at)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 flex gap-2 opacity-0 transition-opacity group-hover:opacity-100">
                    <button
                      type="button"
                      onClick={() => void downloadFile(file)}
                      className={`flex flex-1 items-center justify-center gap-1.5 py-1.5 ${inlineBtnClass}`}
                    >
                      <Download size={13} />
                      下载
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {files.length > 0 && filteredFiles.length === 0 && (
          <div className="py-12 text-center">
            <FileText size={40} className="mx-auto mb-3 text-[var(--color-border)]" />
            <p className="text-sm text-[var(--color-text-muted)]">未找到匹配的文件</p>
          </div>
        )}
      </IndustrialPanel>
    </IndustrialPage>
  );
}
