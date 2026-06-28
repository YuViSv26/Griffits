from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from backend.config import get_settings
from backend.constants import SUBSCALE_NAMES
from backend.db import (
    User,
    get_chat_history,
    get_latest_assessment,
    save_chat_message,
)
from backend.services.profile import is_profile_complete
from backend.utils.age import calculate_age

logger = logging.getLogger(__name__)


def format_nordrouter_error(exc: Exception) -> str:
    text = str(exc)
    if "401" in text or "Invalid API key" in text:
        return (
            "Неверный API-ключ NordRouter. Проверьте NORDROUTER_API_KEY в .env "
            "(кабинет → Доступ) и перезапустите backend."
        )
    if "402" in text or "balance" in text.lower():
        return (
            "Закончился баланс NordRouter. Пополните в кабинете "
            "https://nordrouter.com и перезапустите backend."
        )
    return "Ошибка NordRouter. Попробуйте позже или проверьте ключ и баланс в кабинете."


def _build_system_prompt(user: User) -> str:
    base = (
        "Ты — нейроконсультант для родителей младенцев 0–2 лет. "
        "Ты опираешься на Шкалу психомоторного развития Гриффитс "
        "(субшкалы A–E: двигательная, социальная, речь, зрительно-моторная, игра). "
        "Отвечай на русском, дружелюбно и по делу. "
        "Не ставь медицинских диагнозов. При тревожных симптомах рекомендуй педиатра."
    )

    if not is_profile_complete(user):
        return base + " Профиль ребёнка ещё не заполнен — попроси указать имя и дату рождения в настройках."

    age = calculate_age(user.baby_birthday)
    parts = [
        base,
        f"Ребёнок: {user.baby_name}, возраст {age.label}.",
    ]

    return "\n".join(parts)


async def _get_client() -> AsyncOpenAI:
    settings = get_settings()
    if not settings.nordrouter_api_key:
        raise RuntimeError("NORDROUTER_API_KEY не задан")
    return AsyncOpenAI(
        base_url=settings.nordrouter_base_url,
        api_key=settings.nordrouter_api_key,
    )


async def build_messages(user: User, user_message: str) -> list[dict[str, str]]:
    history = await get_chat_history(user.id, limit=20)
    messages: list[dict[str, str]] = [
        {"role": "system", "content": _build_system_prompt(user)}
    ]

    assessment = await get_latest_assessment(user.id)
    if assessment and is_profile_complete(user):
        score_map = {
            "A": assessment.score_a,
            "B": assessment.score_b,
            "C": assessment.score_c,
            "D": assessment.score_d,
            "E": assessment.score_e,
        }
        scores_text = ", ".join(
            f"{SUBSCALE_NAMES[k]}: {score_map[k]}%" for k in "ABCDE"
        )
        messages.append(
            {
                "role": "system",
                "content": f"Последние результаты теста Griffiths: {scores_text}",
            }
        )

    for msg in history:
        if msg.role in ("user", "assistant"):
            messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": user_message})
    return messages


async def chat_stream(user: User, user_message: str) -> AsyncGenerator[str, None]:
    settings = get_settings()
    client = await _get_client()
    messages = await build_messages(user, user_message)

    await save_chat_message(user.id, "user", user_message)

    full_response: list[str] = []

    try:
        stream = await client.chat.completions.create(
            model=settings.nordrouter_model,
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=1024,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                full_response.append(delta)
                yield f"data: {json.dumps({'content': delta}, ensure_ascii=False)}\n\n"

        assistant_text = "".join(full_response)
        if assistant_text:
            await save_chat_message(user.id, "assistant", assistant_text)

        yield "data: [DONE]\n\n"

    except Exception as exc:
        logger.exception("NordRouter stream error")
        yield f"data: {json.dumps({'error': format_nordrouter_error(exc)}, ensure_ascii=False)}\n\n"


async def chat_complete(user: User, user_message: str) -> str:
    settings = get_settings()
    client = await _get_client()
    messages = await build_messages(user, user_message)

    await save_chat_message(user.id, "user", user_message)

    try:
        response = await client.chat.completions.create(
            model=settings.nordrouter_model,
            messages=messages,
            stream=False,
            temperature=0.7,
            max_tokens=1024,
        )
    except Exception as exc:
        logger.exception("NordRouter error")
        raise RuntimeError(format_nordrouter_error(exc)) from exc

    content = response.choices[0].message.content or ""
    if content:
        await save_chat_message(user.id, "assistant", content)
    return content
