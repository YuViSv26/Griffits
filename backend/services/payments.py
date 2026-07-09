"""Оплата плана PDF через ЮKassa."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import HTTPException

from backend.config import get_settings
from backend.db import (
    PlanPayment,
    User,
    get_plan_payment,
    get_user_by_id,
    mark_plan_payment_emailed,
    save_plan_payment,
    update_plan_payment_status,
)
from backend.schemas.payments import CreatePlanPaymentResponse, PlanPaymentStatusResponse
from backend.services.email import send_plan_pdf_email, smtp_configured
from backend.services.plan_pdf import generate_plan_pdf
from backend.services.today_plan import get_today_plan
from backend.services.yookassa_client import create_redirect_payment, get_payment

logger = logging.getLogger(__name__)

PRODUCT_PLAN_PDF = "plan_pdf"
PAID_STATUSES = {"succeeded", "waiting_for_capture"}


def _yookassa_configured() -> bool:
    s = get_settings()
    return bool(s.yookassa_shop_id and s.yookassa_secret_key)


async def _maybe_send_plan_pdf_email(record: PlanPayment) -> PlanPayment:
    if record.status not in PAID_STATUSES or record.pdf_emailed:
        return record
    if not smtp_configured():
        logger.warning(
            "SMTP не настроен — PDF не отправлен для платежа %s",
            record.yookassa_payment_id,
        )
        return record

    user = await get_user_by_id(record.user_id)
    if not user:
        return record

    try:
        plan = await get_today_plan(user)
        pdf_bytes = generate_plan_pdf(plan)
        ok, err = send_plan_pdf_email(user.email, plan.baby_name, pdf_bytes)
        if ok:
            logger.info(
                "PDF-план отправлен на %s (платёж %s)",
                user.email,
                record.yookassa_payment_id,
            )
            return await mark_plan_payment_emailed(record.yookassa_payment_id)
        logger.error(
            "Не удалось отправить PDF на %s: %s",
            user.email,
            err,
        )
    except Exception:
        logger.exception(
            "Ошибка генерации/отправки PDF для платежа %s",
            record.yookassa_payment_id,
        )
    return record


def _payment_status_response(record: PlanPayment) -> PlanPaymentStatusResponse:
    paid = record.status in PAID_STATUSES
    return PlanPaymentStatusResponse(
        payment_id=record.yookassa_payment_id,
        status=record.status,
        paid=paid,
        can_download=paid,
        amount_rub=record.amount_rub,
        pdf_emailed=record.pdf_emailed,
    )


async def create_plan_pdf_payment(
    user: User, return_tab: str = "test"
) -> CreatePlanPaymentResponse:
    settings = get_settings()
    if not _yookassa_configured():
        raise HTTPException(
            status_code=503,
            detail="ЮKassa не настроена. Укажите YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY в .env",
        )

    amount = settings.plan_pdf_price_rub
    return_url = f"{settings.frontend_url}/?tab={return_tab}&from_payment=1"

    description = f"План развития PDF — {user.baby_name or 'ребёнок'}"

    try:
        yk = await create_redirect_payment(
            shop_id=settings.yookassa_shop_id,
            secret_key=settings.yookassa_secret_key,
            amount_rub=amount,
            return_url=return_url,
            description=description,
            metadata={
                "user_id": str(user.id),
                "product": PRODUCT_PLAN_PDF,
            },
        )
    except Exception as exc:
        logger.exception("YooKassa create payment failed")
        raise HTTPException(
            status_code=502,
            detail="Не удалось создать платёж в ЮKassa. Попробуйте позже.",
        ) from exc

    payment_id = yk["id"]
    confirmation_url = yk["confirmation"]["confirmation_url"]
    status = yk.get("status", "pending")

    await save_plan_payment(
        user_id=user.id,
        yookassa_payment_id=payment_id,
        amount_rub=amount,
        status=status,
        product=PRODUCT_PLAN_PDF,
    )

    return CreatePlanPaymentResponse(
        payment_id=payment_id,
        confirmation_url=confirmation_url,
        amount_rub=amount,
        status=status,
    )


async def _sync_payment_from_yookassa(record: PlanPayment) -> PlanPayment:
    settings = get_settings()
    if not _yookassa_configured():
        return record

    try:
        yk = await get_payment(
            record.yookassa_payment_id,
            shop_id=settings.yookassa_shop_id,
            secret_key=settings.yookassa_secret_key,
        )
    except Exception:
        logger.exception("YooKassa get payment %s failed", record.yookassa_payment_id)
        return record

    new_status = yk.get("status", record.status)
    if new_status != record.status:
        paid_at = datetime.now(timezone.utc) if new_status in PAID_STATUSES else None
        record = await update_plan_payment_status(
            record.yookassa_payment_id, new_status, paid_at=paid_at
        )
    return record


async def get_plan_payment_status(
    user: User, payment_id: str
) -> PlanPaymentStatusResponse:
    record = await get_plan_payment(payment_id)
    if record is None or record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Платёж не найден")

    record = await _sync_payment_from_yookassa(record)
    record = await _maybe_send_plan_pdf_email(record)
    return _payment_status_response(record)


async def mark_plan_pdf_downloaded(user: User, payment_id: str) -> None:
    record = await get_plan_payment(payment_id)
    if record is None or record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Платёж не найден")
    if record.status not in PAID_STATUSES:
        raise HTTPException(status_code=402, detail="Оплата не завершена")

    from backend.db import mark_plan_payment_downloaded

    await mark_plan_payment_downloaded(payment_id)


async def handle_yookassa_webhook(payload: dict) -> None:
    event = payload.get("event")
    obj = payload.get("object") or {}
    payment_id = obj.get("id")
    if not payment_id:
        return

    record = await get_plan_payment(payment_id)
    if record is None:
        logger.warning("Webhook for unknown payment %s", payment_id)
        return

    status = obj.get("status", record.status)
    if event == "payment.succeeded" or status in PAID_STATUSES:
        record = await update_plan_payment_status(
            payment_id,
            status,
            paid_at=datetime.now(timezone.utc),
        )
        await _maybe_send_plan_pdf_email(record)
    elif event == "payment.canceled":
        await update_plan_payment_status(payment_id, "canceled")
