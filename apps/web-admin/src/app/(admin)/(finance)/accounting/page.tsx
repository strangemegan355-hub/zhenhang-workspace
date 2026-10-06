"use client";

import {
  useAccountingEntriesQuery,
  useAccountingEntryQuery,
  useAccountingStatusQuery,
  useConfirmAccountingEntryMutation,
  useCreateBackfillEntryMutation,
  useCustomersQuery,
  useExportAccountingEntriesMutation,
  useSuppliersQuery,
  useUpdateAccountingEntryMutation,
  useVoidAccountingEntryMutation,
} from "@zhenhang/query-hooks";
import {
  IndustrialPage,
  IndustrialPanel,
  PageHeader,
  WorkspaceToolbarButton,
} from "@zhenhang/ui";
import { apiErrorMessage } from "@/lib/api-error";
import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import {
  dangerActionClass,
  fieldInputClass,
  fieldLabelClass,
  formPanelClass,
  linkActionClass,
  tableBodyRowClass,
  tableHeaderRowClass,
} from "@/lib/form-styles";
import { hasPermission } from "@/lib/access";
import { useAuthStore } from "@/store/auth-store";

function toLedgerRow(row: Record<string, unknown>) {
  return {
    id: String(row.id ?? ""),
    entryNo: String(row.entry_no ?? ""),
    entryKind: String(row.entry_kind ?? ""),
    status: String(row.status ?? ""),
    customerId: String(row.customer_id ?? ""),
    amount: money(row.amount as number | string),
    occurredOn: String(row.occurred_on ?? ""),
    bookedOn: String(row.booked_on ?? ""),
    isBackfill: Boolean(row.is_backfill),
    title: String(row.title ?? ""),
  };
}

const ENTRY_KIND_OPTIONS = [
  { value: "receivable", label: "应收", hint: "客户欠款 / 发票已开待收款" },
  { value: "payable", label: "应付", hint: "欠供应商款 / 收到发票待付款" },
  { value: "receipt", label: "收款", hint: "实际收到客户的款项" },
  { value: "payment", label: "付款", hint: "实际支付给供应商的款项" },
  { value: "revenue", label: "收入", hint: "非主营业务收入（利息、退款等）" },
  { value: "expense", label: "支出", hint: "日常费用支出（办公用品、差旅等）" },
];

const STATUS_LABEL: Record<string, string> = {
  draft: "草稿",
  confirmed: "已确认",
  partial_settled: "部分核销",
  settled: "已结清",
  void: "已作废",
};

const KIND_LABEL = Object.fromEntries(ENTRY_KIND_OPTIONS.map((o) => [o.value, o.label]));

function money(n: number | string | undefined) {
  return Number(n ?? 0).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function todayInputValue() {
  return new Date().toISOString().slice(0, 10);
}

const defaultForm = {
  entry_kind: "receivable",
  customer_id: "",
  supplier_id: "",
  amount: "",
  occurred_on: todayInputValue(),
  due_date: "",
  title: "",
  remark: "",
};

export default function AccountingPage() {
  const user = useAuthStore((s) => s.user);
  const perms = user?.permissions ?? [];
  const canBackfill = hasPermission(perms, "business:accounting:backfill");
  const canConfirm = hasPermission(perms, "business:accounting:confirm");

  const statusQuery = useAccountingStatusQuery();
  const enabled = statusQuery.data?.flags.accounting_enabled ?? false;

  const [page, setPage] = useState(1);
  const [customerFilter, setCustomerFilter] = useState("");
  const [supplierFilter, setSupplierFilter] = useState("");
  const [kindFilter, setKindFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [showVoid, setShowVoid] = useState(false);
  const [showBackfill, setShowBackfill] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [formError, setFormError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [detailId, setDetailId] = useState<string | null>(null);

  // The detail is a query keyed by id, so the panel reads from cache and an edit refreshes it by
  // invalidation rather than by a hand-rolled fetch with its own loading flag.
  const detailQuery = useAccountingEntryQuery(detailId ?? undefined);
  const detail = detailQuery.data ?? null;
  const detailLoading = detailQuery.isFetching;

  const openDetail = (id: string) => {
    setDetailId((current) => (current === id ? null : id));
  };

  const startEdit = (row: typeof rows[0]) => {
    setEditingId(row.id);
    setForm({
      entry_kind: row.entryKind,
      customer_id: row.customerId,
      supplier_id: "",
      amount: String(Number(row.amount.replace(/,/g, "")) || 0),
      occurred_on: row.occurredOn,
      due_date: "",
      title: row.title,
      remark: "",
    });
    setShowBackfill(true);
    setFormError(null);
  };

  const handleEdit = async () => {
    setFormError(null);
    if (!editingId) return;
    if (!form.title.trim()) { setFormError("请填写摘要"); return; }
    try {
      const body: Record<string, unknown> = {
        customer_id: form.customer_id || null,
        supplier_id: form.supplier_id || null,
        amount: Number(form.amount),
        occurred_on: form.occurred_on,
        due_date: form.due_date || null,
        title: form.title.trim(),
        remark: form.remark.trim() || null,
      };
      await updateMutation.mutateAsync({ entryId: editingId, payload: body });
      setForm(defaultForm);
      setEditingId(null);
      setShowBackfill(false);
      // No manual refetch: the mutation invalidates the list and the detail. Calling openDetail here
      // used to toggle the panel closed whenever the edited row was the one being viewed.
    } catch (err) {
      setFormError(apiErrorMessage(err, "编辑失败"));
    }
  };

  const entriesQuery = useAccountingEntriesQuery(
    page,
    {
      customerId: customerFilter || undefined,
      supplierId: supplierFilter || undefined,
      entryKind: kindFilter || undefined,
      includeVoid: showVoid,
      dateFrom: dateFrom || undefined,
      dateTo: dateTo || undefined,
    },
    enabled,
  );
  const customersQuery = useCustomersQuery(1);
  const suppliersQuery = useSuppliersQuery(1);
  const backfillMutation = useCreateBackfillEntryMutation();
  const confirmMutation = useConfirmAccountingEntryMutation();
  const voidMutation = useVoidAccountingEntryMutation();
  const updateMutation = useUpdateAccountingEntryMutation();
  const exportMutation = useExportAccountingEntriesMutation();

  const customerOptions = useMemo(
    () =>
      ((customersQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((c) => ({
        value: String(c.id ?? ""),
        label: String(c.name ?? ""),
      })),
    [customersQuery.data],
  );

  const supplierOptions = useMemo(
    () =>
      ((suppliersQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((s) => ({
        value: String(s.id ?? ""),
        label: String(s.name ?? ""),
      })),
    [suppliersQuery.data],
  );

  const customerNameMap = useMemo(
    () => new Map(customerOptions.map((c) => [c.value, c.label])),
    [customerOptions],
  );

  // A page of ledger rows is cheap to map, and the compiler reported this memo as a conflict it
  // could not preserve while skipping the component. The indirection bought nothing, so it is gone.
  const entryItems =
    (entriesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? [];
  const rows = entryItems.map(toLedgerRow);

  const total = (entriesQuery.data as { total?: number } | undefined)?.total ?? rows.length;
  const needsCustomer = ["receivable", "receipt", "revenue"].includes(form.entry_kind);
  const needsSupplier = ["payable", "payment", "expense"].includes(form.entry_kind);

  const handleBackfill = async () => {
    setFormError(null);
    if (!form.title.trim()) {
      setFormError("请填写摘要");
      return;
    }
    if (!form.amount || Number(form.amount) <= 0) {
      setFormError("请填写有效金额");
      return;
    }
    if (needsCustomer && !form.customer_id) {
      setFormError("请选择客户");
      return;
    }
    if (needsSupplier && !form.supplier_id) {
      setFormError("请选择供应商");
      return;
    }
    try {
      await backfillMutation.mutateAsync({
        entry_kind: form.entry_kind,
        customer_id: form.customer_id || undefined,
        supplier_id: form.supplier_id || undefined,
        amount: Number(form.amount),
        occurred_on: form.occurred_on,
        due_date: form.due_date || undefined,
        title: form.title.trim(),
        remark: form.remark.trim() || undefined,
      });
      setForm(defaultForm);
      setShowBackfill(false);
      void entriesQuery.refetch();
      void statusQuery.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "补录失败");
    }
  };

  const handleExport = useCallback(async () => {
    try {
      const data = await exportMutation.mutateAsync({
        customerId: customerFilter,
        supplierId: supplierFilter,
        entryKind: kindFilter,
        dateFrom,
        dateTo,
      });
      const blob = new Blob([data as BlobPart], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `accounting_entries_${todayInputValue()}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Export failed", e);
    }
  }, [customerFilter, supplierFilter, kindFilter, dateFrom, dateTo, exportMutation]);

  if (!enabled && !statusQuery.isLoading) {
    return (
      <IndustrialPage gap="md" fill>
        <PageHeader title="收支台账" subtitle="记账功能未开启" />
        <IndustrialPanel>
          <p className="text-sm text-[var(--color-text-muted)]">
            请先在
            <Link href="/business-settings" className={`mx-1 ${linkActionClass}`}>
              业务设置
            </Link>
            中开启「记账功能」。
          </p>
        </IndustrialPanel>
      </IndustrialPage>
    );
  }

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader
        title="收支台账"
        subtitle="按客户筛选账目；老板可补录历史账，入账日期自动为今天"
        actions={
          <>
            <WorkspaceToolbarButton onClick={handleExport}>导出CSV</WorkspaceToolbarButton>
            {canBackfill ? (
              <WorkspaceToolbarButton onClick={() => setShowBackfill((v) => !v)}>
                {showBackfill ? "取消补录" : "补录账目"}
              </WorkspaceToolbarButton>
            ) : null}
          </>
        }
      />

      {showBackfill && (canBackfill || editingId) ? (
        <IndustrialPanel title={editingId ? "编辑账目" : "补录账目"}>
          <div className={`${formPanelClass} grid gap-3 md:grid-cols-2 lg:grid-cols-3`}>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>账目类型 {editingId ? "" : "*"}</span>
              <select
                className={fieldInputClass}
                value={form.entry_kind}
                disabled={!!editingId}
                onChange={(e) =>
                  setForm((s) => ({ ...s, entry_kind: e.target.value, customer_id: "", supplier_id: "" }))
                }
              >
                {ENTRY_KIND_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value} title={o.hint}>
                    {o.label}
                  </option>
                ))}
              </select>
              {ENTRY_KIND_OPTIONS.find(o => o.value === form.entry_kind)?.hint ? (
                <p className="mt-0.5 text-[10px] text-[var(--color-text-muted)]">{ENTRY_KIND_OPTIONS.find(o => o.value === form.entry_kind)!.hint}</p>
              ) : null}
            </label>
            {needsCustomer ? (
              <label className="block space-y-1 text-xs">
                <span className={fieldLabelClass}>客户 *</span>
                <select
                  className={fieldInputClass}
                  value={form.customer_id}
                  onChange={(e) => setForm((s) => ({ ...s, customer_id: e.target.value }))}
                >
                  <option value="">请选择客户</option>
                  {customerOptions.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            {needsSupplier ? (
              <label className="block space-y-1 text-xs">
                <span className={fieldLabelClass}>供应商 *</span>
                <select
                  className={fieldInputClass}
                  value={form.supplier_id}
                  onChange={(e) => setForm((s) => ({ ...s, supplier_id: e.target.value }))}
                >
                  <option value="">请选择供应商</option>
                  {supplierOptions.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>业务发生日 *</span>
              <input
                type="date"
                className={fieldInputClass}
                max={todayInputValue()}
                value={form.occurred_on}
                onChange={(e) => setForm((s) => ({ ...s, occurred_on: e.target.value }))}
              />
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>到期日</span>
              <input
                type="date"
                className={fieldInputClass}
                value={form.due_date}
                onChange={(e) => setForm((s) => ({ ...s, due_date: e.target.value }))}
              />
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>金额 *</span>
              <input
                type="number"
                min={0}
                step={0.01}
                className={fieldInputClass}
                value={form.amount}
                onChange={(e) => setForm((s) => ({ ...s, amount: e.target.value }))}
              />
            </label>
            <label className="block space-y-1 text-xs md:col-span-2 lg:col-span-3">
              <span className={fieldLabelClass}>摘要 *</span>
              <input
                className={fieldInputClass}
                value={form.title}
                onChange={(e) => setForm((s) => ({ ...s, title: e.target.value }))}
              />
            </label>
            <label className="block space-y-1 text-xs md:col-span-2 lg:col-span-3">
              <span className={fieldLabelClass}>备注</span>
              <input
                className={fieldInputClass}
                value={form.remark}
                onChange={(e) => setForm((s) => ({ ...s, remark: e.target.value }))}
              />
            </label>
          </div>
          <p className="mt-2 text-xs text-[var(--color-text-muted)]">
            入账日期将自动记录为今天（{todayInputValue()}），业务发生日可选择历史日期。
          </p>
          {formError ? <p className="mt-2 text-xs text-red-500">{formError}</p> : null}
          <div className="mt-3 flex justify-end gap-2">
            <WorkspaceToolbarButton onClick={() => { setShowBackfill(false); setEditingId(null); setForm(defaultForm); }}>取消</WorkspaceToolbarButton>
            <WorkspaceToolbarButton loading={backfillMutation.isPending} onClick={() => editingId ? void handleEdit() : void handleBackfill()}>
              {editingId ? "保存修改" : "保存补录"}
            </WorkspaceToolbarButton>
          </div>
        </IndustrialPanel>
      ) : null}

      <IndustrialPanel title="账目列表">
        <div className="mb-3 flex flex-wrap items-end gap-3">
          <label className="block space-y-1 text-xs">
            <span className={fieldLabelClass}>客户</span>
            <select
              className={fieldInputClass}
              value={customerFilter}
              onChange={(e) => {
                setCustomerFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">全部客户</option>
              {customerOptions.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-1 text-xs">
            <span className={fieldLabelClass}>供应商</span>
            <select
              className={fieldInputClass}
              value={supplierFilter}
              onChange={(e) => {
                setSupplierFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">全部供应商</option>
              {supplierOptions.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-1 text-xs">
            <span className={fieldLabelClass}>类型</span>
            <select
              className={fieldInputClass}
              value={kindFilter}
              onChange={(e) => {
                setKindFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">全部类型</option>
              {ENTRY_KIND_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-1 text-xs">
            <span className={fieldLabelClass}>日期从</span>
            <input
              type="date"
              className={fieldInputClass}
              value={dateFrom}
              onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
            />
          </label>
          <label className="block space-y-1 text-xs">
            <span className={fieldLabelClass}>日期至</span>
            <input
              type="date"
              className={fieldInputClass}
              value={dateTo}
              onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
            />
          </label>
          <label className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
            <input
              type="checkbox"
              checked={showVoid}
              onChange={(e) => {
                setShowVoid(e.target.checked);
                setPage(1);
              }}
            />
            显示作废账目
          </label>
        </div>

        <div className="overflow-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className={tableHeaderRowClass}>
                <th className="px-2 py-2 text-left font-normal">单号</th>
                <th className="px-2 py-2 text-left font-normal">类型</th>
                <th className="px-2 py-2 text-left font-normal">客户</th>
                <th className="px-2 py-2 text-left font-normal">摘要</th>
                <th className="px-2 py-2 text-left font-normal">发生日</th>
                <th className="px-2 py-2 text-left font-normal">入账日</th>
                <th className="px-2 py-2 text-right font-normal">金额</th>
                <th className="px-2 py-2 text-left font-normal">状态</th>
                {canConfirm ? <th className="px-2 py-2 text-left font-normal">操作</th> : null}
              </tr>
            </thead>
            <tbody>
              {entriesQuery.isLoading ? (
                <tr>
                  <td colSpan={canConfirm ? 9 : 8} className="px-2 py-6 text-center text-[var(--color-text-muted)]">
                    加载中…
                  </td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={canConfirm ? 9 : 8} className="px-2 py-6 text-center text-[var(--color-text-muted)]">
                    暂无账目{canBackfill ? "，可点击右上角「补录账目」" : ""}
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr key={row.id} className={`${tableBodyRowClass} cursor-pointer hover:bg-[var(--color-surface-soft)] ${detailId === row.id ? "bg-[var(--color-primary-soft)]" : ""}`} onClick={() => openDetail(row.id)}>
                    <td className="px-2 py-2 font-mono text-[10px]">{row.entryNo}</td>
                    <td className="px-2 py-2">
                      {KIND_LABEL[row.entryKind] ?? row.entryKind}
                      {row.isBackfill ? (
                        <span className="ml-1 text-[10px] text-[var(--color-text-muted)]">补录</span>
                      ) : null}
                    </td>
                    <td className="px-2 py-2">{customerNameMap.get(row.customerId) ?? "—"}</td>
                    <td className="px-2 py-2">{row.title}</td>
                    <td className="px-2 py-2">{row.occurredOn}</td>
                    <td className="px-2 py-2">{row.bookedOn}</td>
                    <td className="px-2 py-2 text-right">{row.amount}</td>
                    <td className="px-2 py-2">{STATUS_LABEL[row.status] ?? row.status}</td>
                    {canConfirm ? (
                      <td className="px-2 py-2" onClick={(e) => e.stopPropagation()}>
                        <div className="flex gap-2">
                          {row.status === "draft" ? (
                            <>
                            <button type="button" className={linkActionClass} onClick={() => startEdit(row)}>编辑</button>
                            <button type="button" className={linkActionClass} onClick={() => void confirmMutation.mutateAsync(row.id)}>确认</button>
                            </>
                          ) : null}
                          {row.status === "draft" || row.status === "confirmed" ? (
                            <button type="button" className={dangerActionClass} onClick={() => {
                              if (!window.confirm(`确定作废账目「${row.entryNo}」吗？`)) return;
                              void voidMutation.mutateAsync(row.id);
                            }}>作废</button>
                          ) : null}
                        </div>
                      </td>
                    ) : null}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {detailId && detail ? (
          <IndustrialPanel title={`分录详情 · ${String(detail.entry_no ?? "")}`} toolbar={<WorkspaceToolbarButton onClick={() => { setDetailId(null); }}>关闭</WorkspaceToolbarButton>}>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4 text-xs">
              <div><span className="text-[var(--color-text-muted)]">类型：</span>{KIND_LABEL[String(detail.entry_kind)] ?? String(detail.entry_kind)}</div>
              <div><span className="text-[var(--color-text-muted)]">状态：</span>{STATUS_LABEL[String(detail.status)] ?? String(detail.status)}</div>
              <div><span className="text-[var(--color-text-muted)]">金额：</span>{money(detail.amount as number)}</div>
              <div><span className="text-[var(--color-text-muted)]">已核销：</span>{money(detail.settled_amount as number)}</div>
              <div><span className="text-[var(--color-text-muted)]">发生日：</span>{String(detail.occurred_on ?? "")}</div>
              <div><span className="text-[var(--color-text-muted)]">入账日：</span>{String(detail.booked_on ?? "")}</div>
              <div><span className="text-[var(--color-text-muted)]">到期日：</span>{String(detail.due_date ?? "—")}</div>
              <div className="md:col-span-2"><span className="text-[var(--color-text-muted)]">摘要：</span>{String(detail.title ?? "")}</div>
            </div>
            {Array.isArray(detail.lines) && detail.lines.length > 0 ? (
              <div className="mt-3">
                <h4 className="mb-2 text-xs font-semibold">分录明细 ({(detail.lines as unknown[]).length} 行)</h4>
                <div className="overflow-auto rounded border border-[var(--color-border)]">
                  <table className="min-w-full text-xs">
                    <thead><tr className={tableHeaderRowClass}>
                      <th className="px-2 py-1 text-left">产品/项目</th><th className="px-2 py-1 text-left">规格</th><th className="px-2 py-1 text-left">单位</th><th className="px-2 py-1 text-right">数量</th><th className="px-2 py-1 text-right">单价</th><th className="px-2 py-1 text-right">行金额</th>
                    </tr></thead>
                    <tbody>
                      {(detail.lines as Array<Record<string, unknown>>).map((line, i) => (
                        <tr key={i} className={tableBodyRowClass}>
                          <td className="px-2 py-1">{String(line.item_name ?? "—")}</td>
                          <td className="px-2 py-1 text-[var(--color-text-muted)]">{String(line.spec ?? "—")}</td>
                          <td className="px-2 py-1">{String(line.unit ?? "—")}</td>
                          <td className="px-2 py-1 text-right">{String(line.qty ?? "—")}</td>
                          <td className="px-2 py-1 text-right">{money(line.unit_price as number)}</td>
                          <td className="px-2 py-1 text-right font-medium">{money(line.line_amount as number)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : <p className="mt-2 text-xs text-[var(--color-text-muted)]">该分录无明细行</p>}
          </IndustrialPanel>
        ) : detailLoading ? (
          <p className="py-4 text-center text-xs text-[var(--color-text-muted)]">加载详情中...</p>
        ) : null}

        <div className="mt-3 flex items-center justify-between text-xs text-[var(--color-text-muted)]">
          <span>
            共 {total} 条 · 第 {page} 页
          </span>
          <div className="flex gap-2">
            <WorkspaceToolbarButton compact disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              上一页
            </WorkspaceToolbarButton>
            <WorkspaceToolbarButton compact disabled={page * 20 >= total} onClick={() => setPage((p) => p + 1)}>
              下一页
            </WorkspaceToolbarButton>
          </div>
        </div>
      </IndustrialPanel>
    </IndustrialPage>
  );
}
