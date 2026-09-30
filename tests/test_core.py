import pytest

pytestmark = pytest.mark.django_db


def test_home_page(client):
    assert client.get("/").status_code == 200


def test_liveness(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness(client):
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_health_endpoints_reject_post(client):
    assert client.post("/healthz").status_code == 405


def test_unknown_page_uses_custom_404(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert b"Page not found" in response.content


def test_health_checks_work_for_any_host_header(client):
    """Load balancers call by internal IP; this must not be rejected as an unknown host."""
    assert client.get("/healthz", HTTP_HOST="10.0.3.7").status_code == 200
    assert client.get("/readyz", HTTP_HOST="10.0.3.7").status_code == 200


def test_other_pages_still_reject_unknown_hosts(client):
    assert client.get("/", HTTP_HOST="evil.example").status_code == 400
