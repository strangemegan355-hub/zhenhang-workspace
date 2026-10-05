"use client";

import { apiErrorMessage } from "@/lib/api-error";

import { useState, useMemo, useEffect } from "react";
import { apiClient } from "@zhenhang/http-client";
import { MasterCreateForm } from "@/components/master/master-create-form";
import { MasterListPage } from "@/components/master/master-list-page";
import { IndustrialPage, WorkspaceToolbarButton } from "@zhenhang/ui";
import { searchInputClass } from "@/lib/form-styles";

// ── Types ──

type TemplateRow = {
  id: string;
  name: string;
  templateType: string;
  machineId: string;
  itemCount: number;
};

type RecordRow = {
  id: string;
  recordNo: string;
  inspectorName: string;
  testDate: string;
  status: string;
  overallResult: string;
  punchCount: number;
};

type PunchItem = {
  id: string;
  description: string;
  severity: string;
  status: string;
  resolution: string;
  resolved_at: string;
};

// ── Status helpers ──

const STATUS_LABEL: Record<string, string> = {
  in_progress: "进行中",
  passed: "已通过",
  failed: "未通过",
};

const STATUS_COLOR: Record<string, string> = {
  in_progress: "text-blue-400",
  passed: "text-emerald-400",
  failed: "text-red-400",
};

const SEVERITY_LABEL: Record<string, string> = {
  minor: "轻微",
  major: "严重",
  critical: "致命",
};

// ── Page ──

export default function AcceptancePage() {
  // Machine / unit selectors
  const [selectedMachineId, setSelectedMachineId] = useState("");
  const [selectedUnitId, setSelectedUnitId] = useState("");
  const [machineOptions, setMachineOptions] = useState<Array<{ value: string; label: string }>>([]);
  const [unitOptions, setUnitOptions] = useState<Array<{ value: string; label: string }>>([]);

  // Templates
  const [templates, setTemplates] = useState<TemplateRow[]>([]);
  const [tplLoading, setTplLoading] = useState(false);
  const [showTplForm, setShowTplForm] = useState(false);
  const [tplEditId, setTplEditId] = useState<string | null>(null);
  const [tplForm, setTplForm] = useState({ name: "", template_type: "fat", items_json: "[]" });
  const [tplError, setTplError] = useState<string | null>(null);

  // Records
  const [records, setRecords] = useState<RecordRow[]>([]);
  const [recLoading, setRecLoading] = useState(false);
  const [showRecForm, setShowRecForm] = useState(false);
  const [recEditId, setRecEditId] = useState<string | null>(null);
  const [recForm, setRecForm] = useState({
    template_id: "",
    inspector_name: "",
    test_date: new Date().toISOString().slice(0, 10),
    remarks: "",
    items_json: "[]",
    status: "",
    overall_result: "",
  });
  const [recError, setRecError] = useState<string | null>(null);

  // Detail modal
  const [detailRecord, setDetailRecord] = useState<Record<string, unknown> | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  const [punchItems, setPunchItems] = useState<PunchItem[]>([]);
  const [punchDesc, setPunchDesc] = useState("");
  const [punchSeverity, setPunchSeverity] = useState("minor");

  const [submitting, setSubmitting] = useState(false);

  // ── Templates ──

  async function loadTemplates(machineId: string) {
    setTplLoading(true);
    try {
      const { data: resp } = await apiClient.get<{ data: Array<Record<string, unknown>> }>(
        `/api/v1/machines/${machineId}/acceptance-templates`
      );
      const rows: TemplateRow[] = (resp.data ?? []).map((t: Record<string, unknown>) => ({
        id: String(t.id ?? ""),
        name: String(t.name ?? ""),
        templateType: String(t.template_type ?? ""),
        machineId: String(t.machine_id ?? ""),
        itemCount: Array.isArray(t.items) ? (t.items as unknown[]).length : 0,
      }));
      setTemplates(rows);
    } catch {
      setTemplates([]);
    } finally {
      setTplLoading(false);
    }
  }

  function handleMachineChange(id: string) {
    setSelectedMachineId(id);
    closeTplForm();
    if (id) loadTemplates(id);
    else setTemplates([]);
  }

  function closeTplForm() {
    setShowTplForm(false);
    setTplEditId(null);
    setTplError(null);
  }

  async function handleSaveTemplate() {
    setTplError(null);
    if (!tplForm.name.trim()) { setTplError("请填写模板名称"); return; }
    let items;
    try { items = JSON.parse(tplForm.items_json); } catch { setTplError("检查项 JSON 格式错误"); return; }
    setSubmitting(true);
    const body = { name: tplForm.name.trim(), template_type: tplForm.template_type, items };
    try {
      if (tplEditId) {
        await apiClient.put(`/api/v1/acceptance-templates/${tplEditId}`, body);
      } else {
        await apiClient.post(`/api/v1/machines/${selectedMachineId}/acceptance-templates`, body);
      }
      closeTplForm();
      await loadTemplates(selectedMachineId);
    } catch (err) {
      setTplError(apiErrorMessage(err, "保存失败"));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteTemplate(id: string, label: string) {
    if (!window.confirm(`确认删除模板「${label}」？`)) return;
    try {
      await apiClient.delete(`/api/v1/acceptance-templates/${id}`);
      await loadTemplates(selectedMachineId);
    } catch (err) {
      window.alert(apiErrorMessage(err, "删除失败"));
    }
  }

  // ── Records ──

  async function loadRecords(unitId: string) {
    setRecLoading(true);
    try {
      const { data: resp } = await apiClient.get<{ data: Array<Record<string, unknown>> }>(
        `/api/v1/equipment-units/${unitId}/acceptance-records`
      );
      const rows: RecordRow[] = (resp.data ?? []).map((r: Record<string, unknown>) => ({
        id: String(r.id ?? ""),
        recordNo: String(r.record_no ?? ""),
        inspectorName: String(r.inspector_name ?? ""),
        testDate: String(r.test_date ?? "").slice(0, 10),
        status: STATUS_LABEL[String(r.status ?? "")] ?? String(r.status ?? ""),
        overallResult: String(r.overall_result ?? "-"),
        punchCount: Array.isArray(r.punch_items) ? (r.punch_items as unknown[]).length : 0,
      }));
      setRecords(rows);
    } catch {
      setRecords([]);
    } finally {
      setRecLoading(false);
    }
  }

  function handleUnitChange(id: string) {
    setSelectedUnitId(id);
    closeRecForm();
    if (id) loadRecords(id);
    else setRecords([]);
  }

  function closeRecForm() {
    setShowRecForm(false);
    setRecEditId(null);
    setRecError(null);
  }

  async function handleSaveRecord() {
    setRecError(null);
    if (!recForm.template_id) { setRecError("请选择验收模板"); return; }
    if (!recForm.inspector_name.trim()) { setRecError("请填写检验人"); return; }
    let items;
    try { items = JSON.parse(recForm.items_json); } catch { setRecError("检验结果 JSON 格式错误"); return; }
    setSubmitting(true);
    const body: Record<string, unknown> = {
      template_id: recForm.template_id,
      test_date: new Date(recForm.test_date).toISOString(),
      inspector_name: recForm.inspector_name.trim(),
      items,
      remarks: recForm.remarks || null,
    };
    try {
      if (recEditId) {
        const updateBody: Record<string, unknown> = { items };
        if (recForm.status) updateBody.status = recForm.status;
        if (recForm.overall_result) updateBody.overall_result = recForm.overall_result;
        await apiClient.put(`/api/v1/acceptance-records/${recEditId}`, updateBody);
      } else {
        await apiClient.post(`/api/v1/equipment-units/${selectedUnitId}/acceptance-records`, body);
      }
      closeRecForm();
      await loadRecords(selectedUnitId);
    } catch (err) {
      setRecError(apiErrorMessage(err, "保存失败"));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteRecord(id: string, label: string) {
    if (!window.confirm(`确认删除记录「${label}」？`)) return;
    try {
      await apiClient.delete(`/api/v1/acceptance-records/${id}`);
      await loadRecords(selectedUnitId);
    } catch (err) {
      window.alert(apiErrorMessage(err, "删除失败"));
    }
  }

  // ── Detail modal & punch items ──

  async function openDetail(recordId: string, focusPunch?: boolean) {
    try {
      const { data: resp } = await apiClient.get<{ data: Record<string, unknown> }>(
        `/api/v1/acceptance-records/${recordId}`
      );
      const data = resp.data as Record<string, unknown>;
      setDetailRecord(data);
      setPunchItems((Array.isArray(data?.punch_items) ? data.punch_items : []) as PunchItem[]);
      setShowDetail(true);
    } catch { /* ignore */ }
  }

  async function handleAddPunch() {
    if (!punchDesc.trim() || !detailRecord) return;
    setSubmitting(true);
    try {
      await apiClient.post(`/api/v1/acceptance-records/${detailRecord.id}/punch-items`, {
        description: punchDesc.trim(),
        severity: punchSeverity,
      });
      setPunchDesc("");
      setPunchSeverity("minor");
      // Reload
      const { data: resp } = await apiClient.get<{ data: Record<string, unknown> }>(
        `/api/v1/acceptance-records/${detailRecord.id}`
      );
      const data = resp.data as Record<string, unknown>;
      setDetailRecord(data);
      setPunchItems((Array.isArray(data?.punch_items) ? data.punch_items : []) as PunchItem[]);
      await loadRecords(selectedUnitId);
    } catch (err) {
      window.alert(apiErrorMessage(err, "添加失败"));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResolvePunch(itemId: string) {
    const resolution = window.prompt("整改措施/说明：");
    if (resolution === null) return;
    try {
      await apiClient.put(`/api/v1/punch-items/${itemId}`, {
        status: "resolved",
        resolution: resolution || undefined,
      });
      if (detailRecord) await openDetail(String(detailRecord.id));
      await loadRecords(selectedUnitId);
    } catch (err) {
      window.alert(apiErrorMessage(err, "操作失败"));
    }
  }

  async function handleDeletePunch(itemId: string) {
    if (!window.confirm("确认删除此整改项？")) return;
    try {
      await apiClient.delete(`/api/v1/punch-items/${itemId}`);
      if (detailRecord) await openDetail(String(detailRecord.id));
      await loadRecords(selectedUnitId);
    } catch (err) {
      window.alert(apiErrorMessage(err, "删除失败"));
    }
  }

  // ── Init ──

  useEffect(() => {
    let ignore = false;
    async function init() {
      try {
        const { data: resp } = await apiClient.get<{ data: { items: Array<Record<string, unknown>> } }>(
          "/api/v1/machines?page=1&page_size=200"
        );
        if (!ignore) {
          const items = resp.data?.items ?? [];
          setMachineOptions(
            items.map((m: Record<string, unknown>) => ({
              value: String(m.id ?? ""),
              label: `${String(m.machine_code ?? "")} ${String(m.name ?? "")}`,
            }))
          );
        }
      } catch { /* ignore */ }
      try {
        const { data: resp } = await apiClient.get<{ data: { items: Array<Record<string, unknown>> } }>(
          "/api/v1/equipment-units?page=1&page_size=200"
        );
        if (!ignore) {
          const items = resp.data?.items ?? [];
          setUnitOptions(
            items.map((u: Record<string, unknown>) => ({
              value: String(u.id ?? ""),
              label: `${String(u.serial_number ?? "")} (${String(u.machine_name ?? "")})`,
            }))
          );
        }
      } catch { /* ignore */ }
    }
    init();
    return () => { ignore = true; };
  }, []);

  // ── Data ──

  const tplRows = useMemo(() => templates, [templates]);
  const recRows = useMemo(() => records, [records]);

  const sampleItemsJson = JSON.stringify([
    { category: "机械系统", check_point: "检查项名称", standard: "验收标准", method: "检验方法" },
  ], null, 2);

  const sampleResultJson = JSON.stringify([
    { category: "机械系统", check_point: "检查项名称", standard: "验收标准", actual_result: "实测结果", pass: true, remark: "" },
  ], null, 2);

  return (
    <IndustrialPage gap="md" fill>
      {/* Template form */}
      {showTplForm ? (
        <MasterCreateForm
          title={tplEditId ? "修改验收模板" : "新增验收模板"}
          fields={[
            { key: "name", label: "模板名称", required: true, placeholder: "如 FAT标准验收" },
            {
              key: "template_type",
              label: "类型",
              type: "select",
              options: [
                { value: "fat", label: "FAT (出厂验收)" },
                { value: "sat", label: "SAT (现场验收)" },
              ],
            },
            {
              key: "items_json",
              label: "检查项 (JSON)",
              type: "textarea",
              placeholder: sampleItemsJson,
            },
          ]}
          values={tplForm}
          onChange={(key, value) => setTplForm((s) => ({ ...s, [key]: String(value) }))}
          onSubmit={() => void handleSaveTemplate()}
          onCancel={closeTplForm}
          submitting={submitting}
          error={tplError}
          submitLabel={tplEditId ? "保存修改" : "保存"}
        />
      ) : null}

      {/* Record form */}
      {showRecForm ? (
        <MasterCreateForm
          title={recEditId ? "修改验收记录" : "新增验收记录"}
          fields={[
            ...(recEditId
              ? [
                  { key: "status", label: "状态", type: "select" as const, options: [
                    { value: "in_progress", label: "进行中" },
                    { value: "passed", label: "已通过" },
                    { value: "failed", label: "未通过" },
                  ]},
                  { key: "overall_result", label: "总体结论", placeholder: "如：所有检验项通过" },
                ]
              : [
                  {
                    key: "template_id",
                    label: "验收模板",
                    type: "select" as const,
                    options: tplRows.map((t) => ({ value: t.id, label: `${t.name} (${t.templateType.toUpperCase()})` })),
                    required: true,
                  },
                  { key: "inspector_name", label: "检验人", required: true, placeholder: "检验人姓名" },
                  { key: "test_date", label: "检验日期", placeholder: "YYYY-MM-DD" },
                  { key: "remarks", label: "备注", placeholder: "备注信息" },
                ]),
            {
              key: "items_json",
              label: "检验结果 (JSON)",
              type: "textarea",
              placeholder: sampleResultJson,
            },
          ]}
          values={recForm}
          onChange={(key, value) => setRecForm((s) => ({ ...s, [key]: String(value) }))}
          onSubmit={() => void handleSaveRecord()}
          onCancel={closeRecForm}
          submitting={submitting}
          error={recError}
          submitLabel={recEditId ? "保存修改" : "保存"}
        />
      ) : null}

      {/* Detail modal with punch list */}
      {showDetail && detailRecord ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowDetail(false)}>
          <div className="max-h-[85vh] w-full max-w-3xl overflow-auto rounded-lg bg-[var(--color-surface)] p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">验收记录详情</h3>
              <button onClick={() => setShowDetail(false)} className="text-gray-400 hover:text-white text-xl leading-none">&times;</button>
            </div>

            {/* Meta */}
            <div className="grid grid-cols-2 gap-2 text-sm mb-4">
              <div><span className="text-gray-400">编号：</span>{String(detailRecord.record_no ?? "-")}</div>
              <div><span className="text-gray-400">检验人：</span>{String(detailRecord.inspector_name ?? "-")}</div>
              <div><span className="text-gray-400">日期：</span>{String(detailRecord.test_date ?? "-").slice(0, 10)}</div>
              <div><span className="text-gray-400">状态：</span>
                <span className={STATUS_COLOR[String(detailRecord.status ?? "")] ?? ""}>
                  {STATUS_LABEL[String(detailRecord.status ?? "")] ?? String(detailRecord.status ?? "-")}
                </span>
              </div>
              {detailRecord.overall_result ? (
                <div className="col-span-2"><span className="text-gray-400">总体结论：</span>{String(detailRecord.overall_result)}</div>
              ) : null}
            </div>

            {/* Inspection items */}
            <div className="mb-4">
              <h4 className="text-sm font-semibold mb-2">检验明细</h4>
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[var(--color-border)] text-gray-400">
                    <th className="p-1 text-left">类别</th>
                    <th className="p-1 text-left">检查项</th>
                    <th className="p-1 text-left">标准</th>
                    <th className="p-1 text-left">实测</th>
                    <th className="p-1 text-center">结果</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.isArray(detailRecord.items) ? (detailRecord.items as Record<string, unknown>[]).map((item, i) => (
                    <tr key={i} className="border-b border-[var(--color-border)]">
                      <td className="p-1">{String(item.category ?? "")}</td>
                      <td className="p-1">{String(item.check_point ?? "")}</td>
                      <td className="p-1">{String(item.standard ?? "")}</td>
                      <td className="p-1">{String(item.actual_result ?? "")}</td>
                      <td className="p-1 text-center">
                        {item.pass || item.pass_ ? (
                          <span className="text-emerald-400">PASS</span>
                        ) : (
                          <span className="text-red-400">FAIL</span>
                        )}
                      </td>
                    </tr>
                  )) : (
                    <tr><td colSpan={5} className="p-2 text-center text-gray-400">暂无检验明细</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Punch list */}
            <div>
              <h4 className="text-sm font-semibold mb-2">整改清单 (Punch List)</h4>
              <div className="flex items-center gap-2 mb-2">
                <input
                  className={searchInputClass + " flex-1"}
                  placeholder="新增整改项描述..."
                  value={punchDesc}
                  onChange={(e) => setPunchDesc(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleAddPunch(); }}
                />
                <select
                  className="h-8 rounded border border-[var(--color-border)] bg-[var(--color-surface-soft)] px-2 text-xs"
                  value={punchSeverity}
                  onChange={(e) => setPunchSeverity(e.target.value)}
                >
                  <option value="minor">轻微</option>
                  <option value="major">严重</option>
                  <option value="critical">致命</option>
                </select>
                <WorkspaceToolbarButton onClick={() => void handleAddPunch()} disabled={submitting}>
                  添加
                </WorkspaceToolbarButton>
              </div>
              {punchItems.length === 0 ? (
                <p className="text-xs text-gray-400">暂无整改项</p>
              ) : (
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--color-border)] text-gray-400">
                      <th className="p-1 text-left">描述</th>
                      <th className="p-1 text-left w-14">严重度</th>
                      <th className="p-1 text-left w-14">状态</th>
                      <th className="p-1 text-left">措施</th>
                      <th className="p-1 text-right w-20">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {punchItems.map((p) => (
                      <tr key={p.id} className="border-b border-[var(--color-border)]">
                        <td className="p-1">{p.description}</td>
                        <td className="p-1">{SEVERITY_LABEL[p.severity] ?? p.severity}</td>
                        <td className="p-1">
                          <span className={p.status === "resolved" ? "text-emerald-400" : "text-amber-400"}>
                            {p.status === "resolved" ? "已解决" : "待处理"}
                          </span>
                        </td>
                        <td className="p-1 max-w-[200px] truncate">{p.resolution ?? "-"}</td>
                        <td className="p-1 text-right">
                          {p.status !== "resolved" ? (
                            <button type="button" className="text-xs text-emerald-400 hover:underline mr-2" onClick={() => handleResolvePunch(p.id)}>
                              解决
                            </button>
                          ) : null}
                          <button type="button" className="text-xs text-red-400 hover:underline" onClick={() => void handleDeletePunch(p.id)}>
                            删除
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      ) : null}

      {/* ── Template section ── */}
      <MasterListPage<TemplateRow>
        embedded
        fill
        title="验收模板"
        persistenceKey="acceptance-templates-v1"
        exportFilename="acceptance-templates"
        columns={[
          { key: "name", title: "模板名称", canView: true, fixed: "left", width: 180 },
          { key: "templateType", title: "类型", canView: true, width: 80 },
          { key: "itemCount", title: "检查项数", canView: true, width: 80 },
        ]}
        rows={tplRows}
        total={tplRows.length}
        page={1}
        onPageChange={() => {}}
        search=""
        onSearchChange={() => {}}
        query={{
          isLoading: tplLoading,
          isError: false,
          isFetching: tplLoading,
          refetch: () => { if (selectedMachineId) loadTemplates(selectedMachineId); },
        }}
        rowKey={(row) => row.id}
        rowActions={(row) => (
          <div className="flex items-center gap-2">
            <button type="button" className="text-xs text-blue-400 hover:underline" onClick={() => {
              closeTplForm();
              setTplEditId(row.id);
              apiClient.get(`/api/v1/acceptance-templates/${row.id}`).then(({ data: resp }) => {
                const d = resp.data as Record<string, unknown>;
                setTplForm({
                  name: String(d.name ?? ""),
                  template_type: String(d.template_type ?? "fat"),
                  items_json: JSON.stringify(d.items ?? [], null, 2),
                });
                setShowTplForm(true);
              }).catch(() => {});
            }}>
              修改
            </button>
            <button type="button" className="text-xs text-red-400 hover:underline" onClick={() => void handleDeleteTemplate(row.id, row.name)}>
              删除
            </button>
          </div>
        )}
        toolbarExtra={
          <div className="flex items-center gap-2">
            <select
              className={searchInputClass}
              value={selectedMachineId}
              onChange={(e) => handleMachineChange(e.target.value)}
            >
              <option value="">选择机型</option>
              {machineOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <WorkspaceToolbarButton
              onClick={() => {
                if (!selectedMachineId) { window.alert("请先选择机型"); return; }
                closeTplForm();
                setTplForm({ name: "", template_type: "fat", items_json: sampleItemsJson });
                setShowTplForm(true);
              }}
              disabled={!selectedMachineId}
            >
              新增模板
            </WorkspaceToolbarButton>
          </div>
        }
        emptyHint={selectedMachineId ? "暂无验收模板，请点击「新增模板」添加" : "请先选择机型后管理验收模板"}
      />

      {/* ── Record section ── */}
      <MasterListPage<RecordRow>
        embedded
        fill
        title="验收记录"
        persistenceKey="acceptance-records-v1"
        exportFilename="acceptance-records"
        columns={[
          { key: "recordNo", title: "编号", canView: true, fixed: "left", width: 170 },
          { key: "inspectorName", title: "检验人", canView: true, width: 100 },
          { key: "testDate", title: "日期", canView: true, width: 110 },
          { key: "status", title: "状态", canView: true, width: 80 },
          { key: "punchCount", title: "整改项", canView: true, width: 70 },
        ]}
        rows={recRows}
        total={recRows.length}
        page={1}
        onPageChange={() => {}}
        search=""
        onSearchChange={() => {}}
        query={{
          isLoading: recLoading,
          isError: false,
          isFetching: recLoading,
          refetch: () => { if (selectedUnitId) loadRecords(selectedUnitId); },
        }}
        rowKey={(row) => row.id}
        rowActions={(row) => (
          <div className="flex items-center gap-1.5">
            <button type="button" className="text-xs text-violet-400 hover:underline" onClick={() => openDetail(row.id)}>
              查看
            </button>
            <button type="button" className="text-xs text-blue-400 hover:underline" onClick={() => {
              closeRecForm();
              setRecEditId(row.id);
              apiClient.get(`/api/v1/acceptance-records/${row.id}`).then(({ data: resp }) => {
                const d = resp.data as Record<string, unknown>;
                setRecForm({
                  template_id: String(d.template_id ?? ""),
                  inspector_name: String(d.inspector_name ?? ""),
                  test_date: String(d.test_date ?? "").slice(0, 10),
                  remarks: String(d.remarks ?? ""),
                  items_json: JSON.stringify(d.items ?? [], null, 2),
                  status: String(d.status ?? ""),
                  overall_result: String(d.overall_result ?? ""),
                });
                setShowRecForm(true);
              }).catch(() => {});
            }}>
              修改
            </button>
            <button type="button" className="text-xs text-red-400 hover:underline" onClick={() => void handleDeleteRecord(row.id, row.recordNo)}>
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
                if (!selectedUnitId) { window.alert("请先选择设备"); return; }
                closeRecForm();
                setRecForm({
                  template_id: "",
                  inspector_name: "",
                  test_date: new Date().toISOString().slice(0, 10),
                  remarks: "",
                  items_json: sampleResultJson,
                  status: "",
                  overall_result: "",
                });
                setShowRecForm(true);
              }}
              disabled={!selectedUnitId}
            >
              新增记录
            </WorkspaceToolbarButton>
          </div>
        }
        emptyHint={selectedUnitId ? "暂无验收记录，请点击「新增记录」创建" : "请先选择设备后查看验收记录"}
      />
    </IndustrialPage>
  );
}
