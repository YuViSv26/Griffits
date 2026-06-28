"""Расчёт суммы баллов и возрастного эквивалента по нормам Гриффитс (Кешишян)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.data.assessment_scales import SCALE_BALL_BY_TEXT, SCALE_KEYS, SCALE_NAMES

_DATA = json.loads((Path(__file__).parent / "griffiths_scale.json").read_text(encoding="utf-8"))
TOTAL_NORM_BY_MONTH: list[dict] = _DATA["totalNormByMonth"]
SUBSCALE_NORM_BY_MONTH: dict[str, dict[str, int]] = _DATA["subscaleNormByMonth"]

# normMonth пункта (возрастной эквивалент субшкалы по PDF)
_NORM_MONTH_BY_TEXT: dict[str, dict[str, int]] = {}
for key, items in _DATA["scales"].items():
    _NORM_MONTH_BY_TEXT[key] = {item["text"]: item["normMonth"] for item in items}


def total_norm_for_age(age_months: int) -> dict:
    """Нормативная сумма баллов для хронологического возраста."""
    month = max(1, min(24, age_months if age_months > 0 else 1))
    row = next(r for r in TOTAL_NORM_BY_MONTH if r["month"] == month)
    return {"month": month, "min": row["min"], "max": row["max"]}


def subscale_norm_ball_for_age(scale_key: str, age_months: int) -> int:
    month = max(1, min(24, age_months if age_months > 0 else 1))
    return SUBSCALE_NORM_BY_MONTH[scale_key][str(month)]


def age_equivalent_from_total(total: int) -> int:
    """Месяц жизни по сводной таблице суммы баллов."""
    if total <= 0:
        return 0
    for row in TOTAL_NORM_BY_MONTH:
        if row["min"] <= total <= row["max"]:
            return row["month"]
    if total < TOTAL_NORM_BY_MONTH[0]["min"]:
        return 1
    if total > TOTAL_NORM_BY_MONTH[-1]["max"]:
        return 24
    best_month = 1
    best_dist = float("inf")
    for row in TOTAL_NORM_BY_MONTH:
        mid = (row["min"] + row["max"]) / 2
        dist = abs(total - mid)
        if dist < best_dist:
            best_dist = dist
            best_month = row["month"]
    return best_month


def age_equivalent_from_subscale_ball(scale_key: str, ball: int | None) -> int | None:
    """Возрастной эквивалент субшкалы: месяц, к которому относится достигнутый балл."""
    if not ball or ball <= 0:
        return None
    norms = SUBSCALE_NORM_BY_MONTH[scale_key]
    best = 1
    for m in range(1, 25):
        if norms[str(m)] <= ball:
            best = m
    return best


def compute_griffiths_summary(
    results: dict[str, str | None],
    chronologic_age_months: int,
) -> dict:
    scale_items = []
    total_balls = 0

    for key in SCALE_KEYS:
        skill = results.get(key)
        ball = SCALE_BALL_BY_TEXT.get(key, {}).get(skill) if skill else None
        if ball:
            total_balls += ball
        norm_month = (
            _NORM_MONTH_BY_TEXT.get(key, {}).get(skill)
            if skill
            else None
        )
        age_eq = norm_month if ball else None
        scale_items.append(
            {
                "scale": key,
                "name": SCALE_NAMES[key],
                "skill": skill,
                "ball": ball,
                "age_equivalent_months": age_eq if ball else None,
                "norm_month": norm_month,
            }
        )

    norm_total = total_norm_for_age(chronologic_age_months)
    total_age_eq = age_equivalent_from_total(total_balls)

    return {
        "chronologic_age_months": chronologic_age_months,
        "total_balls": total_balls,
        "total_age_equivalent_months": total_age_eq,
        "norm_total_at_age": norm_total,
        "scales": scale_items,
    }
