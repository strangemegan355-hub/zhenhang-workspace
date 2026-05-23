#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FORBIDDEN_IMPORT_PATTERNS, LAYER_ALLOWED_IMPORTS, PACKAGE_LAYERS } from "./config.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "../../..");
const packagesDir = path.join(repoRoot, "packages");
const appsDir = path.join(repoRoot, "apps");

function getLayerForPackage(name) {
  const short = name.replace("@zhenhang/", "");
  for (const [layer, pkgs] of Object.entries(PACKAGE_LAYERS)) {
    if (pkgs.includes(short)) return layer;
  }
  return null;
}

function readPackageJson(dir) {
  const p = path.join(dir, "package.json");
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

function collectWorkspacePackages() {
  const map = new Map();
  for (const base of [packagesDir, appsDir]) {
    if (!fs.existsSync(base)) continue;
    for (const entry of fs.readdirSync(base, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const dir = path.join(base, entry.name);
      const pkg = readPackageJson(dir);
      if (!pkg?.name) continue;
      map.set(pkg.name, { dir, pkg, layer: getLayerForPackage(pkg.name) ?? (base.includes("apps") ? "apps" : null) });
    }
  }
  return map;
}

function buildDependencyGraph(workspace) {
  const graph = new Map();
  for (const [name, meta] of workspace) {
    const deps = {
      ...meta.pkg.dependencies,
      ...meta.pkg.devDependencies,
      ...meta.pkg.peerDependencies,
    };
    const internal = Object.keys(deps ?? {}).filter((d) => d.startsWith("@zhenhang/"));
    graph.set(name, internal);
  }
  return graph;
}

function detectCycles(graph) {
  const cycles = [];
  const visited = new Set();
  const stack = new Set();
  const path = [];

  function dfs(node) {
    if (stack.has(node)) {
      const idx = path.indexOf(node);
      cycles.push([...path.slice(idx), node]);
      return;
    }
    if (visited.has(node)) return;
    visited.add(node);
    stack.add(node);
    path.push(node);
    for (const dep of graph.get(node) ?? []) {
      if (graph.has(dep)) dfs(dep);
    }
    path.pop();
    stack.delete(node);
  }

  for (const node of graph.keys()) dfs(node);
  return cycles;
}

function getInternalDeps(meta) {
  const deps = {
    ...meta.pkg.dependencies,
    ...meta.pkg.devDependencies,
    ...meta.pkg.peerDependencies,
  };
  return Object.keys(deps ?? {}).filter((d) => d.startsWith("@zhenhang/"));
}

function checkLayerBoundaries(workspace) {
  const violations = [];
  for (const [name, meta] of workspace) {
    const fromLayer = meta.layer ?? "apps";
    const allowed = LAYER_ALLOWED_IMPORTS[fromLayer] ?? LAYER_ALLOWED_IMPORTS.apps;
    for (const dep of getInternalDeps(meta)) {
      const depMeta = workspace.get(dep);
      const toLayer = depMeta?.layer;
      if (!toLayer) continue;
      if (!allowed.includes(toLayer)) {
        violations.push({ from: name, to: dep, fromLayer, toLayer });
      }
    }
  }
  return violations;
}

function extractImportSources(content) {
  const sources = [];
  const patterns = [
    /import\s+(?:type\s+)?(?:[\w*{}\s,]+\s+from\s+)?['"]([^'"]+)['"]/g,
    /require\s*\(\s*['"]([^'"]+)['"]\s*\)/g,
  ];
  for (const re of patterns) {
    let m;
    while ((m = re.exec(content)) !== null) sources.push(m[1]);
  }
  return sources;
}

function scanForbiddenImports() {
  const violations = [];
  const appsRoot = path.join(repoRoot, "apps");
  if (!fs.existsSync(appsRoot)) return violations;
  walk(appsRoot, (file) => {
    if (!/\.(ts|tsx|js|jsx|mjs)$/.test(file)) return;
    if (file.includes("node_modules")) return;
    if (/eslint\.config|next\.config/.test(file)) return;
    const content = fs.readFileSync(file, "utf8");
    const sources = extractImportSources(content);
    for (const src of sources) {
      for (const rule of FORBIDDEN_IMPORT_PATTERNS) {
        if (rule.pattern.test(src)) {
          violations.push({ file: path.relative(repoRoot, file), message: `${rule.message} (${src})` });
        }
      }
    }
  });
  return violations;
}

function walk(dir, onFile) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name === ".next") continue;
      walk(full, onFile);
    } else onFile(full);
  }
}

function main() {
  const workspace = collectWorkspacePackages();
  const graph = buildDependencyGraph(workspace);
  const cycles = detectCycles(graph);
  const layerViolations = checkLayerBoundaries(workspace);
  const forbidden = scanForbiddenImports();

  let failed = false;
  console.log("=== Zhenhang Dependency Analyzer ===\n");

  if (cycles.length) {
    failed = true;
    console.log("CYCLE DETECTED:");
    cycles.forEach((c) => console.log("  -", c.join(" -> ")));
  } else {
    console.log("Cycles: none");
  }

  if (layerViolations.length) {
    failed = true;
    console.log("\nLAYER BOUNDARY VIOLATIONS:");
    layerViolations.forEach((v) =>
      console.log(`  - ${v.from} (${v.fromLayer}) -> ${v.to} (${v.toLayer})`),
    );
  } else {
    console.log("Layer boundaries: ok");
  }

  if (forbidden.length) {
    failed = true;
    console.log("\nFORBIDDEN IMPORTS:");
    forbidden.forEach((v) => console.log(`  - ${v.file}: ${v.message}`));
  } else {
    console.log("Forbidden imports (apps): ok");
  }

  console.log(`\nPackages scanned: ${workspace.size}`);
  process.exit(failed ? 1 : 0);
}

main();
