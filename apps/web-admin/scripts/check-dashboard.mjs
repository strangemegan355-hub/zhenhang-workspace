import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dir = path.join(path.dirname(fileURLToPath(import.meta.url)), "../src/components/dashboard");
const files = ["SalesOverviewPanel", "WorkflowProgressCard", "SystemStatusCard", "RecentQuotesCard", "dashboard-skeleton"];

for (const f of files) {
  const t = fs.readFileSync(path.join(dir, `${f}.tsx`), "utf8");
  const titles = [...t.matchAll(/title=(?:"([^"]+)"|{`([^`]+)`})/g)].map((m) => m[1] ?? m[2]);
  console.log(f, titles.slice(0, 2));
}
