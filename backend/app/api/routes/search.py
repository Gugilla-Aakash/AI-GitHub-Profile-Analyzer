from typing import Any

from fastapi import APIRouter, HTTPException, Query
from hakiapi.core.exceptions import (
    AuthenticationError,
    ClientError,
    RateLimitError,
    RequestTimeoutError,
    ServerError,
)

from app.clients.github_client import AppGitHubClient
from app.config import settings

router = APIRouter()


@router.get("/")
def search_users(
    q: str = Query(..., min_length=1),
) -> Any:
    client = AppGitHubClient(token=settings.GITHUB_TOKEN)

    try:
        return client.search_users(q)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc
    except RateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail=str(exc),
        ) from exc
    except RequestTimeoutError as exc:
        raise HTTPException(
            status_code=529,
            detail=str(exc),
        ) from exc
    except ClientError as exc:
        raise HTTPException(
            status_code=exc.status_code or 400,
            detail=str(exc),
        ) from exc
    except ServerError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
