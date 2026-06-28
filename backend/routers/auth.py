import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Response

from backend.auth_utils import create_access_token, hash_password, verify_password
from backend.config import get_settings
from backend.db import (
    create_password_reset_token,
    create_user,
    get_user_by_email,
    get_valid_reset_token,
    mark_reset_token_used,
    update_user_password,
)
from backend.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from backend.services.email import send_password_reset_email, smtp_configured
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


@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest, response: Response) -> AuthResponse:
    existing = await get_user_by_email(body.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    try:
        user = await create_user(body.email, hash_password(body.password))
    except Exception:
        logger.exception("Register failed")
        raise HTTPException(status_code=500, detail="Ошибка регистрации")

    token = create_access_token(user.id, user.email)
    _set_auth_cookie(response, token)
    return AuthResponse(user_id=user.id, email=user.email, access_token=token)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, response: Response) -> AuthResponse:
    user = await get_user_by_email(body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    token = create_access_token(user.id, user.email)
    _set_auth_cookie(response, token)
    return AuthResponse(user_id=user.id, email=user.email, access_token=token)


@router.post("/logout")
async def logout(response: Response) -> dict:
    settings = get_settings()
    response.delete_cookie(settings.cookie_name)
    return {"ok": True}


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(body: ForgotPasswordRequest) -> ForgotPasswordResponse:
    settings = get_settings()
    email_sent = False
    reset_url: str | None = None

    user = await get_user_by_email(body.email)
    if user:
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        await create_password_reset_token(user.id, token, expires)
        reset_url = f"{settings.frontend_url}/?reset={token}"

        if smtp_configured():
            email_sent, smtp_error = send_password_reset_email(user.email, reset_url)
            if not email_sent:
                logger.error("SMTP error: %s", smtp_error)
        else:
            logger.info("SMTP не настроен. Ссылка сброса: %s", reset_url)

    if email_sent:
        message = "Ссылка для сброса пароля отправлена на ваш email. Проверьте входящие и папку «Спам»."
    elif user and settings.app_debug and reset_url:
        message = (
            "Почта не настроена на сервере — используйте ссылку ниже "
            "(режим разработки)."
        )
    else:
        message = (
            "Если этот email зарегистрирован, инструкции будут отправлены на почту. "
            "Если письма нет — проверьте спам или обратитесь к администратору."
        )

    return ForgotPasswordResponse(
        message=message,
        email_sent=email_sent,
        reset_url=reset_url if (settings.app_debug and user and not email_sent) else None,
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(body: ResetPasswordRequest) -> ResetPasswordResponse:
    row = await get_valid_reset_token(body.token)
    if not row:
        raise HTTPException(
            status_code=400,
            detail="Ссылка недействительна или истекла. Запросите сброс снова.",
        )

    await update_user_password(row.user_id, hash_password(body.password))
    await mark_reset_token_used(body.token)

    return ResetPasswordResponse(message="Пароль обновлён. Теперь можно войти.")
