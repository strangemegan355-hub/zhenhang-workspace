"use client";

import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import {
  useAdvanceEquipmentStatusMutation,
  useCreateEquipmentUnitMutation,
  useEquipmentUnitsQuery,
  useEquipmentUnitDetailQuery,
  useUpdateEquipmentUnitMutation,
  useMachinesQuery,
  useCustomersQuery,
} from "@zhenhang/query-hooks";
import { IndustrialPage, WorkspaceToolbarButton } from "@zhenhang/ui";
import { useMemo, useState } from "react";

type UnitRow = {
  id: string;
  serialNumber: string;
  machineName: string;
  buildStatus: string;
  buildStatusDisplay: string;
  customerName: string;
  buildStartDate: string;
  shipDate: string;
  installDate: string;
  remarks: string;
};

const BUILD_STATUS_LABEL: Record<string, string> = {
  in_production: "生产中",
  in_stock: "已入库",
  shipped: "已发货",
  installed: "已安装",
  running: "运行中",
  under_maintenance: "维修中",
  decommissioned: "已报废",
};

const BUILD_STATUS_COLOR: Record<string, string> = {
  in_production: "text-blue-400",
  in_stock: "text-emerald-400",
  shipped: "text-amber-400",
  installed: "text-violet-400",
  running: "text-green-500",
  under_maintenance: "text-orange-400",
  decommissioned: "text-red-400",
};

const BUILD_STATUS_OPTIONS = Object.entries(BUILD_STATUS_LABEL).map(([value, label]) => ({
  value,
  label,
}));

const VALID_TRANSITIONS: Record<string, string[]> = {
  in_production: ["in_stock"],
  in_stock: ["shipped"],
  shipped: ["installed"],
  installed: ["running", "under_maintenance"],
  running: ["under_maintenance", "decommissioned"],
  under_maintenance: ["running", "decommissioned"],
  decommissioned: [],
};

const INITIAL_CREATE_FORM = {
  serial_number: "",
  machine_id: "",
  build_status: "in_production",
  build_start_date: "",
  remarks: "",
};

export default function EquipmentUnitsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [machineFilter, setMachineFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [createForm, setCreateForm] = useState(INITIAL_CREATE_FORM);
  const [error, setError] = useState<string | null>(null);
  const [advancing, setAdvancing] = useState<string | null>(null);

  const unitsQuery = useEquipmentUnitsQuery(
    page,
    20,
    search.trim() || undefined,
    statusFilter || undefined,
    machineFilter || undefined,
  );
  const editQuery = useEquipmentUnitDetailQuery(editId ?? "");
  const createMut = useCreateEquipmentUnitMutation();
  const updateMut = useUpdateEquipmentUnitMutation();
  const advanceMut = useAdvanceEquipmentStatusMutation();
  const machinesQuery = useMachinesQuery(1);
  const customersQuery = useCustomersQuery(1);

  const unitData = (unitsQuery.data as { items?: Record<string, unknown>[]; total?: number } | undefined) ?? {};
  const machineItems = (machinesQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? [];
  const customerItems = (customersQuery.data as { items?: Record<string, unknown>[] } | undefined)?.items ?? [];

  const machineOptions = useMemo(
    () =>
      machineItems.map((m) => ({
        value: String(m.id ?? ""),
        label: `${String(m.machine_code ?? "")} ${String(m.name ?? "")}`,
      })),
    [machineItems],
  );

  const rows: UnitRow[] = useMemo(
    () =>
      ((unitData.items ?? []) as Record<string, unknown>[]).map((row) => {
        const rawStatus = String(row.build_status ?? "");
        return {
          id: String(row.id ?? ""),
          serialNumber: String(row.serial_number ?? ""),
          machineName: String(row.machine_name ?? row.machine_code ?? "-"),
          buildStatus: rawStatus,
          buildStatusDisplay: BUILD_STATUS_LABEL[rawStatus] ?? rawStatus,
          customerName: String(row.customer_name ?? "-"),
          buildStartDate: row.build_start_date ? String(row.build_start_date) : "-",
          shipDate: row.ship_date ? String(row.ship_date) : "-",
          installDate: row.install_date ? String(row.install_date) : "-",
          remarks: String(row.remarks ?? ""),
        };
      }),
    [unitData.items],
  );

  const closeForm = () => {
    setShowCreate(false);
    setEditId(null);
    setError(null);
    setCreateForm(INITIAL_CREATE_FORM);
  };

  const handleCreate = async () => {
    setError(null);
    if (!createForm.serial_number.trim() || !createForm.machine_id) {
      setError("请填写序列号和选择机型");
      return;
    }
    const body: Record<string, unknown> = {
      serial_number: createForm.serial_number.trim(),
      machine_id: createForm.machine_id,
      build_status: createForm.build_status || "in_production",
      build_start_date: createForm.build_start_date || null,
      remarks: createForm.remarks.trim() || null,
    };
    try {
      await createMut.mutateAsync(body);
      closeForm();
      void unitsQuery.refetch();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
    }
  };

  const handleSaveEdit = async () => {
    if (!editId) return;
    setError(null);
    const body: Record<string, unknown> = {};
    if (createForm.serial_number) body.serial_number = createForm.serial_number.trim();
    if (createForm.machine_id) body.machine_id = createForm.machine_id;
    if (createForm.remarks !== undefined) body.remarks = createForm.remarks.trim() || null;
    try {
      await updateMut.mutateAsync({ id: editId, body });
      closeForm();
      void unitsQuery.refetch();
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新失败");
    }
  };

  const handleAdvance = async (unitId: string, unitRow: UnitRow, newStatus: string) => {
    const fromLabel = BUILD_STATUS_LABEL[unitRow.buildStatus] ?? unitRow.buildStatus;
    const toLabel = BUILD_STATUS_LABEL[newStatus] ?? newStatus;
    if (!window.confirm(`确认将 ${unitRow.serialNumber} 从「${fromLabel}」变更为「${toLabel}」？`)) return;
    setAdvancing(unitId);
    try {
      await advanceMut.mutateAsync({ id: unitId, newStatus });
      void unitsQuery.refetch();
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "状态变更失败");
    } finally {
      setAdvancing(null);
    }
  };

  const openEdit = (row: UnitRow) => {
    setEditId(row.id);
    setCreateForm({
      serial_number: row.serialNumber,
      machine_id: "",
      build_status: row.buildStatus,
      build_start_date: "",
      remarks: row.remarks,
    });
    setShowCreate(true);
  };

  const machineSelectOptionsForForm = useMemo(
    () => (editId ? machineOptions : machineOptions),
    [machineOptions, editId],
  );

  return (
    <IndustrialPage gap="md" fill>
      {showCreate ? (
        <MasterCreateForm
          title={editId ? "修改设备信息" : "新增设备序列号"}
          fields={[
            {
              key: "serial_number",
              label: "设备序列号",
              required: true,
              placeholder: "如 ZH-2026-0012",
            },
            ...(editId
              ? []
              : [
                  {
                    key: "machine_id" as string,
                    label: "所属机型",
                    type: "select" as const,
                    options: machineSelectOptionsForForm,
                    required: true,
                  },
                  {
                    key: "build_start_date" as string,
                    label: "生产开始日期",
                    placeholder: "YYYY-MM-DD",
                  },
                ]),
            {
              key: "remarks",
              label: "备注",
              placeholder: "备注信息",
            },
          ]}
          values={createForm}
          onChange={(key, value) => setCreateForm((s) => ({ ...s, [key]: String(value) }))}
          onSubmit={editId ? () => void handleSaveEdit() : () => void handleCreate()}
          onCancel={closeForm}
          submitting={createMut.isPending || updateMut.isPending}
          error={error}
          submitLabel={editId ? "保存修改" : "创建"}
        />
      ) : null}

      <MasterListPage<UnitRow>
        fill
        title="设备序列号"
        persistenceKey="equipment-units-v1"
        exportFilename="equipment-units"
        columns={[
          { key: "serialNumber", title: "序列号", canView: true, fixed: "left", width: 160 },
          { key: "machineName", title: "机型", canView: true, width: 160 },
          { key: "buildStatusDisplay", title: "状态", canView: true, width: 100 },
          { key: "customerName", title: "客户", canView: true, width: 120 },
          { key: "buildStartDate", title: "生产开始", canView: true },
          { key: "remarks", title: "备注", canView: true },
        ]}
        rows={rows}
        total={unitData.total ?? rows.length}
        page={page}
        onPageChange={setPage}
        search={search}
        onSearchChange={setSearch}
        query={unitsQuery}
        rowKey={(row) => row.id}
        rowActions={(row) => {
          const transitions = VALID_TRANSITIONS[row.buildStatus] ?? [];
          return (
            <div className="flex items-center gap-1.5">
              {transitions.map((nextStatus) => (
                <button
                  key={nextStatus}
                  type="button"
                  disabled={advancing === row.id}
                  className="text-xs text-emerald-400 hover:underline disabled:opacity-50"
                  onClick={() => void handleAdvance(row.id, row, nextStatus)}
                >
                  {BUILD_STATUS_LABEL[nextStatus] ?? nextStatus}
                </button>
              ))}
              <button
                type="button"
                className="text-xs text-blue-400 hover:underline"
                onClick={() => openEdit(row)}
              >
                修改
              </button>
            </div>
          );
        }}
        toolbarExtra={
          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="h-8 rounded border border-[var(--color-border)] bg-[var(--color-surface-soft)] px-2 text-xs"
            >
              <option value="">全部状态</option>
              {BUILD_STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <WorkspaceToolbarButton onClick={() => { closeForm(); setShowCreate(true); }}>
              新增序列号
            </WorkspaceToolbarButton>
          </div>
        }
        emptyHint="录入每台整机的唯一序列号，追踪从生产、发货、安装到售后全生命周期。"
      />
    </IndustrialPage>
  );
}
