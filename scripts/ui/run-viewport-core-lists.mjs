/**
 * Viewport smoke for quotes / procurement / accounting (no @playwright/test).
 * Usage (from repo root, with Chromium already installed via playwright):
 *   node logs/run-viewport-core-lists.mjs
 * Env: WEB_BASE_URL, TRIAL_*_PASSWORD / TRIAL_BOSS_PASSWORD, optional USER.
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const OUT = path.resolve("logs/viewport-core-lists-out.txt");
const RUN_LOG = path.resolve("logs/viewport-core-lists-run.txt");
const lines = [];
function log(msg) {
  lines.push(msg);
  console.log(msg);
}

function loadEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return;
  for (const line of fs.readFileSync(filePath, "utf8").split(/\r?\n/)) {
    const m = line.match(/^\s*([^#=]+)=(.*)$/);
    if (!m) continue;
    const k = m[1].trim();
    const v = m[2].trim();
    if (!process.env[k]) process.env[k] = v;
  }
}

loadEnvFile(path.resolve("logs/trial-passwords.local.env"));

const BASE = process.env.WEB_BASE_URL || "http://127.0.0.1:3000";
const USER = process.env.TRIAL_USER || "boss";
const PASS =
  process.env.TRIAL_BOSS_PASSWORD ||
  process.env.TRIAL_ADMIN_PASSWORD ||
  process.env.TRIAL_SALES_PASSWORD ||
  "";

function resolvePlaywright() {
  const candidates = [
    path.resolve("node_modules/playwright-core"),
    path.resolve("node_modules/playwright"),
    path.join(
      process.env.USERPROFILE || "",
      "AppData/Local/npm-cache/_npx/0cf6ff1fad43f633/node_modules/playwright-core",
    ),
    path.join(
      process.env.USERPROFILE || "",
      "AppData/Local/npm-cache/_npx/0cf6ff1fad43f633/node_modules/playwright",
    ),
  ];
  for (const c of candidates) {
    if (fs.existsSync(path.join(c, "index.js")) || fs.existsSync(path.join(c, "package.json"))) {
      try {
        return require(c);
      } catch {
        /* try next */
      }
    }
  }
  try {
    return require("playwright-core");
  } catch {
    return require("playwright");
  }
}

async function apiLogin() {
  if (!PASS) throw new Error("Missing trial password env (logs/trial-passwords.local.env)");
  const apiBase = process.env.API_BASE_URL || "http://127.0.0.1:8000";
  const loginRes = await fetch(`${apiBase}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: USER, password: PASS }),
  });
  if (!loginRes.ok) throw new Error(`API login HTTP ${loginRes.status}`);
  const loginJson = await loginRes.json();
  const tokens = loginJson?.data;
  if (!tokens?.access_token) throw new Error("API login missing access_token");
  const meRes = await fetch(`${apiBase}/api/v1/users/me`, {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  });
  if (!meRes.ok) throw new Error(`API /users/me HTTP ${meRes.status}`);
  const meJson = await meRes.json();
  const profile = meJson?.data;
  if (!profile?.id) throw new Error("API /users/me missing profile");
  return { tokens, profile, apiBase };
}

/**
 * UI form login did not emit /auth/login under headless Chromium in this batch
 * (fields filled, submit click, zero XHR). Use API + zustand persist inject instead.
 */
async function injectSession(page, { tokens, profile }) {
  const roles = Array.isArray(profile.roles)
    ? profile.roles.map((r) => String(r.code ?? r.name ?? "role"))
    : [];
  const permissions = Array.isArray(profile.permissions)
    ? profile.permissions.map((p) => String(p.code ?? p))
    : [];
  const state = {
    state: {
      token: {
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
      },
      user: {
        id: String(profile.id),
        username: String(profile.username ?? USER),
        full_name: profile.full_name ? String(profile.full_name) : undefined,
        roles,
        permissions,
        data_scope: String(profile.data_scope ?? "self"),
      },
    },
    version: 0,
  };
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.evaluate((payload) => {
    localStorage.setItem("zhenhang-web-admin-auth", JSON.stringify(payload));
  }, state);
  await page.goto(`${BASE}/dashboard`, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(800);
  if (page.url().includes("/login")) {
    throw new Error("session inject failed — still on /login");
  }
}

async function moneyAlignSample(page) {
  return page.evaluate(() => {
    const nodes = [
      ...document.querySelectorAll(
        "td.text-right, th.text-right, [class*='text-right'][class*='tabular-nums']",
      ),
    ];
    // Quote center left list: amount lines often contain ¥ + tabular-nums
    const yen = [...document.querySelectorAll("p, span, td, th")].filter((n) =>
      /¥|￥/.test(n.textContent || ""),
    );
    const candidates = nodes.length ? nodes : yen;
    if (!candidates.length) return { found: 0, ok: false, reason: "no money-like cells" };
    let right = 0;
    for (const n of candidates.slice(0, 12)) {
      const s = getComputedStyle(n);
      if (s.textAlign === "right" || s.textAlign === "end") right += 1;
    }
    return {
      found: candidates.length,
      ok: right > 0,
      reason: right > 0 ? `right=${right}/${Math.min(candidates.length, 12)}` : "no right-aligned sample",
    };
  });
}

async function main() {
  log(`START ${new Date().toISOString()} BASE=${BASE} USER=${USER}`);
  const pw = resolvePlaywright();
  const chromium = pw.chromium;
  if (!chromium?.launch) throw new Error("playwright chromium.launch unavailable");
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  let failed = false;
  try {
    const session = await apiLogin();
    log(`API_LOGIN=OK api=${session.apiBase}`);
    await injectSession(page, session);
    log(`SESSION_INJECT=OK url=${page.url()}`);

    const routes = [
      { path: "/quotes", titleHints: ["报价中心", "报价"] },
      { path: "/procurement", titleHints: ["采购预备", "采购"] },
      { path: "/accounting", titleHints: ["财务", "账目", "应收", "应付"] },
    ];

    for (const r of routes) {
      await page.goto(`${BASE}${r.path}`, { waitUntil: "domcontentloaded", timeout: 60000 });
      await page.waitForTimeout(2500);
      const body = await page.locator("body").innerText();
      const hasTitle = r.titleHints.some((h) => body.includes(h));
      const headerOrFilter = (await page.locator('[role="search"], h1, h2, header').count()) > 0;
      const money = await moneyAlignSample(page);
      const shot = path.resolve(`logs/viewport${r.path.replace(/\//g, "-") || "-root"}.png`);
      await page.screenshot({ path: shot, fullPage: false }).catch(() => {});
      const line = `${r.path}: title=${hasTitle} header/filter=${headerOrFilter} money=${money.reason} (found=${money.found}) shot=${path.basename(shot)}`;
      log(line);
      log(`${r.path}: bodySnippet=${body.replace(/\s+/g, " ").slice(0, 220)}`);
      if (!hasTitle || !headerOrFilter) failed = true;
      if (money.found > 0 && !money.ok) failed = true;
      if (money.found === 0) log(`${r.path}: NOTE empty/loading — money align not asserted`);
    }
  } catch (e) {
    failed = true;
    log(`ERROR ${e instanceof Error ? e.stack || e.message : String(e)}`);
  } finally {
    await browser.close().catch(() => {});
  }
  log(failed ? "RESULT=FAIL" : "RESULT=PASS");
  const text = lines.join("\n") + "\n";
  fs.writeFileSync(OUT, text, "utf8");
  fs.writeFileSync(RUN_LOG, text, "utf8");
  process.exit(failed ? 1 : 0);
}

main();
