"""The admin app must serve the security headers that do not depend on deployment details.

Round 205 measured two surfaces round 203 had flagged as "absent from the backend", and they turned out to be opposites:

* **CSRF — correctly absent.** No cookie-based authentication exists anywhere in the backend (zero uses of
  `set_cookie`, `Cookie(` or `request.cookies`), and `POST /auth/login` returns
  `TokenResponse(access_token=..., refresh_token=...)` **in the body**, so the client sends `Authorization: Bearer`. A
  cross-site form post cannot attach that header, so CSRF protection is not merely missing — it is unnecessary.
* **Security headers — genuinely absent.** Nothing in `apps/web-admin/next.config.ts` and nothing anywhere else under
  `apps/` or `packages/` set any of them, so the admin UI served HTML with no clickjacking control and no
  content-type protection.

This pins the four headers that are safe to send regardless of how the app is deployed beyond HTTPS.

**A `Content-Security-Policy` is deliberately not asserted, and not set.** A restrictive policy that has not been
exercised in a real browser breaks whatever it was not tested against, and this session cannot run one — so shipping one
would be a claim this project could not check. When a browser check exists, that is the change that adds it.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "apps" / "web-admin" / "next.config.ts"

REQUIRED_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


def test_the_admin_app_sets_the_deployment_independent_security_headers():
    assert CONFIG.is_file(), f"the admin app's Next config is missing: {CONFIG}"
    source = CONFIG.read_text(encoding="utf-8", errors="replace")

    missing = [key for key in REQUIRED_HEADERS if key not in source]
    assert missing == [], (
        "the admin app no longer sets these security headers, so it serves HTML without them:\n  "
        + "\n  ".join(missing)
        + "\nRound 205 measured that none were set; this test is what keeps that from happening again."
    )

    wrong = [
        key
        for key, value in REQUIRED_HEADERS.items()
        if f'"{key}"' in source and f'"{value}"' not in source and value not in source
    ]
    assert wrong == [], f"these headers are set but not to the recorded value: {wrong}"

    assert "headers()" in source or "headers:" in source, (
        "the config no longer defines a `headers()` function, so the header block may have been left unreachable"
    )
