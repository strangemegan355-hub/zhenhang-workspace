"""401/403 must not inflate enterprise_metrics error_rate (workshop/auth polling)."""

from app.core.enterprise_metrics import EnterpriseMetrics


def test_auth_challenges_excluded_from_error_rate():
    m = EnterpriseMetrics()
    m.mark_request(elapsed_ms=1.0, status_code=200)
    m.mark_request(elapsed_ms=2.0, status_code=401)
    m.mark_request(elapsed_ms=3.0, status_code=403)
    m.mark_request(elapsed_ms=4.0, status_code=500)

    snap = m.snapshot()["api"]
    assert snap["request_total"] == 4
    assert snap["error_total"] == 1
    assert snap["auth_challenge_total"] == 2
    assert snap["error_rate"] == 0.25


def test_client_4xx_still_counts_as_error_except_auth():
    m = EnterpriseMetrics()
    m.mark_request(elapsed_ms=1.0, status_code=400)
    m.mark_request(elapsed_ms=1.0, status_code=404)
    m.mark_request(elapsed_ms=1.0, status_code=422)

    snap = m.snapshot()["api"]
    assert snap["request_total"] == 3
    assert snap["error_total"] == 3
    assert snap["auth_challenge_total"] == 0
    assert snap["error_rate"] == 1.0
