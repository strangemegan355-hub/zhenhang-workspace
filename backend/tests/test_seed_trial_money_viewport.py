"""Static checks for trial money-viewport seeder (no live DB required)."""

from __future__ import annotations

import ast
from pathlib import Path

SEEDER = Path(__file__).resolve().parents[1] / "scripts" / "seed_trial_money_viewport.py"


def test_seed_trial_money_viewport_script_exists_and_parses():
    assert SEEDER.is_file()
    src = SEEDER.read_text(encoding="utf8")
    tree = ast.parse(src)
    assert "Idempotent" in src or "idempotent" in src.lower()
    assert "accounting_enabled" in src
    assert "TRIAL-MAT-001" in src
    assert "TRIAL-PR-0001" in src
    assert "TRIAL-AR-0001" in src
    assert "TRIAL-AP-0001" in src
    assert "TRIAL-PR-0003" in src
    assert "--with-pending-approval" in src
    assert "allow-non-local" in src
    assert "local-trial only" in src or "local trial" in src.lower()
    # Finance safety: seed only creates draft samples; no confirm/void helpers.
    assert 'status="draft"' in src
    assert "confirm_entry" not in src
    assert "void_entry" not in src
    assert "draft only" in src
    # Optional pending flag must remain opt-in (default OFF).
    assert "with_pending_approval" in src
    assert "approve_request" not in src
    assert "action=approve" not in src
    # Smoke: argparse defaults — with-pending-approval is store_true (off unless passed).
    main_fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    src_main = ast.get_source_segment(src, main_fn) or ""
    assert 'add_argument(\n        "--with-pending-approval"' in src or '"--with-pending-approval"' in src_main
    assert "store_true" in src_main
