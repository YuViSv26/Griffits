from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.auth_utils import decode_access_token
from backend.config import get_settings
from backend.db import User, get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


async def get_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str | None:
    settings = get_settings()
    if credentials and credentials.credentials:
        return credentials.credentials
    return request.cookies.get(settings.cookie_name)


async def get_current_user(token: str | None = Depends(get_token)) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
        )
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
        )
    user = await get_user_by_id(int(payload["sub"]))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    return user


async def get_optional_user(token: str | None = Depends(get_token)) -> User | None:
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    return await get_user_by_id(int(payload["sub"]))
