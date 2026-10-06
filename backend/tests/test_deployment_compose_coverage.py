"""The deployment guards round 67 started, extended to every compose, both images, and the healthcheck tools.

`tests/test_deployment_image_contents.py` pins one invariant well: whatever `docker-compose.prod.yml` starts
with `python -m`/`python scripts/…` must be copied by `backend/Dockerfile`. Measuring around it found three gaps
in that guard — not in the deployment:

* it reads **one** compose, while `docker-compose.yml` runs `python scripts/bootstrap_admin.py`,
  `python scripts/seed_workflows.py` and `python -m workers.event_worker` through the same image;
* it reads **one** Dockerfile, while `apps/web-admin/Dockerfile` exists with its own `CMD` and `HEALTHCHECK`;
* it never asks whether a healthcheck's tool exists in the image it probes.

That last one turned out to be correct everywhere, and `UPSTREAM_IMAGE_TOOLS` records how that was established:
five images were probed by running them (they are cached here) and the sixth, `node:20-alpine`, is not cached,
so its case is covered by its Dockerfile installing curl.
"""

from __future__ import annotations

import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent

# An explicit list rather than a glob: a recursive match would also find vendor compose files under node_modules.
COMPOSES = (
    "docker-compose.yml",
    "docker-compose.prod.yml",
    "backend/integration_tests/docker-compose.integration.yml",
)
LOCAL_DOCKERFILES = (BACKEND / "Dockerfile", REPO / "apps" / "web-admin" / "Dockerfile")

MODULE_COMMAND = re.compile(r"python\s+-m\s+([A-Za-z_][\w.]*)")
SCRIPT_COMMAND = re.compile(r"python\s+(scripts/[\w./-]+\.py)")
COPY_SOURCE = re.compile(r"^COPY\s+(\S+)", re.MULTILINE)
SERVICE_HEADER = re.compile(r"^  ([\w.-]+):\s*$", re.MULTILINE)
HEALTHCHECK_TOOL = re.compile(r"\"(?:CMD|CMD-SHELL)\",\s*\"(?:sh -c )?\"?([\w-]+)")
INSTALLED_TOOL = re.compile(r"(?:apk add|apt-get install)[^\n]*?(curl|wget)")

# Measured, not assumed: `docker run --rm --entrypoint sh <image> -c 'command -v …'` for the five that are
# cached on this machine. `node:20-alpine` is not cached, and its Dockerfile installs curl itself.
UPSTREAM_IMAGE_TOOLS: dict[str, set[str]] = {
    "postgres:16-alpine": {"pg_isready", "wget"},
    "redis:7-alpine": {"redis-cli", "wget"},
    "minio/minio:latest": {"curl"},
    "nginx:1.27-alpine": {"wget", "curl"},
}


def _copied_sources(dockerfile_text: str) -> set[str]:
    return {match.strip("./") for match in COPY_SOURCE.findall(dockerfile_text)}


def _compose_texts() -> dict[str, str]:
    texts: dict[str, str] = {}
    for relative in COMPOSES:
        path = REPO / relative
        assert path.exists(), f"{relative} is listed in COMPOSES but missing"
        texts[relative] = path.read_text(encoding="utf-8")
    return texts


def _services(text: str) -> dict[str, str]:
    """Split a compose into service blocks, two spaces of indentation.

    The document's other top-level sections (`volumes:`, `networks:`) use the same indentation, so the text is
    cut at the first of them; otherwise a named volume is reported as a service.
    """
    for section in ("\nvolumes:", "\nnetworks:", "\nconfigs:", "\nsecrets:"):
        cut = text.find(section)
        if cut != -1:
            text = text[:cut]
    starts = [(match.start(), match.group(1)) for match in SERVICE_HEADER.finditer(text)]
    blocks: dict[str, str] = {}
    for index, (position, name) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(text)
        blocks[name] = text[position:end]
    return blocks


def _installed_tools() -> set[str]:
    return {
        tool
        for path in LOCAL_DOCKERFILES
        for tool in INSTALLED_TOOL.findall(path.read_text(encoding="utf-8"))
    }


def test_every_python_command_in_any_compose_is_copied_into_the_image():
    copied = _copied_sources((BACKEND / "Dockerfile").read_text(encoding="utf-8"))
    modules: set[str] = set()
    scripts: set[str] = set()
    for text in _compose_texts().values():
        modules |= {match.split(".")[0] for match in MODULE_COMMAND.findall(text)}
        scripts |= {match.split("/")[0] for match in SCRIPT_COMMAND.findall(text)}

    missing = sorted((modules | scripts) - copied)
    assert missing == [], (
        f"a compose starts containers that import {missing}, but backend/Dockerfile does not copy them; the "
        "container would exit with ModuleNotFoundError"
    )
    assert "workers" in modules and "scripts" in scripts, (
        "the composes should still start a workers module and a script, or this check passes vacuously"
    )


def test_every_compose_that_runs_python_builds_from_a_local_dockerfile():
    """The check above compares every compose against backend/Dockerfile, so that assumption is checked."""
    offenders = [
        relative
        for relative, text in _compose_texts().items()
        if (MODULE_COMMAND.search(text) or SCRIPT_COMMAND.search(text)) and "dockerfile:" not in text
    ]
    assert offenders == [], (
        f"these composes run python without a dockerfile:, so their commands cannot be compared against a "
        f"local image: {offenders}"
    )


def test_every_healthcheck_tool_exists_in_the_image_it_probes():
    problems: list[str] = []
    checked = 0
    installed = _installed_tools()

    for relative, text in _compose_texts().items():
        for name, block in _services(text).items():
            if "healthcheck:" not in block:
                continue
            tool = HEALTHCHECK_TOOL.search(block)
            if not tool:
                continue
            tool_name = tool.group(1)
            if tool_name not in {"curl", "wget", "pg_isready", "redis-cli"}:
                continue
            checked += 1

            upstream = re.search(r"^\s*image:\s*(\S+)", block, re.MULTILINE)
            if upstream:
                image = upstream.group(1).split(":")[0] + ":" + upstream.group(1).split(":", 1)[-1]
                known = next((tools for key, tools in UPSTREAM_IMAGE_TOOLS.items() if key.startswith(upstream.group(1).split(":")[0])), None)
                if known is not None and tool_name not in known:
                    problems.append(f"{relative}#{name}: {image} lacks {tool_name} (has {sorted(known)})")
                continue

            if tool_name not in installed:
                problems.append(
                    f"{relative}#{name}: the service builds locally but no local Dockerfile installs {tool_name}"
                )

    assert checked >= 4, f"expected several tool-based healthchecks, found {checked}"
    assert problems == [], "these healthchecks would never pass:\n  " + "\n  ".join(problems)
