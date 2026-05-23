import * as React from "react";
import {
  computeFields,
  computePricing,
  createQuoteRuntime,
  defaultQuoteLayout,
  type LayoutBlock,
  type QuoteRuntime,
} from "@zhenhang/quote-runtime";

export { computeFields, computePricing, createQuoteRuntime, defaultQuoteLayout };
export type { LayoutBlock, QuoteRuntime };

export * from "./types";
export { BomTreeEditor, flatBomToTree } from "./bom-tree-editor";
export { BomWorkspaceLayout } from "./bom-workspace-layout";
export type { BomWorkspaceLayoutProps } from "./bom-workspace-layout";
export { FormulaLivePanel } from "./formula-live-panel";
export { CostVisualization } from "./cost-visualization";
export { ApprovalUxPanel } from "./approval-ux-panel";
export { ExportTemplatePicker, ExportTemplateBlockPreview, DEFAULT_EXPORT_TEMPLATES } from "./export-template-blocks";
export { QuoteLineEditor } from "./quote-line-editor";
export { QuoteWorkbench, DEFAULT_EXPORT_TEMPLATES as WORKBENCH_EXPORT_TEMPLATES } from "./quote-workbench";
export type { QuoteWorkbenchProps } from "./quote-workbench";
export { QuoteDiffPanel } from "./quote-diff-panel";
export type { DiffRow } from "./quote-diff-panel";
export { AIAnalysisPanel } from "./ai-analysis-panel";
export type { AIAnalysisData } from "./ai-analysis-panel";
export { DemoGuideStrip } from "./demo-guide";
export { WorkbenchToolbar } from "./workbench-toolbar";
export { useUndoRedo } from "./use-undo-redo";
export { QuoteCreationWizard } from "./quote-creation-wizard";
export type { QuoteWizardForm, WizardMasterOption } from "./quote-creation-wizard";
export { computeLineFormula, formatFormulaExpr } from "./inline-formula";

const DefaultBlock: React.FC<{ title: string }> = ({ title }) => (
  <section className="rounded border p-3">{title}</section>
);

const defaultRegistry: Record<string, React.FC<{ title: string }>> = {
  equipment_bom: ({ title }) => <section className="rounded border p-3 md:col-span-3">{title}</section>,
  configurator: ({ title }) => <section className="rounded border p-3 md:col-span-6">{title}</section>,
  cost_profit: ({ title }) => <section className="rounded border p-3 md:col-span-3">{title}</section>,
  approval_flow: ({ title }) => <section className="rounded border p-3">{title}</section>,
};

export function QuoteBuilderLayout({
  layout,
  registry = defaultRegistry,
}: {
  layout?: LayoutBlock[];
  registry?: Record<string, React.FC<{ title: string }>>;
}) {
  const runtime = createQuoteRuntime({ layout: layout ?? defaultQuoteLayout });
  const main = runtime.getMainBlocks();
  const bottom = runtime.getBottomBlocks();
  return (
    <div className="grid gap-3">
      <div className="grid gap-3 md:grid-cols-12">
        {main.map((b) => {
          const Component = registry[b.id] ?? DefaultBlock;
          return <Component key={b.id} title={b.title} />;
        })}
      </div>
      {bottom.map((b) => {
        const Component = registry[b.id] ?? DefaultBlock;
        return <Component key={b.id} title={b.title} />;
      })}
    </div>
  );
}

/** @deprecated Use QuoteWorkbench */
export function QuoteBuilderShell() {
  return <QuoteBuilderLayout />;
}
