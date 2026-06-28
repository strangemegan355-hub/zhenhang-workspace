"use client";

import {
  DEFAULT_EXPORT_TEMPLATES,
  QuoteLineEditor,
  type QuoteLineRow,
} from "@zhenhang/quote-builder";
import {
  useApprovalTemplatesQuery,
  useBomItemsQuery,
  useBomsListQuery,
  useCreateQuoteVersionMutation,
  useCreateQuoteWizardMutation,
  useCustomersQuery,
  useExportTemplatesQuery,
  useMachinesQuery,
  useProductCostTemplatesQuery,
  useProductPriceTemplatesQuery,
  useProductsQuery,
  useQuoteApprovalsQuery,
  useQuoteDetailQuery,
  useQuoteExportMutation,
  useQuoteExportTaskQuery,
  useQuoteTransitionMutation,
  useQuotesQuery,
  useWorkflowActionsQuery,
} from "@zhenhang/query-hooks";
import { useToastStore } from "@zhenhang/realtime";
import { EmptyState, IndustrialPage, StatusBadge, typography, workflowStateToStatus } from "@zhenhang/ui";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useMemo, useRef, useState } from "react";
import {
  QuoteProductPanel,
  mapBomItemsToNodes,
  type CreateQuoteForm,
  type MasterOption,
} from "@/components/quotes/quote-product-panel";
import { QuoteProfitPanel } from "@/components/quotes/quote-profit-panel";
import QuoteItemOptionsPanel from "@/components/quotes/quote-item-options-panel";
import { useAuthStore } from "@/store/auth-store";
import { apiClient } from "@zhenhang/http-client";

const STATUS_LABEL: Record<string, string> = {
  draft: "草稿",
  reviewing: "审批中",
  approved: "已批准",
  rejected: "已驳回",
};

const DEFAULT_CREATE_FORM: CreateQuoteForm = {
  title: "",
  customerId: "",
  productId: "",
  costTemplateId: "",
  priceTemplateId: "",
  machineId: "",
  bomId: "",
  approvalTemplateId: "",
  currency: "CNY",
  remark: "",
  seedFromProduct: true,
  seedFromBom: false,
};

function mapOptions(items: Record<string, unknown>[] | undefined, labelKeys: string[]): MasterOption[] {
  return (items ?? []).map((row) => {
    const label = labelKeys.map((k) => row[k]).filter(Boolean).join(" · ") || String(row.id ?? "");
    return {
      id: String(row.id ?? ""),
      label,
      sub: row.machine_id ? String(row.machine_id) : undefined,
    };
  });
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
  return (
    <Suspense fallback={null}>
      <QuotesPageContent />
    </Suspense>
  );
}

function QuotesPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const selectedFromUrl = searchParams.get("selected");
  const createFromUrl = searchParams.get("create") === "1";

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [createMode, setCreateMode] = useState(createFromUrl);
  const [createForm, setCreateForm] = useState<CreateQuoteForm>(DEFAULT_CREATE_FORM);
  const [createError, setCreateError] = useState<string | undefined>();
  const [exportTaskId, setExportTaskId] = useState<string | null>(null);
  const [exportTaskSnapshot, setExportTaskSnapshot] = useState<Record<string, unknown> | null>(null);
  const [exportNotice, setExportNotice] = useState<{
    message?: string | null;
    error?: string | null;
    fileName?: string | null;
  } | null>(null);
  const [marginRate, setMarginRate] = useState(0.2);
  const [templateId, setTemplateId] = useState(DEFAULT_EXPORT_TEMPLATES[0].id);
  const toastSeq = useRef(0);
  const pushToast = useToastStore((s) => s.push);
  const token = useAuthStore((s) => s.token?.accessToken);

  const listQuery = useQuotesQuery({ page: 1 });
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

  const activeQuoteId = createMode ? null : (selectedFromUrl ?? selectedId ?? rows[0]?.id ?? null);
  const detailQuery = useQuoteDetailQuery(activeQuoteId);
  const detail = detailQuery.data as Record<string, unknown> | undefined;
  const bomId = detail?.bom_id ? String(detail.bom_id) : null;
  const productId = detail?.product_id ? String(detail.product_id) : null;
  const quoteCostTemplateId = detail?.cost_template_id ? String(detail.cost_template_id) : undefined;
  const quotePriceTemplateId = detail?.price_template_id ? String(detail.price_template_id) : undefined;
  const bomItemsQuery = useBomItemsQuery(bomId);
  const bomItems = (bomItemsQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? [];

  const linesFromDetail = useMemo(() => detailItemsToLines(detail?.items), [detail?.items]);
  const [linesDraft, setLinesDraft] = useState<QuoteLineRow[] | null>(null);
  const lines = linesDraft ?? linesFromDetail;

  const detailItemsWithIds = useMemo(
    () =>
      ((detail?.items as Record<string, unknown>[]) ?? []).map((i) => ({
        id: String(i.id ?? ""),
        item_name: String(i.item_name ?? ""),
        unit_price: Number(i.unit_price ?? 0),
        selected_options: (i.selected_options as string[]) ?? [],
        machine_id: i.machine_id ? String(i.machine_id) : undefined,
      })),
    [detail?.items],
  );

  const workflowState = String(detail?.workflow_state ?? "draft");
  const readOnly = workflowState === "approved";
  const effectiveTemplateId =
    templateId !== DEFAULT_EXPORT_TEMPLATES[0].id
      ? templateId
      : workflowState === "approved"
        ? "company-branded-xlsx"
        : templateId;

  const customersQuery = useCustomersQuery();
  const productsQuery = useProductsQuery(1);
  const costTemplatesQuery = useProductCostTemplatesQuery(1);
  const priceTemplatesQuery = useProductPriceTemplatesQuery(1);
  const machinesQuery = useMachinesQuery();
  const bomsQuery = useBomsListQuery();
  const approvalTemplatesQuery = useApprovalTemplatesQuery();
  const wizardMut = useCreateQuoteWizardMutation();

  const customers = useMemo(
    () => mapOptions((customersQuery.data as { items?: Record<string, unknown>[] })?.items, ["code", "name"]),
    [customersQuery.data],
  );
  const products = useMemo(
    () => mapOptions((productsQuery.data as { items?: Record<string, unknown>[] })?.items, ["code", "name"]),
    [productsQuery.data],
  );
  const costTemplates = useMemo(
    () =>
      ((costTemplatesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((t) => ({
        id: String(t.id ?? ""),
        label: `${String(t.code ?? "")} · ${String(t.name ?? "")}`,
        sub: t.product_id ? String(t.product_id) : undefined,
      })),
    [costTemplatesQuery.data],
  );
  const priceTemplates = useMemo(
    () =>
      ((priceTemplatesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((t) => ({
        id: String(t.id ?? ""),
        label: `${String(t.code ?? "")} · ${String(t.name ?? "")}`,
        sub: t.product_id ? String(t.product_id) : undefined,
      })),
    [priceTemplatesQuery.data],
  );
  const productName = useMemo(() => {
    if (!productId) return undefined;
    const hit = products.find((p) => p.id === productId);
    return hit?.label;
  }, [productId, products]);
  const machines = useMemo(
    () => mapOptions((machinesQuery.data as { items?: Record<string, unknown>[] })?.items, ["machine_code", "name"]),
    [machinesQuery.data],
  );
  const boms = useMemo(
    () =>
      mapOptions((bomsQuery.data as { items?: Record<string, unknown>[] })?.items, ["version", "status"]).map((b, i) => {
        const raw = (bomsQuery.data as { items?: Record<string, unknown>[] })?.items?.[i];
        return {
          ...b,
          label: `BOM ${raw?.version ?? b.id} · ${raw?.status ?? ""}`,
          sub: raw?.machine_id ? String(raw.machine_id) : undefined,
        };
      }),
    [bomsQuery.data],
  );
  const approvalTemplates = useMemo(
    () => mapOptions((approvalTemplatesQuery.data as { items?: Record<string, unknown>[] })?.items, ["code", "name"]),
    [approvalTemplatesQuery.data],
  );

  const actionsQuery = useWorkflowActionsQuery({ entityType: "quote", currentState: workflowState });
  const approvalsQuery = useQuoteApprovalsQuery(activeQuoteId);
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
  const exportTask = (exportTaskQuery.data ?? exportTaskSnapshot) as Record<string, unknown> | undefined;
  const exportCompletedRef = useRef<string | null>(null);
  const selectedTemplate = exportTemplates.find((t) => t.id === effectiveTemplateId) ?? exportTemplates[0];
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  const polledExportMessage = useMemo(() => {
    if (!exportTask?.id) return null;
    const status = String(exportTask.status ?? "");
    if (status === "pending") return "正在生成导出文件，请稍候…";
    if (status === "completed") return "导出已完成，请点击「下载文件」保存到电脑（浏览器默认下载目录）";
    return null;
  }, [exportTask]);

  const polledExportError = useMemo(() => {
    if (!exportTask?.id || String(exportTask.status ?? "") !== "failed") return null;
    return String(exportTask.error_message ?? "导出失败，请重试");
  }, [exportTask]);

  const polledExportFileName = useMemo(() => {
    if (!exportTask?.id || String(exportTask.status ?? "") !== "completed") return null;
    const quoteNo = String(detail?.quote_no ?? "quote");
    const ext = selectedTemplate?.format === "pdf" ? "pdf" : "xlsx";
    return `${quoteNo}.${ext}`;
  }, [exportTask, detail?.quote_no, selectedTemplate?.format]);

  const nextToastId = (prefix: string) => {
    toastSeq.current += 1;
    return `${prefix}-${toastSeq.current}`;
  };

  const exportMessage = exportNotice?.message ?? polledExportMessage;
  const exportError = exportNotice?.error ?? polledExportError;
  const exportFileName = exportNotice?.fileName ?? polledExportFileName;

  const approvalRecords = (approvalsQuery.data ?? []).map((a) => {
    const rec = a as Record<string, unknown>;
    return {
      actor: String(rec.approver_id ?? "—").slice(0, 8),
      action: String(rec.action ?? ""),
      at: String(rec.acted_at ?? rec.created_at ?? ""),
      comment: rec.comment ? String(rec.comment) : undefined,
    };
  });

  const bomItemsRaw = bomItems.map((i) => ({
    id: String(i.id ?? i.item_code),
    item_code: String(i.item_code ?? ""),
    item_name: String(i.item_name ?? ""),
    quantity: Number(i.quantity ?? 0),
    unit_cost: Number(i.unit_cost ?? 0),
    line_total: Number(i.line_total ?? 0),
  }));
  const bomNodes = mapBomItemsToNodes(bomItemsRaw);

  const selectQuote = (id: string) => {
    setSelectedId(id);
    setLinesDraft(null);
    setCreateMode(false);
    router.replace(`/quotes?selected=${id}`, { scroll: false });
  };

  const openCreateMode = (open: boolean) => {
    setCreateMode(open);
    setCreateError(undefined);
    if (open) {
      router.replace("/quotes?create=1", { scroll: false });
    } else if (activeQuoteId) {
      router.replace(`/quotes?selected=${activeQuoteId}`, { scroll: false });
    } else {
      router.replace("/quotes", { scroll: false });
    }
  };

  const handleCreateSubmit = async () => {
    setCreateError(undefined);
    try {
      const body: Record<string, unknown> = {
        title: createForm.title.trim(),
        customer_id: createForm.customerId,
        currency: createForm.currency,
        remark: createForm.remark || null,
        seed_from_product: createForm.seedFromProduct,
      };
      if (createForm.productId) body.product_id = createForm.productId;
      if (createForm.machineId) body.machine_id = createForm.machineId;
      if (createForm.costTemplateId) body.cost_template_id = createForm.costTemplateId;
      if (createForm.priceTemplateId) body.price_template_id = createForm.priceTemplateId;
      if (createForm.bomId && createForm.seedFromBom) body.bom_id = createForm.bomId;
      if (createForm.approvalTemplateId) body.approval_template_id = createForm.approvalTemplateId;

      const created = await wizardMut.mutateAsync(body);
      const id = String((created as Record<string, unknown>).id ?? "");
      setCreateForm(DEFAULT_CREATE_FORM);
      setCreateMode(false);
      listQuery.refetch();
      if (id) selectQuote(id);
      pushToast({ id: nextToastId("create"), title: "报价已创建", description: createForm.title });
    } catch (e) {
      setCreateError(e instanceof Error ? e.message : "创建失败");
    }
  };

  const handleDownloadExport = async () => {
    if (!exportTask?.file_id || !token) return;
    try {
      const resp = await fetch(`${apiBase}/api/v1/files/${exportTask.file_id}/download`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const blob = await resp.blob();
      const disposition = resp.headers.get("content-disposition") ?? "";
      const utfMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i);
      const plainMatch = disposition.match(/filename="([^"]+)"/i);
      const filename = decodeURIComponent(utfMatch?.[1] ?? plainMatch?.[1] ?? exportFileName ?? "quote-export.xlsx");
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      anchor.click();
      URL.revokeObjectURL(url);
      setExportNotice({
        fileName: filename,
        message: `文件已下载：${filename}（保存在浏览器默认下载目录）`,
        error: null,
      });
    } catch (e) {
      setExportNotice({ error: e instanceof Error ? e.message : "下载失败" });
    }
  };

  const handleExport = async () => {
    if (!activeQuoteId || !selectedTemplate) return;
    setExportNotice(null);
    exportCompletedRef.current = null;
    try {
      const task = (await exportMut.mutateAsync({
        format: selectedTemplate.format,
        template_id: selectedTemplate.id,
      })) as Record<string, unknown>;
      setExportTaskId(String(task.id ?? ""));
      setExportTaskSnapshot(task);
      setExportNotice({
        message:
          task.status === "completed"
            ? "导出已完成，请点击「下载文件」保存到电脑（浏览器默认下载目录）"
            : "正在生成导出文件，请稍候…",
        error: null,
        fileName: null,
      });
      void exportTaskQuery.refetch();
    } catch (e) {
      setExportNotice({ error: e instanceof Error ? e.message : "导出失败" });
    }
  };

  const handleTransition = async (actionCode: string, comment?: string) => {
    if (!activeQuoteId) return;
    try {
      await transitionMut.mutateAsync({ action_code: actionCode, comment });
      pushToast({ id: nextToastId("wf"), title: "状态已更新", description: actionCode });
      detailQuery.refetch();
      listQuery.refetch();
    } catch (e) {
      pushToast({
        id: nextToastId("wf-err"),
        title: "操作失败",
        description: e instanceof Error ? e.message : "Transition failed",
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
      setLinesDraft(null);
    } catch (e) {
      pushToast({
        id: nextToastId("ver-err"),
        title: "保存失败",
        description: e instanceof Error ? e.message : "Save failed",
      });
    }
  };

  const importProductToLines = async () => {
    if (!productId) return;
    try {
      const { data } = await apiClient.get<{ data: Record<string, unknown> }>(
        `/api/v1/products/${productId}/quote-payload`,
        {
          params: {
            cost_template_id: quoteCostTemplateId,
            price_template_id: quotePriceTemplateId,
          },
        },
      );
      const payload = data.data;
      const payloadLines = (payload.lines as Record<string, unknown>[]) ?? [];
      const imported: QuoteLineRow[] = payloadLines.map((line) => ({
        item_code: String(line.item_code ?? ""),
        item_name: String(line.item_name ?? ""),
        unit: String(line.unit ?? "EA"),
        quantity: Number(line.quantity ?? 1),
        unit_price: Number(line.unit_price ?? 0),
        unit_cost: Number(line.unit_cost ?? 0),
      }));
      if (payload.margin_rate) setMarginRate(Number(payload.margin_rate));
      setLinesDraft(imported.length ? imported : lines);
      pushToast({ id: nextToastId("product"), title: "产品模板已导入", description: `${imported.length} 行` });
    } catch (e) {
      pushToast({
        id: nextToastId("product-err"),
        title: "导入失败",
        description: e instanceof Error ? e.message : "无法加载产品报价数据",
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

  const workflowActions = actionsQuery.data ?? [];
  const centerWorkflowActions = workflowState === "reviewing" ? [] : workflowActions;
  const masterLoading =
    customersQuery.isLoading || machinesQuery.isLoading || productsQuery.isLoading;

  return (
    <IndustrialPage fill className="!gap-0 !p-0">
      <div className="flex h-full min-h-0 flex-col">
        <header className="shrink-0 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5">
          <h1 className={`${typography.pageTitle} text-base`}>报价中心</h1>
          <p className="text-[11px] text-[var(--color-text-muted)]">左选产品 · 中编明细 · 右看成本利润，单页完成全部操作</p>
        </header>

        <div className="grid min-h-0 flex-1 grid-cols-[280px_minmax(0,1fr)_300px]">
          <QuoteProductPanel
            quotes={rows}
            activeQuoteId={activeQuoteId}
            onSelectQuote={selectQuote}
            createMode={createMode}
            onCreateModeChange={openCreateMode}
            createForm={createForm}
            onCreateFormChange={setCreateForm}
            onCreateSubmit={handleCreateSubmit}
            creating={wizardMut.isPending}
            createError={createError}
            customers={customers}
            products={products}
            costTemplates={costTemplates}
            priceTemplates={priceTemplates}
            machines={machines}
            boms={boms}
            approvalTemplates={approvalTemplates}
            bomNodes={bomNodes}
            bomLoading={Boolean(bomId) && bomItemsQuery.isLoading}
            quoteNo={detail?.quote_no ? String(detail.quote_no) : undefined}
            productName={productName}
            onImportBom={bomId ? importBomToLines : undefined}
            onImportProduct={productId && !readOnly ? () => void importProductToLines() : undefined}
            readOnly={readOnly}
            loading={listQuery.isLoading || masterLoading}
          />

          <main className="flex min-h-0 min-w-0 flex-col bg-[var(--color-surface)]">
            {createMode ? (
              <div className="flex flex-1 items-center justify-center p-6">
                <EmptyState message="填写左侧产品信息并创建报价" hint="创建后在此编辑报价明细行" />
              </div>
            ) : activeQuoteId ? (
              <>
                <div className="flex shrink-0 flex-wrap items-center gap-2 border-b border-[var(--color-border)] px-4 py-2.5">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-sm font-semibold text-[#0f1a2e] dark:text-[#f1f5f9]">
                        {String(detail?.quote_no ?? "—")}
                      </span>
                      <StatusBadge
                        status={workflowStateToStatus(workflowState)}
                        label={STATUS_LABEL[workflowState] ?? workflowState}
                        compact
                      />
                    </div>
                    <p className="truncate text-xs text-[#8896a8]">{String(detail?.title ?? "")}</p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {!readOnly ? (
                      <button
                        type="button"
                        disabled={saveVersionMut.isPending || !lines.length}
                        onClick={handleSaveVersion}
                        className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                      >
                        {saveVersionMut.isPending ? "保存中…" : "保存版本"}
                      </button>
                    ) : null}
                    {centerWorkflowActions.map((a) => (
                      <button
                        key={a.action_code}
                        type="button"
                        disabled={transitionMut.isPending}
                        onClick={() => handleTransition(a.action_code)}
                        className={`rounded-lg px-3 py-1.5 text-xs font-medium disabled:opacity-50 ${
                          a.action_code === "reject"
                            ? "border border-red-200 text-red-600 hover:bg-red-50"
                            : a.action_code === "approve"
                              ? "bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)]"
                              : "border border-[var(--color-border)] text-[var(--color-text)] hover:bg-[var(--color-surface-soft)]"
                        }`}
                      >
                        {a.action_name}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="min-h-0 flex-1 overflow-auto p-3">
                  {detailQuery.isLoading && !detail ? (
                    <p className="text-xs text-[#8896a8]">加载报价明细…</p>
                  ) : detailQuery.isError ? (
                    <div className="space-y-2 text-center">
                      <EmptyState message="加载报价详情失败" hint="请重试或选择其他报价单" />
                      <button
                        type="button"
                        onClick={() => detailQuery.refetch()}
                        className="text-xs text-[var(--color-text)] underline-offset-2 hover:underline"
                      >
                        重试
                      </button>
                    </div>
                  ) : (
                    <QuoteLineEditor
                      lines={lines}
                      onChange={setLinesDraft}
                      readOnly={readOnly}
                      marginRate={marginRate}
                      onAdd={
                        readOnly
                          ? undefined
                          : () =>
                              setLinesDraft([
                                ...lines,
                                {
                                  item_code: "",
                                  item_name: "",
                                  unit: "EA",
                                  quantity: 1,
                                  unit_price: 0,
                                  unit_cost: 0,
                                },
                              ])
                      }
                    />
                  )}
                </div>
              </>
            ) : (
              <div className="flex flex-1 items-center justify-center p-6">
                <EmptyState message="请选择报价单" hint="在左侧列表选择，或点击「新建」创建" />
              </div>
            )}
          </main>

          <div className="flex min-h-0 flex-col gap-2 overflow-auto border-l border-[var(--color-border)] bg-[var(--color-surface)] p-2">
            {activeQuoteId && detailItemsWithIds.length > 0 && !createMode ? (
              <QuoteItemOptionsPanel
                quoteId={activeQuoteId}
                items={detailItemsWithIds}
                onOptionsUpdated={() => detailQuery.refetch()}
              />
            ) : null}
            <QuoteProfitPanel
            lines={createMode || !activeQuoteId ? [] : lines}
            marginRate={marginRate}
            onMarginRateChange={setMarginRate}
            workflowState={createMode ? "draft" : workflowState}
            workflowActions={workflowActions}
            approvalRecords={approvalRecords}
            onTransition={handleTransition}
            transitionPending={transitionMut.isPending}
            exportTemplates={exportTemplates}
            selectedTemplateId={effectiveTemplateId}
            onTemplateSelect={setTemplateId}
            onExport={handleExport}
            exporting={exportMut.isPending}
            exportStatus={exportTask?.status ? String(exportTask.status) : undefined}
            exportFileName={exportFileName ?? undefined}
            exportMessage={exportMessage}
            exportError={exportError}
            onDownloadExport={
              exportTask?.status === "completed" && exportTask.file_id ? handleDownloadExport : undefined
            }
            readOnly={readOnly || createMode || !activeQuoteId}
          />
          </div>
        </div>
      </div>
    </IndustrialPage>
  );
}
