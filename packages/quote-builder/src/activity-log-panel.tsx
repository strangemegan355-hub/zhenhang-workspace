"use client";

export type ActivityLogEntry = {
  id?: string;
  at: string;
  actor: string;
  action: string;
  comment?: string;
  level?: "info" | "warn" | "error";
};

const LEVEL_COLOR: Record<string, string> = {
  info: "#94A3B8",
  warn: "#F59E0B",
  error: "#EF4444",
};

/**
 * The quote workbench's activity log: the approval records handed to it, which are real events with
 * real timestamps. This panel used to hard-code five fictional rows and render them unconditionally,
 * so the tab presented invented activity as fact.
 */
export function ActivityLogPanel({ entries = [] }: { entries?: ActivityLogEntry[] }) {
  if (entries.length === 0) {
    return (
      <p
        className="rounded border border-[#334155] px-3 py-6 text-center text-xs"
        style={{ backgroundColor: "#111827", color: "#64748B" }}
      >
        暂无活动记录
      </p>
    );
  }

  return (
    <ul className="space-y-1 font-mono text-xs">
      {entries.map((row, index) => (
        <li
          key={row.id ?? `${row.at}-${index}`}
          className="flex gap-3 rounded border border-[#334155] px-2 py-1.5"
          style={{ backgroundColor: "#111827" }}
        >
          <span className="shrink-0 text-[#64748B]">{row.at}</span>
          <span className="shrink-0 text-[#CBD5E1]">{row.actor}</span>
          <span
            className="min-w-0 flex-1 truncate"
            style={{ color: LEVEL_COLOR[row.level ?? "info"] ?? "#CBD5E1" }}
          >
            {row.action}
            {row.comment ? ` · ${row.comment}` : ""}
          </span>
        </li>
      ))}
    </ul>
  );
}
