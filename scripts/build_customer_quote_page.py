# -*- coding: utf-8 -*-
"""Build customer quote page.tsx with UTF-8 Chinese from labels JSON."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = json.loads((ROOT / "scripts" / "customer_quote_labels.json").read_text(encoding="utf-8-sig"))
TEMPLATE = (ROOT / "scripts" / "customer_quote_page.template.tsx").read_text(encoding="utf-8")
OUT = ROOT / "apps/web-admin/src/app/(admin)/(quotes)/quotes/customer/page.tsx"


def main() -> None:
    text = TEMPLATE
    for key, value in LABELS.items():
        text = text.replace(f"@@{key}@@", value)
    if "@@" in text:
        missing = [part for part in text.split("@@") if part and part in LABELS]
        raise SystemExit(f"Unresolved placeholders remain in template")
    OUT.write_text(text, encoding="utf-8")
    print(f"Wrote {OUT} ({len(text)} bytes)")


if __name__ == "__main__":
    main()
