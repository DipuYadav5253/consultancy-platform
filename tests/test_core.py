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
