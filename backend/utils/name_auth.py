from __future__ import annotations

import re
from datetime import date


def _normalize_part(value: str) -> str:
    return re.sub(r"\s+", "", value.strip())


def first_two_letters(value: str) -> str:
    cleaned = _normalize_part(value)
    if not cleaned:
        return ""
    return cleaned[:2].upper()


def build_login_code(first_name: str, patronymic: str, last_name: str) -> str:
    parts = (
        first_two_letters(first_name),
        first_two_letters(patronymic),
        first_two_letters(last_name),
    )
    code = "".join(parts)
    if len(code) < 2:
        raise ValueError("Укажите имя, отчество и фамилию")
    return code


def parse_login_code_parts(login_code: str) -> tuple[str, str, str]:
    code = login_code.strip().upper()
    return code[0:2], code[2:4], code[4:6]


def build_display_name(first_name: str, patronymic: str, last_name: str) -> str:
    return " ".join(
        part.strip()
        for part in (first_name, patronymic, last_name)
        if part.strip()
    )


def parse_birth_date(day: int, month: int, year: int) -> date:
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise ValueError("Некорректная дата рождения") from exc
