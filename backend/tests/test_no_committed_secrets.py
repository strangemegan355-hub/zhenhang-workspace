"""No key material or environment file may be tracked by git.

The repository is already clean — the only key-like files on disk are a self-signed development
certificate pair, ignored since `94b5a7d` and never committed — but "clean today" is not a guard
rail. The `.gitignore` rules are what prevent a private key from being committed, and a rule can be
edited away by accident. These tests pin the outcome:

  * no tracked file contains a private key header;
  * the certificate paths are actually ignored (asked of git, not inferred from the filename);
  * every environment file present on disk is ignored.

They read git rather than guessing, and they skip where there is no git checkout (a source tarball).
A positive control makes the detector itself falsifiable: a test that cannot fail is decoration.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent

PRIVATE_KEY_HEADER = re.compile(r"BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY")

CERTIFICATES = [
    "deploy/nginx/certs/privkey.pem",
    "deploy/nginx/certs/fullchain.pem",
]
ENVIRONMENT_FILES = [
    ".env",
    "backend/.env",
    "backend/.env.prod",
    "apps/web-admin/.env.local",
    "apps/workshop-terminal/.env.local",
]
SKIP_DIRS = {".git", "node_modules", ".venv", ".next", "__pycache__"}


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git_available() -> bool:
    return _git("rev-parse", "--is-inside-work-tree").stdout.strip() == "true"


pytestmark = pytest.mark.skipif(not _git_available(), reason="not a git checkout")


# Composed at runtime, never written literally: a real header in this file would (correctly) make
# test_no_tracked_file_contains_private_key_material fail, since the detector cannot tell a fixture
# from a leaked key and should not try.
SAMPLE_KEY_HEADER = "-----BEGIN " + "RSA " + "PRIVATE KEY-----" + "\nMIIE..."
SAMPLE_OPENSSH_HEADER = "-----BEGIN " + "OPENSSH " + "PRIVATE KEY-----"
SAMPLE_CERTIFICATE_HEADER = "-----BEGIN " + "CERTIFICATE-----"


def test_the_detector_recognises_a_private_key():
    """Positive control: without this the file could pass by matching nothing at all."""
    assert PRIVATE_KEY_HEADER.search(SAMPLE_KEY_HEADER)
    assert PRIVATE_KEY_HEADER.search(SAMPLE_OPENSSH_HEADER)
    assert not PRIVATE_KEY_HEADER.search(SAMPLE_CERTIFICATE_HEADER)


def test_no_tracked_file_contains_private_key_material():
    tracked = [line for line in _git("ls-files").stdout.splitlines() if line.strip()]
    assert tracked, "git reported no tracked files"

    offenders: list[str] = []
    for relative in tracked:
        path = REPO / relative
        if any(part in SKIP_DIRS for part in Path(relative).parts):
            continue
        try:
            body = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if PRIVATE_KEY_HEADER.search(body):
            offenders.append(relative)

    assert offenders == [], f"private key material is committed in: {offenders}"


def test_certificate_paths_are_ignored():
    """Ask git, so the verdict does not depend on reading the pattern correctly by eye."""
    for relative in CERTIFICATES:
        result = _git("check-ignore", "--no-index", relative)
        assert result.returncode == 0, (
            f"{relative} is not ignored; a private key committed by accident is exactly what the "
            "rule exists to prevent"
        )


def test_environment_files_on_disk_are_ignored():
    present = [relative for relative in ENVIRONMENT_FILES if (REPO / relative).exists()]
    ignored = []
    for relative in present:
        if _git("check-ignore", relative).returncode == 0:
            ignored.append(relative)
    assert ignored == present, (
        "these environment files exist but are not ignored, so a real credential could be "
        f"committed: {sorted(set(present) - set(ignored))}"
    )


def test_gitignore_still_carries_the_certificate_rules():
    """The rule the two tests above depend on, stated where a reader will look for it."""
    patterns = (REPO / ".gitignore").read_text(encoding="utf-8")
    for expected in ("deploy/nginx/certs/*.pem", "deploy/nginx/certs/*.key"):
        assert expected in patterns, f".gitignore no longer excludes {expected}"


def test_no_stray_key_files_outside_the_ignored_directory():
    """A key anywhere else would sit outside the ignore rules entirely."""
    found: list[str] = []
    for base, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith((".pem", ".key", ".p12", ".pfx", ".jks", ".keystore")):
                relative = os.path.relpath(os.path.join(base, name), REPO).replace("\\", "/")
                if not relative.startswith("deploy/nginx/certs/"):
                    found.append(relative)
    assert found == [], f"key-like files outside the ignored directory: {found}"
