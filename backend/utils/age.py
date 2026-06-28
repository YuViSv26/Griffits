from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from dateutil.relativedelta import relativedelta


class AgeValidationError(ValueError):
    """Ошибка валидации даты рождения."""


@dataclass(frozen=True)
class AgeResult:
    total_months: int
    extra_days: int
    label: str
    warning: str | None = None


def parse_birthday(text: str) -> date:
    """Парсит ISO (YYYY-MM-DD), ДД.ММ.ГГГГ или ДД.ММ.ГГ."""
    text = text.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise AgeValidationError(
        "Неверный формат даты. Используйте ГГГГ-ММ-ДД или ДД.ММ.ГГГГ"
    )


def calculate_age(birthday: date, today: date | None = None) -> AgeResult:
    today = today or date.today()

    if birthday > today:
        raise AgeValidationError("Дата рождения не может быть в будущем.")

    delta = relativedelta(today, birthday)
    total_months = delta.years * 12 + delta.months
    extra_days = delta.days
    label = f"{total_months} мес. {extra_days} дн."

    warning = None
    if total_months > 24:
        warning = (
            "Возраст ребёнка больше 24 месяцев — сервис ориентирован на 0–2 года, "
            "но вы всё равно можете пользоваться рекомендациями."
        )

    return AgeResult(
        total_months=total_months,
        extra_days=extra_days,
        label=label,
        warning=warning,
    )
