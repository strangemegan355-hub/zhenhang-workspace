import * as XLSX from "xlsx";

/** Parse BOM CSV/TSV/XLSX. Supports Chinese or English headers. */
export type ParsedBomRow = {
  item_code: string;
  item_name: string;
  unit: string;
  quantity: number;
  unit_cost: number;
};

const HEADER_ALIASES: Record<string, keyof ParsedBomRow | "skip"> = {
  item_code: "item_code",
  code: "item_code",
  "物料编码": "item_code",
  编码: "item_code",
  item_name: "item_name",
  name: "item_name",
  "物料名称": "item_name",
  名称: "item_name",
  unit: "unit",
  单位: "unit",
  quantity: "quantity",
  qty: "quantity",
  数量: "quantity",
  unit_cost: "unit_cost",
  cost: "unit_cost",
  "单位成本": "unit_cost",
  成本: "unit_cost",
  spec: "skip",
  规格: "skip",
  remark: "skip",
  备注: "skip",
};

function normalizeHeader(value: unknown): string {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .replace(/\s/g, "");
}

function mapHeader(value: unknown): keyof ParsedBomRow | "skip" {
  const raw = String(value ?? "").trim();
  const lower = raw.toLowerCase();
  return HEADER_ALIASES[lower] ?? HEADER_ALIASES[normalizeHeader(raw)] ?? "skip";
}

function toNumber(value: unknown): number {
  if (typeof value === "number") return Number.isFinite(value) ? value : 0;
  return Number(String(value ?? "").replace(/,/g, "")) || 0;
}

function rowFromCells(headers: unknown[], cells: unknown[]): ParsedBomRow | null {
  const row: Partial<ParsedBomRow> = { unit: "EA", quantity: 1, unit_cost: 0 };
  headers.forEach((header, idx) => {
    const key = mapHeader(header);
    if (key === "skip") return;
    const raw = cells[idx];
    if (key === "quantity" || key === "unit_cost") {
      row[key] = toNumber(raw);
    } else {
      row[key] = String(raw ?? "").trim();
    }
  });
  if (!row.item_code || !row.item_name) return null;
  return {
    item_code: String(row.item_code),
    item_name: String(row.item_name),
    unit: String(row.unit || "EA"),
    quantity: Number(row.quantity) || 1,
    unit_cost: Number(row.unit_cost) || 0,
  };
}

function splitCsvLine(line: string): string[] {
  const out: string[] = [];
  let cur = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      inQuotes = !inQuotes;
      continue;
    }
    if ((ch === "," || ch === "\t") && !inQuotes) {
      out.push(cur.trim());
      cur = "";
      continue;
    }
    cur += ch;
  }
  out.push(cur.trim());
  return out;
}

export function parseBomSpreadsheet(text: string): ParsedBomRow[] {
  const lines = text
    .replace(/^\uFEFF/, "")
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  if (lines.length < 2) return [];

  const headers = splitCsvLine(lines[0]);
  const rows: ParsedBomRow[] = [];
  for (const line of lines.slice(1)) {
    const parsed = rowFromCells(headers, splitCsvLine(line));
    if (parsed) rows.push(parsed);
  }
  return rows;
}

function parseBomWorkbook(buffer: ArrayBuffer): ParsedBomRow[] {
  const workbook = XLSX.read(buffer, { type: "array" });
  const sheetName = workbook.SheetNames[0];
  if (!sheetName) return [];
  const sheet = workbook.Sheets[sheetName];
  const matrix = XLSX.utils.sheet_to_json<(string | number | null)[]>(sheet, {
    header: 1,
    defval: "",
    raw: false,
  }) as unknown[][];
  if (matrix.length < 2) return [];

  const headers = matrix[0] ?? [];
  const rows: ParsedBomRow[] = [];
  for (const cells of matrix.slice(1)) {
    const parsed = rowFromCells(headers, cells ?? []);
    if (parsed) rows.push(parsed);
  }
  return rows;
}

export async function parseBomFile(file: File): Promise<ParsedBomRow[]> {
  const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
  if (ext === "xlsx" || ext === "xls") {
    return parseBomWorkbook(await file.arrayBuffer());
  }
  return parseBomSpreadsheet(await file.text());
}

export function buildBomImportTemplateXlsx(): Blob {
  const sheet = XLSX.utils.aoa_to_sheet([
    ["物料编码", "物料名称", "单位", "数量", "单位成本"],
    ["SCREW-M30", "螺杆总成", "EA", 1, 4200.5],
    ["BARREL-280", "料筒", "EA", 1, 3800],
  ]);
  sheet["!cols"] = [{ wch: 16 }, { wch: 20 }, { wch: 8 }, { wch: 8 }, { wch: 12 }];
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, sheet, "BOM明细");
  const bytes = XLSX.write(workbook, { type: "array", bookType: "xlsx" });
  return new Blob([bytes], {
    type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });
}

export const BOM_IMPORT_TEMPLATE = `物料编码,物料名称,单位,数量,单位成本
SCREW-M30,螺杆总成,EA,1,4200.50
BARREL-280,料筒,EA,1,3800.00
`;
