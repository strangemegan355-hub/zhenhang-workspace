"use client";

import { DataGrid } from "@zhenhang/data-grid";
import {
  DEFAULT_EXPORT_TEMPLATES,
  QuoteWorkbench,
  type QuoteLineRow,
} from "@zhenhang/quote-builder";
import {
  useBomItemsQuery,
  useCreateQuoteVersionMutation,
  useExportTemplatesQuery,
  useQuoteApprovalsQuery,
  useQuoteCopilotQuery,
  useQuoteDetailQuery,
  useQuoteDiffQuery,
  useQuoteExportMutation,
  useQuoteExportTaskQuery,
  useQuoteTransitionMutation,
  useQuotesQuery,
  useWorkflowActionsQuery,
} from "@zhenhang/query-hooks";
import { useToastStore } from "@zhenhang/realtime";
import { IndustrialPage, IndustrialPanel, typography } from "@zhenhang/ui";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useMemo, useRef, useState } from "react";

function mapBomDiff(bomDiff: Record<string, unknown> | undefined) {
  if (!bomDiff) return [];
  const added = (bomDiff.added as string[] | undefined) ?? [];
  const removed = (bomDiff.removed as string[] | undefined) ?? [];
  const changed =
    (bomDiff.changed as Array<{ item_code: string; from?: { line_total?: string }; to?: { line_total?: string } }>) ?? [];
  const rows: Array<{ item: string; oldValue: number; newValue: number; changeType: "added" | "removed" | "changed" }> = [];
  added.forEach((code) => rows.push({ item: code, oldValue: 0, newValue: 1, changeType: "added" }));
  removed.forEach((code) => rows.push({ item: code, oldValue: 1, newValue: 0, changeType: "removed" }));
  changed.forEach((c) =>
    rows.push({
      item: c.item_code,
      oldValue: Number(c.from?.line_total ?? 0),
      newValue: Number(c.to?.line_total ?? 0),
      changeType: "changed",
    }),
  );
  return rows;
}

function detailItemsToLines(items: unknown): QuoteLineRow[] {
  return ((items as Record<string, unknown>[]) ?? []).map((i) => ({
    item_code: String(i.item_code ?? ""),
    item_name: String(i.item_name ?? ""),
    unit: String(i.unit ?? "EA"),
    quantity: Number(i.quantity ?? 1),
    unit_price: Number(i.unit_price ?? 0),
    unit_cost: Number(i.unit_cost ?? i.unit_price ?? 0) * 0.7,
  }));
}

export default function QuotesPage() {
  const searchParams = useSearchParams();
  const selectedFromUrl = searchParams.get("selected");
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [fromVersionNo, setFromVersionNo] = useState(1);
  const [toVersionNo, setToVersionNo] = useState(2);
  const [exportTaskId, setExportTaskId] = useState<string | null>(null);
  const [marginRate, setMarginRate] = useState(0.2);
  const [templateId, setTemplateId] = useState(DEFAULT_EXPORT_TEMPLATES[0].id);
  const toastSeq = useRef(0);
  const pushToast = useToastStore((s) => s.push);

  const listQuery = useQuotesQuery({ page });
  const listData = (listQuery.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};
  const rows = useMemo(
    () =>
      (listData.items ?? []).map((item) => ({
        id: String(item.id ?? ""),
        quoteNo: String(item.quote_no ?? ""),
        title: String(item.title ?? ""),
        amount: Number(item.total_amount ?? 0),
        status: String(item.workflow_state ?? ""),
      })),
    [listData.items],
  );

  const activeQuoteId = selectedFromUrl ?? selectedId ?? rows[0]?.id ?? null;
  const detailQuery = useQuoteDetailQuery(activeQuoteId);
  const detail = detailQuery.data as Record<string, unknown> | undefined;
  const bomId = detail?.bom_id ? String(detail.bom_id) : null;
  const bomItemsQuery = useBomItemsQuery(bomId);
  const bomItems = (bomItemsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? [];

  const linesFromDetail = useMemo(() => detailItemsToLines(detail?.items), [detail?.items]);
  const [linesDraft, setLinesDraft] = useState<QuoteLineRow[] | null>(null);
  const lines = linesDraft ?? linesFromDetail;
  const currentVersionNo = Number(
    (detail?.current_version as Record<string, unknown> | undefined)?.version_no ?? 1,
  );

  const workflowState = String(detail?.workflow_state ?? "draft");
  const readOnly = workflowState === "approved";
  const actionsQuery = useWorkflowActionsQuery({ entityType: "quote", currentState: workflowState });
  const approvalsQuery = useQuoteApprovalsQuery(activeQuoteId);
  const diffQuery = useQuoteDiffQuery({
    quoteId: activeQuoteId ?? "",
    fromVersionNo,
    toVersionNo,
  });
  const copilotQuery = useQuoteCopilotQuery({
    quoteId: activeQuoteId ?? "",
    fromVersionNo,
    toVersionNo,
  });
  const templatesQuery = useExportTemplatesQuery();
  const exportTemplates =
    (templatesQuery.data as Array<{ id: string; name: string; format: string; description?: string }> | undefined)?.map(
      (t) => ({
        id: t.id,
        name: t.name,
        format: t.format as "pdf" | "xlsx",
        description: t.description,
      }),
    ) ?? DEFAULT_EXPORT_TEMPLATES;

  const transitionMut = useQuoteTransitionMutation(activeQuoteId ?? "");
  const exportMut = useQuoteExportMutation(activeQuoteId ?? "");
  const saveVersionMut = useCreateQuoteVersionMutation(activeQuoteId ?? "");
  const exportTaskQuery = useQuoteExportTaskQuery(exportTaskId, Boolean(exportTaskId));
  const exportTask = exportTaskQuery.data as Record<string, unknown> | undefined;

  const selectedTemplate = exportTemplates.find((t) => t.id === templateId) ?? exportTemplates[0];
  const diffRows = mapBomDiff((diffQuery.data as { bom_diff?: Record<string, unknown> } | undefined)?.bom_diff);
  const copilot = copilotQuery.data as Record<string, unknown> | undefined;
  const copilotData = copilot
    ? {
        summary: String(copilot.summary ?? ""),
        highlights: (copilot.highlights as string[] | undefined) ?? [],
        riskLevel: (copilot.risk_level as "low" | "medium" | "high") ?? "medium",
        recommendations: (copilot.recommendations as string[] | undefined) ?? [],
        riskAnalysis: (copilot.risk_analysis as string[] | undefined) ?? [],
        bomCostAnomalies: (copilot.bom_cost_anomalies as string[] | undefined) ?? [],
        profitSuggestions: (copilot.profit_suggestions as string[] | undefined) ?? [],
        approvalSuggestions: (copilot.approval_suggestions as string[] | undefined) ?? [],
        similarQuotes: (copilot.similar_quotes as Array<Record<string, unknown>> | undefined)?.map((q) => ({
          quote_no: String(q.quote_no ?? ""),
          title: String(q.title ?? ""),
          total_amount: String(q.total_amount ?? ""),
          workflow_state: String(q.workflow_state ?? ""),
        })),
        similarProjects: (copilot.similar_projects as Array<Record<string, unknown>> | undefined)?.map((q) => ({
          quote_no: String(q.quote_no ?? ""),
          title: String(q.title ?? ""),
          total_amount: String(q.total_amount ?? ""),
          workflow_state: String(q.workflow_state ?? ""),
        })),
        deliveryRisks: (copilot.delivery_risks as string[] | undefined) ?? [],
        bomRisks: (copilot.bom_risks as string[] | undefined) ?? [],
        customerInsights: (copilot.customer_insights as Record<string, unknown>) ?? {},
        loading: copilotQuery.isFetching,
        onRefresh: () => copilotQuery.refetch(),
      }
    : undefined;
  const approvalRecords = (approvalsQuery.data ?? []).map((a) => {
    const rec = a as Record<string, unknown>;
    return {
      actor: String(rec.approver_id ?? "—").slice(0, 8),
      action: String(rec.action ?? ""),
      at: String(rec.acted_at ?? rec.created_at ?? ""),
      comment: rec.comment ? String(rec.comment) : undefined,
    };
  });

  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const nextToastId = (prefix: string) => {
    toastSeq.current += 1;
    return `${prefix}-${toastSeq.current}`;
  };

  const handleTransition = async (actionCode: string, comment?: string) => {
    if (!activeQuoteId) return;
    try {
      await transitionMut.mutateAsync({ action_code: actionCode, comment });
      pushToast({ id: nextToastId("wf"), title: "状态已更新", description: actionCode });
    } catch (e) {
      pushToast({
        id: nextToastId("wf-err"),
        title: "操作失败",
        description: e instanceof Error ? e.message : "Transition failed",
      });
    }
  };

  const handleExport = async () => {
    if (!activeQuoteId || !selectedTemplate) return;
    try {
      const task = (await exportMut.mutateAsync({
        format: selectedTemplate.format,
        template_id: selectedTemplate.id,
      })) as Record<string, unknown>;
      setExportTaskId(String(task.id ?? ""));
      pushToast({ id: nextToastId("exp"), title: "导出已提交", description: selectedTemplate.name });
    } catch (e) {
      pushToast({
        id: nextToastId("exp-err"),
        title: "导出失败",
        description: e instanceof Error ? e.message : "Export failed",
      });
    }
  };

  const handleSaveVersion = async () => {
    if (!activeQuoteId || !lines.length) return;
    try {
      await saveVersionMut.mutateAsync(
        lines.map((l) => ({
          item_code: l.item_code,
          item_name: l.item_name,
          unit: l.unit,
          quantity: l.quantity,
          unit_price: l.unit_price,
          source_type: "manual",
        })),
      );
      pushToast({ id: nextToastId("ver"), title: "版本已保存", description: `${lines.length} 行` });
      detailQuery.refetch();
      setToVersionNo((v) => v + 1);
    } catch (e) {
      pushToast({
        id: nextToastId("ver-err"),
        title: "保存失败",
        description: e instanceof Error ? e.message : "Save failed",
      });
    }
  };

  const importBomToLines = () => {
    const imported: QuoteLineRow[] = bomItems.map((i) => ({
      item_code: String(i.item_code ?? ""),
      item_name: String(i.item_name ?? ""),
      unit: String(i.unit ?? "EA"),
      quantity: Number(i.quantity ?? 1),
      unit_price: Number(i.unit_cost ?? 0) * 1.3,
      unit_cost: Number(i.unit_cost ?? 0),
    }));
    setLinesDraft(imported.length ? imported : lines);
    pushToast({ id: nextToastId("bom"), title: "BOM 已导入", description: `${imported.length} 行` });
  };

  const bomItemsRaw = bomItems.map((i) => ({
    id: String(i.id ?? i.item_code),
    item_code: String(i.item_code ?? ""),
    item_name: String(i.item_name ?? ""),
    quantity: Number(i.quantity ?? 0),
    unit_cost: Number(i.unit_cost ?? 0),
    line_total: Number(i.line_total ?? 0),
  }));

  return (
    <IndustrialPage gap="md">
      <IndustrialPanel
        title="报价中心"
        toolbar={
          <>
            <span className={typography.caption}>选择报价单进入工业工作台</span>
            <Link
              href="/quotes/new"
              className="inline-flex h-8 items-center rounded border border-blue-700 bg-blue-600 px-3 text-xs font-medium text-white hover:bg-blue-700"
            >
              新建报价
            </Link>
          </>
        }
        loading={listQuery.isLoading}
        contentClassName="!p-0"
      >
        <div className="p-4">
          <DataGrid
            columns={[
              { key: "quoteNo", title: "报价单号", canView: true, fixed: "left", width: 160 },
              { key: "title", title: "标题", canView: true },
              { key: "amount", title: "金额", canView: true },
              { key: "status", title: "状态", canView: true },
            ]}
            rows={rows}
            rowKey={(row) => String(row.id)}
            page={page}
            total={listData.total ?? rows.length}
            onPageChange={setPage}
            persistenceKey="quote-grid-v3"
            onRowClick={(row) => {
              setSelectedId(String(row.id));
              setLinesDraft(null);
            }}
          />
        </div>
      </IndustrialPanel>

      {activeQuoteId ? (
        <QuoteWorkbench
          key={`wb-${activeQuoteId}-v${currentVersionNo}`}
          panelLoading={detailQuery.isLoading && !detail}
          errorMessage={detailQuery.isError ? "加载报价详情失败，请重试" : undefined}
          onErrorRetry={() => detailQuery.refetch()}
          bomLoading={Boolean(bomId) && bomItemsQuery.isLoading}
          quoteNo={String(detail?.quote_no ?? "")}
            title={String(detail?.title ?? "工业报价工作台")}
            workflowState={workflowState}
            readOnly={readOnly}
            lines={lines}
            onLinesChange={setLinesDraft}
            marginRate={marginRate}
            onMarginRateChange={setMarginRate}
            bomItemsRaw={bomItemsRaw}
            onImportBom={bomId ? importBomToLines : undefined}
            workflowActions={actionsQuery.data ?? []}
            approvalRecords={approvalRecords}
            onTransition={handleTransition}
            transitionPending={transitionMut.isPending}
            exportTemplates={exportTemplates}
            selectedTemplateId={templateId}
            onTemplateSelect={setTemplateId}
            onExport={handleExport}
            exporting={exportMut.isPending}
            exportStatus={exportTask?.status ? String(exportTask.status) : undefined}
            onDownloadExport={
              exportTask?.status === "completed" && exportTask.file_id
                ? () => window.open(`${apiBase}/api/v1/files/${exportTask.file_id}/preview`, "_blank")
                : undefined
            }
            diffFromVersion={fromVersionNo}
            diffToVersion={toVersionNo}
            onDiffVersionChange={(from, to) => {
              setFromVersionNo(from);
              setToVersionNo(to);
            }}
            diffRows={diffRows}
            onSaveVersion={readOnly ? undefined : handleSaveVersion}
            savingVersion={saveVersionMut.isPending}
            copilotData={copilotData}
            showDemoGuide={process.env.NODE_ENV === "development"}
          />
      ) : (
        <p className="text-center text-sm text-zinc-500">请先创建或选择一条报价记录</p>
      )}
    </IndustrialPage>
  );
}
