"use client";

import * as React from "react";
import {
  StatusBadge,
  WorkspaceToolbarButton,
  designTokens,
  exportStatusToInteraction,
  interactionTokens,
  typography,
} from "@zhenhang/ui";
import type { ExportTemplateOption } from "./types";

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
  onDownload,
}: {
  templates: ExportTemplateOption[];
  selectedId?: string;
  onSelect: (id: string) => void;
  onExport: () => void;
  exporting?: boolean;
  exportStatus?: string;
  onDownload?: () => void;
}) {
  const selected = templates.find((t) => t.id === selectedId) ?? templates[0];
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
      <div className="flex flex-wrap items-center gap-2 border-t pt-2" style={{ borderColor: designTokens.colors.border.default }}>
        <WorkspaceToolbarButton
          variant="primary"
          loading={exporting}
          disabled={exporting || !selected}
          keyboardHint="Ctrl+Shift+E"
          onClick={onExport}
        >
          {exporting ? "生成中…" : `导出 ${selected?.format?.toUpperCase()}`}
        </WorkspaceToolbarButton>
        {exportStatus ? (
          <StatusBadge
            status={exportStatusToInteraction(exportStatus)}
            label={exportStatus}
            compact
            pulse={exportStatus !== "completed"}
          />
        ) : null}
        {onDownload ? (
          <WorkspaceToolbarButton onClick={onDownload}>下载文件</WorkspaceToolbarButton>
        ) : null}
      </div>
    </div>
  );
}
