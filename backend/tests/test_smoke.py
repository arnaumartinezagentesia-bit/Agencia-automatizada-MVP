from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_app_imports_and_is_titled():
    assert app.title == "Agencia Automatizada MVP-0"


def test_docs_and_openapi_are_served():
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_no_business_routes_in_openapi():
    # Phase 1 guard: no routes of any kind until their phase.
    assert client.get("/openapi.json").json()["paths"] == {}
