"use client";

import * as React from "react";

const STEPS = [
  "选择报价单",
  "BOM 导入 → 调价",
  "查看行内公式与成本图",
  "保存版本",
  "审批 / 导出",
];

export function DemoGuideStrip({ onDismiss }: { onDismiss?: () => void }) {
  const [open, setOpen] = React.useState(true);
  if (!open) return null;
  return (
    <div className="rounded-lg border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 px-4 py-3 dark:border-amber-900 dark:from-amber-950/40 dark:to-orange-950/30">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-semibold text-amber-900 dark:text-amber-200">演示模式 · 5 步完成工业报价闭环</span>
        <button
          type="button"
          className="text-xs text-amber-700 hover:underline"
          onClick={() => {
            setOpen(false);
            onDismiss?.();
          }}
        >
          关闭
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {STEPS.map((s, i) => (
          <span
            key={s}
            className="inline-flex items-center gap-1 rounded-full border border-amber-300/60 bg-white/80 px-2.5 py-1 text-xs font-medium text-amber-900 dark:bg-zinc-900/50 dark:text-amber-100"
          >
            <span className="flex h-4 w-4 items-center justify-center rounded-full bg-amber-500 text-[10px] text-white">
              {i + 1}
            </span>
            {s}
          </span>
        ))}
      </div>
    </div>
  );
}
