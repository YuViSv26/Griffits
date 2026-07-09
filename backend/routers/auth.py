import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, Response

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


def _allowed_frontend_origins(settings) -> set[str]:
    origins = {settings.frontend_url.rstrip("/")}
    origins.update(origin.rstrip("/") for origin in settings.cors_origins)
    return origins


def _resolve_reset_base_url(candidate: str | None, settings) -> str:
    if candidate:
        base = candidate.strip().rstrip("/")
        if base in _allowed_frontend_origins(settings):
            return base
        logger.warning(
            "reset_base_url %s не в списке разрешённых адресов, используем FRONTEND_URL",
            base,
        )
    return settings.frontend_url.rstrip("/")


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
async def forgot_password(
    body: ForgotPasswordRequest, request: Request
) -> ForgotPasswordResponse:
    settings = get_settings()
    email_sent = False
    reset_url: str | None = None

    smtp_error: str | None = None
    user = await get_user_by_email(body.email)
    if user:
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        await create_password_reset_token(user.id, token, expires)
        base_url = _resolve_reset_base_url(
            body.reset_base_url or request.headers.get("origin"),
            settings,
        )
        reset_url = f"{base_url}/?reset={token}"

        if smtp_configured():
            email_sent, smtp_error = send_password_reset_email(user.email, reset_url)
            if not email_sent:
                logger.error(
                    "Не удалось отправить письмо сброса пароля на %s: %s",
                    user.email,
                    smtp_error,
                )
        else:
            logger.warning(
                "SMTP не настроен (SMTP_HOST, SMTP_FROM, SMTP_USER, SMTP_PASSWORD). "
                "Ссылка сброса для %s: %s",
                user.email,
                reset_url,
            )

    if email_sent:
        message = (
            "Ссылка для сброса пароля отправлена на ваш email. "
            "Проверьте входящие и папку «Спам»."
        )
    elif user and settings.app_debug and reset_url:
        message = (
            "Почта не настроена или не отправилась — используйте ссылку ниже "
            "(режим разработки)."
        )
        if smtp_error:
            message += f" Ошибка SMTP: {smtp_error}"
    elif user and not email_sent:
        message = (
            "Не удалось отправить письмо. Попробуйте позже или обратитесь к администратору."
        )
        logger.error(
            "forgot-password: пользователь %s найден, но письмо не отправлено",
            body.email,
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
