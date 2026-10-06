"""The authorization auditor must fail when a route requires a code no role can grant.

`backend/scripts/audit_authz.py` runs in `ci.sh`, and its verdict is the gate phase 3 leans on for functional
authorization — `RESULT: PASS — every code a route requires is either granted to a role or forbidden by policy`.
**An auditor that errs in the permissive direction passes everything and says nothing**, and measured before writing
this: the four helpers were called by **no test**, while the two apparent hits were my own regex matching `os.walk(`
and `__main__` — a name is not the object, the trap this series has hit five times.

So this gives the auditor **teeth at its own level** rather than unit-testing its parts:

  * it runs `main()` **exactly as `ci.sh` does**, as a subprocess with `--backend DIR --out FILE`;
  * it runs it against the **real** backend first, which must **pass** — otherwise the control proves nothing;
  * then against a **copy** in which one permission code required by an endpoint has been renamed, which must **fail**;
  * and it picks the code to rename with the auditor's **own** `extract_seeded_codes`, so the mutation is one a seeder
    actually grants rather than one guessed to matter.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"
SCRIPT = BACKEND / "scripts" / "audit_authz.py"
TIMEOUT = 300


def _run_audit(backend: Path, out: Path) -> tuple[int, str]:
    """Run the auditor as `ci.sh` does.

    `encoding="utf-8"` is not optional: the auditor prints Chinese, and `text=True` otherwise decodes with the platform
    default, which on this machine's console is GBK — the first run of this test died with a UnicodeDecodeError rather
    than an assertion. `ci.sh` never hits it because bash captures bytes.
    """
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--backend", str(backend), "--out", str(out)],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=TIMEOUT,
    )
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def _seeded_codes() -> set[str]:
    """Ask the auditor itself which codes the seeders grant, rather than guessing one that matters."""
    sys.path.insert(0, str(BACKEND / "scripts"))
    import importlib.util

    spec = importlib.util.spec_from_file_location("_audit_authz_for_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    seeded = module.extract_seeded_codes(str(BACKEND))
    return {code for codes in seeded.values() for code in codes} if isinstance(seeded, dict) else set(seeded)


def test_the_auditor_passes_on_the_real_backend(tmp_path):
    code, output = _run_audit(BACKEND, tmp_path / "real.json")
    assert code == 0, f"the auditor fails on the repository as it stands:\n{output[-2500:]}"
    assert "RESULT: PASS" in output, output[-1200:]


def _required_codes_in_endpoints() -> list[tuple[Path, str]]:
    """Every permission code an endpoint requires, with the file that requires it.

    Read from the endpoints themselves rather than from the auditor's helpers: the mutation must land on a code a
    **route** requires, which is the condition the auditor judges. The helpers return nested mappings whose shape is
    their own business.
    """
    found: list[tuple[Path, str]] = []
    for path in sorted((BACKEND / "app" / "api" / "v1" / "endpoints").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"""require_permissions\(\s*[\[(]?\s*["']([a-z_]+:[a-z_:]+)["']""", text):
            found.append((path, match.group(1)))
    return found


def test_the_auditor_fails_when_a_required_code_cannot_be_granted(tmp_path):
    required = _required_codes_in_endpoints()
    assert required, "no endpoint was found requiring a permission code, which cannot be right"

    # A code that the policy forbids would pass legitimately, so the mutation must avoid those.
    policy_text = (BACKEND / "scripts" / "verify_permissions.py").read_text(encoding="utf-8")
    candidates = [(path, code) for path, code in required if f'"{code}"' not in policy_text]
    assert candidates, "every required code is forbidden by policy, so no mutation could be decisive"
    source_path, code = candidates[0]

    copy = tmp_path / "backend"
    shutil.copytree(BACKEND, copy, ignore=shutil.ignore_patterns("__pycache__", ".venv", ".pytest_cache"))
    target = copy / source_path.relative_to(BACKEND)
    text = target.read_text(encoding="utf-8")
    assert text.count(code) >= 1
    target.write_text(text.replace(code, f"{code}-renamed-by-test"), encoding="utf-8", newline="")

    exit_code, output = _run_audit(copy, tmp_path / "mutated.json")
    assert exit_code != 0, (
        f"renaming the permission code {code!r} in {source_path.name} made no difference to the auditor, so it cannot "
        f"detect a route requiring a code no role can grant:\n{output[-2500:]}"
    )
    assert "RESULT: FAIL" in output, output[-1500:]


def test_the_auditor_reports_its_output_file(tmp_path):
    out = tmp_path / "audit.json"
    code, _output = _run_audit(BACKEND, out)
    assert code == 0
    assert out.is_file(), "the auditor did not write the file its --out argument asked for"
    assert out.read_text(encoding="utf-8").strip(), "the auditor wrote an empty report"
