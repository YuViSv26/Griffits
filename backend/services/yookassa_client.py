"""Клиент API ЮKassa (v3)."""

from __future__ import annotations

import base64
import uuid
from typing import Any

import httpx

YOOKASSA_API = "https://api.yookassa.ru/v3"


def _auth_header(shop_id: str, secret_key: str) -> str:
    token = base64.b64encode(f"{shop_id}:{secret_key}".encode()).decode()
    return f"Basic {token}"


async def create_redirect_payment(
    *,
    shop_id: str,
    secret_key: str,
    amount_rub: int,
    return_url: str,
    description: str,
    metadata: dict[str, str],
) -> dict[str, Any]:
    headers = {
        "Authorization": _auth_header(shop_id, secret_key),
        "Idempotence-Key": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    body = {
        "amount": {"value": f"{amount_rub:.2f}", "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": return_url},
        "capture": True,
        "description": description,
        "metadata": metadata,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{YOOKASSA_API}/payments", json=body, headers=headers
        )
        response.raise_for_status()
        return response.json()


async def get_payment(
    payment_id: str, *, shop_id: str, secret_key: str
) -> dict[str, Any]:
    headers = {"Authorization": _auth_header(shop_id, secret_key)}
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{YOOKASSA_API}/payments/{payment_id}", headers=headers
        )
        response.raise_for_status()
        return response.json()
