"use client";

import * as React from "react";
import {
  StatusBadge,
  WorkspaceToolbarButton,
  designTokens,
  exportStatusToInteraction,
  typography,
} from "@zhenhang/ui";
import type { ExportTemplateOption } from "./types";

export const DEFAULT_EXPORT_TEMPLATES: ExportTemplateOption[] = [
  {
    id: "default-pdf",
    name: "标准 PDF",
    format: "pdf",
    description: "适合常规报价确认与归档",
  },
  {
    id: "detailed-pdf",
    name: "明细 PDF",
    format: "pdf",
    description: "包含 BOM、成本与签章区",
  },
  {
    id: "company-branded-xlsx",
    name: "公司报价表（含公式）",
    format: "xlsx",
    description: "抬头使用公司名称，含小计/利润/毛利率 Excel 公式",
  },
  {
    id: "default-xlsx",
    name: "报价 Excel",
    format: "xlsx",
    description: "用于客户表格流转",
  },
  {
    id: "cost-xlsx",
    name: "成本 Excel",
    format: "xlsx",
    description: "用于内部成本复核",
  },
];

const BLOCK_LAYOUTS: Record<string, Array<{ id: string; label: string; h: number }>> = {
  "default-pdf": [
    { id: "header", label: "抬头 / 客户", h: 2 },
    { id: "summary", label: "报价摘要", h: 1 },
    { id: "lines", label: "行项目表", h: 4 },
    { id: "total", label: "合计与条款", h: 1 },
  ],
  "detailed-pdf": [
    { id: "header", label: "抬头", h: 2 },
    { id: "bom", label: "BOM 明细", h: 3 },
    { id: "lines", label: "报价行", h: 3 },
    { id: "cost", label: "成本分析", h: 2 },
    { id: "sign", label: "签章区", h: 1 },
  ],
  "company-branded-xlsx": [
    { id: "header", label: "公司抬头", h: 2 },
    { id: "meta", label: "报价信息", h: 2 },
    { id: "lines", label: "明细表（含公式）", h: 5 },
    { id: "summary", label: "合计/利润/毛利率", h: 2 },
  ],
  "default-xlsx": [
    { id: "meta", label: "元数据", h: 1 },
    { id: "lines", label: "数据表", h: 5 },
    { id: "chart", label: "图表", h: 2 },
  ],
  "cost-xlsx": [
    { id: "summary", label: "汇总", h: 2 },
    { id: "cost", label: "成本列", h: 4 },
    { id: "margin", label: "毛利列", h: 2 },
  ],
};

export function ExportTemplateBlockPreview({ template }: { template: ExportTemplateOption }) {
  const blocks = BLOCK_LAYOUTS[template.id] ?? BLOCK_LAYOUTS["default-pdf"];
  return (
    <div className="rounded-md border border-dashed border-zinc-300 bg-white p-3 dark:border-zinc-600 dark:bg-zinc-950">
      <div className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-zinc-500">版面预览 · A4</div>
      <div className="mx-auto max-w-[200px] space-y-1 rounded border border-zinc-200 bg-zinc-50 p-2 shadow-inner dark:border-zinc-700 dark:bg-zinc-900">
        {blocks.map((b) => (
          <div
            key={b.id}
            className="rounded border border-blue-200 bg-blue-50/80 px-2 py-1 text-[10px] font-medium text-blue-900 dark:border-blue-800 dark:bg-blue-950/50 dark:text-blue-200"
            style={{ minHeight: `${b.h * 12}px` }}
          >
            {b.label}
          </div>
        ))}
      </div>
    </div>
  );
}

export function ExportTemplatePicker({
  templates,
  selectedId,
  onSelect,
  onExport,
  exporting,
  exportStatus,
  exportFileName,
  exportMessage,
  exportError,
  onDownload,
}: {
  templates: ExportTemplateOption[];
  selectedId?: string;
  onSelect: (id: string) => void;
  onExport: () => void;
  exporting?: boolean;
  exportStatus?: string;
  exportFileName?: string;
  exportMessage?: string | null;
  exportError?: string | null;
  onDownload?: () => void;
}) {
  const selected = templates.find((t) => t.id === selectedId) ?? templates[0];
  const statusLabel =
    exportStatus === "completed"
      ? "已完成"
      : exportStatus === "pending"
        ? "生成中…"
        : exportStatus === "failed"
          ? "失败"
          : exportStatus;
  return (
    <div className="space-y-3 rounded-lg border border-zinc-200 bg-white p-3 shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
      <div className="text-sm font-semibold">导出模板 · 区块编排</div>
      <div className="grid gap-2 sm:grid-cols-2">
        {templates.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => onSelect(t.id)}
            className={`rounded-lg border p-2.5 text-left transition ${
              selected?.id === t.id
                ? "border-blue-500 bg-blue-50/80 ring-2 ring-blue-500/30 dark:bg-blue-950/30"
                : "hover:border-zinc-300 dark:hover:border-zinc-600"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">{t.name}</span>
              <span className="rounded bg-zinc-200 px-1.5 text-[10px] uppercase dark:bg-zinc-700">{t.format}</span>
            </div>
            {t.description ? <p className="mt-1 text-xs text-zinc-500">{t.description}</p> : null}
          </button>
        ))}
      </div>
      {selected ? <ExportTemplateBlockPreview template={selected} /> : null}
      {exportError ? (
        <p className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-800 dark:bg-red-950/40 dark:text-red-200">
          {exportError}
        </p>
      ) : null}
      {exportMessage ? (
        <p className="rounded-md border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200">
          {exportMessage}
        </p>
      ) : null}
      {exportFileName && exportStatus === "completed" ? (
        <p className={`${typography.caption} text-zinc-600 dark:text-zinc-400`}>
          文件：<span className="font-medium text-zinc-900 dark:text-zinc-100">{exportFileName}</span>
          <span className="ml-2">点击「下载文件」将保存到浏览器默认下载目录</span>
        </p>
      ) : null}
      <div className="flex flex-wrap items-center gap-2 border-t pt-2" style={{ borderColor: designTokens.colors.border.default }}>
        <WorkspaceToolbarButton
          variant="primary"
          loading={exporting || exportStatus === "pending"}
          disabled={exporting || exportStatus === "pending" || !selected}
          keyboardHint="Ctrl+Shift+E"
          onClick={onExport}
        >
          {exporting || exportStatus === "pending" ? "生成中…" : `导出 ${selected?.format?.toUpperCase()}`}
        </WorkspaceToolbarButton>
        {exportStatus ? (
          <StatusBadge
            status={exportStatusToInteraction(exportStatus)}
            label={statusLabel ?? exportStatus}
            compact
            pulse={exportStatus !== "completed" && exportStatus !== "failed"}
          />
        ) : null}
        {onDownload ? (
          <WorkspaceToolbarButton variant="primary" onClick={onDownload}>
            下载文件
          </WorkspaceToolbarButton>
        ) : null}
      </div>
    </div>
  );
}
