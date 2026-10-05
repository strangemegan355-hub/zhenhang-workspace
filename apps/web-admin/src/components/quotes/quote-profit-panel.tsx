"use client";

import {
  ApprovalUxPanel,
  CostVisualization,
  ExportTemplatePicker,
  type ApprovalRecordView,
  type ExportTemplateOption,
  type QuoteLineRow,
  type WorkflowActionOption,
} from "@zhenhang/quote-builder";
import { StatusBadge, workflowStateToStatus, typography } from "@zhenhang/ui";

const STATUS_LABEL: Record<string, string> = {
  draft: "草稿",
  reviewing: "审批中",
  approved: "已批准",
  rejected: "已驳回",
};

type QuoteProfitPanelProps = {
  lines: QuoteLineRow[];
  marginRate: number;
  onMarginRateChange: (rate: number) => void;
  workflowState: string;
  workflowActions: WorkflowActionOption[];
  approvalRecords: ApprovalRecordView[];
  onTransition: (actionCode: string, comment?: string) => void;
  transitionPending?: boolean;
  exportTemplates: ExportTemplateOption[];
  selectedTemplateId?: string;
  onTemplateSelect: (id: string) => void;
  onExport: () => void;
  exporting?: boolean;
  exportStatus?: string;
  exportFileName?: string;
  exportMessage?: string | null;
  exportError?: string | null;
  onDownloadExport?: () => void;
  readOnly?: boolean;
};

export function QuoteProfitPanel({
  lines,
  marginRate,
  onMarginRateChange,
  workflowState,
  workflowActions,
  approvalRecords,
  onTransition,
  transitionPending,
  exportTemplates,
  selectedTemplateId,
  onTemplateSelect,
  onExport,
  exporting,
  exportStatus,
  exportFileName,
  exportMessage,
  exportError,
  onDownloadExport,
  readOnly,
}: QuoteProfitPanelProps) {
  const showExport = workflowState === "approved" || workflowState === "draft" || workflowState === "reviewing";

  return (
    <aside className="flex h-full min-h-0 flex-col border-l border-[var(--color-border)] bg-[var(--color-surface)]">
      <div className="border-b border-[var(--color-border)] p-3">
        <h2 className={`${typography.cardTitle} text-sm`}>成本与利润</h2>
        <div className="mt-2 flex items-center gap-2">
          <StatusBadge
            status={workflowStateToStatus(workflowState)}
            label={STATUS_LABEL[workflowState] ?? workflowState}
            compact
            pulse={workflowState === "reviewing"}
          />
        </div>
        <label className="mt-3 flex items-center gap-2 text-[11px] text-[var(--color-text-muted)]">
          目标毛利率
          <input
            type="range"
            min={0}
            max={50}
            disabled={readOnly}
            value={Math.round(marginRate * 100)}
            onChange={(e) => onMarginRateChange(Number(e.target.value) / 100)}
            className="flex-1"
          />
          <span className="w-8 font-mono tabular-nums text-[var(--color-text)]">{(marginRate * 100).toFixed(0)}%</span>
        </label>
      </div>

      <div className="min-h-0 flex-1 space-y-3 overflow-auto p-3">
        <CostVisualization lines={lines} marginRate={marginRate} />

        {workflowState === "reviewing" ? (
          <div className="rounded-xl border border-[var(--color-border)] p-2">
            <ApprovalUxPanel
              workflowState={workflowState}
              actions={workflowActions}
              records={approvalRecords}
              onTransition={onTransition}
              pending={transitionPending}
            />
          </div>
        ) : null}

        {showExport ? (
          <div className="rounded-xl border border-[var(--color-border)] p-2">
            <p className="mb-2 text-xs font-medium text-[var(--color-text)] dark:text-[#f1f5f9]">导出</p>
            <ExportTemplatePicker
              templates={exportTemplates}
              selectedId={selectedTemplateId}
              onSelect={onTemplateSelect}
              onExport={onExport}
              exporting={exporting}
              exportStatus={exportStatus}
              exportFileName={exportFileName}
              exportMessage={exportMessage}
              exportError={exportError}
              onDownload={onDownloadExport}
            />
          </div>
        ) : null}
      </div>
    </aside>
  );
}
