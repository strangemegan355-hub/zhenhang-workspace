"""Industrial quote PDF/Excel template engine (Jinja metadata + ReportLab/OpenPyXL)."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "templates" / "quote"

EXPORT_TEMPLATES: dict[str, dict[str, Any]] = {
    "default-pdf": {
        "name": "标准报价单",
        "format": "pdf",
        "layout": "standard",
        "description": "A4 竖版，含抬头与合计",
    },
    "detailed-pdf": {
        "name": "详细报价单（含 BOM）",
        "format": "pdf",
        "layout": "detailed",
        "description": "含物料明细、BOM 快照与版本号",
    },
    "default-xlsx": {
        "name": "标准报价表",
        "format": "xlsx",
        "layout": "standard",
        "description": "Excel 可编辑",
    },
    "cost-xlsx": {
        "name": "成本分析表",
        "format": "xlsx",
        "layout": "cost",
        "description": "含成本/毛利分列",
    },
}


def list_template_catalog() -> list[dict[str, Any]]:
    return [{"id": k, **v} for k, v in EXPORT_TEMPLATES.items()]


def resolve_template(template_id: str | None, export_format: str) -> dict[str, Any]:
    if template_id and template_id in EXPORT_TEMPLATES:
        tpl = EXPORT_TEMPLATES[template_id]
        if tpl["format"] == export_format:
            return {"id": template_id, **tpl}
    fallback = "default-pdf" if export_format == "pdf" else "default-xlsx"
    return {"id": fallback, **EXPORT_TEMPLATES[fallback]}


def _money(value: Any) -> str:
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def render_document(payload: dict, template_id: str | None = None) -> tuple[bytes, str]:
    export_format = payload.get("format", "pdf")
    tpl = resolve_template(template_id or payload.get("template_id"), export_format)
    layout = tpl["layout"]
    if tpl["format"] == "pdf":
        if layout == "detailed":
            return render_quote_pdf_detailed(payload), "pdf"
        return render_quote_pdf_standard(payload), "pdf"
    if layout == "cost":
        return render_quote_excel_cost(payload), "xlsx"
    return render_quote_excel_standard(payload), "xlsx"


def render_quote_pdf_standard(payload: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    width, height = A4
    pdf = canvas.Canvas(buffer, pagesize=A4)

    company = payload.get("company_name", "振航智能制造")
    pdf.setFillColor(colors.HexColor("#1e3a5f"))
    pdf.rect(0, height - 45 * mm, width, 45 * mm, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(20 * mm, height - 22 * mm, company)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(20 * mm, height - 32 * mm, "INDUSTRIAL QUOTATION / 工业报价单")

    y = height - 55 * mm
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(20 * mm, y, f"报价单号: {payload.get('quote_no', '')}")
    y -= 8 * mm
    pdf.setFont("Helvetica", 10)
    info_lines = [
        f"标题: {payload.get('title', '')}",
        f"客户: {payload.get('customer_name', '')}",
        f"设备: {payload.get('machine_name', '')}",
        f"币种: {payload.get('currency', 'CNY')}",
        f"状态: {payload.get('workflow_state', '')}",
        f"版本: V{payload.get('version_no', 1)}",
        f"日期: {payload.get('printed_at', date.today().isoformat())}",
    ]
    for line in info_lines:
        pdf.drawString(20 * mm, y, line)
        y -= 6 * mm

    y -= 4 * mm
    pdf.setFont("Helvetica-Bold", 9)
    cols = [20, 55, 115, 135, 160, 185]
    headers = ["编码", "名称", "数量", "单价", "小计"]
    for i, h in enumerate(headers):
        pdf.drawString(cols[i] * mm, y, h)
    y -= 5 * mm
    pdf.line(20 * mm, y, 200 * mm, y)
    y -= 4 * mm
    pdf.setFont("Helvetica", 9)
    for item in payload.get("items", [])[:40]:
        if y < 40 * mm:
            pdf.showPage()
            y = height - 30 * mm
        pdf.drawString(cols[0] * mm, y, str(item.get("item_code", ""))[:14])
        pdf.drawString(cols[1] * mm, y, str(item.get("item_name", ""))[:28])
        pdf.drawRightString(cols[3] * mm, y, str(item.get("quantity", "")))
        pdf.drawRightString(cols[4] * mm, y, _money(item.get("unit_price", 0)))
        pdf.drawRightString(200 * mm, y, _money(item.get("line_total", 0)))
        y -= 5 * mm

    y -= 6 * mm
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawRightString(200 * mm, y, f"报价合计: {_money(payload.get('total_amount', 0))}")
    y -= 6 * mm
    pdf.drawRightString(200 * mm, y, f"成本合计: {_money(payload.get('total_cost', 0))}")
    y -= 6 * mm
    pdf.drawRightString(200 * mm, y, f"利润: {_money(payload.get('profit_amount', 0))} ({payload.get('profit_rate', '0')}%)")

    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.grey)
    pdf.drawString(20 * mm, 15 * mm, payload.get("footer_note", "本报价单由振航 ERP 系统自动生成。"))
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def render_quote_pdf_detailed(payload: dict) -> bytes:
    return _render_pdf_combined(payload)


def _render_pdf_combined(payload: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    width, height = A4
    pdf = canvas.Canvas(buffer, pagesize=A4)
    # Page 1 — reuse standard drawing inline (call standard then add page2)
    std = BytesIO(render_quote_pdf_standard(payload))
    del std
    company = payload.get("company_name", "振航智能制造")
    pdf.setFillColor(colors.HexColor("#1e3a5f"))
    pdf.rect(0, height - 45 * mm, width, 45 * mm, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(20 * mm, height - 22 * mm, company)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(20 * mm, height - 32 * mm, "DETAILED QUOTATION / 详细工业报价单")
    y = height - 55 * mm
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(20 * mm, y, f"报价单号: {payload.get('quote_no', '')}")
    y -= 20 * mm
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(20 * mm, y, "报价行项目")
    y -= 8 * mm
    pdf.setFont("Helvetica", 9)
    for item in payload.get("items", [])[:25]:
        pdf.drawString(20 * mm, y, f"{item.get('item_code')} {item.get('item_name')} … {_money(item.get('line_total', 0))}")
        y -= 5 * mm
    pdf.showPage()
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(20 * mm, height - 25 * mm, "BOM 成本快照")
    y = height - 38 * mm
    pdf.setFont("Helvetica", 9)
    bom = payload.get("bom_snapshot") or {}
    for bi in (bom.get("items") or [])[:45]:
        if y < 20 * mm:
            break
        pdf.drawString(20 * mm, y, f"{bi.get('item_code')} | {bi.get('item_name')} | {bi.get('quantity')} | {bi.get('unit_cost')}")
        y -= 5 * mm
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def render_quote_excel_standard(payload: dict) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = "报价单"
    ws.merge_cells("A1:F1")
    ws["A1"] = payload.get("company_name", "振航智能制造") + " — 工业报价单"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A1"].fill = PatternFill("solid", fgColor="1E3A5F")
    meta = [
        ("报价单号", payload.get("quote_no")),
        ("客户", payload.get("customer_name")),
        ("设备", payload.get("machine_name")),
        ("版本", f"V{payload.get('version_no', 1)}"),
        ("合计", payload.get("total_amount")),
    ]
    row = 3
    for label, val in meta:
        ws[f"A{row}"] = label
        ws[f"B{row}"] = val
        row += 1
    row += 1
    for col, title in enumerate(["编码", "名称", "数量", "单价", "小计"], 1):
        cell = ws.cell(row=row, column=col, value=title)
        cell.font = Font(bold=True)
    row += 1
    for item in payload.get("items", []):
        ws.cell(row=row, column=1, value=item.get("item_code"))
        ws.cell(row=row, column=2, value=item.get("item_name"))
        ws.cell(row=row, column=3, value=float(item.get("quantity", 0)))
        ws.cell(row=row, column=4, value=float(item.get("unit_price", 0)))
        ws.cell(row=row, column=5, value=float(item.get("line_total", 0)))
        row += 1
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def render_quote_excel_cost(payload: dict) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = "成本分析"
    ws["A1"] = "成本分析表"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = payload.get("quote_no", "")
    headers = ["编码", "名称", "数量", "单价", "成本", "小计", "毛利"]
    for i, h in enumerate(headers, 1):
        ws.cell(row=4, column=i, value=h).font = Font(bold=True)
    row = 5
    for item in payload.get("items", []):
        qty = float(item.get("quantity", 0))
        price = float(item.get("unit_price", 0))
        cost = float(item.get("unit_cost", price * 0.7))
        line = qty * price
        ws.cell(row=row, column=1, value=item.get("item_code"))
        ws.cell(row=row, column=2, value=item.get("item_name"))
        ws.cell(row=row, column=3, value=qty)
        ws.cell(row=row, column=4, value=price)
        ws.cell(row=row, column=5, value=cost * qty)
        ws.cell(row=row, column=6, value=line)
        ws.cell(row=row, column=7, value=line - cost * qty)
        row += 1
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def render_jinja_text_preview(template_id: str, payload: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_ROOT / "pdf")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    try:
        tpl = env.get_template("default_quote.j2")
        return tpl.render(**payload)
    except Exception:
        return f"Quote {payload.get('quote_no', '')}"
