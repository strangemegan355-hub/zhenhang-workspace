# -*- coding: utf-8 -*-
"""Patch customer quote page UTF-8 Chinese labels."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = json.loads((ROOT / "scripts" / "customer_quote_labels.json").read_text(encoding="utf-8-sig"))
PAGE = ROOT / "apps/web-admin/src/app/(admin)/(quotes)/quotes/customer/page.tsx"

c = PAGE.read_text(encoding="utf-8")

c = c.replace('String(p.unit ?? "?")', 'String(p.unit ?? "台")')
c = c.replace('} ? ${String(p.name', f'}} {S["dot"]}${{String(p.name')
c = c.replace(
    'status: String(row.workflow_state ?? "draft") === "draft" ? "??"',
    f'status: String(row.workflow_state ?? "draft") === "draft" ? "{S["draft"]}"',
)
c = c.replace('{p.spec || "?"}', '{p.spec || "—"}')
c = c.replace('placeholder="?"', 'placeholder="—"')
c = c.replace('{p.name} ? {p.spec || "—"}', '{p.name} · {p.spec || "—"}')

c = re.sub(
    r"\n  const motorModelOptions = useMemo\([\s\S]*?\n  \);\n",
    "\n",
    c,
    count=1,
)

# Form errors and actions
c = c.replace('setFormError("???????");', f'setFormError("{S["err_title"]}");')
c = c.replace('setFormError("?????");', f'setFormError("{S["err_customer"]}");')
c = c.replace('setFormError("?????????????");', f'setFormError("{S["err_lines"]}");')
c = c.replace('err.message : "????")', f'err.message : "{S["err_save"]}")')
c = c.replace('err.message : "????");', f'err.message : "{S["err_delete"]}");')
c = re.sub(
    r"window\.confirm\(`[^`]*\$\{label\}[^`]*`\)",
    f'window.confirm(`{S["confirm_delete"]}`.replace("{{label}}", label))',
    c,
)

# Edit shell
c = c.replace('title="??????"', f'title="{S["loading_title"]}"')
c = c.replace('>????...</p>', f'>{S["loading"]}</p>')
c = c.replace('{editId ? "??????" : "??????"}', f'{{editId ? "{S["edit_title"]}" : "{S["new_title"]}"}}')
c = c.replace('>????</WorkspaceToolbarButton>', f'>{S["back_list"]}</WorkspaceToolbarButton>')
c = c.replace('? "???..." : "????"', f'? "{S["saving"]}" : "{S["save_quote"]}"')

# Hint block
c = re.sub(
    r"<p className=\"text-xs text-\[var\(--color-text-muted\)\]\">\s*[^\n<]+\n",
    f'<p className="text-xs text-[var(--color-text-muted)]">\n          {S["hint_link"]}\n',
    c,
    count=1,
)
c = re.sub(
    r"\{\" \"\}\s*[^\n]+\n\s*<Link href=\"/projects\"",
    f'{{" "}}\n              {S["hint_no_project"]}\n              <Link href="/projects"',
    c,
    count=1,
)
c = re.sub(
    r'>\s*\?\?\?\?\s*</Link>\s*\n\s*\?\?\?\?\?\?\?\?\?',
    f'>\n                {S["projects"]}\n              </Link>\n              {S["hint_after_project"]}',
    c,
    count=1,
)

# Basic info panel - first title="????"
c = re.sub(r'(<IndustrialPanel title=")\?\?\?\?(">)', rf'\1{S["basic_info"]}\2', c, count=1)
c = c.replace('>???? *</span>', f'>{S["label_title"]}</span>')
c = c.replace('>?? *</span>', f'>{S["label_customer"]}</span>')
c = c.replace('placeholder="? XX??????"', f'placeholder="{S["ph_title"]}"')
c = c.replace('<option value="">???</option>', f'<option value="">{S["please_select"]}</option>')
c = c.replace('>????</span>', f'>{S["label_project"]}</span>')
c = c.replace('<option value="">??</option>', f'<option value="">{S["no_project"]}</option>')
c = c.replace('>??(%)</span>', f'>{S["label_tax"]}</span>')
c = c.replace('>??</span>', f'>{S["label_remark"]}</span>')

# Lines panel
c = re.sub(
    r'(<IndustrialPanel\s+title=")\?\?\?\?\?\?\?\?\?\?\?\?\?\?\?\?(")',
    rf'\1{S["lines_title"]}\2',
    c,
    count=1,
)
c = re.sub(
    r">(\?\?\?)</WorkspaceToolbarButton>",
    f'>{S["add_line"]}</WorkspaceToolbarButton>',
    c,
    count=1,
)

# Empty catalog hints
c = re.sub(
    r"暂无产品库数据，请先在[\s\S]*?维护[^\n]+",
    f'{S["empty_catalog_1"]}\n              <Link href="/products" className={{`mx-1 ${{linkActionClass}}`}}>\n                {S["products"]}\n              </Link>\n              {S["empty_catalog_2"]}',
    c,
    count=1,
)
if "empty_motor_hint" in S and "尚未检测到" not in c:
    c = c.replace(
        "{productCatalog.length === 0 ? (",
        f'{{motorCatalog.length === 0 && productCatalog.length > 0 ? (\n            <p className="mb-2 text-xs text-[var(--color-text-muted)]">{S["empty_motor_hint"]}</p>\n          ) : null}}\n          {{productCatalog.length === 0 ? (',
        1,
    )

# Table header
header = f"""                <tr className={{tableHeaderRowClass}}>
                  <th className="px-2 py-2 text-left font-normal">{S["col_name"]}</th>
                  <th className="px-2 py-2 text-left font-normal">{S["col_spec"]}</th>
                  <th className="px-2 py-2 text-left font-normal">{S["col_unit"]}</th>
                  <th className="px-2 py-2 text-left font-normal">{S["col_power"]}</th>
                  <th className="px-2 py-2 text-left font-normal">{S["col_price"]}</th>
                  <th className="px-2 py-2 text-left font-normal">{S["col_qty"]}</th>
                  <th className="px-2 py-2 text-left font-normal">{S["col_amount"]}</th>
                  <th className="px-2 py-2 text-left font-normal">{S["col_action"]}</th>
                </tr>"""
c = re.sub(
    r"<tr className=\{tableHeaderRowClass\}>[\s\S]*?</tr>\s*</thead>\s*<tbody>\s*\{lines\.map",
    header + "\n              </thead>\n              <tbody>\n                {lines.map",
    c,
    count=1,
)

c = c.replace('<option value="">??????</option>', f'<option value="">{S["sel_name"]}</option>')
c = c.replace('<option value="">??????</option>', f'<option value="">{S["sel_spec"]}</option>')
c = c.replace('<option value="">????</option>', f'<option value="">{S["sel_motor"]}</option>')
c = re.sub(r">\s*\?\?\s*</button>", f">\n                          {S['delete']}\n                        </button>", c)

# Summary panel
c = re.sub(r'(<IndustrialPanel title=")\?\?\?\?(">\s*<div className="grid)', rf'\1{S["summary"]}\2', c, count=1)
c = re.sub(r">(\?\?\?\?\?\?)\{money\(subtotal\)\}", rf">{S['subtotal']}{{money(subtotal)}}", c, count=1)
c = re.sub(
    r">\?\? \{taxRate\} \?\?\?\{money\(taxAmount\)\}",
    f">税率 {{taxRate}}{S['tax_suffix']}{{money(taxAmount)}}",
    c,
    count=1,
)
c = re.sub(r">(\?\?\?\?\?)\{money\(finalTotal\)\}", rf">{S['total']}{{money(finalTotal)}}", c, count=1)

# List view
c = re.sub(
    r"<span>对客报价面向客户销售，[^\n]+</span>",
    f"<span>{S['list_hint']}</span>",
    c,
    count=1,
)
c = re.sub(r"<span>\?\?\?\?\?\?\?\?\?\?\?\?\?\?\?\?\?\?\?\?\?\?\?\?\?\?</span>", f"<span>{S['list_hint']}</span>", c, count=1)
c = re.sub(r'(<Link href="/quotes"[^>]*>\s*)\?\?\?\?\?\?/BOM', rf'\1{S["back_internal"]}', c, count=1)
c = re.sub(r'title="对客报价"|title="\?\?\?\?"', f'title="{S["page_title"]}"', c, count=1)
c = c.replace('title: "????", canView: true, fixed: "left"', f'title: "{S["col_quote_no"]}", canView: true, fixed: "left"')
c = c.replace('title: "??", canView: true, width: 200', f'title: "{S["col_title"]}", canView: true, width: 200')
c = c.replace('title: "????", canView: true,', f'title: "{S["col_final"]}", canView: true,')
c = c.replace('title: "??", canView: true, width: 80', f'title: "{S["col_status"]}", canView: true, width: 80')
c = re.sub(r'>\s*\?\?\s*</button>\s*\n\s*<button type="button" className=\{dangerActionClass\}', f'>\n              {S["edit"]}\n            </button>\n            <button type="button" className={{dangerActionClass}}', c, count=1)
c = re.sub(r'className=\{dangerActionClass\} onClick=\{\(\) => void handleDelete[^}]+\}\}>\s*\?\?\s*</button>', f'className={{dangerActionClass}} onClick={{() => void handleDelete(row.id, row.title)}}>\n              {S["delete"]}\n            </button>', c, count=1)
c = re.sub(r'emptyHint="[^"]+"', f'emptyHint="{S["empty_hint"]}"', c, count=1)
c = re.sub(r'>\?\?\?\?\?\?</WorkspaceToolbarButton>', f'>{S["new_btn"]}</WorkspaceToolbarButton>', c, count=1)

# Motor amount hint
c = re.sub(r"含电机 ", S["motor_amount_prefix"], c)

PAGE.write_text(c, encoding="utf-8")
print("Patched", PAGE)
