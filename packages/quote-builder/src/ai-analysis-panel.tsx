"use client";

import * as React from "react";

export type AIAnalysisData = {
  summary?: string;
  highlights?: string[];
  riskLevel?: "low" | "medium" | "high";
  recommendations?: string[];
  riskAnalysis?: string[];
  bomCostAnomalies?: string[];
  profitSuggestions?: string[];
  approvalSuggestions?: string[];
  similarQuotes?: Array<{ quote_no?: string; title?: string; total_amount?: string; workflow_state?: string }>;
  similarProjects?: Array<{ quote_no?: string; title?: string; total_amount?: string; workflow_state?: string }>;
  deliveryRisks?: string[];
  bomRisks?: string[];
  customerInsights?: Record<string, unknown>;
  loading?: boolean;
  onRefresh?: () => void;
};

export function AIAnalysisPanel({ data }: { data: AIAnalysisData }) {
  const risk = data.riskLevel ?? "medium";
  const riskStyle =
    risk === "high"
      ? "bg-red-100 text-red-800"
      : risk === "low"
        ? "bg-emerald-100 text-emerald-800"
        : "bg-amber-100 text-amber-800";

  const sections: Array<{ title: string; items: string[] }> = [
    { title: "风险分析", items: data.riskAnalysis ?? [] },
    { title: "BOM 风险", items: data.bomRisks ?? data.bomCostAnomalies ?? [] },
    { title: "交付风险", items: data.deliveryRisks ?? [] },
    { title: "利润建议", items: data.profitSuggestions ?? [] },
    { title: "审批建议", items: data.approvalSuggestions ?? [] },
  ];

  const insights = data.customerInsights ?? {};
  const similar = data.similarQuotes ?? [];

  return (
    <div className="overflow-hidden rounded-lg border border-zinc-200 bg-gradient-to-br from-white to-zinc-50 shadow-sm dark:border-zinc-700 dark:from-zinc-900 dark:to-zinc-950">
      <div className="flex items-center justify-between border-b border-zinc-200 bg-white/80 px-3 py-2 dark:border-zinc-700">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-violet-600 text-xs text-white">AI</span>
          <span className="text-sm font-semibold">工业 Copilot</span>
          <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${riskStyle}`}>
            风险 {risk === "high" ? "高" : risk === "low" ? "低" : "中"}
          </span>
        </div>
        {data.onRefresh ? (
          <button
            type="button"
            className="rounded border px-2 py-1 text-xs hover:bg-zinc-50 dark:hover:bg-zinc-800"
            disabled={data.loading}
            onClick={data.onRefresh}
          >
            {data.loading ? "分析中…" : "重新分析"}
          </button>
        ) : null}
      </div>
      <div className="grid gap-3 p-3 lg:grid-cols-3">
        <section className="lg:col-span-2">
          <h4 className="mb-1 text-xs font-semibold uppercase text-zinc-500">执行摘要</h4>
          <p className="text-sm leading-relaxed text-zinc-800 dark:text-zinc-200">
            {data.loading ? "正在生成工业分析…" : data.summary || "暂无分析，请选择报价并刷新。"}
          </p>
          <h4 className="mb-1 mt-3 text-xs font-semibold uppercase text-zinc-500">关键发现</h4>
          <ul className="space-y-1">
            {(data.highlights ?? []).slice(0, 6).map((h) => (
              <li key={h} className="flex gap-1.5 text-xs text-zinc-600 dark:text-zinc-400">
                <span className="text-blue-500">•</span>
                {h}
              </li>
            ))}
          </ul>
        </section>
        <section className="rounded-md border border-zinc-100 bg-white/60 p-2 dark:border-zinc-800 dark:bg-zinc-900/60">
          <h4 className="mb-1 text-xs font-semibold uppercase text-zinc-500">客户成交</h4>
          {insights.customer_name ? (
            <dl className="space-y-1 text-xs">
              <div>
                <dt className="text-zinc-500">客户</dt>
                <dd className="font-medium">{String(insights.customer_name)}</dd>
              </div>
              <div>
                <dt className="text-zinc-500">历史已批</dt>
                <dd>{String(insights.approved_quotes ?? 0)} 单</dd>
              </div>
              <div>
                <dt className="text-zinc-500">累计金额</dt>
                <dd>¥{Number(insights.historical_amount_total ?? 0).toLocaleString()}</dd>
              </div>
              <div>
                <dt className="text-zinc-500">信号</dt>
                <dd className="text-violet-700 dark:text-violet-300">{String(insights.deal_signal ?? "—")}</dd>
              </div>
            </dl>
          ) : (
            <p className="text-xs text-zinc-500">未绑定客户</p>
          )}
        </section>
      </div>
      <div className="grid gap-2 border-t border-zinc-200 p-3 md:grid-cols-2 dark:border-zinc-700">
        {sections.map(
          (s) =>
            s.items.length > 0 && (
              <section key={s.title}>
                <h4 className="mb-1 text-xs font-semibold text-zinc-500">{s.title}</h4>
                <ul className="space-y-0.5">
                  {s.items.map((item) => (
                    <li key={item} className="text-xs text-zinc-700 dark:text-zinc-300">
                      {item}
                    </li>
                  ))}
                </ul>
              </section>
            ),
        )}
      </div>
      {(data.similarProjects?.length ?? 0) > 0 ? (
        <div className="border-t border-zinc-200 px-3 py-2 dark:border-zinc-700">
          <h4 className="mb-1 text-xs font-semibold text-zinc-500">历史相似项目（同设备）</h4>
          <div className="flex flex-wrap gap-2">
            {data.similarProjects!.map((q) => (
              <span
                key={q.quote_no}
                className="rounded border border-emerald-200 bg-emerald-50 px-2 py-1 text-[10px] dark:border-emerald-800 dark:bg-emerald-950/40"
              >
                {q.quote_no} · {q.workflow_state}
              </span>
            ))}
          </div>
        </div>
      ) : null}
      {similar.length > 0 ? (
        <div className="border-t border-zinc-200 px-3 py-2 dark:border-zinc-700">
          <h4 className="mb-1 text-xs font-semibold text-zinc-500">历史相似报价（同客户）</h4>
          <div className="flex flex-wrap gap-2">
            {similar.map((q) => (
              <span
                key={q.quote_no}
                className="rounded border border-zinc-200 bg-zinc-50 px-2 py-1 text-[10px] dark:border-zinc-700 dark:bg-zinc-900"
              >
                {q.quote_no} · {q.workflow_state} · ¥{Number(q.total_amount ?? 0).toLocaleString()}
              </span>
            ))}
          </div>
        </div>
      ) : null}
      {(data.recommendations?.length ?? 0) > 0 ? (
        <div className="border-t border-zinc-200 bg-zinc-50/50 px-3 py-2 dark:border-zinc-700">
          <h4 className="mb-1 text-xs font-semibold text-zinc-500">综合建议</h4>
          <div className="flex flex-wrap gap-2">
            {data.recommendations!.map((r) => (
              <span
                key={r}
                className="rounded-md border border-violet-200 bg-violet-50 px-2 py-1 text-xs dark:border-violet-800 dark:bg-violet-950/40"
              >
                {r}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
