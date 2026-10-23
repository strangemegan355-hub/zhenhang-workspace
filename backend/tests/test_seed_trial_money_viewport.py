"""Static checks for trial money-viewport seeder (no live DB required)."""

from __future__ import annotations

import ast
from pathlib import Path

SEEDER = Path(__file__).resolve().parents[1] / "scripts" / "seed_trial_money_viewport.py"


def test_seed_trial_money_viewport_script_exists_and_parses():
    assert SEEDER.is_file()
    src = SEEDER.read_text(encoding="utf8")
    ast.parse(src)
    assert "Idempotent" in src or "idempotent" in src.lower()
    assert "accounting_enabled" in src
    assert "TRIAL-MAT-001" in src
    assert "TRIAL-PR-0001" in src
    assert "TRIAL-AR-0001" in src
    assert "TRIAL-AP-0001" in src
    # Finance safety: seed only creates draft samples; no confirm/void helpers.
    assert 'status="draft"' in src
    assert "confirm_entry" not in src
    assert "void_entry" not in src
    assert "draft only" in src
