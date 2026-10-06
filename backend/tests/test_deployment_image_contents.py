"""Every module a container starts must be copied into the image that starts it.

`docker-compose.prod.yml` starts containers with `python -m workers.event_worker` and
`python -m workers.maintenance_worker`, and `backend/Dockerfile` did not copy `workers/` — so both would
have failed with `ModuleNotFoundError` in production. That is worse than a crashed container: the event
dispatcher runs in the worker, so events would have stopped being dispatched while the API stayed healthy.

The build could not be run to check this (Docker Hub is unreachable from this machine and the base images
are not cached), so the invariant is pinned statically instead: what the Dockerfile copies must cover what
the container commands import. A positive control keeps the check falsifiable, in the same spirit as the
secrets guard.
"""

from __future__ import annotations

import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent

# The compose is read as text: it is a small file and the question is only which commands run.
MODULE_COMMAND = re.compile(r"python\s+-m\s+([A-Za-z_][\w.]*)")
SCRIPT_COMMAND = re.compile(r"python\s+(scripts/[\w./-]+\.py)")
COPY_SOURCE = re.compile(r"^COPY\s+(\S+)", re.MULTILINE)


def _copied_sources(dockerfile_text: str) -> set[str]:
    return {match.strip("./") for match in COPY_SOURCE.findall(dockerfile_text)}


def _commands(compose_text: str) -> tuple[set[str], set[str]]:
    modules = {match.split(".")[0] for match in MODULE_COMMAND.findall(compose_text)}
    scripts = {match.split("/")[0] for match in SCRIPT_COMMAND.findall(compose_text)}
    return modules, scripts


def test_the_compose_still_starts_python_modules_and_scripts():
    """If the compose stopped invoking python, the checks below would pass vacuously."""
    compose = (REPO / "docker-compose.prod.yml").read_text(encoding="utf-8")
    modules, scripts = _commands(compose)
    assert "workers" in modules, f"expected a workers module command, found {sorted(modules)}"
    assert "scripts" in scripts, f"expected a scripts command, found {sorted(scripts)}"


def test_every_module_a_container_starts_is_copied_into_the_image():
    compose = (REPO / "docker-compose.prod.yml").read_text(encoding="utf-8")
    copied = _copied_sources((BACKEND / "Dockerfile").read_text(encoding="utf-8"))
    modules, scripts = _commands(compose)

    missing = sorted((modules | scripts) - copied)
    assert missing == [], (
        "docker-compose.prod.yml starts containers that import "
        f"{missing}, but backend/Dockerfile does not copy them; the container would exit with "
        "ModuleNotFoundError"
    )


def test_the_check_notices_a_missing_copy():
    """A check that cannot fail is decoration: run it against the Dockerfile as it was before the fix."""
    pre_fix = """FROM python:3.11-slim
COPY requirements.txt /app/requirements.txt
COPY alembic.ini /app/alembic.ini
COPY scripts /app/scripts
COPY alembic /app/alembic
COPY app /app/app
CMD ["uvicorn", "app.main:app"]
"""
    copied = _copied_sources(pre_fix)
    assert "workers" not in copied, "the positive control must model the pre-fix Dockerfile"
    assert "app" in copied and "scripts" in copied, "the control should still find the copies that were there"
