"use client";

import * as React from "react";
import {
  INDUSTRIAL_SHORTCUT_HINTS,
  StatusBadge,
  WorkspaceDock,
  WorkspaceMain,
  WorkspacePanel,
  WorkspaceSidebar,
  WorkspaceSidebarNav,
  WorkspaceToolbar,
  WorkspaceToolbarButton,
  useIndustrialShortcuts,
  workflowStateToStatus,
} from "@zhenhang/ui";
import { BomWorkspaceLayout } from "./bom-workspace-layout";
import { AIAnalysisPanel } from "./ai-analysis-panel";
import { ActivityLogPanel } from "./activity-log-panel";
import { ApprovalUxPanel } from "./approval-ux-panel";
import { BomTreeEditor, flatBomToTree } from "./bom-tree-editor";
import { CostVisualization } from "./cost-visualization";
import { DemoGuideStrip } from "./demo-guide";
import { ExportTemplatePicker, DEFAULT_EXPORT_TEMPLATES } from "./export-template-blocks";
import { FormulaLivePanel } from "./formula-live-panel";
import { QuoteDiffPanel } from "./quote-diff-panel";
import { QuoteLineEditor } from "./quote-line-editor";
import { useUndoRedo } from "./use-undo-redo";
import type {
  ApprovalRecordView,
  BomTreeNode,
  ExportTemplateOption,
  QuoteLineRow,
  WorkflowActionOption,
} from "./types";

export { DEFAULT_EXPORT_TEMPLATES };

export type QuoteWorkbenchProps = {
  quoteNo?: string;
  title?: string;
  workflowState: string;
  readOnly?: boolean;
  lines: QuoteLineRow[];
  onLinesChange: (lines: QuoteLineRow[]) => void;
  marginRate: number;
  onMarginRateChange: (rate: number) => void;
  bomNodes?: BomTreeNode[];
  bomItemsRaw?: Array<{
    id: string;
    item_code: string;
    item_name: string;
    quantity: number;
    unit_cost: number;
    line_total?: number;
  }>;
  onImportBom?: () => void;
  workflowActions: WorkflowActionOption[];
  approvalRecords: ApprovalRecordView[];
  onTransition: (actionCode: string, comment?: string) => void;
  transitionPending?: boolean;
  exportTemplates?: ExportTemplateOption[];
  selectedTemplateId?: string;
  onTemplateSelect: (id: string) => void;
  onExport: () => void;
  exporting?: boolean;
  exportStatus?: string;
  onDownloadExport?: () => void;
  diffFromVersion?: number;
  diffToVersion?: number;
  onDiffVersionChange?: (from: number, to: number) => void;
  diffRows?: Array<{ item: string; oldValue: number; newValue: number; changeType: "added" | "removed" | "changed" }>;
  onSaveVersion?: () => void;
  savingVersion?: boolean;
  copilotSummary?: string;
  copilotHighlights?: string[];
  copilotLoading?: boolean;
  onCopilotRefresh?: () => void;
  copilotData?: import("./ai-analysis-panel").AIAnalysisData;
  showDemoGuide?: boolean;
  aiSlot?: React.ReactNode;
  panelLoading?: boolean;
  errorMessage?: string;
  onErrorRetry?: () => void;
  bomLoading?: boolean;
};

const MODULE_NAV = [
  { id: "bom", label: "BOM 树" },
  { id: "lines", label: "行项目" },
  { id: "formula", label: "公式 LIVE" },
  { id: "cost", label: "成本视图" },
] as const;

export function QuoteWorkbench(props: QuoteWorkbenchProps) {
  const {
    quoteNo,
    title,
    workflowState,
    readOnly,
    lines,
    onLinesChange,
    marginRate,
    onMarginRateChange,
    bomNodes,
    bomItemsRaw,
    onImportBom,
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
    onDownloadExport,
    diffFromVersion = 1,
    diffToVersion = 2,
    onDiffVersionChange,
    diffRows = [],
    onSaveVersion,
    savingVersion,
    copilotSummary,
    copilotHighlights = [],
    copilotLoading,
    onCopilotRefresh,
    copilotData,
    showDemoGuide = false,
    aiSlot,
    panelLoading,
    errorMessage,
    onErrorRetry,
    bomLoading,
  } = props;

  const resetKey = quoteNo ?? "default";
  const undo = useUndoRedo(lines, resetKey);
  const [localBom, setLocalBom] = React.useState<BomTreeNode[]>([]);
  const [activeModule, setActiveModule] = React.useState<string>("lines");
  const [dockTabId, setDockTabId] = React.useState("approval");
  const [dockCollapsed, setDockCollapsed] = React.useState(false);
  const [showExportPicker, setShowExportPicker] = React.useState(false);

  const treeNodes =
    bomNodes ??
    (bomItemsRaw ? flatBomToTree(bomItemsRaw, true) : localBom.length ? localBom : []);

  React.useEffect(() => {
    if (bomItemsRaw?.length) setLocalBom(flatBomToTree(bomItemsRaw, true));
  }, [bomItemsRaw]);

  const commitLines = React.useCallback(
    (next: QuoteLineRow[]) => {
      undo.commit(next);
      onLinesChange(next);
    },
    [onLinesChange, undo],
  );

  const handleUndo = () => onLinesChange(undo.undo());
  const handleRedo = () => onLinesChange(undo.redo());

  useIndustrialShortcuts([
    {
      id: "undo",
      key: "z",
      ctrl: true,
      enabled: !readOnly,
      handler: (e) => {
        if (e.shiftKey) return;
        onLinesChange(undo.undo());
      },
    },
    {
      id: "redo-y",
      key: "y",
      ctrl: true,
      enabled: !readOnly,
      handler: () => onLinesChange(undo.redo()),
    },
    {
      id: "redo-z",
      key: "z",
      ctrl: true,
      shift: true,
      enabled: !readOnly,
      handler: () => onLinesChange(undo.redo()),
    },
    {
      id: "save",
      key: "s",
      ctrl: true,
      enabled: !readOnly && Boolean(onSaveVersion) && !savingVersion,
      handler: () => onSaveVersion?.(),
    },
    {
      id: "export",
      key: "e",
      ctrl: true,
      shift: true,
      enabled: !exporting,
      handler: () => onExport(),
    },
    { id: "dock-1", key: "1", alt: true, handler: () => setDockTabId("approval") },
    { id: "dock-2", key: "2", alt: true, handler: () => setDockTabId("diff") },
    { id: "dock-3", key: "3", alt: true, handler: () => setDockTabId("ai") },
    { id: "dock-4", key: "4", alt: true, handler: () => setDockTabId("log") },
    {
      id: "esc",
      key: "Escape",
      preventDefault: false,
      handler: () => {
        setShowExportPicker(false);
        setDockCollapsed(true);
      },
    },
  ]);

  const displayLines = lines;
  const addLine = () => {
    commitLines([
      ...displayLines,
      {
        item_code: `ITEM-${displayLines.length + 1}`,
        item_name: "新物料",
        unit: "EA",
        quantity: 1,
        unit_price: 0,
        unit_cost: 0,
      },
    ]);
  };

  const riskLevel: "low" | "medium" | "high" =
    copilotData?.riskLevel ??
    ((copilotHighlights?.length ?? 0) > 4 ? "high" : marginRate < 0.1 ? "medium" : "low");

  const templates = exportTemplates ?? DEFAULT_EXPORT_TEMPLATES;
  const approveAction = workflowActions.find((a) => a.action_code === "approve");
  const rejectAction = workflowActions.find((a) => a.action_code === "reject");
  const busy = Boolean(savingVersion || transitionPending || exporting);

  const dockTabs = [
    {
      id: "approval",
      label: "审批",
      badge: workflowState === "reviewing" ? "!" : undefined,
      content: (
        <ApprovalUxPanel
          workflowState={workflowState}
          actions={workflowActions}
          records={approvalRecords}
          onTransition={onTransition}
          pending={transitionPending}
        />
      ),
    },
    {
      id: "diff",
      label: "版本对比",
      content: (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-[#94A3B8]">对比</span>
            <input
              type="number"
              min={1}
              className="h-7 w-14 rounded border border-[#334155] bg-[#0F172A] px-1 text-xs text-[#F8FAFC]"
              value={diffFromVersion}
              onChange={(e) => onDiffVersionChange?.(Number(e.target.value), diffToVersion)}
            />
            <span className="text-[#64748B]">→</span>
            <input
              type="number"
              min={1}
              className="h-7 w-14 rounded border border-[#334155] bg-[#0F172A] px-1 text-xs text-[#F8FAFC]"
              value={diffToVersion}
              onChange={(e) => onDiffVersionChange?.(diffFromVersion, Number(e.target.value))}
            />
          </div>
          <QuoteDiffPanel
            fromVersion={`V${diffFromVersion}`}
            toVersion={`V${diffToVersion}`}
            diffRows={diffRows.length ? diffRows : [{ item: "—", oldValue: 0, newValue: 0, changeType: "changed" }]}
          />
        </div>
      ),
    },
    {
      id: "ai",
      label: "AI 分析",
      content:
        aiSlot ?? (
          <AIAnalysisPanel
            data={
              copilotData ?? {
                summary: copilotSummary,
                highlights: copilotHighlights,
                riskLevel,
                recommendations:
                  workflowState === "reviewing"
                    ? ["建议核对 BOM 成本快照", "关注毛利率是否达标", "大额变更需二次审批"]
                    : ["可提交审批或导出发客户"],
                loading: copilotLoading,
                onRefresh: onCopilotRefresh,
              }
            }
          />
        ),
    },
    {
      id: "log",
      label: "活动日志",
      content: <ActivityLogPanel />,
    },
  ];

  return (
    <div className="space-y-2">
      {showDemoGuide ? <DemoGuideStrip /> : null}

      <BomWorkspaceLayout
        minHeight={720}
        loading={busy}
        loadingLabel={savingVersion ? "保存版本中…" : exporting ? "导出中…" : "处理中…"}
        inlineLoading={copilotLoading}
        panelLoading={panelLoading}
        errorMessage={errorMessage}
        onErrorRetry={onErrorRetry}
        toolbar={
          <WorkspaceToolbar
            title={title ?? "工业报价工作台"}
            subtitle={
              <>
                {quoteNo ?? "—"} ·{" "}
                <StatusBadge
                  status={workflowStateToStatus(workflowState)}
                  label={WORKFLOW_LABELS[workflowState] ?? workflowState}
                  compact
                  pulse={workflowState === "reviewing"}
                />
              </>
            }
            loading={busy}
            leading={
              <div className="flex items-center gap-1 border-r border-[#334155] pr-2">
                <WorkspaceToolbarButton
                  keyboardHint="Ctrl+Z"
                  disabled={!undo.canUndo || readOnly}
                  onClick={handleUndo}
                >
                  撤销
                </WorkspaceToolbarButton>
                <WorkspaceToolbarButton
                  keyboardHint="Ctrl+Y"
                  disabled={!undo.canRedo || readOnly}
                  onClick={handleRedo}
                >
                  重做
                </WorkspaceToolbarButton>
              </div>
            }
            actions={
              <>
                <span className="hidden text-xs text-[#94A3B8] sm:inline">
                  {displayLines.length} 行 · BOM {treeNodes.length}
                </span>
                <label className="hidden items-center gap-1 text-xs text-[#CBD5E1] lg:flex">
                  毛利率
                  <input
                    type="range"
                    min={0}
                    max={50}
                    disabled={readOnly}
                    value={Math.round(marginRate * 100)}
                    onChange={(e) => onMarginRateChange(Number(e.target.value) / 100)}
                    className="w-20"
                  />
                  <span className="w-8 font-mono tabular-nums">{(marginRate * 100).toFixed(0)}%</span>
                </label>
                {!readOnly && onSaveVersion ? (
                  <WorkspaceToolbarButton
                    variant="primary"
                    keyboardHint={INDUSTRIAL_SHORTCUT_HINTS.save}
                    loading={savingVersion}
                    disabled={savingVersion}
                    onClick={onSaveVersion}
                  >
                    新版本
                  </WorkspaceToolbarButton>
                ) : null}
                <WorkspaceToolbarButton
                  keyboardHint={INDUSTRIAL_SHORTCUT_HINTS.export}
                  active={showExportPicker}
                  loading={exporting}
                  disabled={exporting}
                  onClick={() => setShowExportPicker((v) => !v)}
                >
                  导出
                </WorkspaceToolbarButton>
                {workflowState === "reviewing" && approveAction ? (
                  <WorkspaceToolbarButton
                    variant="primary"
                    loading={transitionPending}
                    disabled={transitionPending}
                    onClick={() => onTransition(approveAction.action_code)}
                  >
                    批准
                  </WorkspaceToolbarButton>
                ) : null}
                {workflowState === "reviewing" && rejectAction ? (
                  <WorkspaceToolbarButton
                    variant="danger"
                    loading={transitionPending}
                    disabled={transitionPending}
                    onClick={() => onTransition(rejectAction.action_code)}
                  >
                    驳回
                  </WorkspaceToolbarButton>
                ) : null}
              </>
            }
          />
        }
        sidebar={
          <WorkspaceSidebar title="BOM / 模块">
            <WorkspaceSidebarNav
              sectionLabel="模块"
              items={MODULE_NAV.map((m) => ({ id: m.id, label: m.label }))}
              activeId={activeModule}
              onSelect={setActiveModule}
            />
            <BomTreeEditor
              nodes={treeNodes}
              rootLabel={quoteNo ? `BOM · ${quoteNo}` : "设备 BOM"}
              onImportToQuote={readOnly ? undefined : onImportBom}
              onNodesReorder={readOnly ? undefined : setLocalBom}
              readOnly={readOnly}
              embedded
              loading={bomLoading}
            />
          </WorkspaceSidebar>
        }
        main={
          <WorkspaceMain>
            {showExportPicker ? (
              <WorkspacePanel title="导出模板" className="shrink-0">
                <ExportTemplatePicker
                  templates={templates}
                  selectedId={selectedTemplateId}
                  onSelect={onTemplateSelect}
                  onExport={onExport}
                  exporting={exporting}
                  exportStatus={exportStatus}
                  onDownload={onDownloadExport}
                />
              </WorkspacePanel>
            ) : null}
            <div className="grid min-h-0 flex-1 gap-3 lg:grid-cols-12">
              <div className="flex min-h-0 flex-col gap-3 lg:col-span-7">
                <WorkspacePanel title="报价行编辑" className="min-h-[280px] flex-1">
                  <QuoteLineEditor
                    lines={displayLines}
                    onChange={commitLines}
                    onAdd={readOnly ? undefined : addLine}
                    readOnly={readOnly}
                    marginRate={marginRate}
                  />
                </WorkspacePanel>
                {(activeModule === "formula" || activeModule === "lines") && (
                  <WorkspacePanel title="公式 LIVE" className="shrink-0">
                    <FormulaLivePanel lines={displayLines} marginRate={marginRate} />
                  </WorkspacePanel>
                )}
              </div>
              <div className="lg:col-span-5">
                {(activeModule === "cost" || activeModule === "lines") && (
                  <WorkspacePanel title="成本可视化" className="h-full min-h-[200px]">
                    <CostVisualization lines={displayLines} marginRate={marginRate} />
                  </WorkspacePanel>
                )}
              </div>
            </div>
          </WorkspaceMain>
        }
        dock={
          <WorkspaceDock
            tabs={dockTabs}
            activeTabId={dockTabId}
            onTabChange={setDockTabId}
            collapsed={dockCollapsed}
            onCollapsedChange={setDockCollapsed}
          />
        }
      />
    </div>
  );
}

const WORKFLOW_LABELS: Record<string, string> = {
  draft: "草稿",
  reviewing: "审批中",
  approved: "已批准",
  rejected: "已驳回",
};
