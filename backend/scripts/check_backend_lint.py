"""Non-blocking backend lint/type report (K-007).

Exit code is always 0 unless --strict is passed (for future CI). Writes a summary to stdout
and optionally to --baseline-out. Installs nothing; requires `ruff` (and optionally `mypy`)
on PATH or in the active venv.

  python scripts/check_backend_lint.py
  python scripts/check_backend_lint.py --baseline-out ../../logs/ruff-backend-baseline.txt
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when ruff/mypy report findings (default: always 0).",
    )
    parser.add_argument(
        "--baseline-out",
        type=Path,
        default=None,
        help="Write condensed baseline counts to this path.",
    )
    parser.add_argument("--skip-mypy", action="store_true")
    args = parser.parse_args()

    lines: list[str] = []
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines.append(f"# backend lint baseline {ts}")
    lines.append(f"# cwd={BACKEND_ROOT}")
    lines.append("# mode=non-blocking (K-007); --strict to fail CI later")

    findings = 0
    py = sys.executable
    code, out = _run(
        [py, "-m", "ruff", "check", "app", "scripts", "tests", "integration_tests", "workers", "--statistics"]
    )
    if "No module named ruff" in out or "No module named 'ruff'" in out:
        lines.append("ruff: NOT_INSTALLED")
        print("\n".join(lines))
        print("Install: pip install ruff mypy", file=sys.stderr)
        return 1 if args.strict else 0

    lines.append(f"ruff_exit={code}")
    issue_count = 0
    for ln in out.splitlines():
        # Strip ANSI; statistics rows look like "104\tUP037\t..."
        plain = "".join(ch for ch in ln if ch == "\t" or 32 <= ord(ch) < 127)
        parts = plain.strip().split()
        if len(parts) >= 2 and parts[0].isdigit() and parts[1][:1].isalpha():
            issue_count += int(parts[0])
        if plain.strip().startswith("Found ") and " error" in plain:
            try:
                issue_count = max(issue_count, int(plain.split()[1]))
            except (IndexError, ValueError):
                pass
    findings += issue_count
    lines.append(f"ruff_issue_count={issue_count}")
    lines.append("--- ruff check --statistics ---")
    lines.append(out.rstrip() or "(clean)")

    if not args.skip_mypy:
        # No path args → mypy uses [tool.mypy] files= from pyproject (scoped adopt).
        mcode, mout = _run([py, "-m", "mypy"])
        if "No module named mypy" in mout or "No module named 'mypy'" in mout:
            lines.append("mypy: NOT_INSTALLED")
        else:
            mypy_errors = 0
            for ln in mout.splitlines():
                if ln.startswith("Found ") and " error" in ln:
                    try:
                        mypy_errors = int(ln.split()[1])
                    except (IndexError, ValueError):
                        pass
            findings += mypy_errors
            lines.append(f"mypy_exit={mcode}")
            lines.append(f"mypy_error_count={mypy_errors}")
            lines.append("--- mypy (scoped files in pyproject) ---")
            lines.append(mout.rstrip() or "(clean)")

    lines.append(f"total_findings≈{findings}")
    text = "\n".join(lines) + "\n"
    print(text)
    if args.baseline_out:
        args.baseline_out.parent.mkdir(parents=True, exist_ok=True)
        args.baseline_out.write_text(text, encoding="utf-8")
        print(f"wrote {args.baseline_out}", file=sys.stderr)

    if args.strict and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
