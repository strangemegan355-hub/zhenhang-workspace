import fs from "node:fs";

const files = [
  "apps/web-admin/src/app/(admin)/(finance)/accounting/page.tsx",
  "apps/web-admin/src/app/(admin)/(finance)/accounting/ledger/page.tsx",
  "apps/web-admin/src/app/(admin)/(finance)/accounting/supplier-ledger/page.tsx",
  "apps/web-admin/src/app/(admin)/(supply)/procurement/page.tsx",
  "apps/web-admin/src/app/(admin)/(quotes)/quotes/page.tsx",
  "apps/web-admin/src/app/(admin)/(quotes)/quotes/customer/page.tsx",
  "packages/ui/src/components/layout/filter-bar.tsx",
  "packages/ui/src/index.ts",
  "apps/web-admin/src/lib/form-styles.ts",
  "packages/data-grid/src/index.tsx",
];

let ok = true;
for (const f of files) {
  if (!fs.existsSync(f)) {
    console.log("MISSING", f);
    ok = false;
    continue;
  }
  const t = fs.readFileSync(f, "utf8");
  const checks = [];
  if (f.includes("/accounting/") || f.endsWith("accounting/page.tsx") || f.includes("accounting\\")) {
    if (!t.includes("FilterBar")) checks.push("no FilterBar");
    if (!t.includes("moneyCellClass")) checks.push("no moneyCellClass");
    if (!t.includes("PageHeader")) checks.push("no PageHeader");
    if (!t.includes("filterFieldClass")) checks.push("no filterFieldClass");
  }
  if (f.includes("procurement")) {
    if (!t.includes("PageHeader")) checks.push("no PageHeader");
    if (!t.includes('variant="primary"')) checks.push("no primary action");
    if (!t.includes("hideInternalHeader")) checks.push("no hideInternalHeader");
    if (!t.includes('align: "right"')) checks.push("no money/qty align:right");
    if (!t.includes("planAmount")) checks.push("no planAmount column");
  }
  if (f.includes("quotes/page") || f.includes("quotes\\page") || f.includes("quotes/customer")) {
    if (!t.includes("PageHeader")) checks.push("no PageHeader");
  }
  if (f.includes("quotes/customer") || f.includes("quotes\\customer")) {
    if (!t.includes("moneyCellClass")) checks.push("no moneyCellClass on detail table");
    if (!t.includes('align: "right"')) checks.push("no finalTotal align:right");
  }
  if (f.includes("filter-bar")) {
    if (!t.includes('role="search"')) checks.push("no search role");
  }
  if (f.endsWith("index.ts") && f.includes("packages/ui")) {
    if (!t.includes("FilterBar")) checks.push("FilterBar not exported");
    if (!t.includes("PageHeader")) checks.push("PageHeader not exported");
  }
  if (f.includes("form-styles")) {
    if (!t.includes("moneyCellClass")) checks.push("no moneyCellClass export");
    if (!t.includes("filterFieldClass")) checks.push("no filterFieldClass export");
  }
  if (f.includes("data-grid")) {
    if (!t.includes("GridColumnAlign")) checks.push("no GridColumnAlign type");
    if (!t.includes("align?: GridColumnAlign")) checks.push("no align on GridColumn");
    if (!t.includes("alignClass")) checks.push("no alignClass helper");
    if (!t.includes('text-right tabular-nums')) checks.push("no right+tabular class");
  }
  if (checks.length) {
    console.log("FAIL", f, checks.join(", "));
    ok = false;
  } else {
    console.log("OK", f);
  }
}
process.exit(ok ? 0 : 1);
