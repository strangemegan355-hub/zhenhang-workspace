"use client";

import { QuoteCreationWizard, type QuoteWizardForm } from "@zhenhang/quote-builder";
import {
  useApprovalTemplatesQuery,
  useBomsListQuery,
  useCreateQuoteWizardMutation,
  useCustomersQuery,
  useMachinesQuery,
} from "@zhenhang/query-hooks";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

function mapOptions(items: Record<string, unknown>[] | undefined, labelKeys: string[]) {
  return (items ?? []).map((row) => {
    const label = labelKeys.map((k) => row[k]).filter(Boolean).join(" · ") || String(row.id ?? "");
    return {
      id: String(row.id ?? ""),
      label,
      sub: row.machine_id ? String(row.machine_id) : undefined,
    };
  });
}

const defaultForm: QuoteWizardForm = {
  title: "",
  customerId: "",
  machineId: "",
  bomId: "",
  approvalTemplateId: "",
  currency: "CNY",
  validUntil: "",
  remark: "",
  seedFromBom: true,
};

export default function NewQuotePage() {
  const router = useRouter();
  const [form, setForm] = useState<QuoteWizardForm>(defaultForm);
  const [error, setError] = useState<string | undefined>();

  const customersQuery = useCustomersQuery();
  const machinesQuery = useMachinesQuery();
  const bomsQuery = useBomsListQuery();
  const templatesQuery = useApprovalTemplatesQuery();
  const wizardMut = useCreateQuoteWizardMutation();

  const customers = useMemo(
    () => mapOptions((customersQuery.data as { items?: Record<string, unknown>[] })?.items, ["code", "name"]),
    [customersQuery.data],
  );
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
    () => mapOptions((templatesQuery.data as { items?: Record<string, unknown>[] })?.items, ["code", "name"]),
    [templatesQuery.data],
  );

  const handleSubmit = async () => {
    setError(undefined);
    try {
      const body: Record<string, unknown> = {
        title: form.title.trim(),
        customer_id: form.customerId,
        machine_id: form.machineId,
        currency: form.currency,
        remark: form.remark || null,
      };
      if (form.validUntil) body.valid_until = form.validUntil;
      if (form.bomId && form.seedFromBom) body.bom_id = form.bomId;
      if (form.approvalTemplateId) body.approval_template_id = form.approvalTemplateId;

      const created = await wizardMut.mutateAsync(body);
      const id = String((created as Record<string, unknown>).id ?? "");
      router.push(id ? `/quotes?selected=${id}` : "/quotes");
    } catch (e) {
      setError(e instanceof Error ? e.message : "创建失败");
    }
  };

  const loading = customersQuery.isLoading || machinesQuery.isLoading;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between text-sm text-zinc-500">
        <Link href="/quotes" className="hover:text-blue-600">
          ← 返回报价列表
        </Link>
        <Link href="/dashboard" className="hover:text-blue-600">
          运营看板
        </Link>
      </div>
      {loading ? (
        <p className="text-sm text-zinc-500">加载主数据…</p>
      ) : (
        <QuoteCreationWizard
          customers={customers}
          machines={machines}
          boms={boms}
          approvalTemplates={approvalTemplates}
          value={form}
          onChange={setForm}
          onSubmit={handleSubmit}
          submitting={wizardMut.isPending}
          error={error}
        />
      )}
    </div>
  );
}
