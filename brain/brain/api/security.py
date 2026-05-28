"""Bearer token guard. Constant-time compare contra BRAIN_API_TOKEN."""
from __future__ import annotations

import hmac

from fastapi import HTTPException, Request, status


async def require_bearer(request: Request) -> None:
    expected: str = request.app.state.settings.api_token
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = header[len("Bearer ") :].strip()
    if not hmac.compare_digest(token, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="invalid bearer token",
        )
