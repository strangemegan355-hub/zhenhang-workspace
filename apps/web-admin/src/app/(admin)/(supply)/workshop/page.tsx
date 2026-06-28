"use client";

import { useWorkshopBoardQuery } from "@zhenhang/query-hooks";
import {
  EmptyState,
  ErrorBanner,
  IndustrialPage,
  IndustrialPanel,
  KpiCard,
  RealtimeDot,
  StatusBadge,
  TableSkeleton,
  WorkspaceToolbarButton,
  typography,
  useIndustrialShortcuts,
  workflowStateToStatus,
} from "@zhenhang/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo } from "react";
import { linkActionClass } from "@/lib/form-styles";

export default function WorkshopPage() {
  const router = useRouter();
  const query = useWorkshopBoardQuery(true);
  const board = query.data as Record<string, unknown> | undefined;

  useIndustrialShortcuts([
    { id: "nav-customers", key: "1", alt: true, handler: () => router.push("/customers") },
    { id: "nav-machines", key: "2", alt: true, handler: () => router.push("/machines") },
    { id: "nav-boms", key: "3", alt: true, handler: () => router.push("/boms") },
    { id: "nav-workshop", key: "4", alt: true, handler: () => router.push("/workshop") },
    { id: "back-dashboard", key: "Escape", handler: () => router.push("/dashboard") },
  ]);

  const equipment = (board?.equipment as Array<Record<string, unknown>>) ?? [];
  const alarms = (board?.alarms as Array<Record<string, unknown>>) ?? [];
  const lines = ((board?.production as Record<string, unknown> | undefined)?.lines as Array<Record<string, unknown>>) ?? [];
  const stats = useMemo(() => {
    const production = (board?.production as Record<string, unknown>) ?? {};
    const oee = (board?.oee as Record<string, unknown>) ?? {};
    const pipeline = (production.quote_pipeline as Array<{ state: string; count: number }>) ?? [];
    return {
      reviewing: pipeline.find((p) => p.state === "reviewing")?.count ?? 0,
      approved: pipeline.find((p) => p.state === "approved")?.count ?? 0,
      oeePct: Number(oee.oee ?? 0) * 100,
    };
  }, [board]);

  if (query.isLoading) {
    return (
      <IndustrialPage gap="md">
        <TableSkeleton rows={6} cols={4} />
      </IndustrialPage>
    );
  }

  if (query.isError) {
    return (
      <IndustrialPage gap="md">
        <ErrorBanner message="???????????" onRetry={() => query.refetch()} />
      </IndustrialPage>
    );
  }

  return (
    <IndustrialPage gap="md">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className={typography.pageTitle}>????</h1>
          <p className={typography.caption}>???? ? OEE ? ???Esc ?????</p>
        </div>
        <WorkspaceToolbarButton keyboardHint="Ctrl+S" title="??" onClick={() => query.refetch()}>
          ??
        </WorkspaceToolbarButton>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <KpiCard title="?????" value={String(stats.reviewing)} trend="?" />
        <KpiCard title="?????" value={String(stats.approved)} trend="?" />
        <KpiCard title="?? OEE" value={`${stats.oeePct.toFixed(1)}%`} trend="??" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <IndustrialPanel title="????" inlineLoading={query.isFetching}>
          {lines.length === 0 ? (
            <EmptyState message="??????" hint="?? workshop/board ????????" />
          ) : (
            <ul className="space-y-2">
              {lines.map((line, idx) => (
                <li
                  key={String(line.id ?? idx)}
                  className="flex items-center justify-between rounded px-2 py-2 hover:bg-[var(--color-surface-soft)]"
                  style={{ minHeight: 32 }}
                >
                  <div className="flex items-center gap-2">
                    <RealtimeDot level="ok" label={String(line.name ?? `?? ${idx + 1}`)} />
                    <StatusBadge status={workflowStateToStatus("approved")} label="??" compact />
                  </div>
                  <span className={typography.monoNumber}>OEE {String(line.oee ?? "?")}%</span>
                </li>
              ))}
            </ul>
          )}
        </IndustrialPanel>

        <IndustrialPanel title="?????">
          {equipment.length === 0 && alarms.length === 0 ? (
            <EmptyState message="????/??" />
          ) : (
            <div className="space-y-3">
              {equipment.slice(0, 5).map((eq, idx) => (
                <div key={String(eq.id ?? idx)} className={`${typography.body} flex justify-between`}>
                  <span>{String(eq.name ?? eq.code ?? "??")}</span>
                  <span className={typography.caption}>{String(eq.status ?? "?")}</span>
                </div>
              ))}
              {alarms.slice(0, 5).map((alarm, idx) => (
                <p key={String(alarm.id ?? idx)} className={`${typography.caption} text-[var(--color-warning)]`}>
                  {String(alarm.message ?? alarm.title ?? "??")}
                </p>
              ))}
            </div>
          )}
        </IndustrialPanel>
      </div>

      <p className={`${typography.caption} text-center`}>
        ?????????
        <Link href="/dashboard" className={`mx-1 ${linkActionClass}`}>
          ????
        </Link>
        ????? <code className="text-xs">npm run dev:workshop</code>
      </p>
    </IndustrialPage>
  );
}
