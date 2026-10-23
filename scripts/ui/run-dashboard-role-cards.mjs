/**
 * UX-006 / K-006: multi-role Dashboard card visibility (headless).
 * Roles: trialadmin / finance01 / sales01 / workshop01 (passwords from trial env).
 *
 * Cards gated by permission:
 *   财务待办   → business:accounting:read
 *   审批中心   → business:approval:read
 *   最近工单   → business:work_order:read
 *
 * Usage (repo root; web:3000 + api:8000):
 *   node scripts/ui/run-dashboard-role-cards.mjs
 * Evidence: logs/dashboard-role-cards-out.txt
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "../..");
const OUT = path.resolve(REPO_ROOT, "logs/dashboard-role-cards-out.txt");
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

loadEnvFile(path.resolve(REPO_ROOT, "logs/trial-passwords.local.env"));

const BASE = process.env.WEB_BASE_URL || "http://127.0.0.1:3000";
const API = process.env.API_BASE_URL || "http://127.0.0.1:8000";

/** Seed-aligned expectations (setup_trial_users TRIAL_ROLE_DEFS). */
const ROLES = [
  {
    user: "trialadmin",
    envPass: "TRIAL_ADMIN_PASSWORD",
    expect: { finance: false, approval: false, workOrders: false },
  },
  {
    user: "finance01",
    envPass: "TRIAL_FINANCE_PASSWORD",
    expect: { finance: true, approval: true, workOrders: true },
  },
  {
    user: "sales01",
    envPass: "TRIAL_SALES_PASSWORD",
    expect: { finance: true, approval: false, workOrders: true },
  },
  {
    user: "workshop01",
    envPass: "TRIAL_WORKSHOP_PASSWORD",
    expect: { finance: false, approval: false, workOrders: true },
  },
];

const GATES = {
  finance: "business:accounting:read",
  approval: "business:approval:read",
  workOrders: "business:work_order:read",
};

function resolvePlaywright() {
  const candidates = [
    path.resolve(REPO_ROOT, "node_modules/playwright-core"),
    path.resolve(REPO_ROOT, "node_modules/playwright"),
    path.resolve(REPO_ROOT, "apps/web-admin/node_modules/playwright-core"),
    path.resolve(REPO_ROOT, "apps/web-admin/node_modules/playwright"),
  ];
  for (const c of candidates) {
    if (fs.existsSync(path.join(c, "index.js")) || fs.existsSync(path.join(c, "package.json"))) {
      try {
        return require(c);
      } catch {
        /* next */
      }
    }
  }
  try {
    return require("playwright-core");
  } catch {
    return require("playwright");
  }
}

function permSet(profile) {
  const raw = Array.isArray(profile.permissions) ? profile.permissions : [];
  return new Set(raw.map((p) => String(p.code ?? p)));
}

async function apiLogin(username, password) {
  const loginRes = await fetch(`${API}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!loginRes.ok) throw new Error(`login HTTP ${loginRes.status} user=${username}`);
  const loginJson = await loginRes.json();
  const tokens = loginJson?.data;
  if (!tokens?.access_token) throw new Error(`login missing token user=${username}`);
  const meRes = await fetch(`${API}/api/v1/users/me`, {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  });
  if (!meRes.ok) throw new Error(`/users/me HTTP ${meRes.status} user=${username}`);
  const meJson = await meRes.json();
  const profile = meJson?.data;
  if (!profile?.id) throw new Error(`/users/me missing profile user=${username}`);
  return { tokens, profile };
}

async function injectSession(page, { tokens, profile, username }) {
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
        username: String(profile.username ?? username),
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
  await page.waitForTimeout(2200);
  if (page.url().includes("/login")) {
    throw new Error(`session inject failed for ${username}`);
  }
}

async function readCards(page) {
  return page.evaluate(() => {
    const text = document.body?.innerText || "";
    const h3 = [...document.querySelectorAll("h3")].map((n) => (n.textContent || "").trim());
    return {
      finance: h3.includes("财务待办") || text.includes("财务待办"),
      approval: h3.includes("审批中心"),
      workOrders: h3.includes("最近工单"),
      // "审批中心" also appears in empty-state copy elsewhere? Prefer h3 titles from DashboardCard.
      h3Sample: h3.slice(0, 16),
    };
  });
}

async function main() {
  log(`START ${new Date().toISOString()} BASE=${BASE} API=${API}`);
  let failed = false;
  let browser;
  try {
    const pw = resolvePlaywright();
    browser = await pw.chromium.launch({ headless: true });
  } catch (e) {
    log(`ERROR playwright: ${e instanceof Error ? e.message : String(e)}`);
    log("RESULT=SKIP (playwright unavailable)");
    fs.writeFileSync(OUT, lines.join("\n") + "\n", "utf8");
    process.exit(0);
  }

  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  try {
    for (const role of ROLES) {
      const pass = process.env[role.envPass] || "";
      if (!pass) {
        log(`SKIP ${role.user}: missing ${role.envPass}`);
        failed = true;
        continue;
      }
      const session = await apiLogin(role.user, pass);
      const perms = permSet(session.profile);
      const apiExpect = {
        finance: perms.has(GATES.finance),
        approval: perms.has(GATES.approval),
        workOrders: perms.has(GATES.workOrders),
      };
      const apiMatch =
        apiExpect.finance === role.expect.finance &&
        apiExpect.approval === role.expect.approval &&
        apiExpect.workOrders === role.expect.workOrders;
      log(
        `API ${role.user}: finance=${apiExpect.finance} approval=${apiExpect.approval} workOrders=${apiExpect.workOrders} seedMatch=${apiMatch}`,
      );
      if (!apiMatch) {
        failed = true;
        log(`FAIL ${role.user}: live perms diverge from seed expectations ${JSON.stringify(role.expect)}`);
      }

      await injectSession(page, { ...session, username: role.user });
      const cards = await readCards(page);
      const shot = path.resolve(REPO_ROOT, `logs/viewport-dashboard-${role.user}.png`);
      await page.screenshot({ path: shot, fullPage: false }).catch(() => {});
      const domMatch =
        cards.finance === role.expect.finance &&
        cards.approval === role.expect.approval &&
        cards.workOrders === role.expect.workOrders;
      log(
        `DOM ${role.user}: finance=${cards.finance} approval=${cards.approval} workOrders=${cards.workOrders} expectMatch=${domMatch} shot=${path.basename(shot)} h3=${JSON.stringify(cards.h3Sample)}`,
      );
      if (!domMatch) {
        failed = true;
        log(`FAIL ${role.user}: DOM cards != expect ${JSON.stringify(role.expect)}`);
      }
    }
  } catch (e) {
    failed = true;
    log(`ERROR ${e instanceof Error ? e.stack || e.message : String(e)}`);
  } finally {
    await browser.close().catch(() => {});
  }

  log(failed ? "RESULT=FAIL" : "RESULT=PASS");
  fs.writeFileSync(OUT, lines.join("\n") + "\n", "utf8");
  process.exit(failed ? 1 : 0);
}

main();
