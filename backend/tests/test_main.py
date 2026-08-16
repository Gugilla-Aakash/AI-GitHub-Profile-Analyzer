from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_health_check_returns_200():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "github-analyzer Backend",
    }


def test_health_endpoint_returns_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "github-analyzer Backend",
    }


def test_cors_middleware_headers():
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    # Reflects the request origin when credentials are enabled
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_api_v1_routes_are_mounted():
    openapi_paths = app.openapi()["paths"].keys()

    assert "/api/v1/search/" in openapi_paths
    assert "/api/v1/analyze/{username}" in openapi_paths
    assert "/api/v1/report/{username}" in openapi_paths
    assert "/api/v1/chat/start/{username}" in openapi_paths
    assert "/api/v1/chat/message" in openapi_paths
