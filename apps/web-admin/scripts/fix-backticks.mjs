import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dir = path.join(path.dirname(fileURLToPath(import.meta.url)), "../src/components/dashboard");
const targets = fs.readdirSync(dir).filter((f) => f.endsWith(".tsx"));

for (const name of targets) {
  const file = path.join(dir, name);
  let content = fs.readFileSync(file, "utf8");
  if (!content.includes("\\`")) continue;
  content = content.replace(/\\`/g, "`");
  fs.writeFileSync(file, content, "utf8");
  console.log("unescaped", name);
}
