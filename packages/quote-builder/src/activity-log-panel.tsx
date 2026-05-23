"use client";

const MOCK_LOGS = [
  { id: "1", at: "10:32:01", actor: "系统", action: "加载报价版本 V2", level: "info" },
  { id: "2", at: "10:28:44", actor: "张三", action: "保存行项目变更 (12 行)", level: "info" },
  { id: "3", at: "10:15:02", actor: "李四", action: "提交审批 · reviewing", level: "warn" },
  { id: "4", at: "09:58:11", actor: "系统", action: "BOM 成本快照同步", level: "info" },
  { id: "5", at: "09:40:00", actor: "王五", action: "导出 PDF 任务排队", level: "info" },
];

const LEVEL_COLOR: Record<string, string> = {
  info: "#94A3B8",
  warn: "#F59E0B",
  error: "#EF4444",
};

export function ActivityLogPanel() {
  return (
    <ul className="space-y-1 font-mono text-xs">
      {MOCK_LOGS.map((row) => (
        <li
          key={row.id}
          className="flex gap-3 rounded border border-[#334155] px-2 py-1.5"
          style={{ backgroundColor: "#111827" }}
        >
          <span className="shrink-0 text-[#64748B]">{row.at}</span>
          <span className="shrink-0 text-[#CBD5E1]">{row.actor}</span>
          <span className="min-w-0 flex-1 truncate" style={{ color: LEVEL_COLOR[row.level] ?? "#CBD5E1" }}>
            {row.action}
          </span>
        </li>
      ))}
    </ul>
  );
}
