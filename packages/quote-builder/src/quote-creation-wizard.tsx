"use client";

import * as React from "react";

export type WizardMasterOption = { id: string; label: string; sub?: string };

export type QuoteWizardForm = {
  title: string;
  customerId: string;
  machineId: string;
  bomId: string;
  approvalTemplateId: string;
  currency: string;
  validUntil: string;
  remark: string;
  seedFromBom: boolean;
};

const STEPS = [
  { id: 1, title: "客户与项目", hint: "选择真实客户与目标设备" },
  { id: 2, title: "BOM 与审批", hint: "绑定物料清单与审批模板" },
  { id: 3, title: "确认创建", hint: "核对信息并生成首版报价" },
] as const;

export function QuoteCreationWizard({
  customers,
  machines,
  boms,
  approvalTemplates,
  value,
  onChange,
  onSubmit,
  submitting,
  error,
}: {
  customers: WizardMasterOption[];
  machines: WizardMasterOption[];
  boms: WizardMasterOption[];
  approvalTemplates: WizardMasterOption[];
  value: QuoteWizardForm;
  onChange: (next: QuoteWizardForm) => void;
  onSubmit: () => void;
  submitting?: boolean;
  error?: string;
}) {
  const [step, setStep] = React.useState(1);
  const filteredBoms = React.useMemo(
    () => (value.machineId ? boms.filter((b) => b.sub?.includes(value.machineId)) : boms),
    [boms, value.machineId],
  );

  const patch = (partial: Partial<QuoteWizardForm>) => onChange({ ...value, ...partial });

  const canNext =
    (step === 1 && value.title.trim() && value.customerId && value.machineId) ||
    (step === 2 && (!value.seedFromBom || value.bomId)) ||
    step === 3;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="rounded-lg border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
        <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">新建工业报价</h1>
        <p className="mt-1 text-sm text-zinc-500">向导将创建报价单，并可选从 BOM 生成首版行项目。</p>
        <div className="mt-4 flex gap-2">
          {STEPS.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setStep(s.id)}
              className={`flex-1 rounded-md border px-2 py-2 text-left text-xs transition ${
                step === s.id
                  ? "border-blue-500 bg-blue-50 dark:border-blue-600 dark:bg-blue-950/40"
                  : "border-zinc-200 dark:border-zinc-700"
              }`}
            >
              <div className="font-semibold">{s.title}</div>
              <div className="text-zinc-500">{s.hint}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-700 dark:bg-zinc-900">
        {step === 1 && (
          <div className="space-y-4">
            <label className="block text-sm">
              <span className="font-medium">报价标题</span>
              <input
                className="mt-1 w-full rounded border px-3 py-2 text-sm dark:border-zinc-600 dark:bg-zinc-950"
                value={value.title}
                onChange={(e) => patch({ title: e.target.value })}
                placeholder="例如：XX 产线改造报价"
              />
            </label>
            <label className="block text-sm">
              <span className="font-medium">客户</span>
              <select
                className="mt-1 w-full rounded border px-3 py-2 text-sm dark:border-zinc-600 dark:bg-zinc-950"
                value={value.customerId}
                onChange={(e) => patch({ customerId: e.target.value })}
              >
                <option value="">请选择客户</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm">
              <span className="font-medium">设备</span>
              <select
                className="mt-1 w-full rounded border px-3 py-2 text-sm dark:border-zinc-600 dark:bg-zinc-950"
                value={value.machineId}
                onChange={(e) => patch({ machineId: e.target.value, bomId: "" })}
              >
                <option value="">请选择设备</option>
                {machines.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block text-sm">
                <span className="font-medium">币种</span>
                <select
                  className="mt-1 w-full rounded border px-3 py-2 text-sm dark:border-zinc-600 dark:bg-zinc-950"
                  value={value.currency}
                  onChange={(e) => patch({ currency: e.target.value })}
                >
                  <option value="CNY">CNY</option>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                </select>
              </label>
              <label className="block text-sm">
                <span className="font-medium">有效期至</span>
                <input
                  type="date"
                  className="mt-1 w-full rounded border px-3 py-2 text-sm dark:border-zinc-600 dark:bg-zinc-950"
                  value={value.validUntil}
                  onChange={(e) => patch({ validUntil: e.target.value })}
                />
              </label>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={value.seedFromBom}
                onChange={(e) => patch({ seedFromBom: e.target.checked })}
              />
              <span>从 BOM 自动生成首版报价行（推荐）</span>
            </label>
            <label className="block text-sm">
              <span className="font-medium">BOM 版本</span>
              <select
                className="mt-1 w-full rounded border px-3 py-2 text-sm dark:border-zinc-600 dark:bg-zinc-950"
                value={value.bomId}
                onChange={(e) => patch({ bomId: e.target.value })}
                disabled={!value.seedFromBom}
              >
                <option value="">不绑定 / 稍后选择</option>
                {filteredBoms.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm">
              <span className="font-medium">审批模板</span>
              <select
                className="mt-1 w-full rounded border px-3 py-2 text-sm dark:border-zinc-600 dark:bg-zinc-950"
                value={value.approvalTemplateId}
                onChange={(e) => patch({ approvalTemplateId: e.target.value })}
              >
                <option value="">默认流程</option>
                {approvalTemplates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm">
              <span className="font-medium">备注</span>
              <textarea
                className="mt-1 w-full rounded border px-3 py-2 text-sm dark:border-zinc-600 dark:bg-zinc-950"
                rows={3}
                value={value.remark}
                onChange={(e) => patch({ remark: e.target.value })}
              />
            </label>
          </div>
        )}

        {step === 3 && (
          <dl className="grid gap-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-zinc-500">标题</dt>
              <dd className="font-medium">{value.title}</dd>
            </div>
            <div>
              <dt className="text-zinc-500">客户</dt>
              <dd>{customers.find((c) => c.id === value.customerId)?.label ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-zinc-500">设备</dt>
              <dd>{machines.find((m) => m.id === value.machineId)?.label ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-zinc-500">BOM 首版</dt>
              <dd>{value.seedFromBom ? filteredBoms.find((b) => b.id === value.bomId)?.label ?? "自动" : "手动录入"}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-zinc-500">备注</dt>
              <dd>{value.remark || "—"}</dd>
            </div>
          </dl>
        )}

        {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}

        <div className="mt-6 flex justify-between gap-2">
          <button
            type="button"
            className="rounded border px-4 py-2 text-sm disabled:opacity-50"
            disabled={step <= 1}
            onClick={() => setStep((s) => Math.max(1, s - 1))}
          >
            上一步
          </button>
          {step < 3 ? (
            <button
              type="button"
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white disabled:opacity-50"
              disabled={!canNext}
              onClick={() => setStep((s) => Math.min(3, s + 1))}
            >
              下一步
            </button>
          ) : (
            <button
              type="button"
              className="rounded bg-emerald-600 px-4 py-2 text-sm text-white disabled:opacity-50"
              disabled={submitting || !canNext}
              onClick={onSubmit}
            >
              {submitting ? "创建中…" : "创建报价并进入工作台"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
