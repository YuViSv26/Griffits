import logging
import smtplib
from email.message import EmailMessage

from backend.config import get_settings

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    s = get_settings()
    return bool(s.smtp_host and s.smtp_from and s.smtp_user and s.smtp_password)


def send_password_reset_email(to_email: str, reset_url: str) -> tuple[bool, str | None]:
    """Возвращает (успех, текст ошибки)."""
    settings = get_settings()
    if not smtp_configured():
        logger.warning(
            "SMTP не настроен полностью (нужны SMTP_HOST, SMTP_FROM, SMTP_USER, SMTP_PASSWORD)"
        )
        return False, "SMTP не настроен на сервере"

    msg = EmailMessage()
    msg["Subject"] = "Сброс пароля — Нейроконсультант Гриффитс"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content(
        f"Здравствуйте!\n\n"
        f"Для сброса пароля перейдите по ссылке (действует 1 час):\n{reset_url}\n\n"
        f"Если вы не запрашивали сброс, проигнорируйте это письмо."
    )

    try:
        if settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(
                settings.smtp_host, settings.smtp_port, timeout=20
            ) as server:
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        logger.info("Письмо сброса пароля отправлено на %s", to_email)
        return True, None
    except smtplib.SMTPAuthenticationError:
        logger.exception("Ошибка авторизации SMTP")
        return False, "Неверный логин или пароль SMTP"
    except Exception as exc:
        logger.exception("Не удалось отправить письмо на %s", to_email)
        return False, str(exc)
