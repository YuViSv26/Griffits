import logging
import smtplib
from email.message import EmailMessage

from backend.config import get_settings

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    s = get_settings()
    return bool(s.smtp_host and s.smtp_from and s.smtp_user and s.smtp_password)


def _send_message(msg: EmailMessage) -> tuple[bool, str | None]:
    settings = get_settings()
    if not smtp_configured():
        logger.warning(
            "SMTP не настроен полностью (нужны SMTP_HOST, SMTP_FROM, SMTP_USER, SMTP_PASSWORD)"
        )
        return False, "SMTP не настроен на сервере"

    try:
        if settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
                timeout=30,
                local_hostname="localhost",
            ) as server:
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=30,
                local_hostname="localhost",
            ) as server:
                server.ehlo()
                if server.has_extn("starttls"):
                    server.starttls()
                    server.ehlo()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        return True, None
    except smtplib.SMTPAuthenticationError:
        logger.exception("Ошибка авторизации SMTP для %s", settings.smtp_user)
        return False, "Неверный логин или пароль SMTP"
    except smtplib.SMTPException as exc:
        logger.exception("Ошибка SMTP при отправке")
        return False, str(exc)
    except OSError as exc:
        logger.exception(
            "Сетевая ошибка SMTP (%s:%s)", settings.smtp_host, settings.smtp_port
        )
        return False, f"Не удалось подключиться к SMTP: {exc}"
    except Exception as exc:
        logger.exception("Не удалось отправить письмо")
        return False, str(exc)


def send_password_reset_email(to_email: str, reset_url: str) -> tuple[bool, str | None]:
    """Возвращает (успех, текст ошибки)."""
    settings = get_settings()
    msg = EmailMessage()
    msg["Subject"] = "Сброс пароля — Нейроконсультант Гриффитс"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content(
        f"Здравствуйте!\n\n"
        f"Для сброса пароля перейдите по ссылке (действует 1 час):\n{reset_url}\n\n"
        f"Если вы не запрашивали сброс, проигнорируйте это письмо."
    )
    ok, err = _send_message(msg)
    if ok:
        logger.info("Письмо сброса пароля отправлено на %s", to_email)
    return ok, err


def send_plan_pdf_email(
    to_email: str, baby_name: str, pdf_bytes: bytes
) -> tuple[bool, str | None]:
    """Отправляет PDF-план развития на email пользователя."""
    settings = get_settings()
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in baby_name)
    filename = f"plan-{safe_name}.pdf"

    msg = EmailMessage()
    msg["Subject"] = f"План развития для {baby_name} — Нейроконсультант Гриффитс"
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content(
        f"Здравствуйте!\n\n"
        f"Спасибо за оплату! Во вложении — персональный план развития для "
        f"{baby_name}.\n\n"
        f"В PDF вы найдёте:\n"
        f"• ориентиры по шкале Гриффитс на текущий возраст\n"
        f"• на что обратить внимание\n"
        f"• игры для развития\n"
        f"• рекомендации по занятиям\n\n"
        f"С уважением,\nНейроконсультант Гриффитс"
    )
    msg.add_attachment(
        pdf_bytes,
        maintype="application",
        subtype="pdf",
        filename=filename,
    )

    ok, err = _send_message(msg)
    if ok:
        logger.info("PDF-план отправлен на %s", to_email)
    return ok, err


def send_assessment_results_email(
    to_email: str,
    organization: str,
    baby_name: str,
    age_label: str,
    parent_email: str,
    test_date: str,
    body_text: str,
) -> tuple[bool, str | None]:
    """Отправляет результаты теста в медицинскую организацию."""
    settings = get_settings()
    msg = EmailMessage()
    msg["Subject"] = (
        f"Результат шкалы Гриффитс — {baby_name} ({organization})"
    )
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content(
        f"Здравствуйте!\n\n"
        f"Родитель направил результат тестирования по шкале Гриффитс.\n\n"
        f"{body_text}\n\n"
        f"— Нейроконсультант Гриффитс"
    )

    ok, err = _send_message(msg)
    if ok:
        logger.info(
            "Результаты теста отправлены в %s (%s)", organization, to_email
        )
    return ok, err
