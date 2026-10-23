/**
 * Viewport smoke for quotes / procurement / accounting (no @playwright/test required).
 * Usage (repo root; Chromium via playwright / playwright-core):
 *   node scripts/ui/run-viewport-core-lists.mjs
 *   node logs/run-viewport-core-lists.mjs
 * Env: WEB_BASE_URL, API_BASE_URL, TRIAL_*_PASSWORD / TRIAL_BOSS_PASSWORD
 *
 * Auth: tries UI form login after hydration (K-029); always keeps API+localStorage inject fallback.
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "../..");
const OUT = path.resolve(REPO_ROOT, "logs/viewport-core-lists-out.txt");
const RUN_LOG = path.resolve(REPO_ROOT, "logs/viewport-core-lists-run.txt");
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
const USER = process.env.TRIAL_USER || "boss";
const PASS =
  process.env.TRIAL_BOSS_PASSWORD ||
  process.env.TRIAL_ADMIN_PASSWORD ||
  process.env.TRIAL_SALES_PASSWORD ||
  "";

function resolvePlaywright() {
  const candidates = [
    path.resolve(REPO_ROOT, "node_modules/playwright-core"),
    path.resolve(REPO_ROOT, "node_modules/playwright"),
    path.resolve(REPO_ROOT, "apps/web-admin/node_modules/playwright-core"),
    path.resolve(REPO_ROOT, "apps/web-admin/node_modules/playwright"),
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
    try {
      return require("playwright");
    } catch (e) {
      throw new Error(
        `playwright/playwright-core not found — install with: npm i -D playwright-core@1.51.1 (or use existing npx cache). ${e}`,
      );
    }
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
 * Optional UI login path (K-029): wait for data-hydrated=1, then submit.
 * Returns true if /auth/login XHR observed and left /login.
 */
async function tryUiLogin(page) {
  const loginReqs = [];
  const onReq = (r) => {
    if (r.url().includes("/auth/login") && r.method() === "POST") loginReqs.push(r.url());
  };
  page.on("request", onReq);
  try {
    await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForSelector('#username, [data-testid="login-form"]', { timeout: 20000 });
    await page.waitForFunction(
      () => document.querySelector("[data-testid='login-form']")?.getAttribute("data-hydrated") === "1",
      { timeout: 20000 },
    );
    await page.fill("#username", USER);
    await page.fill("#password", PASS);
    await page.click('[data-testid="login-submit"], button[type="submit"]');
    await page.waitForTimeout(2500);
    const leftLogin = !page.url().includes("/login");
    log(`UI_LOGIN xhr=${loginReqs.length} leftLogin=${leftLogin} url=${page.url()}`);
    return loginReqs.length > 0 && leftLogin;
  } catch (e) {
    log(`UI_LOGIN_SKIP ${e instanceof Error ? e.message : String(e)}`);
    return false;
  } finally {
    page.off("request", onReq);
  }
}

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

async function waitQuotesSettled(page) {
  const deadline = Date.now() + 25000;
  let last = { loading: true, hasYen: false, empty: false, onLogin: false };
  let stable = 0;
  while (Date.now() < deadline) {
    last = await page.evaluate(() => {
      const body = document.body?.innerText || "";
      return {
        loading: body.includes("加载报价列表"),
        hasYen: /¥|￥/.test(body),
        empty: body.includes("暂无报价"),
        onLogin: body.includes("登录您的账户"),
      };
    });
    if (last.onLogin) return last;
    // Require settled non-loading twice (avoid hydration flicker), or money/empty visible.
    if (!last.loading && (last.hasYen || last.empty)) return last;
    if (!last.loading) {
      stable += 1;
      if (stable >= 2) return last;
    } else {
      stable = 0;
    }
    await page.waitForTimeout(500);
  }
  return last;
}

async function moneyAlignSample(page) {
  return page.evaluate(() => {
    const nodes = [
      ...document.querySelectorAll(
        "td.text-right, th.text-right, [class*='text-right'][class*='tabular-nums'], p.text-right.tabular-nums, .text-right.tabular-nums",
      ),
    ];
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
  let browser;
  try {
    const pw = resolvePlaywright();
    const chromium = pw.chromium;
    if (!chromium?.launch) throw new Error("playwright chromium.launch unavailable");
    browser = await chromium.launch({ headless: true });
  } catch (e) {
    log(`ERROR ${e instanceof Error ? e.message : String(e)}`);
    log("RESULT=SKIP (playwright unavailable — see KNOWN_ISSUES K-029/Playwright)");
    const text = lines.join("\n") + "\n";
    fs.writeFileSync(OUT, text, "utf8");
    fs.writeFileSync(RUN_LOG, text, "utf8");
    process.exit(0);
  }

  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  let failed = false;
  try {
    const session = await apiLogin();
    log(`API_LOGIN=OK api=${session.apiBase}`);

    const uiOk = await tryUiLogin(page);
    // Always ensure persist payload is present (UI login should have written it; inject is idempotent fallback).
    if (!uiOk) {
      await injectSession(page, session);
      log(`SESSION_INJECT=OK url=${page.url()} (UI login fallback)`);
    } else {
      // Re-assert localStorage in case persist flush lagged before the next hard navigation.
      await page.evaluate(
        ({ tokens, profile, USER }) => {
          const roles = Array.isArray(profile.roles)
            ? profile.roles.map((r) => String(r.code ?? r.name ?? "role"))
            : [];
          const permissions = Array.isArray(profile.permissions)
            ? profile.permissions.map((p) => String(p.code ?? p))
            : [];
          const raw = localStorage.getItem("zhenhang-web-admin-auth");
          if (!raw) {
            localStorage.setItem(
              "zhenhang-web-admin-auth",
              JSON.stringify({
                state: {
                  token: {
                    accessToken: tokens.access_token,
                    refreshToken: tokens.refresh_token,
                  },
                  user: {
                    id: String(profile.id),
                    username: String(profile.username ?? USER),
                    roles,
                    permissions,
                    data_scope: String(profile.data_scope ?? "self"),
                  },
                },
                version: 0,
              }),
            );
          }
        },
        { tokens: session.tokens, profile: session.profile, USER },
      );
      log(`SESSION_UI=OK url=${page.url()}`);
    }

    const routes = [
      { path: "/quotes", titleHints: ["报价中心", "报价"], waitQuotes: true },
      { path: "/procurement", titleHints: ["采购预备", "采购"] },
      { path: "/accounting", titleHints: ["财务", "账目", "应收", "应付"] },
    ];

    for (const r of routes) {
      await page.goto(`${BASE}${r.path}`, { waitUntil: "domcontentloaded", timeout: 60000 });
      if (r.waitQuotes) {
        const settled = await waitQuotesSettled(page);
        log(`/quotes settle loading=${settled.loading} yen=${settled.hasYen} empty=${settled.empty}`);
        if (settled.loading) failed = true;
      } else {
        await page.waitForTimeout(2500);
      }
      const body = await page.locator("body").innerText();
      const hasTitle = r.titleHints.some((h) => body.includes(h));
      const headerOrFilter = (await page.locator('[role="search"], h1, h2, header').count()) > 0;
      const money = await moneyAlignSample(page);
      const shot = path.resolve(REPO_ROOT, `logs/viewport${r.path.replace(/\//g, "-") || "-root"}.png`);
      await page.screenshot({ path: shot, fullPage: false }).catch(() => {});
      const line = `${r.path}: title=${hasTitle} header/filter=${headerOrFilter} money=${money.reason} (found=${money.found}) shot=${path.basename(shot)}`;
      log(line);
      log(`${r.path}: bodySnippet=${body.replace(/\s+/g, " ").slice(0, 220)}`);
      if (!hasTitle || !headerOrFilter) failed = true;
      if (money.found > 0 && !money.ok) failed = true;
      if (money.found === 0) {
        if (r.path === "/procurement") {
          log(`${r.path}: NOTE 采购库无试用行（materials/entries=0），浏览器无法验金额列；非对齐缺陷`);
        } else {
          log(`${r.path}: NOTE empty/loading — money align not asserted`);
        }
      }
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
