import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.deps import get_current_user
from backend.db import User
from backend.schemas.payments import (
    CreatePlanPaymentRequest,
    CreatePlanPaymentResponse,
    PlanPaymentStatusResponse,
)
from backend.db import get_latest_plan_payment
from backend.services.payments import (
    _maybe_send_plan_pdf_email,
    _sync_payment_from_yookassa,
    create_plan_pdf_payment,
    get_plan_payment_status,
    handle_yookassa_webhook,
    mark_plan_pdf_downloaded,
)
from backend.services.profile import is_profile_complete

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["payments"])


def _require_profile(user: User) -> None:
    if not is_profile_complete(user):
        raise HTTPException(
            status_code=400,
            detail="Сначала заполните профиль ребёнка",
        )


@router.post("/plan-pdf/create", response_model=CreatePlanPaymentResponse)
async def create_plan_payment(
    body: CreatePlanPaymentRequest | None = None,
    user: User = Depends(get_current_user),
) -> CreatePlanPaymentResponse:
    _require_profile(user)
    return_tab = body.return_tab if body else "test"
    return await create_plan_pdf_payment(user, return_tab=return_tab)


@router.get("/plan-pdf/{payment_id}", response_model=PlanPaymentStatusResponse)
async def plan_payment_status(
    payment_id: str,
    user: User = Depends(get_current_user),
) -> PlanPaymentStatusResponse:
    _require_profile(user)
    return await get_plan_payment_status(user, payment_id)


@router.get("/plan-pdf/latest/status", response_model=PlanPaymentStatusResponse)
async def latest_plan_payment_status(
    user: User = Depends(get_current_user),
) -> PlanPaymentStatusResponse:
    """Статус последнего платежа (после возврата с ЮKassa)."""
    _require_profile(user)
    record = await get_latest_plan_payment(user.id)
    if record is None:
        raise HTTPException(status_code=404, detail="Платежей пока нет")
    record = await _sync_payment_from_yookassa(record)
    record = await _maybe_send_plan_pdf_email(record)
    return await get_plan_payment_status(user, record.yookassa_payment_id)


@router.post("/plan-pdf/{payment_id}/downloaded")
async def plan_pdf_downloaded(
    payment_id: str,
    user: User = Depends(get_current_user),
) -> dict:
    _require_profile(user)
    await mark_plan_pdf_downloaded(user, payment_id)
    return {"ok": True}


@router.post("/yookassa/webhook")
async def yookassa_webhook(request: Request) -> dict:
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc
    logger.info("YooKassa webhook: %s", payload.get("event"))
    await handle_yookassa_webhook(payload)
    return {"ok": True}
