"""Guard: procurement list must serialize ProcurementEntryRead, not AccountingEntryRead.

Empty lists hid a wrong response_model; once trial rows exist, FastAPI returns 500.
"""

from __future__ import annotations

import ast
from pathlib import Path

ENDPOINT = Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "endpoints" / "procurement_entries.py"


def test_list_procurement_entries_uses_procurement_read_model():
    src = ENDPOINT.read_text(encoding="utf8")
    tree = ast.parse(src)
    list_fn = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "list_procurement_entries":
            list_fn = node
            break
    assert list_fn is not None, "list_procurement_entries missing"
    decorator_src = ast.get_source_segment(src, list_fn.decorator_list[0]) if list_fn.decorator_list else ""
    # Prefer source segment; fall back to unparse for robustness.
    joined = " ".join(ast.unparse(d) for d in list_fn.decorator_list)
    haystack = f"{decorator_src or ''} {joined}"
    assert "PageResponse[ProcurementEntryRead]" in haystack or "PageResponse[ProcurementEntryRead]" in src
    assert "PageResponse[AccountingEntryRead]" not in haystack
    assert "AccountingEntryRead" not in src
