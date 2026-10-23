"use client";

import { useToastStore } from "@zhenhang/realtime";

import {
  fetchInstallationPlan,
  useCreateInstallationPlanMutation,
  useDeleteInstallationPlanMutation,
  useEquipmentUnitsQuery,
  useInstallationPlanQuery,
  useInstallationPlansQuery,
  useUpdateInstallationPlanMutation,
} from "@zhenhang/query-hooks";
import { apiErrorMessage } from "@/lib/api-error";

import { useState, useMemo } from "react";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { IndustrialPage, WorkspaceToolbarButton } from "@zhenhang/ui";
import { searchInputClass } from "@/lib/form-styles";

type PlanRow = {
  id: string;
  unitLabel: string;
  status: string;
  statusDisplay: string;
  plannedStart: string;
  plannedEnd: string;
  actualStart: string;
  actualEnd: string;
  customerAccepted: boolean;
  customerAcceptedDisplay: string;
  installCount: number;
  commCount: number;
};

const STATUS_LABEL: Record<string, string> = {
  planned: "计划中",
  in_progress: "进行中",
  completed: "已完成",
};

const STATUS_COLOR: Record<string, string> = {
  planned: "text-gray-400",
  in_progress: "text-blue-400",
  completed: "text-emerald-400",
};

export default function InstallationPage() {
  const [selectedUnitId, setSelectedUnitId] = useState("");
  // Units, plans and the detail all come from queries now, so the page owns only its selections.
  const unitsQuery = useEquipmentUnitsQuery(1, 200);
  const unitOptions = useMemo(
    () =>
      ((unitsQuery.data as { items?: Array<Record<string, unknown>> } | undefined)?.items ?? []).map(
        (unit) => ({
          value: String(unit.id ?? ""),
          label: `${String(unit.serial_number ?? "")} (${String(unit.machine_name ?? "")}) [${String(unit.build_status ?? "")}]`,
        }),
      ),
    [unitsQuery.data],
  );
  const plansQuery = useInstallationPlansQuery(selectedUnitId || undefined);
  const updatePlanMutation = useUpdateInstallationPlanMutation();
  const createPlanMutation = useCreateInstallationPlanMutation();
  const deletePlanMutation = useDeleteInstallationPlanMutation();

  // Form
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState({
    planned_start_date: "",
    planned_end_date: "",
    remarks: "",
    install_json: "[]",
    comm_json: "[]",
    status: "",
    customer_representative: "",
    customer_accepted: "false",
  });
  const [error, setError] = useState<string | null>(null);

  // Detail modal: the id drives a query, so the panel refreshes by invalidation after an edit.
  const [detailPlanId, setDetailPlanId] = useState<string | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  const detailQuery = useInstallationPlanQuery(detailPlanId ?? undefined);
  const detail = detailQuery.data ?? null;

  const [submitting, setSubmitting] = useState(false);


  function handleUnitChange(id: string) {
    setSelectedUnitId(id);
    closeForm();
  }

  function closeForm() {
    setShowForm(false);
    setEditId(null);
    setError(null);
  }

  async function handleSave() {
    setError(null);
    let installItems = [];
    let commItems = [];
    try { installItems = JSON.parse(form.install_json); } catch { setError("安装步骤 JSON 格式错误"); return; }
    try { commItems = JSON.parse(form.comm_json); } catch { setError("调试项 JSON 格式错误"); return; }

    setSubmitting(true);
    try {
      if (editId) {
        const body: Record<string, unknown> = {
          install_items: installItems,
          commissioning_items: commItems,
        };
        if (form.status) body.status = form.status;
        if (form.customer_representative) body.customer_representative = form.customer_representative;
        if (form.customer_accepted === "true") body.customer_accepted = true;
        await updatePlanMutation.mutateAsync({ planId: editId, payload: body });
      } else {
        await createPlanMutation.mutateAsync({
          unitId: selectedUnitId,
          payload: {
            equipment_unit_id: selectedUnitId,
            planned_start_date: form.planned_start_date
              ? new Date(form.planned_start_date).toISOString()
              : null,
            planned_end_date: form.planned_end_date
              ? new Date(form.planned_end_date).toISOString()
              : null,
            install_items: installItems,
            commissioning_items: commItems,
            remarks: form.remarks || null,
          },
        });
      }
      closeForm();
    } catch (err) {
      setError(apiErrorMessage(err, "保存失败"));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm("确认删除此安装计划？")) return;
    try {
      await deletePlanMutation.mutateAsync(id);
    } catch (err) {
      notify(apiErrorMessage(err, "删除失败"));
    }
  }

  function openDetail(planId: string) {
    setDetailPlanId(planId);
    setShowDetail(true);
  }

  async function handleQuickAction(action: string, planId: string) {
    const updates: Record<string, unknown> = {};
    if (action === "start") updates.status = "in_progress";
    else if (action === "complete") updates.status = "completed";

    try {
      await updatePlanMutation.mutateAsync({ planId, payload: updates });
      // No refetch: the mutation invalidates the list and the detail panel.
    } catch (err) {
      notify(apiErrorMessage(err, "操作失败"));
    }
  }


  const planRows: PlanRow[] = useMemo(
    () =>
      (plansQuery.data ?? []).map((plan) => {
        const rawStatus = String(plan.status ?? "");
        return {
          id: String(plan.id ?? ""),
          unitLabel: String(plan.equipment_unit_id ?? "").slice(0, 8),
          status: rawStatus,
          statusDisplay: STATUS_LABEL[rawStatus] ?? rawStatus,
          plannedStart: String(plan.planned_start_date ?? "").slice(0, 10),
          plannedEnd: String(plan.planned_end_date ?? "").slice(0, 10),
          actualStart: String(plan.actual_start_date ?? "").slice(0, 10) || "-",
          actualEnd: String(plan.actual_end_date ?? "").slice(0, 10) || "-",
          customerAccepted: Boolean(plan.customer_accepted),
          customerAcceptedDisplay: plan.customer_accepted ? "已验收" : "未验收",
          installCount: Array.isArray(plan.install_items) ? (plan.install_items as unknown[]).length : 0,
          commCount: Array.isArray(plan.commissioning_items)
            ? (plan.commissioning_items as unknown[]).length
            : 0,
        };
      }),
    [plansQuery.data],
  );

  const sampleInstallJson = JSON.stringify([
    { step: "1", description: "开箱检查", completed: false, remark: "" },
    { step: "2", description: "定位安装", completed: false, remark: "" },
  ], null, 2);

  const sampleCommJson = JSON.stringify([
    { category: "机械", check_point: "水平度", expected: "<0.5mm/m", actual_result: "", pass: true, remark: "" },
    { category: "电气", check_point: "电压", expected: "380V±5%", actual_result: "", pass: true, remark: "" },
  ], null, 2);

  return (
    <IndustrialPage gap="md" fill>
      {/* Form */}
      {showForm ? (
        <MasterCreateForm
          title={editId ? "修改安装计划" : "新增安装计划"}
          fields={[
            ...(editId
              ? [
                  { key: "status", label: "状态", type: "select" as const, options: [
                    { value: "planned", label: "计划中" },
                    { value: "in_progress", label: "进行中" },
                    { value: "completed", label: "已完成" },
                  ]},
                  { key: "customer_representative", label: "客户代表", placeholder: "签收人姓名" },
                  { key: "customer_accepted", label: "客户验收", type: "select" as const, options: [
                    { value: "false", label: "未验收" },
                    { value: "true", label: "已验收" },
                  ]},
                ]
              : [
                  { key: "planned_start_date", label: "计划开始", type: "date" as const },
                  { key: "planned_end_date", label: "计划结束", type: "date" as const },
                  { key: "remarks", label: "备注", placeholder: "备注信息" },
                ]),
            { key: "install_json", label: "安装步骤 (JSON)", type: "textarea" as const, placeholder: sampleInstallJson },
            { key: "comm_json", label: "调试清单 (JSON)", type: "textarea" as const, placeholder: sampleCommJson },
          ]}
          values={form}
          onChange={(key, value) => setForm((s) => ({ ...s, [key]: String(value) }))}
          onSubmit={() => void handleSave()}
          onCancel={closeForm}
          submitting={submitting}
          error={error}
          submitLabel={editId ? "保存修改" : "保存"}
        />
      ) : null}

      {/* Detail modal */}
      {showDetail && detail ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowDetail(false)}>
          <div className="max-h-[85vh] w-full max-w-3xl overflow-auto rounded-lg bg-[var(--color-surface)] p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">安装计划详情</h3>
              <button onClick={() => setShowDetail(false)} className="text-gray-400 hover:text-white text-xl">&times;</button>
            </div>

            <div className="grid grid-cols-3 gap-2 text-sm mb-4">
              <div><span className="text-gray-400">状态：</span><span className={STATUS_COLOR[String(detail.status ?? "")]}>{STATUS_LABEL[String(detail.status ?? "")]}</span></div>
              <div><span className="text-gray-400">计划开始：</span>{String(detail.planned_start_date ?? "-").slice(0, 10)}</div>
              <div><span className="text-gray-400">计划结束：</span>{String(detail.planned_end_date ?? "-").slice(0, 10)}</div>
              <div><span className="text-gray-400">实际开始：</span>{String(detail.actual_start_date ?? "-").slice(0, 10)}</div>
              <div><span className="text-gray-400">实际结束：</span>{String(detail.actual_end_date ?? "-").slice(0, 10)}</div>
              <div><span className="text-gray-400">客户验收：</span>
                {detail.customer_accepted ? (
                  <span className="text-emerald-400">已验收 ({String(detail.customer_accepted_date ?? "").slice(0, 10)})</span>
                ) : <span className="text-gray-400">未验收</span>}
              </div>
              {detail.customer_representative ? (
                <div><span className="text-gray-400">客户代表：</span>{String(detail.customer_representative)}</div>
              ) : null}
            </div>

            {/* Install steps */}
            <div className="mb-4">
              <h4 className="text-sm font-semibold mb-2">安装步骤</h4>
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[var(--color-border)] text-gray-400">
                    <th className="p-1 text-left w-12">步骤</th>
                    <th className="p-1 text-left">描述</th>
                    <th className="p-1 text-center w-14">完成</th>
                    <th className="p-1 text-left">备注</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.isArray(detail.install_items) && (detail.install_items as Record<string, unknown>[]).length > 0 ? (
                    (detail.install_items as Record<string, unknown>[]).map((item, i) => (
                      <tr key={i} className="border-b border-[var(--color-border)]">
                        <td className="p-1">{String(item.step ?? "")}</td>
                        <td className="p-1">{String(item.description ?? "")}</td>
                        <td className="p-1 text-center">
                          {item.completed ? <span className="text-emerald-400">✓</span> : <span className="text-gray-400">-</span>}
                        </td>
                        <td className="p-1">{String(item.remark ?? "")}</td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan={4} className="p-2 text-center text-gray-400">暂无安装步骤</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Commissioning items */}
            <div>
              <h4 className="text-sm font-semibold mb-2">调试清单</h4>
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[var(--color-border)] text-gray-400">
                    <th className="p-1 text-left">类别</th>
                    <th className="p-1 text-left">检查项</th>
                    <th className="p-1 text-left">期望值</th>
                    <th className="p-1 text-left">实测值</th>
                    <th className="p-1 text-center w-14">结果</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.isArray(detail.commissioning_items) && (detail.commissioning_items as Record<string, unknown>[]).length > 0 ? (
                    (detail.commissioning_items as Record<string, unknown>[]).map((item, i) => (
                      <tr key={i} className="border-b border-[var(--color-border)]">
                        <td className="p-1">{String(item.category ?? "")}</td>
                        <td className="p-1">{String(item.check_point ?? "")}</td>
                        <td className="p-1">{String(item.expected ?? "")}</td>
                        <td className="p-1">{String(item.actual_result ?? "")}</td>
                        <td className="p-1 text-center">
                          {item.pass ? <span className="text-emerald-400">PASS</span> : <span className="text-red-400">FAIL</span>}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan={5} className="p-2 text-center text-gray-400">暂无调试项</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}

      {/* Plan list */}
      <MasterListPage<PlanRow>
        embedded
        fill
        title="安装调试与验收"
        persistenceKey="installation-plans-v1"
        exportFilename="installation-plans"
        columns={[
          { key: "unitLabel", title: "设备", canView: true, fixed: "left", width: 80 },
          { key: "statusDisplay", title: "状态", canView: true, width: 80 },
          { key: "plannedStart", title: "计划开始", canView: true, width: 100 },
          { key: "plannedEnd", title: "计划结束", canView: true, width: 100 },
          { key: "actualStart", title: "实际开始", canView: true, width: 100 },
          { key: "actualEnd", title: "实际结束", canView: true, width: 100 },
          { key: "customerAcceptedDisplay", title: "客户验收", canView: true, width: 80 },
          { key: "installCount", title: "安装项", canView: true, width: 60 },
          { key: "commCount", title: "调试项", canView: true, width: 60 },
        ]}
        rows={planRows}
        total={planRows.length}
        page={1}
        onPageChange={() => {}}
        search=""
        onSearchChange={() => {}}
        query={{
          isLoading: plansQuery.isLoading,
          isError: plansQuery.isError,
          isFetching: plansQuery.isFetching,
          refetch: () => { void plansQuery.refetch(); },
        }}
        rowKey={(row) => row.id}
        rowActions={(row) => (
          <div className="flex items-center gap-1.5">
            <button type="button" className="text-xs text-violet-400 hover:underline" onClick={() => openDetail(row.id)}>
              查看
            </button>
            {row.status === "planned" ? (
              <button type="button" className="text-xs text-blue-400 hover:underline" onClick={() => handleQuickAction("start", row.id)}>
                开始
              </button>
            ) : null}
            {row.status === "in_progress" ? (
              <button type="button" className="text-xs text-emerald-400 hover:underline" onClick={() => handleQuickAction("complete", row.id)}>
                完成
              </button>
            ) : null}
            <button type="button" className="text-xs text-blue-400 hover:underline" onClick={() => {
              closeForm();
              setEditId(row.id);
              void fetchInstallationPlan(row.id).then((d) => {
                setForm({
                  planned_start_date: String(d.planned_start_date ?? "").slice(0, 10),
                  planned_end_date: String(d.planned_end_date ?? "").slice(0, 10),
                  remarks: String(d.remarks ?? ""),
                  install_json: JSON.stringify(d.install_items ?? [], null, 2),
                  comm_json: JSON.stringify(d.commissioning_items ?? [], null, 2),
                  status: String(d.status ?? ""),
                  customer_representative: String(d.customer_representative ?? ""),
                  customer_accepted: d.customer_accepted ? "true" : "false",
                });
                setShowForm(true);
              }).catch(() => {});
            }}>
              修改
            </button>
            <button type="button" className="text-xs text-red-400 hover:underline" onClick={() => void handleDelete(row.id)}>
              删除
            </button>
          </div>
        )}
        toolbarExtra={
          <div className="flex items-center gap-2">
            <select
              className={searchInputClass}
              value={selectedUnitId}
              onChange={(e) => handleUnitChange(e.target.value)}
            >
              <option value="">选择设备</option>
              {unitOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <WorkspaceToolbarButton
              onClick={() => {
                if (!selectedUnitId) { notify("请先选择设备"); return; }
                closeForm();
                setForm({
                  planned_start_date: "",
                  planned_end_date: "",
                  remarks: "",
                  install_json: sampleInstallJson,
                  comm_json: sampleCommJson,
                  status: "",
                  customer_representative: "",
                  customer_accepted: "false",
                });
                setShowForm(true);
              }}
              disabled={!selectedUnitId}
            >
              新增计划
            </WorkspaceToolbarButton>
          </div>
        }
        emptyHint={selectedUnitId ? "暂无安装计划，请点击「新增计划」创建" : "请先选择设备后管理安装计划"}
      />
    </IndustrialPage>
  );
}

function notify(title: string) {
  useToastStore.getState().push({ title });
}
