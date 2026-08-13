from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from hakiapi.core.exceptions import (
    AuthenticationError,
    ClientError,
    RateLimitError,
    RequestTimeoutError,
    ServerError,
)

from app.api.routes.search import router

# Setup a dummy app to mount the router for testing
app = FastAPI()
app.include_router(router)
client = TestClient(app)

MOCK_CLIENT_PATH = "app.api.routes.search.AppGitHubClient"


def test_search_users_returns_data_on_success():
    with patch(MOCK_CLIENT_PATH) as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        mock_instance.search_users.return_value = {"items": [{"login": "octocat"}]}

        response = client.get("/?q=octocat")

        assert response.status_code == 200
        assert response.json() == {"items": [{"login": "octocat"}]}
        mock_instance.search_users.assert_called_once_with("octocat")


def test_search_users_fails_if_query_is_missing_or_empty():
    # Missing completely
    response_missing = client.get("/")
    assert response_missing.status_code == 422

    # Empty string (violates min_length=1)
    response_empty = client.get("/?q=")
    assert response_empty.status_code == 422


def test_search_users_handles_authentication_error():
    with patch(MOCK_CLIENT_PATH) as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        exc = AuthenticationError("Invalid token")
        mock_instance.search_users.side_effect = exc

        response = client.get("/?q=test")

        assert response.status_code == 401
        assert response.json() == {"detail": str(exc)}


def test_search_users_handles_rate_limit_error():
    with patch(MOCK_CLIENT_PATH) as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        exc = RateLimitError("API limit exceeded")
        mock_instance.search_users.side_effect = exc

        response = client.get("/?q=test")

        assert response.status_code == 429
        assert response.json() == {"detail": str(exc)}


def test_search_users_handles_request_timeout_error():
    with patch(MOCK_CLIENT_PATH) as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        exc = RequestTimeoutError("Timeout")
        mock_instance.search_users.side_effect = exc

        response = client.get("/?q=test")

        assert response.status_code == 529
        assert response.json() == {"detail": str(exc)}


def test_search_users_handles_client_error_with_custom_status():
    with patch(MOCK_CLIENT_PATH) as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        exc = ClientError("Not Found", status_code=404)
        mock_instance.search_users.side_effect = exc

        response = client.get("/?q=test")

        assert response.status_code == 404
        assert response.json() == {"detail": str(exc)}


def test_search_users_handles_client_error_default_status():
    with patch(MOCK_CLIENT_PATH) as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        exc = ClientError("Bad Request")
        mock_instance.search_users.side_effect = exc

        response = client.get("/?q=test")

        assert response.status_code == 400  # Defaults to 400 in your router
        assert response.json() == {"detail": str(exc)}


def test_search_users_handles_server_error():
    with patch(MOCK_CLIENT_PATH) as mock_client_cls:
        mock_instance = mock_client_cls.return_value
        exc = ServerError("GitHub is down")
        mock_instance.search_users.side_effect = exc

        response = client.get("/?q=test")

        assert response.status_code == 502
        assert response.json() == {"detail": str(exc)}
