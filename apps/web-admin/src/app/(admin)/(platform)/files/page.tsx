"use client";

import { IndustrialPage, IndustrialPanel, typography } from "@zhenhang/ui";
import {
  FileText,
  Image,
  FileSpreadsheet,
  FileArchive,
  Upload,
  Download,
  Trash2,
  Search,
  FolderOpen,
  MoreHorizontal,
  Clock,
  User,
} from "lucide-react";
import { useState } from "react";
import { fieldInputClass, inlineBtnClass, inlineBtnDangerClass } from "@/lib/form-styles";

type FileItem = {
  id: string;
  name: string;
  type: string;
  size: string;
  uploadedBy: string;
  uploadedAt: string;
  category: string;
};

const mockFiles: FileItem[] = [
  { id: "1", name: "技术方案_V3.2.pdf", type: "pdf", size: "2.4 MB", uploadedBy: "张工", uploadedAt: "2026-05-28", category: "技术文档" },
  { id: "2", name: "产品规格书.docx", type: "docx", size: "856 KB", uploadedBy: "李经理", uploadedAt: "2026-05-27", category: "产品资料" },
  { id: "3", name: "报价模板_2026Q2.xlsx", type: "xlsx", size: "1.2 MB", uploadedBy: "王销售", uploadedAt: "2026-05-26", category: "报价文件" },
  { id: "4", name: "现场照片_20260525.jpg", type: "jpg", size: "3.8 MB", uploadedBy: "赵工", uploadedAt: "2026-05-25", category: "现场资料" },
  { id: "5", name: "BOM清单_项目A.xlsx", type: "xlsx", size: "512 KB", uploadedBy: "陈工", uploadedAt: "2026-05-24", category: "BOM" },
  { id: "6", name: "合同模板.zip", type: "zip", size: "4.1 MB", uploadedBy: "刘法务", uploadedAt: "2026-05-23", category: "合同文件" },
  { id: "7", name: "设备安装图.dwg", type: "dwg", size: "8.6 MB", uploadedBy: "周工", uploadedAt: "2026-05-22", category: "图纸" },
  { id: "8", name: "质量检验报告.pdf", type: "pdf", size: "1.5 MB", uploadedBy: "质检部", uploadedAt: "2026-05-21", category: "质检" },
];

const FILE_TYPE_ICONS: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  pdf: FileText,
  docx: FileText,
  xlsx: FileSpreadsheet,
  jpg: Image,
  png: Image,
  zip: FileArchive,
  rar: FileArchive,
};

const FILE_TYPE_COLORS: Record<string, string> = {
  pdf: "text-[var(--color-danger)] bg-[var(--color-accent-soft)]",
  docx: "text-[var(--color-primary)] bg-[var(--color-primary-soft)]",
  xlsx: "text-[var(--color-success)] bg-[#f0fdf4]",
  jpg: "text-[#7c3aed] bg-[#faf5ff]",
  png: "text-[#7c3aed] bg-[#faf5ff]",
  zip: "text-[var(--color-warning)] bg-[#fffbeb]",
  rar: "text-[var(--color-warning)] bg-[#fffbeb]",
};

const CATEGORIES = ["全部", "技术文档", "产品资料", "报价文件", "BOM", "合同文件", "图纸", "质检", "现场资料"];

export default function FilesPage() {
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("全部");

  const filteredFiles = mockFiles.filter((f) => {
    const matchCategory = activeCategory === "全部" || f.category === activeCategory;
    const matchSearch = !search || f.name.toLowerCase().includes(search.toLowerCase());
    return matchCategory && matchSearch;
  });

  return (
    <IndustrialPage gap="md">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className={typography.pageTitle}>文件中心</h1>
          <p className={typography.caption}>管理所有项目文档与资料</p>
        </div>
        <button type="button" className="btn-primary h-8 gap-2 px-3 text-xs">
          <Upload size={14} />
          上传文件
        </button>
      </div>

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

      <IndustrialPanel title={`文件列表 (${filteredFiles.length})`}>
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

        <div className="grid gap-3 sm:grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
          {filteredFiles.map((file) => {
            const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
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
                    <p className="truncate text-sm font-medium text-[var(--color-text)]">{file.name}</p>
                    <p className="mt-0.5 text-[11px] text-[var(--color-text-muted)]">{file.size}</p>
                    <div className="mt-2 flex items-center gap-3 text-[11px] text-[var(--color-text-muted)]">
                      <span className="flex items-center gap-1">
                        <User size={11} />
                        {file.uploadedBy}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock size={11} />
                        {file.uploadedAt}
                      </span>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="invisible shrink-0 rounded-lg p-1.5 text-[var(--color-text-muted)] transition-colors group-hover:visible hover:bg-[var(--color-surface-soft)] hover:text-[var(--color-text)]"
                  >
                    <MoreHorizontal size={16} />
                  </button>
                </div>
                <div className="mt-3 flex gap-2 opacity-0 transition-opacity group-hover:opacity-100">
                  <button type="button" className={`flex flex-1 items-center justify-center gap-1.5 py-1.5 ${inlineBtnClass}`}>
                    <Download size={13} />
                    下载
                  </button>
                  <button type="button" className={`flex flex-1 items-center justify-center gap-1.5 py-1.5 ${inlineBtnClass}`}>
                    <FolderOpen size={13} />
                    移动
                  </button>
                  <button type="button" className={`flex flex-1 items-center justify-center gap-1.5 py-1.5 ${inlineBtnDangerClass}`}>
                    <Trash2 size={13} />
                    删除
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {filteredFiles.length === 0 && (
          <div className="py-12 text-center">
            <FileText size={40} className="mx-auto mb-3 text-[var(--color-border)]" />
            <p className="text-sm text-[var(--color-text-muted)]">未找到匹配的文件</p>
          </div>
        )}
      </IndustrialPanel>
    </IndustrialPage>
  );
}
