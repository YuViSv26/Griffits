import logging

from fastapi import APIRouter, HTTPException, Response

from backend.auth_utils import create_access_token
from backend.config import get_settings
from backend.db import create_user, get_user_by_login, sync_baby_profile_from_auth
from backend.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from backend.utils.name_auth import build_display_name

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.jwt_expire_minutes * 60,
    )


def _auth_response(user, response: Response) -> AuthResponse:
    display_name = build_display_name(user.first_name, user.patronymic, user.last_name)
    if not display_name.strip():
        display_name = user.login_code
    token = create_access_token(user.id, display_name)
    _set_auth_cookie(response, token)
    return AuthResponse(
        user_id=user.id,
        display_name=display_name,
        login_code=user.login_code,
        access_token=token,
    )


@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest, response: Response) -> AuthResponse:
    login_code = body.login_code
    birth_date = body.birth_date()

    existing = await get_user_by_login(login_code, birth_date)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким именем и датой рождения уже зарегистрирован",
        )

    try:
        user = await create_user(
            login_code=body.login_code,
            user_birthday=birth_date,
        )
    except Exception:
        logger.exception("Register failed")
        raise HTTPException(status_code=500, detail="Ошибка регистрации")

    return _auth_response(user, response)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, response: Response) -> AuthResponse:
    login_code = body.login_code
    birth_date = body.birth_date()

    user = await get_user_by_login(login_code, birth_date)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Неверное имя или дата рождения",
        )

    user = await sync_baby_profile_from_auth(user.id)

    return _auth_response(user, response)


@router.post("/logout")
async def logout(response: Response) -> dict:
    settings = get_settings()
    response.delete_cookie(settings.cookie_name)
    return {"ok": True}
