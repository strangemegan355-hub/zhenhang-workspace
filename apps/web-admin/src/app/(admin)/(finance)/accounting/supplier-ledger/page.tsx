"use client";

import {
  useAccountingStatusQuery,
  useSupplierLedgerQuery,
  useSupplierLedgerDetailQuery,
  useRegisterSupplierLedgerMutation,
  useCreateSupplierPayableMutation,
  useCreateSupplierPaymentMutation,
  useSuppliersQuery,
  type SupplierPayablePayload,
  type PaymentPayload,
} from "@zhenhang/query-hooks";
import {
  IndustrialPage,
  IndustrialPanel,
  PageHeader,
  WorkspaceToolbarButton,
} from "@zhenhang/ui";
import Link from "next/link";
import { useMemo, useState } from "react";
import { FinanceSubNav } from "@/components/finance/finance-sub-nav";
import {
  fieldInputClass,
  fieldLabelClass,
  formPanelClass,
  linkActionClass,
  tableBodyRowClass,
  tableHeaderRowClass,
} from "@/lib/form-styles";

function money(n: number | string | undefined) {
  return Number(n ?? 0).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function todayInputValue() {
  return new Date().toISOString().slice(0, 10);
}

const defaultPayableForm = {
  amount: "",
  occurred_on: todayInputValue(),
  due_date: "",
  title: "",
  remark: "",
};

const defaultPaymentForm = {
  amount: "",
  occurred_on: todayInputValue(),
  title: "",
  remark: "",
};

export default function SupplierLedgerPage() {
  const statusQuery = useAccountingStatusQuery();
  const enabled = statusQuery.data?.flags.accounting_enabled ?? false;

  const [page, setPage] = useState(1);
  const [outstandingOnly, setOutstandingOnly] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedSupplierId, setSelectedSupplierId] = useState<string | null>(null);
  const [showRegister, setShowRegister] = useState(false);
  const [showPayable, setShowPayable] = useState(false);
  const [showPayment, setShowPayment] = useState(false);
  const [payableForm, setPayableForm] = useState(defaultPayableForm);
  const [paymentForm, setPaymentForm] = useState(defaultPaymentForm);
  const [formError, setFormError] = useState<string | null>(null);

  const ledgerQuery = useSupplierLedgerQuery(page, { outstandingOnly, q: query || undefined }, enabled);
  const suppliersQuery = useSuppliersQuery(1);
  const detailQuery = useSupplierLedgerDetailQuery(selectedSupplierId);
  const registerMutation = useRegisterSupplierLedgerMutation();
  const payableMutation = useCreateSupplierPayableMutation();
  const paymentMutation = useCreateSupplierPaymentMutation();

  const supplierOptions = useMemo(
    () =>
      ((suppliersQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((s) => ({
        value: String(s.id ?? ""),
        label: String(s.name ?? ""),
      })),
    [suppliersQuery.data],
  );

  const supplierNameMap = useMemo(
    () => new Map(supplierOptions.map((s) => [s.value, s.label])),
    [supplierOptions],
  );

  const rows = useMemo(
    () =>
      ((ledgerQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? []).map((row) => ({
        id: String(row.supplier_id ?? ""),
        name: String(row.supplier_name ?? ""),
        code: String(row.supplier_code ?? ""),
        payableTotal: money(row.payable_total as number),
        paidTotal: money(row.paid_total as number),
        outstanding: money(row.outstanding_total as number),
        openBills: Number(row.open_bill_count ?? 0),
        registered: Boolean(row.is_registered),
      })),
    [ledgerQuery.data],
  );

  const total = (ledgerQuery.data as { total?: number } | undefined)?.total ?? rows.length;
  const detail = detailQuery.data as Record<string, unknown> | undefined;
  const detailEntries = (detail?.entries as Record<string, unknown>[]) ?? [];

  const handleRegister = async (supplierId: string) => {
    try {
      await registerMutation.mutateAsync(supplierId);
      void ledgerQuery.refetch();
    } catch { /* ignore */ }
  };

  const handleCreatePayable = async () => {
    setFormError(null);
    if (!selectedSupplierId) { setFormError("请先在列表中选择供应商"); return; }
    if (!payableForm.title.trim()) { setFormError("请填写摘要"); return; }
    if (!payableForm.amount || Number(payableForm.amount) <= 0) { setFormError("请填写有效金额"); return; }
    try {
      const body: SupplierPayablePayload = {
        amount: Number(payableForm.amount),
        occurred_on: payableForm.occurred_on,
        due_date: payableForm.due_date || undefined,
        title: payableForm.title.trim(),
        remark: payableForm.remark.trim() || undefined,
      };
      await payableMutation.mutateAsync({ supplierId: selectedSupplierId, body });
      setPayableForm(defaultPayableForm);
      setShowPayable(false);
      void ledgerQuery.refetch();
      if (detailQuery.data) void detailQuery.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "录入失败");
    }
  };

  const handleCreatePayment = async () => {
    setFormError(null);
    if (!selectedSupplierId) { setFormError("请先在列表中选择供应商"); return; }
    // Collect open payables for allocation
    const openPayables = detailEntries
      .filter((e: Record<string, unknown>) => String(e.entry_kind) === "payable" && Number(e.open_amount ?? 0) > 0)
      .map((e: Record<string, unknown>) => ({
        id: String(e.id),
        entry_no: String(e.entry_no),
        title: String(e.title),
        open_amount: Number(e.open_amount ?? 0),
      }));
    if (openPayables.length === 0) { setFormError("该供应商没有待付款的应付账目"); return; }
    if (!paymentForm.title.trim()) { setFormError("请填写摘要"); return; }
    if (!paymentForm.amount || Number(paymentForm.amount) <= 0) { setFormError("请填写有效金额"); return; }
    try {
      const totalAmount = Number(paymentForm.amount);
      // ponytail: auto-allocate to first open payable
      const firstPayable = openPayables[0];
      const body: PaymentPayload = {
        supplier_id: selectedSupplierId,
        amount: totalAmount,
        occurred_on: paymentForm.occurred_on,
        title: paymentForm.title.trim(),
        remark: paymentForm.remark.trim() || undefined,
        allocations: [{
          payable_entry_id: firstPayable.id,
          amount: Math.min(totalAmount, firstPayable.open_amount),
        }],
      };
      await paymentMutation.mutateAsync(body);
      setPaymentForm(defaultPaymentForm);
      setShowPayment(false);
      void ledgerQuery.refetch();
      if (detailQuery.data) void detailQuery.refetch();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "付款失败");
    }
  };

  if (!enabled && !statusQuery.isLoading) {
    return (
      <IndustrialPage gap="md" fill>
        <PageHeader title="财务中心 · 供应商应付" subtitle="记账功能未开启" />
        <FinanceSubNav />
        <IndustrialPanel>
          <p className="text-sm text-[var(--color-text-muted)]">
            请先在
            <Link href="/business-settings" className={`mx-1 ${linkActionClass}`}>业务设置</Link>
            中开启「记账功能」。
          </p>
        </IndustrialPanel>
      </IndustrialPage>
    );
  }

  return (
    <IndustrialPage gap="md" fill>
      <PageHeader title="财务中心 · 供应商应付" subtitle="管理供应商应付与付款" />
      <FinanceSubNav />

      <IndustrialPanel title="供应商应付汇总">
        <div className="mb-3 flex flex-wrap items-end gap-3">
          <label className="block space-y-1 text-xs">
            <span className={fieldLabelClass}>搜索</span>
            <input className={fieldInputClass} value={query} onChange={(e) => { setQuery(e.target.value); setPage(1); }} placeholder="供应商名称/编码" />
          </label>
          <label className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
            <input type="checkbox" checked={outstandingOnly} onChange={(e) => { setOutstandingOnly(e.target.checked); setPage(1); }} />
            仅显示有欠款
          </label>
          <WorkspaceToolbarButton onClick={() => { setShowRegister(true); void suppliersQuery.refetch(); }}>登记供应商</WorkspaceToolbarButton>
        </div>

        <div className="overflow-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className={tableHeaderRowClass}>
                <th className="px-2 py-2 text-left font-normal">供应商</th>
                <th className="px-2 py-2 text-left font-normal">应付总额</th>
                <th className="px-2 py-2 text-left font-normal">已付</th>
                <th className="px-2 py-2 text-left font-normal">欠款</th>
                <th className="px-2 py-2 text-left font-normal">未结单数</th>
                <th className="px-2 py-2 text-left font-normal">操作</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className={tableBodyRowClass}>
                  <td className="px-2 py-2">
                    <button type="button" className={linkActionClass} onClick={() => setSelectedSupplierId(selectedSupplierId === row.id ? null : row.id)}>
                      {row.name} {row.code ? `(${row.code})` : ""}
                    </button>
                  </td>
                  <td className="px-2 py-2">{row.payableTotal}</td>
                  <td className="px-2 py-2">{row.paidTotal}</td>
                  <td className="px-2 py-2 font-semibold text-[var(--color-danger)]">{row.outstanding}</td>
                  <td className="px-2 py-2">{row.openBills}</td>
                  <td className="px-2 py-2">
                    {!row.registered ? (
                      <button type="button" className={linkActionClass} onClick={() => handleRegister(row.id)}>登记</button>
                    ) : (
                      <span className="text-xs text-[var(--color-text-muted)]">已登记</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-[var(--color-text-muted)]">共 {total} 条</p>
      </IndustrialPanel>

      {/* Register modal-like inline form */}
      {showRegister ? (
        <IndustrialPanel title="登记供应商到台账">
          <div className="mb-3">
            <select className={fieldInputClass} onChange={(e) => { if (e.target.value) { handleRegister(e.target.value); setShowRegister(false); } }} defaultValue="">
              <option value="">选择供应商...</option>
              {supplierOptions.filter(s => !rows.some(r => r.id === s.value && r.registered)).map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
          <WorkspaceToolbarButton onClick={() => setShowRegister(false)}>取消</WorkspaceToolbarButton>
        </IndustrialPanel>
      ) : null}

      {/* Payable form */}
      {showPayable && selectedSupplierId ? (
        <IndustrialPanel title="录入应付">
          <div className={`${formPanelClass} grid gap-3 md:grid-cols-2`}>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>金额 *</span>
              <input type="number" min={0} step={0.01} className={fieldInputClass} value={payableForm.amount} onChange={(e) => setPayableForm(s => ({ ...s, amount: e.target.value }))} />
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>业务日 *</span>
              <input type="date" className={fieldInputClass} max={todayInputValue()} value={payableForm.occurred_on} onChange={(e) => setPayableForm(s => ({ ...s, occurred_on: e.target.value }))} />
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>到期日</span>
              <input type="date" className={fieldInputClass} value={payableForm.due_date} onChange={(e) => setPayableForm(s => ({ ...s, due_date: e.target.value }))} />
            </label>
            <label className="block space-y-1 text-xs md:col-span-2">
              <span className={fieldLabelClass}>摘要 *</span>
              <input className={fieldInputClass} value={payableForm.title} onChange={(e) => setPayableForm(s => ({ ...s, title: e.target.value }))} />
            </label>
            <label className="block space-y-1 text-xs md:col-span-2">
              <span className={fieldLabelClass}>备注</span>
              <input className={fieldInputClass} value={payableForm.remark} onChange={(e) => setPayableForm(s => ({ ...s, remark: e.target.value }))} />
            </label>
          </div>
          {formError ? <p className="mt-2 text-xs text-red-500">{formError}</p> : null}
          <div className="mt-3 flex justify-end gap-2">
            <WorkspaceToolbarButton onClick={() => { setShowPayable(false); setFormError(null); }}>取消</WorkspaceToolbarButton>
            <WorkspaceToolbarButton loading={payableMutation.isPending} onClick={() => void handleCreatePayable()}>保存</WorkspaceToolbarButton>
          </div>
        </IndustrialPanel>
      ) : null}

      {/* Payment form */}
      {showPayment && selectedSupplierId ? (
        <IndustrialPanel title="录入付款">
          <div className={`${formPanelClass} grid gap-3 md:grid-cols-2`}>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>金额 *</span>
              <input type="number" min={0} step={0.01} className={fieldInputClass} value={paymentForm.amount} onChange={(e) => setPaymentForm(s => ({ ...s, amount: e.target.value }))} />
            </label>
            <label className="block space-y-1 text-xs">
              <span className={fieldLabelClass}>业务日 *</span>
              <input type="date" className={fieldInputClass} max={todayInputValue()} value={paymentForm.occurred_on} onChange={(e) => setPaymentForm(s => ({ ...s, occurred_on: e.target.value }))} />
            </label>
            <label className="block space-y-1 text-xs md:col-span-2">
              <span className={fieldLabelClass}>摘要 *</span>
              <input className={fieldInputClass} value={paymentForm.title} onChange={(e) => setPaymentForm(s => ({ ...s, title: e.target.value }))} />
            </label>
            <label className="block space-y-1 text-xs md:col-span-2">
              <span className={fieldLabelClass}>备注</span>
              <input className={fieldInputClass} value={paymentForm.remark} onChange={(e) => setPaymentForm(s => ({ ...s, remark: e.target.value }))} />
            </label>
          </div>
          <p className="mt-2 text-xs text-[var(--color-text-muted)]">付款将自动核销到最早到期的应付账目</p>
          {formError ? <p className="mt-2 text-xs text-red-500">{formError}</p> : null}
          <div className="mt-3 flex justify-end gap-2">
            <WorkspaceToolbarButton onClick={() => { setShowPayment(false); setFormError(null); }}>取消</WorkspaceToolbarButton>
            <WorkspaceToolbarButton loading={paymentMutation.isPending} onClick={() => void handleCreatePayment()}>保存</WorkspaceToolbarButton>
          </div>
        </IndustrialPanel>
      ) : null}

      {/* Detail panel */}
      {selectedSupplierId && detail ? (
        <IndustrialPanel title={`${supplierNameMap.get(selectedSupplierId) ?? ""} 应付明细`}>
          <div className="mb-3 grid grid-cols-3 gap-4 text-xs">
            <div><span className="text-[var(--color-text-muted)]">应付总额：</span><span className="font-semibold text-[var(--color-danger)]">{money(detail.payable_total as number)}</span></div>
            <div><span className="text-[var(--color-text-muted)]">已付：</span>{money(detail.paid_total as number)}</div>
            <div><span className="text-[var(--color-text-muted)]">欠款：</span><span className="font-semibold text-[var(--color-danger)]">{money(detail.outstanding_total as number)}</span></div>
          </div>
          <div className="mb-3 flex gap-2">
            <WorkspaceToolbarButton onClick={() => { setShowPayable(true); setFormError(null); }}>录入应付</WorkspaceToolbarButton>
            <WorkspaceToolbarButton onClick={() => { setShowPayment(true); setFormError(null); }}>录入付款</WorkspaceToolbarButton>
          </div>
          <div className="overflow-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr className={tableHeaderRowClass}>
                  <th className="px-2 py-2 text-left font-normal">单号</th>
                  <th className="px-2 py-2 text-left font-normal">类型</th>
                  <th className="px-2 py-2 text-left font-normal">摘要</th>
                  <th className="px-2 py-2 text-left font-normal">金额</th>
                  <th className="px-2 py-2 text-left font-normal">已付</th>
                  <th className="px-2 py-2 text-left font-normal">未付</th>
                  <th className="px-2 py-2 text-left font-normal">发生日</th>
                </tr>
              </thead>
              <tbody>
                {detailEntries.map((e: Record<string, unknown>, idx: number) => (
                  <tr key={idx} className={tableBodyRowClass}>
                    <td className="px-2 py-2">{String(e.entry_no ?? "")}</td>
                    <td className="px-2 py-2">{String(e.entry_kind) === "payable" ? "应付" : "付款"}</td>
                    <td className="px-2 py-2">{String(e.title ?? "")}</td>
                    <td className="px-2 py-2">{money(e.amount as number)}</td>
                    <td className="px-2 py-2">{money(e.settled_amount as number)}</td>
                    <td className="px-2 py-2 font-semibold text-[var(--color-danger)]">{money(e.open_amount as number)}</td>
                    <td className="px-2 py-2">{String(e.occurred_on ?? "").slice(0, 10)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </IndustrialPanel>
      ) : null}
    </IndustrialPage>
  );
}
