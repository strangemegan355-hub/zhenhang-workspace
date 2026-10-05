"""OEE must carry one scale and must say where it came from.

The board returned a single `oee` object whether the numbers were measured MES snapshots or derived
from quote states, and both front ends multiplied it by 100 while the API reports percentages — a
real 72.675 rendered as 7267.5%. These tests pin the scale, the provenance marker, the averaging
rule and the front ends' arithmetic.

They import the service module, so `SECRET_KEY` is set before that import, as elsewhere in this
suite: collection of every test module happens before the session fixtures run.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "0123456789012345678901234567890123")

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
SERVICE = BACKEND / "app" / "services" / "workshop_board_service.py"
BOARD_PAGE = (
    REPO / "apps" / "web-admin" / "src" / "app" / "(admin)" / "(supply)" / "workshop" / "page.tsx"
)
TERMINAL = REPO / "apps" / "workshop-terminal" / "src" / "App.tsx"


def test_estimate_is_expressed_as_a_percentage():
    from app.services.workshop_board_service import _estimate_oee

    estimate = _estimate_oee(approved=8, reviewing=2, export_pending=1, total_active=10)
    assert estimate["availability"] == 80.0
    assert estimate["performance"] == 84.0
    assert estimate["quality"] == 95.0
    assert estimate["oee"] == round(80.0 * 84.0 * 95.0 / 10000, 3)
    for value in estimate.values():
        assert 0 <= value <= 100, "the payload and the displays share one scale: percentages"


def test_mes_average_recomputes_oee_from_the_components():
    from app.services.workshop_board_service import _average_mes_oee

    summary = _average_mes_oee(
        {
            "L1": {"availability": 90.0, "performance": 80.0, "quality": 100.0, "oee": 72.0},
            "L2": {"availability": 70.0, "performance": 60.0, "quality": 90.0, "oee": 37.8},
        }
    )
    assert summary is not None
    assert summary["line_count"] == 2
    assert summary["availability"] == 80.0
    assert summary["performance"] == 70.0
    assert summary["quality"] == 95.0
    # Recomputed from the averaged components, not the average of the two OEE values (54.9).
    assert summary["oee"] == round(80.0 * 70.0 * 95.0 / 10000, 3)


def test_no_snapshot_means_no_measured_value():
    from app.services.workshop_board_service import _average_mes_oee

    assert _average_mes_oee({}) is None


def test_the_payload_states_its_source():
    source = SERVICE.read_text(encoding="utf-8")
    assert '"source": oee_source' in source
    for marker in ('oee_source = "mes"', 'oee_source = "estimated"'):
        assert marker in source, marker
    assert '"unit": "percent"' in source


def test_front_ends_do_not_rescale_the_oee():
    """Both boards must display the percentage as delivered, and label an estimate."""
    for path in (BOARD_PAGE, TERMINAL):
        text = path.read_text(encoding="utf-8")
        oee_lines = [line for line in text.splitlines() if "oee.oee" in line and "Number(" in line]
        assert oee_lines, f"{path.name} no longer reads oee.oee"
        for line in oee_lines:
            assert "* 100" not in line, f"{path.name} rescales a percentage: {line.strip()}"
        assert "oeeSource" in text, f"{path.name} does not distinguish measured from estimated"
        assert re.search(r'oeeSource === "mes"', text), f"{path.name} does not render the origin"
